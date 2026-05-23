# src/classifier.py
from src.config import CATEGORY_KEYWORDS

# 需要剔除的关键词（频道名中包含这些词则丢弃）
EXCLUDED_KEYWORDS = ["旅游", "春晚","游戏"]

def is_excluded_channel(channel_name: str) -> bool:
    """检查频道名是否包含排除关键词"""
    name_lower = channel_name.lower()
    for kw in EXCLUDED_KEYWORDS:
        if kw in name_lower:
            return True
    return False

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
    """将所有频道分类，并过滤掉排除的频道，返回 {分类名称: [channel_dict, ...]}"""
    classified = {}
    total_before = len(channels)
    filtered_count = 0

    for ch in channels:
        # 剔除包含排除关键词的频道
        if is_excluded_channel(ch.name):
            filtered_count += 1
            continue

        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        classified[cat].append(ch.to_dict())   # 使用 to_dict() 方法

    # 对每个分类内的频道按名称排序
    for cat in classified:
        classified[cat].sort(key=lambda x: x["name"])

    print(f"📊 分类统计：")
    print(f"  剔除频道（旅游/春晚）: {filtered_count}")
    for cat, lst in classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    print(f"  总计有效频道: {sum(len(lst) for lst in classified.values())}")
    return classified
