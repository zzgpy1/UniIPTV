#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import IPTV_SOURCES, OUTPUT_DIR, ENABLE_IP_RESOLVE
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch, check_ffprobe
from src.classifier import classify_all
from src.generator import generate_outputs
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region
from src.database import IPTVDatabase

def init_ip_resolver():
    if not ENABLE_IP_RESOLVE:
        print("⚙️ IP 解析未启用")
        return
    resolver = get_resolver()
    if resolver.is_available:
        print("✅ IP 解析器已就绪")
    else:
        print("⚠️ IP 解析器不可用")

async def main():
    print("🚀 IPTV 智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")

    init_ip_resolver()
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        await check_ffprobe()

    # 初始化数据库
    db = IPTVDatabase()
    last_check = db.get_last_check_time()
    if last_check:
        print(f"📦 数据库缓存存在，上次检测时间: {last_check}")

    # 1. 拉取所有源（可能需要考虑是否跳过，但为了检测新增源，每次都拉取）
    print("📥 正在拉取源文件...")
    raw_contents = await fetch_all_sources(IPTV_SOURCES)

    # 2. 解析与去重
    print("🔧 解析并去重...")
    channels_dict = parse_and_dedupe(raw_contents)
    if not channels_dict:
        print("❌ 未获取到任何频道，请检查网络或源地址")
        sys.exit(1)

    # 3. 轻量级测速（同时解析 IP）
    valid_channels = await test_channels_concurrent(channels_dict)
    if not valid_channels:
        print("❌ 无有效频道通过测速，请检查网络或增加超时时间")
        sys.exit(1)

    # 4. 深度验证（ffmpeg）并保存到数据库
    valid_channels = await validate_with_ffmpeg_batch(valid_channels)
    if not valid_channels:
        print("❌ 深度验证后无有效频道")
        sys.exit(1)

    # 保存所有有效频道到数据库
    for ch in valid_channels:
        ip_info = getattr(ch, 'ip_info', None) or {}
        db.save_channel({
            'name': ch.name,
            'url': ch.url,
            'latency': getattr(ch, 'latency', 0),
            'province': ip_info.get('province', ''),
            'city': ip_info.get('city', ''),
            'isp': ip_info.get('isp', ''),
            'video_codec': getattr(ch, 'video_codec', ''),
            'group_title': getattr(ch, 'group_title', ''),
            'tvg_id': getattr(ch, 'tvg_id', ''),
            'tvg_logo': getattr(ch, 'tvg_logo', ''),
            'is_valid': True
        })

    # 5. 合并多源频道（同名合并，保留最优5个）
    print("🔄 正在合并多源频道...")
    merged_channels = merge_channels_by_name(valid_channels)

    # 6. 智能分类
    print("📁 执行智能分类...")
    classified = classify_all(merged_channels)

    # 7. 生成输出文件
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")

if __name__ == "__main__":
    asyncio.run(main())
