# src/classifier.py
from src.config import CATEGORY_KEYWORDS

def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类"""
    name = channel.name
    group = getattr(channel, 'group_title', '')

    # 优先使用 group-title
    if group:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == "其他":
                continue
            for kw in keywords:
                if kw.lower() in group.lower():
                    return cat

    # 降级使用频道名匹配
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat == "其他":
            continue
        for kw in keywords:
            if kw.lower() in name.lower():
                return cat

    return "其他"

def classify_all(channels: list) -> dict:
    """将所有频道分类，返回 {分类名称: [channel_dict, ...]}"""
    classified = {}
    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        # 调用 to_dict 方法（MergedChannel 和 Channel 都有）
        classified[cat].append(ch.to_dict())

    # 可对每个分类内的频道按名称排序
    for cat in classified:
        classified[cat].sort(key=lambda x: x["name"])

    # 输出统计
    print("📊 分类统计：")
    for cat, lst in classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    return classified
