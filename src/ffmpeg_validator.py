# src/ffmpeg_validator.py
import asyncio
import subprocess
import json
from src.config import FFMPEG_ENABLE, TIMEOUT, MAX_WORKERS, FFMPEG_STRICT

_ffprobe_available = None

async def check_ffprobe() -> bool:
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

async def validate_with_ffprobe(channel):
    """
    增强版：使用 ffprobe 深度解析流信息
    返回字典，并同时将信息附加到 channel 对象上
    """
    if not FFMPEG_ENABLE:
        channel.video_codec = "unknown"
        channel.has_video = True
        channel.has_audio = True
        channel.ffmpeg_valid = True
        return {"valid": True, "has_video": True, "video_codec": "unknown", "has_audio": True}

    if not await check_ffprobe():
        channel.video_codec = "unknown"
        channel.has_video = True
        channel.has_audio = True
        channel.ffmpeg_valid = True
        return {"valid": True, "has_video": True, "video_codec": "unknown", "has_audio": True}

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
            valid = not FFMPEG_STRICT
            channel.ffmpeg_valid = valid
            channel.has_video = False
            channel.video_codec = ""
            channel.has_audio = False
            return {"valid": valid, "has_video": False, "video_codec": "", "has_audio": False}

        data = json.loads(stdout.decode('utf-8', errors='ignore'))
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

        # 附加到 channel 对象
        channel.ffmpeg_valid = valid
        channel.has_video = has_video
        channel.video_codec = video_codec
        channel.has_audio = has_audio

        return {
            "valid": valid,
            "has_video": has_video,
            "video_codec": video_codec,
            "has_audio": has_audio
        }
    except asyncio.TimeoutError:
        valid = not FFMPEG_STRICT
        channel.ffmpeg_valid = valid
        channel.has_video = False
        channel.video_codec = ""
        channel.has_audio = False
        return {"valid": valid, "has_video": False, "video_codec": "", "has_audio": False}
    except Exception:
        valid = not FFMPEG_STRICT
        channel.ffmpeg_valid = valid
        channel.has_video = False
        channel.video_codec = ""
        channel.has_audio = False
        return {"valid": valid, "has_video": False, "video_codec": "", "has_audio": False}

async def validate_batch(channels: list) -> list:
    if not FFMPEG_ENABLE:
        print("⚙️ ffmpeg 深度验证未启用，跳过")
        return channels

    if not await check_ffprobe():
        print("⚠️ ffprobe 不可用，跳过深度验证，全部频道视为有效")
        return channels

    semaphore = asyncio.Semaphore(min(MAX_WORKERS, 5))

    async def validate_one(ch):
        async with semaphore:
            info = await validate_with_ffprobe(ch)
            if info["valid"]:
                # 确保 video_codec 属性已设置（validate_with_ffprobe 内部已设置，这里再确认一次）
                ch.video_codec = info.get("video_codec", "unknown")
                return ch, True
            else:
                return ch, False

    tasks = [validate_one(ch) for ch in channels]
    results = await asyncio.gather(*tasks)

    valid = [ch for ch, ok in results if ok]
    invalid_count = len(channels) - len(valid)
    print(f"🔍 ffmpeg 深度验证完成，通过 {len(valid)}/{len(channels)} 个频道")
    if invalid_count > 0 and not FFMPEG_STRICT:
        print(f"   （宽松模式，{invalid_count} 个异常或超时频道已保留）")
    return valid

# 对外入口
async def validate_with_ffmpeg_batch(channels: list) -> list:
    return await validate_batch(channels)
