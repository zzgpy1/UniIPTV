# 轻量级 HTTP 头探测（快速测速）
import asyncio
import aiohttp
import time
from src.config import HEADERS, TIMEOUT, MAX_WORKERS

async def probe_channel(session, channel):
    """异步探测单个频道，返回 (channel, latency_ms, success)"""
    url = channel.url
    try:
        start = time.time()
        async with session.head(url, timeout=TIMEOUT, allow_redirects=True, headers=HEADERS) as resp:
            latency = int((time.time() - start) * 1000)
            if resp.status == 200:
                return channel, latency, True
            else:
                return channel, latency, False
    except Exception:
        return channel, 0, False

async def test_channels_concurrent(channels_dict: dict) -> list:
    """并发测速，返回有效的频道列表（按延迟排序）"""
    channels = list(channels_dict.values())
    print(f"⚡ 开始测速，共 {len(channels)} 个频道，并发数 {MAX_WORKERS}...")
    
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    
    async def bounded_probe(session, ch):
        async with semaphore:
            return await probe_channel(session, ch)
    
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_probe(session, ch) for ch in channels]
        results = await asyncio.gather(*tasks)
    
    valid = []
    for ch, latency, ok in results:
        if ok:
            ch.latency = latency  # 附加延迟属性
            valid.append(ch)
    
    # 按延迟排序（升序）
    valid.sort(key=lambda x: getattr(x, 'latency', 9999))
    print(f"✅ 测速完成，有效频道 {len(valid)}/{len(channels)}")
    return valid
