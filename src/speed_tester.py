# src/speed_tester.py
# 轻量级 HTTP 头探测（快速测速），集成 IP 解析

import asyncio
import aiohttp
import time
from src.config import HEADERS, TIMEOUT, MAX_WORKERS, ENABLE_IP_RESOLVE
from src.ip_resolver import get_resolver
from src.database import get_db_cache, channel_key
from src.config import DATABASE_ENABLE

async def probe_channel(session, channel):
    """异步探测单个频道，支持测速结果缓存"""
    url = channel.url
    
    # 1. 检查测速缓存
    if DATABASE_ENABLE:
        db = await get_db_cache()
        ch_key = channel_key(channel.name, url)
        cached = await db.get_speed_result(ch_key)
        if cached:
            print(f"📦 使用测速缓存: {channel.name}")
            channel.latency = cached["latency"]
            channel.video_codec = cached["video_codec"]
            if cached["ip_info"]:
                channel.ip_info = cached["ip_info"]
            return channel, cached["latency"], True, cached["ip_info"]
    
    # 2. 缓存未命中，执行实际测速
    try:
        start = time.time()
        async with session.head(url, timeout=TIMEOUT, allow_redirects=True, headers=HEADERS) as resp:
            latency = int((time.time() - start) * 1000)
            if resp.status == 200:
                # 解析 IP 归属地
                ip_info = None
                if ENABLE_IP_RESOLVE:
                    resolver = get_resolver()
                    if resolver.is_available:
                        ip_info = resolver.resolve_channel_ip(channel)
                
                # 3. 保存到缓存
                if DATABASE_ENABLE:
                    db = await get_db_cache()
                    await db.set_speed_result(ch_key, {
                        "name": channel.name,
                        "url": url,
                        "latency": latency,
                        "video_codec": getattr(channel, 'video_codec', ''),
                        "ip_info": ip_info
                    })
                
                return channel, latency, True, ip_info
            else:
                return channel, latency, False, None
    except Exception:
        return channel, 0, False, None

async def test_channels_concurrent(channels_dict: dict) -> list:
    """并发测速，返回有效的频道列表（按延迟排序），附带 IP 信息"""
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
    for ch, latency, ok, ip_info in results:
        if ok:
            ch.latency = latency
            if ip_info:
                ch.ip_info = ip_info
            valid.append(ch)
    
    # 按延迟排序（升序）
    valid.sort(key=lambda x: x.latency)
    print(f"✅ 测速完成，有效频道 {len(valid)}/{len(channels)}")
    return valid
