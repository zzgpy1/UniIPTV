# src/merger.py
from collections import defaultdict
import re

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    # 移除清晰度、来源等后缀
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方)[\]\)]?', '', name, flags=re.IGNORECASE)
    # 移除空格及特殊符号，保留中文、字母、数字
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def get_channel_sort_key(ch):
    """获取频道的排序键，用于优选"""
    # 编码优先级：h264(0) > hevc/h265(1) > 其他(2) > 未知(3)
    codec = getattr(ch, 'video_codec', '')
    if codec == 'h264':
        codec_priority = 0
    elif codec in ('hevc', 'h265'):
        codec_priority = 1
    elif codec:
        codec_priority = 2
    else:
        codec_priority = 3
    # 延迟（越小越好）
    latency = getattr(ch, 'latency', 9999)
    return (codec_priority, latency)

def merge_channels_by_name(valid_channels: list, max_sources_per_channel: int = 5) -> list:
    """
    按频道名合并多源，并为每个频道保留最多 max_sources_per_channel 个最优源
    优先级规则：1. H.264 编码 > H.265 > 其他 > 未知
               2. 延迟更低
    """
    groups = defaultdict(list)
    for ch in valid_channels:
        norm_name = normalize_channel_name(ch.name)
        groups[norm_name].append(ch)

    merged_channels = []
    for norm_name, channels in groups.items():
        # 按优先级排序
        channels.sort(key=get_channel_sort_key)
        top_channels = channels[:max_sources_per_channel]

        # 使用第一个频道作为模板
        primary = top_channels[0]
        # 创建一个简单的对象来存储合并后的信息
        merged = type('MergedChannel', (), {})()
        merged.name = primary.name
        merged.urls = [ch.url for ch in top_channels]
        merged.latency = primary.latency if hasattr(primary, 'latency') else 9999
        merged.video_codec = getattr(primary, 'video_codec', 'unknown')
        merged.group_title = getattr(primary, 'group_title', '')
        merged.tvg_id = getattr(primary, 'tvg_id', '')
        merged.tvg_logo = getattr(primary, 'tvg_logo', '')
        # 保留原始 channel 对象引用（可选）
        merged.primary_channel = primary
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} 个源 -> {len(merged_channels)} 个频道（每频道最多 {max_sources_per_channel} 个源）")
    return merged_channels
