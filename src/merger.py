# src/merger.py (新建)

from collections import defaultdict

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    import re
    # 移除清晰度、来源等后缀
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方)[\]\)]?', '', name, flags=re.IGNORECASE)
    # 移除空格及特殊符号
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def merge_channels_by_name(valid_channels: list) -> list:
    """
    按频道名合并多源，并为每个频道保留最多 5 个最优源
    优先级规则：1. H.264 编码 > H.265  > 其他
               2. 延迟更低
    """
    groups = defaultdict(list)
    for ch in valid_channels:
        norm_name = normalize_channel_name(ch.name)
        groups[norm_name].append(ch)

    merged_channels = []
    for norm_name, channels in groups.items():
        # 最多保留5个源
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' else 1 if getattr(x, 'video_codec', '') == 'hevc' else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]

        # 创建一个新的频道对象，包含多个 URL
        primary = top_channels[0]
        merged = type('MergedChannel', (), {})()
        merged.name = primary.name
        merged.urls = [ch.url for ch in top_channels]
        merged.latency = primary.latency
        merged.video_codec = primary.video_codec
        merged.group_title = primary.group_title
        merged.tvg_id = primary.tvg_id
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} -> {len(merged_channels)} 个频道（含多源）")
    return merged_channels
