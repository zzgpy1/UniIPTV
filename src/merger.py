# src/merger.py
# 频道合并模块：按名称合并多源，排序后只保留最优源用于输出

from collections import defaultdict
import re
from src.config import MAX_SOURCES_PER_CHANNEL

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道（去除清晰度标签等）"""
    name = re.sub(r'\s*(?:1080[pi]|720[pi]|4K|8K|HD|高清|超清|标清|流畅|付费)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def merge_channels_by_name(valid_channels: list) -> list:
    """
    按频道名合并多源，为每个频道保留最多 MAX_SOURCES_PER_CHANNEL 个源，
    并按优先级排序（H.264 > H.265 > 其他，延迟低优先）。
    返回的频道对象包含 urls 列表（按优先级排序）
    """
    groups = defaultdict(list)
    for ch in valid_channels:
        # 兼容两种输入：Channel/MergedChannel 对象 或 字典
        if isinstance(ch, dict):
            name = ch.get("name", "")
            url = ch.get("url", "")
            latency = ch.get("latency", 9999)
            video_codec = ch.get("video_codec", "")
            group_title = ch.get("group_title", "")
            tvg_id = ch.get("id", "")
            tvg_logo = ch.get("logo", "")
            ip_info = ch.get("ip_info", None)
        else:
            # 对象方式
            name = getattr(ch, 'name', '')
            url = getattr(ch, 'url', '')
            latency = getattr(ch, 'latency', 9999)
            video_codec = getattr(ch, 'video_codec', '')
            group_title = getattr(ch, 'group_title', '')
            tvg_id = getattr(ch, 'tvg_id', '')
            tvg_logo = getattr(ch, 'tvg_logo', '')
            ip_info = getattr(ch, 'ip_info', None)

        norm_name = normalize_channel_name(name)
        groups[norm_name].append({
            "name": name,
            "url": url,
            "latency": latency,
            "video_codec": video_codec,
            "group_title": group_title,
            "tvg_id": tvg_id,
            "tvg_logo": tvg_logo,
            "ip_info": ip_info
        })

    merged_channels = []
    for norm_name, channels in groups.items():
        # 排序：优先 H.264，然后延迟低
        def sort_key(ch):
            codec = ch.get('video_codec', '')
            codec_priority = 0 if codec == 'h264' else 1 if codec == 'hevc' else 2
            latency = ch.get('latency', 9999)
            return (codec_priority, latency)

        channels.sort(key=sort_key)
        top_channels = channels[:MAX_SOURCES_PER_CHANNEL]

        # 使用第一个频道作为模板
        primary = top_channels[0]
        merged = {
            "name": primary["name"],
            "urls": [ch["url"] for ch in top_channels],
            "url": primary["url"],
            "latency": primary["latency"],
            "video_codec": primary["video_codec"],
            "group_title": primary["group_title"],
            "id": primary["tvg_id"],
            "logo": primary["tvg_logo"],
            "ip_info": primary["ip_info"]
        }
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} 个源 -> {len(merged_channels)} 个频道（每个频道最多 {MAX_SOURCES_PER_CHANNEL} 个源）")
    return merged_channels
