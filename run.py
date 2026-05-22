# run.py
import asyncio
from src.config import IPTV_SOURCES
from src.fetcher import fetch_all_sources
from src.parser import parse_and_dedupe
from src.speed_tester import test_channels_concurrent
from src.ffmpeg_validator import validate_with_ffmpeg_batch
from src.classifier import classify_all
from src.generator import generate_outputs

async def main():
    print("🚀 IPTV 智能整理平台启动")
    
    # Phase 1: 并行拉取所有源
    print("📥 拉取源文件...")
    raw_contents = await fetch_all_sources(IPTV_SOURCES)
    
    # Phase 2: 解析与去重
    print("🔧 解析与去重...")
    channels = parse_and_dedupe(raw_contents)
    
    # Phase 3: 轻量级测速
    print("⚡ 快速测速中...")
    valid_channels = await test_channels_concurrent(channels)
    
    # Phase 4: 深度验证 (ffmpeg)
    if os.getenv("FFMPEG_ENABLE") == "true":
        print("🔍 ffmpeg 深度验证中...")
        valid_channels = await validate_with_ffmpeg_batch(valid_channels)
    
    # Phase 5: 智能分类
    print("📁 智能分类中...")
    classified = classify_all(valid_channels)
    
    # Phase 6: 输出生成
    print("📄 生成输出文件...")
    generate_outputs(classified)
    
    print(f"✅ 完成！有效频道数: {len(valid_channels)}")

if __name__ == "__main__":
    asyncio.run(main())
