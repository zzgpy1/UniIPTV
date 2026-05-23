#!/usr/bin/env python3
# 主入口程序（集成数据库缓存）
import asyncio
import sys
import os
import hashlib

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import IPTV_SOURCES, OUTPUT_DIR, ENABLE_REGION_FILTER, PREFERRED_LOCATION, PREFERRED_ISP, ENABLE_IP_RESOLVE
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_all
from src.generator import generate_outputs
from src.merger import merge_channels_by_name
from src.ip_resolver import get_resolver, matches_region
from src.database import init_db, save_channels, load_valid_channels, get_source_hash, set_source_hash

# 计算源列表的hash（用于检测源是否有变化）
def compute_sources_hash():
    content = "".join(IPTV_SOURCES)
    return hashlib.md5(content.encode()).hexdigest()

# 初始化IP解析器
def init_ip_resolver():
    if not ENABLE_IP_RESOLVE:
        print("⚙️ IP 解析未启用")
        return
    resolver = get_resolver()
    if resolver.is_available:
        print("✅ IP 解析器已就绪")
    else:
        print("⚠️ IP 解析器不可用，将跳过地域筛选")

# 地域筛选
def filter_by_region(channels: list) -> list:
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
        ip_info = getattr(ch, 'ip_info', None)
        if ip_info and matches_region(ip_info, preferred_locations, preferred_isps):
            filtered.append(ch)
        elif not ip_info:
            # 尝试重新解析
            ip_info = resolver.resolve_channel_ip(ch)
            if ip_info and matches_region(ip_info, preferred_locations, preferred_isps):
                ch.ip_info = ip_info
                filtered.append(ch)
            elif not ENABLE_REGION_FILTER:
                filtered.append(ch)
    
    print(f"  筛选结果: {len(filtered)}/{len(channels)} 个频道通过地域筛选")
    return filtered

async def main():
    print("🚀 IPTV 智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")
    
    # 初始化数据库
    init_db()
    
    # 初始化 IP 解析器
    init_ip_resolver()
    
    # 预检 ffprobe
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        from src.ffmpeg_validator import check_ffprobe
        await check_ffprobe()
    
    # 检查源是否有变化
    current_hash = compute_sources_hash()
    last_hash = get_source_hash()
    sources_changed = (current_hash != last_hash)
    
    # 尝试从数据库加载缓存（如果源未变化）
    cached_channels = None
    if not sources_changed:
        cached_channels = load_valid_channels()
        if cached_channels:
            print("📦 使用数据库缓存（源无变化）")
            valid_channels = cached_channels
        else:
            print("⚠️ 数据库无有效缓存，重新采集")
            sources_changed = True  # 强制重新采集
    else:
        print("🔄 源列表已变化，重新采集所有频道")
    
    if sources_changed or not cached_channels:
        # 1. 拉取所有源
        print("📥 正在拉取源文件...")
        raw_contents = await fetch_all_sources(IPTV_SOURCES)
        
        # 2. 解析与去重
        print("🔧 解析并去重...")
        channels_dict = parse_and_dedupe(raw_contents)
        
        if not channels_dict:
            print("❌ 未获取到任何频道，请检查网络或源地址")
            sys.exit(1)
        
        # 3. 轻量级测速
        valid_channels = await test_channels_concurrent(channels_dict)
        
        if not valid_channels:
            print("❌ 无有效频道通过测速，请检查网络或增加超时时间")
            sys.exit(1)
        
        # 4. 深度验证（ffmpeg）
        valid_channels = await validate_with_ffmpeg_batch(valid_channels)
        
        if not valid_channels:
            print("❌ 深度验证后无有效频道")
            sys.exit(1)
        
        # 5. 保存到数据库
        save_channels(valid_channels, current_hash)
        
        # 更新源hash
        set_source_hash(current_hash)
    
    # 6. 地域筛选（可选）
    valid_channels = filter_by_region(valid_channels)
    
    if not valid_channels:
        print("❌ 地域筛选后无有效频道")
        sys.exit(1)
    
    # 7. 合并多源（每个频道最多5个源）
    print("🔄 正在合并多源频道...")
    valid_channels = merge_channels_by_name(valid_channels)
    
    # 8. 智能分类
    print("📁 执行智能分类...")
    classified = classify_all(valid_channels)
    
    # 9. 生成输出文件
    generate_outputs(classified)
    
    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")

if __name__ == "__main__":
    asyncio.run(main())
