# ffmpeg/ffprobe 深度验证模块（修复事件循环问题）
import asyncio
import subprocess
import json
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from src.config import FFMPEG_ENABLE, TIMEOUT, MAX_WORKERS, FFMPEG_STRICT

# 全局标志
_ffprobe_available = None
_thread_pool = None

def get_thread_pool():
    """获取线程池单例"""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, 5))
    return _thread_pool

def check_ffprobe_sync():
    """同步检查 ffprobe 是否可用"""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

async def check_ffprobe() -> bool:
    """异步检查 ffprobe 是否可用（使用线程池避免事件循环问题）"""
    global _ffprobe_available
    if _ffprobe_available is not None:
        return _ffprobe_available
    
    loop = asyncio.get_event_loop()
    _ffprobe_available = await loop.run_in_executor(get_thread_pool(), check_ffprobe_sync)
    
    if _ffprobe_available:
        print("✅ ffprobe 可用（深度验证已启用）")
    else:
        print("⚠️ ffprobe 不可用，将跳过深度验证")
    return _ffprobe_available

def validate_with_ffprobe_sync(url: str, timeout: int) -> dict:
    """
    同步版本的 ffprobe 验证（在线程池中运行）
    返回：{"valid": bool, "has_video": bool, "video_codec": str, "has_audio": bool}
    """
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
        "-analyzeduration", "5000000", "-probesize", "5000000",
        url
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            text=True
        )
        if result.returncode != 0:
            return {"valid": not FFMPEG_STRICT, "has_video": False, "video_codec": "", "has_audio": False}
        
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        has_video = False
        video_codec = ""
        for s in streams:
            if s.get("codec_type") == "video":
                has_video = True
                video_codec = s.get("codec_name", "").lower()
                break
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        
        valid = has_video or has_audio
        if not valid and not FFMPEG_STRICT:
            valid = True
        
        return {
            "valid": valid,
            "has_video": has_video,
            "video_codec": video_codec,
            "has_audio": has_audio
        }
    except subprocess.TimeoutExpired:
        return {"valid": not FFMPEG_STRICT, "has_video": False, "video_codec": "", "has_audio": False}
    except Exception:
        return {"valid": not FFMPEG_STRICT, "has_video": False, "video_codec": "", "has_audio": False}

async def validate_with_ffprobe(channel) -> dict:
    """异步版本的 ffprobe 验证（使用线程池避免子进程问题）"""
    if not FFMPEG_ENABLE:
        return {"valid": True, "has_video": True, "video_codec": "unknown", "has_audio": True}
    
    if not await check_ffprobe():
        return {"valid": True, "has_video": True, "video_codec": "unknown", "has_audio": True}
    
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            get_thread_pool(),
            validate_with_ffprobe_sync,
            channel.url,
            TIMEOUT
        )
        return result
    except Exception as e:
        return {"valid": not FFMPEG_STRICT, "has_video": False, "video_codec": "", "has_audio": False}

async def validate_batch(channels: list) -> list:
    """对列表中的频道进行批量深度验证（使用信号量控制并发）"""
    if not FFMPEG_ENABLE:
        print("⚙️ ffmpeg 深度验证未启用，跳过")
        return channels
    
    ffprobe_ok = await check_ffprobe()
    if not ffprobe_ok:
        print("⚠️ ffprobe 不可用，跳过深度验证，全部频道视为有效")
        return channels
    
    semaphore = asyncio.Semaphore(min(MAX_WORKERS, 3))  # 降低并发，避免资源竞争
    
    async def validate_one(ch):
        async with semaphore:
            result = await validate_with_ffprobe(ch)
            if hasattr(ch, 'video_codec'):
                ch.video_codec = result.get("video_codec", "")
            return ch, result.get("valid", True)
    
    tasks = [validate_one(ch) for ch in channels]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid = []
    for item in results:
        if isinstance(item, Exception):
            continue
        ch, ok = item
        if ok:
            valid.append(ch)
    
    invalid_count = len(channels) - len(valid)
    print(f"🔍 ffmpeg 深度验证完成，通过 {len(valid)}/{len(channels)} 个频道")
    return valid

async def validate_with_ffmpeg_batch(channels: list) -> list:
    """对外统一入口"""
    return await validate_batch(channels)

def cleanup():
    """清理线程池（在程序结束时调用）"""
    global _thread_pool
    if _thread_pool:
        _thread_pool.shutdown(wait=False)
        _thread_pool = None
