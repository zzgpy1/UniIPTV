# src/classifier.py
# 智能分类模块

from src.config import CATEGORY_KEYWORDS


def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类，支持 MergedChannel 对象和字典"""
    # 获取频道名和分组
    if hasattr(channel, 'name'):
        name = channel.name
        group = getattr(channel, 'group_title', '')
    else:
        name = channel.get('name', '')
        group = channel.get('group_title', '')
    
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
    """
    将所有频道分类，返回 {分类名称: [频道对象列表]}
    保持每个分类内频道的原始顺序（按延迟排序）
    """
    classified = {}
    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        classified[cat].append(ch)
    
    # 对每个分类内的频道按名称排序（可选）
    for cat in classified:
        if classified[cat] and hasattr(classified[cat][0], 'name'):
            classified[cat].sort(key=lambda x: x.name)
        elif classified[cat] and isinstance(classified[cat][0], dict):
            classified[cat].sort(key=lambda x: x.get('name', ''))
    
    # 输出统计
    print("📊 分类统计：")
    for cat, lst in classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    return classified
