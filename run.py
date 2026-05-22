#!/usr/bin/env python3
# 主入口程序
import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import IPTV_SOURCES, OUTPUT_DIR
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_all
from src.generator import generate_outputs
from src.demo_filter import filter_and_reorder   # 新增

async def main():
    print("🚀 IPTV 智能整理平台启动")
    print(f"📡 配置：超时={os.getenv('TIMEOUT','10')}s, 并发={os.getenv('MAX_WORKERS','10')}, ffmpeg={os.getenv('FFMPEG_ENABLE','true')}")
    
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
    
    # 5. 智能分类
    print("📁 执行智能分类...")
    classified = classify_all(valid_channels)
    
    # 6. 按 demo.txt 过滤和重排（新增）
    print("🎯 根据 demo.txt 过滤频道并重排顺序...")
    classified = filter_and_reorder(classified)
    
    # 7. 生成输出文件
    generate_outputs(classified)
    
    total = sum(len(lst) for lst in classified.values())
    print(f"🎉 完成！有效频道总数: {total}")

if __name__ == "__main__":
    asyncio.run(main())
