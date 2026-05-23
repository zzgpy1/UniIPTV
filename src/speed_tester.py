# 轻量级 HTTP 头探测（快速测速，增加 IP 解析）
import asyncio
import aiohttp
import time
from src.config import HEADERS, TIMEOUT, MAX_WORKERS, ENABLE_IP_RESOLVE
from src.ip_resolver import get_resolver

async def probe_channel(session, channel):
    """异步探测单个频道"""
    url = channel.url
    try:
        start = time.time()
        async with session.head(url, timeout=TIMEOUT, allow_redirects=True, headers=HEADERS) as resp:
            latency = int((time.time() - start) * 1000)
            if resp.status == 200:
                ip_info = None
                if ENABLE_IP_RESOLVE:
                    resolver = get_resolver()
                    if resolver.is_available:
                        ip_info = resolver.resolve_channel_ip(channel)
                return channel, latency, True, ip_info
            else:
                return channel, latency, False, None
    except Exception:
        return channel, 0, False, None

async def test_channels_concurrent(channels_dict: dict) -> list:
    """并发测速，返回有效的频道列表（按延迟排序）"""
    channels = list(channels_dict.values())
    print(f"⚡ 开始测速，共 {len(channels)} 个频道，并发数 {MAX_WORKERS}...")
    
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    
    async def bounded_probe(session, ch):
        async with semaphore:
            return await probe_channel(session, ch)
    
    # 创建带超时的 ClientSession
    connector = aiohttp.TCPConnector(limit=MAX_WORKERS, limit_per_host=5)
    timeout_config = aiohttp.ClientTimeout(total=TIMEOUT + 5)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
        tasks = [bounded_probe(session, ch) for ch in channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid = []
    for res in results:
        if isinstance(res, Exception):
            continue
        ch, latency, ok, ip_info = res
        if ok:
            ch.latency = latency
            if ip_info:
                ch.ip_info = ip_info
            else:
                ch.ip_info = None
            valid.append(ch)
    
    valid.sort(key=lambda x: getattr(x, 'latency', 9999))
    print(f"✅ 测速完成，有效频道 {len(valid)}/{len(channels)}")
    return valid
