# src/merger.py
from collections import defaultdict
import re

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    # 移除清晰度、来源等后缀
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方)[\)\]]?', '', name, flags=re.IGNORECASE)
    # 移除空格及特殊符号
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

class MergedChannel:
    """合并后的频道对象，支持多 URL"""
    def __init__(self, name, urls, latency, video_codec="", group_title="", tvg_id=""):
        self.name = name
        self.urls = urls          # list of URLs
        self.latency = latency    # 最快源的延迟
        self.video_codec = video_codec
        self.group_title = group_title
        self.tvg_id = tvg_id

    def to_dict(self):
        """转换为字典，供分类和输出使用"""
        return {
            "name": self.name,
            "urls": self.urls,
            "latency": self.latency,
            "video_codec": self.video_codec,
            "group_title": self.group_title,
            "id": self.tvg_id,
            # 为了兼容 generator，保留单 url 字段（取第一个）
            "url": self.urls[0] if self.urls else ""
        }

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
        # 按编码和延迟排序
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' else 1 if getattr(x, 'video_codec', '') == 'hevc' else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]   # 最多保留5个源

        primary = top_channels[0]
        urls = [ch.url for ch in top_channels]
        merged = MergedChannel(
            name=primary.name,
            urls=urls,
            latency=primary.latency,
            video_codec=getattr(primary, 'video_codec', ''),
            group_title=getattr(primary, 'group_title', ''),
            tvg_id=getattr(primary, 'tvg_id', '')
        )
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：原始有效频道 {len(valid_channels)} -> 合并后 {len(merged_channels)} 个频道（含多源）")
    return merged_channels
