# 智能分类模块（增加排序）
from src.config import CATEGORY_KEYWORDS

# 定义分类显示顺序（靠前的先输出）
CATEGORY_ORDER = [
    "央视",
    "卫视",
    "北京频道",
    "上海频道",
    "天津频道",
    "重庆频道",
    "广东频道",
    "浙江频道",
    "江苏频道",
    "安徽频道",
    "福建频道",
    "江西频道",
    "山东频道",
    "河南频道",
    "湖北频道",
    "湖南频道",
    "广西频道",
    "海南频道",
    "四川频道",
    "贵州频道",
    "云南频道",
    "陕西频道",
    "甘肃频道",
    "青海频道",
    "宁夏频道",
    "新疆频道",
    "内蒙古频道",
    "山西频道",
    "辽宁频道",
    "吉林频道",
    "黑龙江频道",
    "河北频道",
    "港·澳·台",
    "体育",
    "动漫",
    "新闻",
    "影视",
    "音乐",
    "教育",
    "纪录片",
    "其他"
]

# 央视频道排序（按数字和名称）
CCTV_ORDER = [
    "CCTV-1", "CCTV-1综合", "CCTV1",
    "CCTV-2", "CCTV-2财经", "CCTV2",
    "CCTV-3", "CCTV-3综艺", "CCTV3",
    "CCTV-4", "CCTV-4中文国际", "CCTV4",
    "CCTV-5", "CCTV-5体育", "CCTV5",
    "CCTV-5+", "CCTV5+",
    "CCTV-6", "CCTV-6电影", "CCTV6",
    "CCTV-7", "CCTV-7军事", "CCTV7",
    "CCTV-8", "CCTV-8电视剧", "CCTV8",
    "CCTV-9", "CCTV-9纪录", "CCTV9",
    "CCTV-10", "CCTV-10科教", "CCTV10",
    "CCTV-11", "CCTV-11戏曲", "CCTV11",
    "CCTV-12", "CCTV-12社会与法", "CCTV12",
    "CCTV-13", "CCTV-13新闻", "CCTV13",
    "CCTV-14", "CCTV-14少儿", "CCTV14",
    "CCTV-15", "CCTV-15音乐", "CCTV15",
    "CCTV-16", "CCTV-16奥林匹克", "CCTV16",
    "CCTV-17", "CCTV-17农业", "CCTV17",
    "CCTV世界地理", "CCTV央视台球", "CCTV女性时尚",
    "CCTV怀旧剧场", "CCTV第一剧场", "CCTV风云足球",
    "CCTV老故事", "CGTN", "CGTN俄语", "CGTN法语",
    "CGTN纪录", "CGTN西语", "CGTN阿语"
]

def get_channel_sort_key(channel_name: str, category: str):
    """返回频道的排序键值，用于分类内排序"""
    name_lower = channel_name.lower()
    
    # 央视频道特殊排序
    if category == "央视":
        for idx, pattern in enumerate(CCTV_ORDER):
            if pattern.lower() in name_lower:
                return (0, idx)
        return (1, channel_name)  # 未匹配的放后面按字母排序
    
    # 卫视频道按常见顺序（可扩展）
    if category == "卫视":
        # 优先：湖南、浙江、江苏、东方、北京等
        priority_order = ["湖南", "浙江", "江苏", "东方", "北京", "广东", "深圳"]
        for idx, p in enumerate(priority_order):
            if p in channel_name:
                return (0, idx)
        return (1, channel_name)
    
    # 其他分类按名称排序
    return (2, channel_name)

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
    """将所有频道分类，返回 {分类名称: [channel_obj, ...]}，并按定义顺序和频道名排序"""
    classified = {}
    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        classified[cat].append(ch)
    
    # 为每个分类内的频道排序
    for cat in classified:
        classified[cat].sort(key=lambda x: get_channel_sort_key(x.name, cat))
    
    # 按预定义顺序输出分类（未在 CATEGORY_ORDER 中的分类放最后）
    sorted_classified = {}
    for cat in CATEGORY_ORDER:
        if cat in classified:
            sorted_classified[cat] = classified[cat]
            del classified[cat]
    # 剩余的分类（如“其他”等）追加
    for cat, ch_list in classified.items():
        sorted_classified[cat] = ch_list
    
    # 打印统计
    print("📊 分类统计：")
    for cat, lst in sorted_classified.items():
        print(f"  {cat}: {len(lst)} 个频道")
    return sorted_classified
