import re
from src.config import CATEGORY_KEYWORDS, CATEGORY_ORDER

def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类"""
    name = getattr(channel, 'name', '')
    group = getattr(channel, 'group_title', '')

    if group:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == "其他":
                continue
            for kw in keywords:
                if kw.lower() in group.lower():
                    return cat

    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat == "其他":
            continue
        for kw in keywords:
            if kw.lower() in name.lower():
                return cat
    return "其他"

def extract_cctv_number(name: str) -> int:
    """提取央视频道数字，如 CCTV-1 -> 1, CCTV-5+ -> 5.5"""
    # 匹配 CCTV-数字 或 CCTV数字
    match = re.search(r'CCTV[- ]?(\d+)(?:\+)?', name, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        if '+' in name:
            return num + 0.5
        return num
    # 特殊处理 CCTV-5+ 等
    if 'CCTV-5+' in name or 'CCTV5+' in name:
        return 5.5
    return 999

def sort_cctv_channels(channels):
    """对央视频道按数字顺序排序"""
    return sorted(channels, key=lambda x: extract_cctv_number(x.get('name', '') if isinstance(x, dict) else x.name))

def classify_all(channels: list) -> dict:
    """
    将所有频道分类，返回 {分类名称: [channel_dict, ...]}
    并按 CATEGORY_ORDER 顺序排列分类，央视内部按数字排序
    """
    classified = {cat: [] for cat in CATEGORY_ORDER if cat != "其他"}
    classified["其他"] = []

    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        classified[cat].append(ch)

    # 对每个分类内的频道排序
    for cat in classified:
        if cat == "央视":
            classified[cat] = sort_cctv_channels(classified[cat])
        else:
            # 按名称排序
            classified[cat].sort(key=lambda x: (x.get('name', '') if isinstance(x, dict) else x.name))

    # 移除空分类
    classified = {k: v for k, v in classified.items() if v}

    # 输出统计
    print("📊 分类统计：")
    for cat, lst in classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    return classified
