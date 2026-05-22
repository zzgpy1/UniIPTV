# 源拉取模块（支持并行 + 重试）
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import HEADERS, TIMEOUT, RETRY_MAX_ATTEMPTS, RETRY_BACKOFF_FACTOR, RETRY_MAX_WAIT, ENABLE_RETRY

class FetchError(Exception):
    pass

async def fetch_url(session, url: str) -> str:
    """异步拉取单个 URL 内容，带重试（可选）"""
    async def _fetch():
        try:
            async with session.get(url, timeout=TIMEOUT, headers=HEADERS) as resp:
                if resp.status != 200:
                    raise FetchError(f"HTTP {resp.status}")
                return await resp.text()
        except Exception as e:
            raise FetchError(str(e))

    if ENABLE_RETRY:
        # 使用 tenacity 指数退避重试
        retry_decorator = retry(
            stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=RETRY_BACKOFF_FACTOR, max=RETRY_MAX_WAIT),
            retry=retry_if_exception_type(FetchError),
            reraise=True
        )
        wrapped = retry_decorator(_fetch)
        return await wrapped
    else:
        return await _fetch()

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
