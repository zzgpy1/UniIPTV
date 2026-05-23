# src/classifier.py
from src.config import CATEGORY_KEYWORDS

# 需要剔除的关键词（频道名中包含这些词则丢弃）
EXCLUDED_KEYWORDS = ["旅游", "春晚"]

def is_excluded_channel(channel_name: str) -> bool:
    name_lower = channel_name.lower()
    for kw in EXCLUDED_KEYWORDS:
        if kw in name_lower:
            return True
    return False

def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类，优先匹配省份"""
    name = channel.name
    group = getattr(channel, 'group_title', '')

    # 省份列表（用于地方分类）
    provinces = [
        "北京", "天津", "上海", "重庆",
        "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东",
        "河南", "湖北", "湖南", "广东", "海南", "四川",
        "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
        "内蒙古", "广西", "西藏", "宁夏", "新疆",
        "香港", "澳门"
    ]

    # 优先匹配省份（将频道归入对应省份分类）
    for p in provinces:
        if p in name or p in group:
            return p

    # 再匹配其他预定义分类
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat == "其他":
            continue
        for kw in keywords:
            if kw.lower() in name.lower() or kw.lower() in group.lower():
                return cat

    return "其他"

def classify_all(channels: list) -> dict:
    """将所有频道分类，并过滤掉排除的频道"""
    classified = {}
    total_before = len(channels)
    filtered_count = 0

    for ch in channels:
        if is_excluded_channel(ch.name):
            filtered_count += 1
            continue

        cat = classify_channel(ch)
        # 注意：ch 是 MergedChannel 对象，有 to_dict() 方法
        ch_dict = ch.to_dict()
        if cat not in classified:
            classified[cat] = []
        classified[cat].append(ch_dict)

    # 对每个分类内的频道按名称排序
    for cat in classified:
        classified[cat].sort(key=lambda x: x["name"])

    print(f"📊 分类统计：")
    print(f"  剔除频道（旅游/春晚）: {filtered_count}")
    for cat, lst in classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    print(f"  总计有效频道: {sum(len(lst) for lst in classified.values())}")
    return classified
