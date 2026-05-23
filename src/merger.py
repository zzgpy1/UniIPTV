import re
from collections import defaultdict

def normalize_channel_name(name: str) -> str:
    """标准化频道名：去除清晰度标识、标点，转为小写（中文不变）"""
    name = re.sub(r'[\(\[]?(?:高清|HD|超清|4K|标清|流畅|官方|备胎|备用)[\]\)]?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def merge_channels_by_name(channels: list) -> list:
    """
    按标准化频道名合并多源，每个频道保留最多5个最优源
    最优策略：延迟最低 > H.264编码 > 省份匹配（相同省份优先）
    """
    groups = defaultdict(list)
    for ch in channels:
        # ch 可以是原始Channel对象或数据库返回的dict
        if isinstance(ch, dict):
            name = ch.get('name', '')
            norm_name = normalize_channel_name(name)
            groups[norm_name].append(ch)
        else:
            norm_name = normalize_channel_name(ch.name)
            groups[norm_name].append(ch)

    merged_channels = []
    for norm_name, items in groups.items():
        # 排序规则：延迟升序，编码h264优先，省份匹配（如果有preferred_province）
        def sort_key(item):
            if isinstance(item, dict):
                latency = item.get('latency', 9999)
                codec = item.get('video_codec', '')
                province = item.get('province', '')
            else:
                latency = getattr(item, 'latency', 9999)
                codec = getattr(item, 'video_codec', '')
                province = getattr(item, 'province', '')
            # 编码优先级: h264=0, hevc=1, 其他=2
            codec_priority = 0 if codec == 'h264' else 1 if codec == 'hevc' else 2
            # 省份匹配（暂时无法动态获取用户省份，可留空或从环境变量读取）
            # 这里简单按延迟排序
            return (codec_priority, latency)
        items.sort(key=sort_key)
        top_items = items[:5]

        # 构造合并后的频道对象（使用第一个作为主要信息）
        first = top_items[0]
        if isinstance(first, dict):
            merged = type('MergedChannel', (), {})()
            merged.name = first['name']
            merged.urls = [item['url'] if isinstance(item, dict) else item.url for item in top_items]
            merged.latency = first.get('latency', 0)
            merged.video_codec = first.get('video_codec', '')
            merged.group_title = first.get('group_title', '')
            merged.tvg_id = first.get('tvg_id', '')
            merged.tvg_logo = first.get('tvg_logo', '')
            merged.province = first.get('province', '')
            merged.city = first.get('city', '')
            merged.isp = first.get('isp', '')
        else:
            merged = type('MergedChannel', (), {})()
            merged.name = first.name
            merged.urls = [item.url for item in top_items]
            merged.latency = first.latency if hasattr(first, 'latency') else 0
            merged.video_codec = getattr(first, 'video_codec', '')
            merged.group_title = getattr(first, 'group_title', '')
            merged.tvg_id = getattr(first, 'tvg_id', '')
            merged.tvg_logo = getattr(first, 'tvg_logo', '')
            merged.province = getattr(first, 'province', '')
            merged.city = getattr(first, 'city', '')
            merged.isp = getattr(first, 'isp', '')
        merged_channels.append(merged)

    print(f"🔄 频道合并完成：{len(channels)} 个源 -> {len(merged_channels)} 个频道（含多源）")
    return merged_channels
