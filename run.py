#!/usr/bin/env python3
# 主入口程序
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    IPTV_SOURCES, OUTPUT_DIR, ENABLE_REGION_FILTER,
    PREFERRED_LOCATION, PREFERRED_ISP, ENABLE_IP_RESOLVE
)
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_all
from src.generator import generate_outputs
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region
from src.cache_manager import CacheManager

def init_ip_resolver():
    if not ENABLE_IP_RESOLVE:
        print("⚙️ IP解析未启用")
        return
    resolver = get_resolver()
    if resolver.is_available:
        print("✅ IP解析器已就绪")
    else:
        print("⚠️ IP解析器不可用，将跳过地域筛选")

def filter_by_region(channels):
    if not ENABLE_REGION_FILTER:
        return channels

    preferred_locations = [loc.strip() for loc in PREFERRED_LOCATION.split(",") if loc.strip()]
    preferred_isps = [isp.strip() for isp in PREFERRED_ISP.split(",") if isp.strip()]

    if not preferred_locations and not preferred_isps:
        return channels

    print(f"🎯 地域筛选: 地域={preferred_locations}, 运营商={preferred_isps}")

    resolver = get_resolver()
    if not resolver.is_available:
        print("⚠️ IP解析器不可用，跳过地域筛选")
        return channels

    filtered = []
    for ch in channels:
        ip_info = ch.get("ip_info") if isinstance(ch, dict) else getattr(ch, 'ip_info', None)
        if ip_info and matches_region(ip_info, preferred_locations, preferred_isps):
            filtered.append(ch)
    print(f"  筛选结果: {len(filtered)}/{len(channels)} 个频道通过地域筛选")
    return filtered

async def main():
    print("🚀 IPTV智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")

    init_ip_resolver()

    # 预检 ffprobe（如果启用）
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        from src.ffmpeg_validator import check_ffprobe
        await check_ffprobe()

    # 初始化缓存管理器
    cache = CacheManager()

    # ========== 阶段1：尝试从缓存加载 ==========
    if cache.should_update():
        print("\n📥 执行完整采集流程...")

        # 1. 拉取所有源
        print("📥 正在拉取源文件...")
        raw_contents = await fetch_all_sources(IPTV_SOURCES)

        # 2. 解析与去重
        print("🔧 解析并去重...")
        channels_dict = parse_and_dedupe(raw_contents)
        if not channels_dict:
            print("❌ 未获取到任何频道，请检查网络或源地址")
            sys.exit(1)

        # 3. 转换字典为列表
        channels_list = list(channels_dict.values())

        # 4. 轻量级测速（同时解析IP）
        valid_channels = await test_channels_concurrent(channels_dict)
        if not valid_channels:
            print("❌ 无有效频道通过测速")
            sys.exit(1)

        # 5. 深度验证（ffmpeg）
        valid_channels = await validate_with_ffmpeg_batch(valid_channels)
        if not valid_channels:
            print("❌ 深度验证后无有效频道")
            sys.exit(1)

        # 6. 合并多源频道
        print("🔄 正在合并多源频道...")
        merged_channels = merge_channels_by_name(valid_channels)

        # 7. 地域筛选
        merged_channels = filter_by_region(merged_channels)
        if not merged_channels:
            print("❌ 地域筛选后无有效频道")
            sys.exit(1)

        # 8. 保存到缓存
        cache.save_to_cache(merged_channels)

        final_channels = merged_channels
    else:
        # 从缓存加载
        print("\n📦 使用缓存数据...")
        cached_channels = cache.load_from_cache()
        if not cached_channels:
            print("⚠️ 缓存无数据，执行完整采集...")
            # 强制重新采集
            return await main()
        final_channels = cached_channels

    # ========== 阶段2：分类与输出 ==========
    print("📁 执行智能分类...")
    classified = classify_all(final_channels)

    # 生成输出文件
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")
    print(f"📊 缓存有效期剩余: {cache.get_cache_age() // 3600} 小时")

if __name__ == "__main__":
    asyncio.run(main())
