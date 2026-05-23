# src/classifier.py
# 智能分类模块（修复版）

from src.config import CATEGORY_KEYWORDS, CCTV_ORDER

def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类"""
    # 获取频道名称（兼容 Channel 和 MergedChannel）
    name = getattr(channel, 'name', '')
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
    """
    将所有频道分类，返回 {分类名称: [channel_dict, ...]}
    并按照以下顺序排序：
    1. 央视（内部按 CCTV_ORDER 排序）
    2. 卫视
    3. 地方
    4. 体育
    5. 动漫
    6. 新闻
    7. 影视
    8. 音乐
    9. 教育
    10. 纪录片
    11. 其他
    """
    # 初始化分类字典
    classified = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    classified["其他"] = []
    
    # 分类填入
    for ch in channels:
        cat = classify_channel(ch)
        # 确保分类存在
        if cat not in classified:
            classified[cat] = []
        # 兼容 Channel 对象（有 to_dict 方法）和 MergedChannel（直接转字典）
        if hasattr(ch, 'to_dict'):
            ch_dict = ch.to_dict()
        else:
            # MergedChannel 对象
            ch_dict = {
                "name": getattr(ch, 'name', ''),
                "url": getattr(ch, 'urls', [getattr(ch, 'url', '')])[0] if hasattr(ch, 'urls') else getattr(ch, 'url', ''),
                "urls": getattr(ch, 'urls', [getattr(ch, 'url', '')]),
                "group_title": getattr(ch, 'group_title', ''),
                "id": getattr(ch, 'tvg_id', ''),
                "logo": getattr(ch, 'tvg_logo', ''),
                "latency": getattr(ch, 'latency', 9999),
                "video_codec": getattr(ch, 'video_codec', ''),
                "ip_info": getattr(ch, 'ip_info', None)
            }
        classified[cat].append(ch_dict)
    
    # 定义分类显示顺序（基于 config 中的 CATEGORY_KEYWORDS 键，但将“其他”放在最后）
    category_order = [cat for cat in CATEGORY_KEYWORDS.keys() if cat != "其他"]
    category_order.append("其他")
    
    # 对每个分类内的频道进行排序
    result = {}
    for cat in category_order:
        if cat not in classified:
            result[cat] = []
            continue
        
        if cat == "央视":
            # 央视按 CCTV_ORDER 自定义排序
            def ctv_key(ch):
                name = ch["name"]
                # 尝试匹配顺序列表中的频道
                for idx, standard_name in enumerate(CCTV_ORDER):
                    if standard_name.lower() in name.lower() or name.lower() in standard_name.lower():
                        return idx
                # 未匹配的放到最后，按名称排序
                return len(CCTV_ORDER)
            result[cat] = sorted(classified[cat], key=ctv_key)
        else:
            # 其他分类按频道名称排序
            result[cat] = sorted(classified[cat], key=lambda x: x["name"])
    
    # 输出统计
    print("📊 分类统计：")
    for cat, lst in result.items():
        if lst:
            print(f"  {cat}: {len(lst)} 个频道")
    return result
