#!/usr/bin/env python3
# 主入口程序
import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    IPTV_SOURCES, OUTPUT_DIR,
    ENABLE_REGION_FILTER, PREFERRED_LOCATION, PREFERRED_ISP,
    ENABLE_IP_RESOLVE
)
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch, check_ffprobe
from src.classifier import classify_all
from src.generator import generate_outputs
from src.demo_filter import filter_and_reorder
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region


def init_ip_resolver():
    """初始化 IP 解析器"""
    if not ENABLE_IP_RESOLVE:
        print("⚙️ IP 解析未启用")
        return
    resolver = get_resolver()
    if resolver.is_available:
        print("✅ IP 解析器已就绪")
    else:
        print("⚠️ IP 解析器不可用，将跳过地域筛选")


def filter_by_region(channels: list) -> list:
    """
    按优选地域和运营商筛选频道
    支持 MergedChannel 对象（使用最佳源的 IP 信息）
    """
    if not ENABLE_REGION_FILTER:
        return channels

    preferred_locations = [loc.strip() for loc in PREFERRED_LOCATION.split(",") if loc.strip()]
    preferred_isps = [isp.strip() for isp in PREFERRED_ISP.split(",") if isp.strip()]

    if not preferred_locations and not preferred_isps:
        return channels

    print(f"🎯 地域筛选: 地域={preferred_locations}, 运营商={preferred_isps}")

    resolver = get_resolver()
    if not resolver.is_available:
        print("⚠️ IP 解析器不可用，跳过地域筛选")
        return channels

    filtered = []
    for ch in channels:
        # 尝试获取 IP 信息（MergedChannel 可能没有 ip_info，需要重新解析第一个 URL）
        ip_info = getattr(ch, 'ip_info', None)
        if not ip_info and hasattr(ch, 'urls') and ch.urls:
            # 为合并后的频道解析第一个 URL 的 IP
            ip_info = resolver.resolve_channel_ip(ch)  # 需要传入一个具有 .url 属性的对象
            # 临时构造一个简单对象
            class TempChannel:
                def __init__(self, url):
                    self.url = url
            temp = TempChannel(ch.urls[0])
            ip_info = resolver.resolve_channel_ip(temp)
            if ip_info:
                ch.ip_info = ip_info

        if ip_info and matches_region(ip_info, preferred_locations, preferred_isps):
            filtered.append(ch)
        elif not ip_info and not ENABLE_REGION_FILTER:
            # 严格模式下，没有 IP 信息的频道也保留
            filtered.append(ch)

    print(f"  筛选结果: {len(filtered)}/{len(channels)} 个频道通过地域筛选")
    return filtered


async def main():
    print("🚀 IPTV 智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")

    # 初始化 IP 解析器
    init_ip_resolver()

    # 预检 ffprobe（如果启用）
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

    # 4. 深度验证（ffmpeg）
    valid_channels = await validate_with_ffmpeg_batch(valid_channels)

    if not valid_channels:
        print("❌ 深度验证后无有效频道")
        sys.exit(1)

    # 5. 合并多源频道（将同一频道的多个源合并为一个 MergedChannel）
    print("🔄 正在合并多源频道...")
    valid_channels = merge_channels_by_name(valid_channels)

    # 6. 按地域筛选（可选）
    valid_channels = filter_by_region(valid_channels)

    if not valid_channels:
        print("❌ 地域筛选后无有效频道")
        sys.exit(1)

    # 7. 智能分类
    print("📁 执行智能分类...")
    classified = classify_all(valid_channels)

    # 8. 按 demo.txt 过滤和重排（需要 demo_filter 支持 MergedChannel 对象）
    print("🎯 根据 demo.txt 过滤频道并重排顺序...")
    classified = filter_and_reorder(classified)

    # 9. 生成输出文件
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")


if __name__ == "__main__":
    asyncio.run(main())
