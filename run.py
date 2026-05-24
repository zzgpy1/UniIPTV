#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    IPTV_SOURCES, OUTPUT_DIR, ENABLE_REGION_FILTER,
    PREFERRED_LOCATION, PREFERRED_ISP, ENABLE_IP_RESOLVE,
    ENABLE_DEMO_FILTER, ENABLE_ALIAS, ENABLE_BLACKLIST,
    CCTV_ORDER
)
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_channel
from src.generator import generate_outputs
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region
from src.cache_manager import CacheManager
from src.blacklist_filter import get_blacklist_filter
from src.demo_filter import filter_and_order_by_demo
from src.alias_matcher import get_alias_matcher

ALLOWED_CATEGORIES = {"央视", "卫视", "地方", "港澳台"}

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

def build_classified_from_ordered(ordered_channels, alias_matcher=None):
    temp = {cat: [] for cat in ALLOWED_CATEGORIES}
    for ch in ordered_channels:
        # 获取原始名称
        if hasattr(ch, 'name'):
            orig_name = ch.name
        elif isinstance(ch, dict):
            orig_name = ch.get('name', '')
        else:
            continue
        # 别名映射
        if alias_matcher:
            mapped_name = alias_matcher.match(orig_name)
            if mapped_name:
                if hasattr(ch, 'name'):
                    ch.name = mapped_name
                elif isinstance(ch, dict):
                    ch['name'] = mapped_name
        cat = classify_channel(ch)
        if cat in ["🌊港·澳·台", "港澳台"]:
            cat = "港澳台"
        if cat not in ALLOWED_CATEGORIES:
            continue
        # 转换为字典格式
        if hasattr(ch, 'to_dict'):
            ch_dict = ch.to_dict()
        elif isinstance(ch, dict):
            ch_dict = ch
        else:
            ch_dict = {
                "name": getattr(ch, 'name', ''),
                "url": getattr(ch, 'url', ''),
                "urls": getattr(ch, 'urls', [getattr(ch, 'url', '')]),
                "group_title": getattr(ch, 'group_title', ''),
                "id": getattr(ch, 'tvg_id', ''),
                "logo": getattr(ch, 'tvg_logo', ''),
                "latency": getattr(ch, 'latency', 9999),
                "video_codec": getattr(ch, 'video_codec', ''),
                "ip_info": getattr(ch, 'ip_info', None)
            }
        temp[cat].append(ch_dict)
    # 央视排序
    def ctv_sort_key(ch):
        name = ch["name"]
        for idx, std in enumerate(CCTV_ORDER):
            if std.lower() in name.lower() or name.lower() in std.lower():
                return idx
        return len(CCTV_ORDER)
    if temp["央视"]:
        temp["央视"] = sorted(temp["央视"], key=ctv_sort_key)
    # 按顺序输出
    result = {}
    for cat in ["央视", "卫视", "地方", "港澳台"]:
        if temp.get(cat):
            result[cat] = temp[cat]
        else:
            result[cat] = []
    print("📊 分类统计（强制顺序：央视、卫视、地方、港澳台）：")
    for cat, lst in result.items():
        if lst:
            print(f"  {cat}: {len(lst)} 个频道")
    return result

async def main():
    print("🚀 IPTV智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")
    print(f"📋 增强过滤: demo={ENABLE_DEMO_FILTER}, alias={ENABLE_ALIAS}, blacklist={ENABLE_BLACKLIST}")

    init_ip_resolver()
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        from src.ffmpeg_validator import check_ffprobe
        await check_ffprobe()

    cache = CacheManager()
    alias_matcher = get_alias_matcher() if ENABLE_ALIAS else None

    if cache.should_update():
        print("\n📥 执行完整采集流程...")
        raw_contents = await fetch_all_sources(IPTV_SOURCES)
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
        merged_channels = merge_channels_by_name(valid_channels)

        if ENABLE_BLACKLIST:
            blacklist_filter = get_blacklist_filter()
            merged_channels = blacklist_filter.filter_channels(merged_channels)

        if ENABLE_DEMO_FILTER:
            merged_channels = filter_and_order_by_demo(merged_channels, alias_matcher=alias_matcher)

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

        if ENABLE_BLACKLIST:
            blacklist_filter = get_blacklist_filter()
            merged_channels = blacklist_filter.filter_channels(merged_channels)

        if ENABLE_DEMO_FILTER:
            final_channels = filter_and_order_by_demo(merged_channels, alias_matcher=alias_matcher)
        else:
            final_channels = merged_channels

    classified = build_classified_from_ordered(final_channels, alias_matcher=alias_matcher)
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
