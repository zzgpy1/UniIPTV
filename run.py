#!/usr/bin/env python3
# 主入口程序
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import IPTV_SOURCES, OUTPUT_DIR, ENABLE_IP_RESOLVE
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch, check_ffprobe
from src.merger import merge_channels_by_name
from src.classifier import classify_all
from src.generator import generate_outputs
from src.ip_resolver import get_resolver

def init_ip_resolver():
    """初始化 IP 解析器（可选）"""
    if not ENABLE_IP_RESOLVE:
        print("⚙️ IP 解析未启用")
        return
    resolver = get_resolver()
    if resolver.is_available:
        print("✅ IP 解析器已就绪")
    else:
        print("⚠️ IP 解析器不可用，将跳过地域筛选")

async def main():
    print("🚀 IPTV 智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")

    init_ip_resolver()

    # 预检 ffprobe
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        await check_ffprobe()

    # 1. 拉取所有源
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

    # 4. 深度验证（ffmpeg）并附加编码信息
    valid_channels = await validate_with_ffmpeg_batch(valid_channels)

    if not valid_channels:
        print("❌ 深度验证后无有效频道")
        sys.exit(1)

    # 5. 合并多源（同一个频道保留最多5个最优源）
    print("🔄 正在合并多源频道...")
    valid_channels = merge_channels_by_name(valid_channels)

    if not valid_channels:
        print("❌ 合并后无有效频道")
        sys.exit(1)

    # 6. 智能分类（自动剔除旅游/春晚频道）
    print("📁 执行智能分类...")
    classified = classify_all(valid_channels)

    # 7. 生成输出文件
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！最终输出频道总数: {total}")

if __name__ == "__main__":
    asyncio.run(main())
