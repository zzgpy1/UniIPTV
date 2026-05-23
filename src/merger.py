# 频道合并模块（支持多源，修复属性缺失）
from collections import defaultdict
import re

def normalize_channel_name(name: str) -> str:
    """标准化频道名，用于合并不同来源的同一频道"""
    if not name:
        return ""
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
        # 排序：编码优先，然后延迟
        channels.sort(key=lambda x: (
            0 if getattr(x, 'video_codec', '') == 'h264' else 1 if getattr(x, 'video_codec', '') == 'hevc' else 2,
            getattr(x, 'latency', 9999)
        ))
        top_channels = channels[:5]  # 最多保留5个源

        # 创建一个简单的对象来存储合并后的频道
        primary = top_channels[0]
        
        # 使用一个简单的类或命名元组
        class MergedChannel:
            pass
        
        merged = MergedChannel()
        merged.name = primary.name
        merged.urls = [ch.url for ch in top_channels]
        merged.latency = primary.latency
        merged.video_codec = getattr(primary, 'video_codec', '')
        merged.has_video = getattr(primary, 'has_video', True)
        merged.has_audio = getattr(primary, 'has_audio', True)
        merged.group_title = getattr(primary, 'group_title', '')
        merged.tvg_id = getattr(primary, 'tvg_id', '')
        merged.tvg_logo = getattr(primary, 'tvg_logo', '')
        merged.ip_info = getattr(primary, 'ip_info', None)
        # 保留原始频道对象列表（可选）
        merged.original_channels = top_channels
        
        # 为了兼容 to_dict 方法，添加一个 to_dict 方法
        def to_dict(self):
            return {
                "name": self.name,
                "url": self.urls[0],  # 兼容旧代码，返回第一个URL
                "urls": self.urls,
                "group_title": self.group_title,
                "id": self.tvg_id,
                "logo": self.tvg_logo,
                "latency": self.latency,
                "video_codec": self.video_codec
            }
        merged.to_dict = to_dict.__get__(merged)
        
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(valid_channels)} -> {len(merged_channels)} 个频道（含多源）")
    return merged_channels
