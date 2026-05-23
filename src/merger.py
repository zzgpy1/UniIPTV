# src/merger.py
from collections import defaultdict
import re

def normalize_channel_name(name: str) -> str:
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方)[\)\]]?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

class MergedChannel:
    def __init__(self, name, urls, latency, video_codec="", group_title="", tvg_id=""):
        self.name = name
        self.urls = urls
        self.latency = latency
        self.video_codec = video_codec
        self.group_title = group_title
        self.tvg_id = tvg_id

    def to_dict(self):
        return {
            "name": self.name,
            "urls": self.urls,
            "url": self.urls[0] if self.urls else "",
            "latency": self.latency,
            "video_codec": self.video_codec,
            "group_title": self.group_title,
            "id": self.tvg_id
        }

def merge_channels_by_name(valid_channels: list) -> list:
    groups = defaultdict(list)
    for ch in valid_channels:
        norm_name = normalize_channel_name(ch.name)
        groups[norm_name].append(ch)

    merged_channels = []
    for norm_name, channels in groups.items():
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' else 1 if getattr(x, 'video_codec', '') == 'hevc' else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]
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
