# ffmpeg/ffprobe 深度验证模块
import asyncio
import subprocess
import json
from src.config import FFMPEG_ENABLE, TIMEOUT, MAX_WORKERS

async def validate_with_ffprobe(channel) -> bool:
    """使用 ffprobe 检测流是否包含有效的视频或音频流"""
    if not FFMPEG_ENABLE:
        return True  # 未启用深度验证，默认通过
    
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
        "-analyzeduration", "5000000", "-probesize", "5000000",
        channel.url
    ]
    try:
        # 由于 ffprobe 是同步阻塞的，使用 run_in_executor 避免阻塞事件循环
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        if proc.returncode != 0:
            return False
        data = json.loads(stdout.decode('utf-8', errors='ignore'))
        streams = data.get("streams", [])
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        # 至少需要有音频或视频流
        return has_video or has_audio
    except Exception as e:
        # 解析失败视为无效
        return False

async def validate_batch(channels: list) -> list:
    """对列表中的频道进行批量深度验证（并发有限制）"""
    if not FFMPEG_ENABLE:
        return channels
    
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    
    async def validate_one(ch):
        async with semaphore:
            is_valid = await validate_with_ffprobe(ch)
            return ch, is_valid
    
    tasks = [validate_one(ch) for ch in channels]
    results = await asyncio.gather(*tasks)
    
    valid = [ch for ch, ok in results if ok]
    invalid_count = len(channels) - len(valid)
    print(f"🔍 ffmpeg 深度验证完成，过滤 {invalid_count} 个无效流")
    return valid

# 对外提供统一入口（兼容函数签名）
async def validate_with_ffmpeg_batch(channels: list) -> list:
    return await validate_batch(channels)
