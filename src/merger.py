# src/merger.py
from collections import defaultdict
import re

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    # 移除清晰度、来源等后缀
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方)[\]\)]?', '', name, flags=re.IGNORECASE)
    # 移除空格及特殊符号
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

class MergedChannel:
    """合并后的频道对象，兼容 Channel 类的接口"""
    def __init__(self, primary_channel, urls):
        self.name = primary_channel.name
        self.urls = urls  # 多个 URL 列表
        self.url = urls[0]  # 兼容旧代码，取第一个
        self.latency = getattr(primary_channel, 'latency', 9999)
        self.video_codec = getattr(primary_channel, 'video_codec', 'unknown')
        self.group_title = getattr(primary_channel, 'group_title', '')
        self.tvg_id = getattr(primary_channel, 'tvg_id', '')
        self.tvg_name = getattr(primary_channel, 'tvg_name', '')
        self.tvg_logo = getattr(primary_channel, 'tvg_logo', '')
        self.ip_info = getattr(primary_channel, 'ip_info', None)

    def to_dict(self):
        """转换为字典，兼容原有格式，但保留多源信息"""
        return {
            "name": self.name,
            "url": self.url,          # 主源
            "urls": self.urls,        # 所有源
            "group_title": self.group_title,
            "id": self.tvg_id,
            "logo": self.tvg_logo,
            "latency": self.latency,
            "video_codec": self.video_codec
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
        # 排序：优先 H.264，其次延迟
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' 
            else 1 if getattr(x, 'video_codec', '') == 'hevc' 
            else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]  # 最多保留5个源
        primary = top_channels[0]
        urls = [ch.url for ch in top_channels]
        merged = MergedChannel(primary, urls)
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} -> {len(merged_channels)} 个频道（含多源）")
    return merged_channels
