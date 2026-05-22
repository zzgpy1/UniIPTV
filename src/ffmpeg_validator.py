# ffmpeg/ffprobe 深度验证模块（容错增强版）
import asyncio
import subprocess
import json
from src.config import FFMPEG_ENABLE, TIMEOUT, MAX_WORKERS, FFMPEG_STRICT

# 全局检查 ffprobe 是否可用
_ffprobe_available = None

async def check_ffprobe() -> bool:
    """检查 ffprobe 命令是否可用"""
    global _ffprobe_available
    if _ffprobe_available is not None:
        return _ffprobe_available
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-version",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        await proc.wait()
        ok = proc.returncode == 0
        if ok:
            print("✅ ffprobe 可用（深度验证已启用）")
        else:
            print("⚠️ ffprobe 不可用，将跳过深度验证")
        _ffprobe_available = ok
        return ok
    except Exception as e:
        print(f"⚠️ ffprobe 检查异常: {e}")
        _ffprobe_available = False
        return False

async def validate_with_ffprobe(channel) -> bool:
    """使用 ffprobe 检测流是否包含有效的视频或音频流（容错版）"""
    if not FFMPEG_ENABLE:
        return True  # 未启用深度验证，默认通过

    # 如果 ffprobe 不可用，直接返回 True（只依赖 HTTP 测速）
    if not await check_ffprobe():
        return True

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
        "-analyzeduration", "5000000", "-probesize", "5000000",
        channel.url
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        if proc.returncode != 0:
            # 非零返回码：可能是流不可读、格式不支持等
            if FFMPEG_STRICT:
                return False
            else:
                # 宽松模式：认为有效（已通过 HTTP 测速）
                return True

        data = json.loads(stdout.decode('utf-8', errors='ignore'))
        streams = data.get("streams", [])
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        # 至少需要有音频或视频流
        valid = has_video or has_audio
        if not valid and not FFMPEG_STRICT:
            # 宽松模式下，无音视频流也认为有效（避免误杀）
            valid = True
        return valid
    except asyncio.TimeoutError:
        # 超时：流可能较慢，宽松模式下视为有效
        if FFMPEG_STRICT:
            return False
        else:
            return True
    except Exception as e:
        # 其他异常（如 json 解析错误），宽松模式下视为有效
        if FFMPEG_STRICT:
            return False
        else:
            return True

async def validate_batch(channels: list) -> list:
    """对列表中的频道进行批量深度验证（并发有限制）"""
    if not FFMPEG_ENABLE:
        print("⚙️ ffmpeg 深度验证未启用，跳过")
        return channels

    # 预检 ffprobe 可用性
    ffprobe_ok = await check_ffprobe()
    if not ffprobe_ok:
        print("⚠️ ffprobe 不可用，跳过深度验证，全部频道视为有效")
        return channels

    semaphore = asyncio.Semaphore(min(MAX_WORKERS, 5))  # ffprobe 较重，降低并发

    async def validate_one(ch):
        async with semaphore:
            is_valid = await validate_with_ffprobe(ch)
            return ch, is_valid

    tasks = [validate_one(ch) for ch in channels]
    results = await asyncio.gather(*tasks)

    valid = [ch for ch, ok in results if ok]
    invalid_count = len(channels) - len(valid)
    print(f"🔍 ffmpeg 深度验证完成，通过 {len(valid)}/{len(channels)} 个频道")
    if invalid_count > 0 and not FFMPEG_STRICT:
        print(f"   （宽松模式，{invalid_count} 个异常或超时频道已保留）")
    return valid

# 对外提供统一入口
async def validate_with_ffmpeg_batch(channels: list) -> list:
    return await validate_batch(channels)
