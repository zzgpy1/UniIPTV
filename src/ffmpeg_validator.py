# 在 validate_batch 中，调用 validate_with_ffprobe 后，将信息存入 channel
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
            result = await validate_with_ffprobe(ch)
            # 将结果存储到 channel 对象
            ch.video_codec = result.get('video_codec', 'unknown')
            ch.has_video = result.get('has_video', False)
            ch.has_audio = result.get('has_audio', False)
            return ch, result['valid']

    tasks = [validate_one(ch) for ch in channels]
    results = await asyncio.gather(*tasks)

    valid = [ch for ch, ok in results if ok]
    invalid_count = len(channels) - len(valid)
    print(f"🔍 ffmpeg 深度验证完成，通过 {len(valid)}/{len(channels)} 个频道")
    if invalid_count > 0 and not FFMPEG_STRICT:
        print(f"   （宽松模式，{invalid_count} 个异常或超时频道已保留）")
    return valid
