#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    IPTV_SOURCES, OUTPUT_DIR, ENABLE_REGION_FILTER,
    PREFERRED_LOCATION, PREFERRED_ISP, ENABLE_IP_RESOLVE,
    ENABLE_DEMO_FILTER, ENABLE_ALIAS, ENABLE_BLACKLIST
)
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_channel   # 只用于获取分类标签
from src.generator import generate_outputs
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region
from src.cache_manager import CacheManager
from src.blacklist_filter import get_blacklist_filter
from src.demo_filter import filter_and_order_by_demo

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

def build_classified_from_ordered(ordered_channels):
    """
    根据有序频道列表构建分类字典，保持每个分类内频道的原始顺序
    ordered_channels 中的元素可能是字典或对象
    """
    classified = {}
    for ch in ordered_channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        # 统一转换为字典格式
        if isinstance(ch, dict):
            ch_dict = ch
        elif hasattr(ch, 'to_dict'):
            ch_dict = ch.to_dict()
        else:
            # 对象转字典
            ch_dict = {
                "name": getattr(ch, 'name', ''),
                "urls": getattr(ch, 'urls', [getattr(ch, 'url', '')]),
                "url": getattr(ch, 'url', ''),
                "group_title": getattr(ch, 'group_title', ''),
                "id": getattr(ch, 'tvg_id', ''),
                "logo": getattr(ch, 'tvg_logo', ''),
                "latency": getattr(ch, 'latency', 9999),
                "video_codec": getattr(ch, 'video_codec', ''),
                "ip_info": getattr(ch, 'ip_info', None)
            }
        classified[cat].append(ch_dict)
    print("📊 分类统计（按 demo 顺序）：")
    for cat, lst in classified.items():
        if lst:
            print(f"  {cat}: {len(lst)} 个频道")
    return classified

async def main():
    print("🚀 IPTV智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")
    print(f"📋 增强过滤: demo={ENABLE_DEMO_FILTER}, alias={ENABLE_ALIAS}, blacklist={ENABLE_BLACKLIST}")

    init_ip_resolver()
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        from src.ffmpeg_validator import check_ffprobe
        await check_ffprobe()

    cache = CacheManager()
    if cache.should_update():
        print("\n📥 执行完整采集流程...")
        print("📥 正在拉取源文件...")
        raw_contents = await fetch_all_sources(IPTV_SOURCES)
        print("🔧 解析并去重...")
        channels_dict = parse_and_dedupe(raw_contents)
        if not channels_dict:
            print("❌ 未获取到任何频道，请检查网络或源地址")
            return 1
        valid_channels = await test_channels_concurrent(channels_dict)
        if not valid_channels:
            print("❌ 无有效频道通过测速")
            return 1
        valid_channels = await validate_with_ffmpeg_batch(valid_channels)
        if not valid_channels:
            print("❌ 深度验证后无有效频道")
            return 1
        print("🔄 正在合并多源频道...")
        merged_channels = merge_channels_by_name(valid_channels)

        # 黑名单过滤
        if ENABLE_BLACKLIST:
            blacklist_filter = get_blacklist_filter()
            merged_channels = blacklist_filter.filter_channels(merged_channels)

        # Demo 筛选与排序
        if ENABLE_DEMO_FILTER:
            merged_channels = filter_and_order_by_demo(merged_channels)
        else:
            merged_channels.sort(key=lambda x: x.get('name') if isinstance(x, dict) else x.name)

        # 地域筛选
        merged_channels = filter_by_region(merged_channels)

        if not merged_channels:
            print("❌ 过滤后无有效频道")
            return 1
        cache.save_to_cache(merged_channels)
        final_channels = merged_channels
    else:
        print("\n📦 使用缓存数据...")
        cached_records = cache.load_from_cache()
        if not cached_records:
            print("⚠️ 缓存无数据，执行完整采集...")
            return await main()
        # 将缓存记录重新组织为频道对象（按名称合并）
        class SimpleChannel:
            def __init__(self, data):
                self.name = data['name']
                self.url = data['url']
                self.latency = data.get('latency', 9999)
                self.video_codec = data.get('video_codec', '')
                self.group_title = data.get('group_title', '')
                self.tvg_id = data.get('id', '')
                self.tvg_logo = data.get('logo', '')
                self.ip_info = data.get('ip_info')
        simple_channels = [SimpleChannel(rec) for rec in cached_records]
        merged_channels = merge_channels_by_name(simple_channels)
        if ENABLE_DEMO_FILTER:
            final_channels = filter_and_order_by_demo(merged_channels)
        else:
            final_channels = merged_channels

    classified = build_classified_from_ordered(final_channels)
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")
    print(f"📊 缓存有效期剩余: {cache.get_cache_age() // 3600} 小时")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)
