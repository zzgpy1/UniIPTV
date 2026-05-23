#!/usr/bin/env python3
import asyncio
import sys
import os
import hashlib

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
from src.db_manager import DatabaseManager

def compute_sources_hash(raw_contents: dict) -> str:
    """计算所有源内容的联合哈希值，用于判断数据是否变化"""
    combined = ""
    for url, content in sorted(raw_contents.items()):
        if content:
            combined += content
    return hashlib.md5(combined.encode('utf-8')).hexdigest()

def init_ip_resolver():
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
    if os.getenv("FFMPEG_ENABLE", "true").lower() == "true":
        await check_ffprobe()

    db = DatabaseManager()

    # 1. 拉取所有源
    print("📥 正在拉取源文件...")
    raw_contents = await fetch_all_sources(IPTV_SOURCES)
    current_hash = compute_sources_hash(raw_contents)

    # 检查是否有源变化（取第一个源的哈希作为简单判断，可改进）
    # 为了简化，我们比较所有源合并后的哈希是否与存储的一致
    # 存储一个全局哈希（例如存储 sources_hash 表中的一条记录）
    cursor = db.conn.cursor()
    cursor.execute("SELECT content_hash FROM source_hash WHERE source_url='__global__'")
    row = cursor.fetchone()
    cached_hash = row[0] if row else None

    if cached_hash == current_hash:
        print("♻️ 源数据无变化，从缓存加载频道...")
        valid_channels = db.load_all_channels()
        if valid_channels:
            print(f"✅ 从缓存加载了 {len(valid_channels)} 个频道")
            # 跳过拉取、测速、验证等步骤，直接进入合并和分类
            valid_channels = merge_channels_by_name(valid_channels)
            classified = classify_all(valid_channels)
            generate_outputs(classified)
            total = sum(len(lst) for lst in classified.values())
            print(f"🎉 完成（缓存模式）！最终输出频道总数: {total}")
            return
        else:
            print("⚠️ 缓存为空，将重新检测...")
    else:
        print("🔄 源数据已变化，重新检测所有频道...")

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
    db.save_channels(valid_channels)
    # 更新全局哈希
    db.update_source_hash('__global__', current_hash)
    print("💾 检测结果已缓存到数据库")

    # 6. 合并多源
    valid_channels = merge_channels_by_name(valid_channels)
    if not valid_channels:
        print("❌ 合并后无有效频道")
        sys.exit(1)

    # 7. 分类并过滤
    classified = classify_all(valid_channels)

    # 8. 生成输出文件
    generate_outputs(classified)

    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！最终输出频道总数: {total}")

if __name__ == "__main__":
    asyncio.run(main())
