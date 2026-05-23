# 源拉取模块（支持并行 + 手动重试）
import asyncio
import aiohttp
import time
from src.config import HEADERS, TIMEOUT, RETRY_MAX_ATTEMPTS, RETRY_BACKOFF_FACTOR, RETRY_MAX_WAIT, ENABLE_RETRY
from src.database import get_db_cache
from src.config import DATABASE_ENABLE

class FetchError(Exception):
    pass

async def fetch_url(session, url: str) -> str:
    """异步拉取单个 URL 内容，支持缓存读取和保存"""
    
    # 1. 尝试从缓存读取
    if DATABASE_ENABLE:
        db = await get_db_cache()
        cached_content = await db.get_raw_source(url)
        if cached_content is not None:
            print(f"📦 使用缓存: {url}")
            return cached_content
    
    # 2. 缓存未命中，执行实际拉取
    attempt = 0
    last_exception = None

    async def _fetch():
        async with session.get(url, timeout=TIMEOUT, headers=HEADERS) as resp:
            if resp.status != 200:
                raise FetchError(f"HTTP {resp.status}")
            return await resp.text()

    while True:
        attempt += 1
        try:
            content = await _fetch()
            
            # 3. 保存到缓存
            if DATABASE_ENABLE:
                db = await get_db_cache()
                await db.set_raw_source(url, content)
            
            return content
        except Exception as e:
            last_exception = e
            if not ENABLE_RETRY or attempt >= RETRY_MAX_ATTEMPTS:
                raise FetchError(str(e))
            wait_time = min(RETRY_BACKOFF_FACTOR ** (attempt - 1), RETRY_MAX_WAIT)
            print(f"  重试 {url} ({attempt}/{RETRY_MAX_ATTEMPTS})，等待 {wait_time}s")
            await asyncio.sleep(wait_time)

async def fetch_all_sources(sources: list) -> dict:
    """并行拉取所有源，返回 {url: content} 字典"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = {}
        for url, res in zip(sources, results):
            if isinstance(res, Exception):
                print(f"⚠️ 拉取失败 {url}: {res}")
                output[url] = None
            else:
                output[url] = res
        return output
