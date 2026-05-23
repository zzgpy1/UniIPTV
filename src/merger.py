# src/merger.py
# 频道合并模块：将同一频道的多个源合并为一个条目，最多保留5个最优源

from collections import defaultdict
from typing import List

class MergedChannel:
    """合并后的频道对象，包含多个备选URL"""
    def __init__(self, name: str, urls: List[str], latency: int, video_codec: str,
                 group_title: str = "", tvg_id: str = "", tvg_logo: str = ""):
        self.name = name
        self.urls = urls          # 多个URL列表
        self.latency = latency    # 最佳源的延迟
        self.video_codec = video_codec
        self.group_title = group_title
        self.tvg_id = tvg_id
        self.tvg_logo = tvg_logo

    def to_dict(self):
        """转换为字典格式，供分类器使用"""
        return {
            "name": self.name,
            "urls": self.urls,
            "latency": self.latency,
            "video_codec": self.video_codec,
            "group_title": self.group_title,
            "id": self.tvg_id,
            "logo": self.tvg_logo
        }

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    import re
    # 移除清晰度、来源等后缀
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方|LIVE|直播)[\)\]]?', '', name, flags=re.IGNORECASE)
    # 移除空格及特殊符号
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def merge_channels_by_name(valid_channels: list) -> list:
    """
    按频道名合并多源，并为每个频道保留最多 5 个最优源
    优先级规则：1. H.264 编码 > H.265 > 其他
               2. 延迟更低
    """
    groups = defaultdict(list)
    for ch in valid_channels:
        norm_name = normalize_channel_name(ch.name)
        groups[norm_name].append(ch)

    merged_channels = []
    for norm_name, channels in groups.items():
        # 排序：编码优先，然后延迟
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' else 1 if getattr(x, 'video_codec', '') == 'hevc' else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]

        # 取最佳源的信息
        primary = top_channels[0]
        urls = [ch.url for ch in top_channels]
        merged = MergedChannel(
            name=primary.name,
            urls=urls,
            latency=primary.latency,
            video_codec=getattr(primary, 'video_codec', 'unknown'),
            group_title=getattr(primary, 'group_title', ''),
            tvg_id=getattr(primary, 'tvg_id', ''),
            tvg_logo=getattr(primary, 'tvg_logo', '')
        )
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} 个源 -> {len(merged_channels)} 个频道（含多源）")
    return merged_channels
