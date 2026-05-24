# src/classifier.py
# 智能分类模块（兼容字典和对象）

from src.config import CATEGORY_KEYWORDS, CCTV_ORDER

PROVINCES = [
    "北京", "天津", "上海", "重庆",
    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "海南", "四川",
    "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆",
    "香港", "澳门"
]

CITY_SUFFIX = ["市", "州", "地区", "盟"]

def _get_name_and_group(channel):
    """统一获取频道名和 group_title，兼容对象和字典"""
    if isinstance(channel, dict):
        return channel.get('name', ''), channel.get('group_title', '')
    else:
        return getattr(channel, 'name', ''), getattr(channel, 'group_title', '')

def classify_channel(channel) -> str:
    """根据频道名匹配分类（兼容对象和字典）"""
    name, group = _get_name_and_group(channel)
    
    # 优先使用 group-title
    if group:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == "其他":
                continue
            for kw in keywords:
                if kw.lower() in group.lower():
                    return cat
    
    # 央视匹配
    for kw in CATEGORY_KEYWORDS.get("央视", []):
        if kw.lower() in name.lower():
            return "央视"
    
    # 卫视匹配
    if "卫视" in name:
        return "卫视"
    
    # 地方匹配
    for prov in PROVINCES:
        if prov in name:
            return "地方"
    for suffix in CITY_SUFFIX:
        if suffix in name:
            return "地方"
    if any(k in name for k in ["电视台", "综合频道", "公共频道", "生活频道", "新闻综合"]):
        return "地方"
    
    # 其他分类
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat in ["央视", "卫视", "地方", "其他"]:
            continue
        for kw in keywords:
            if kw.lower() in name.lower():
                return cat
    
    return "其他"

def classify_all(channels: list) -> dict:
    """分类所有频道（兼容对象和字典）"""
    classified = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    classified["其他"] = []
    
    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        # 转换为字典格式
        if isinstance(ch, dict):
            ch_dict = ch
        elif hasattr(ch, 'to_dict'):
            ch_dict = ch.to_dict()
        else:
            ch_dict = {
                "name": getattr(ch, 'name', ''),
                "url": getattr(ch, 'url', ''),
                "urls": getattr(ch, 'urls', [getattr(ch, 'url', '')]),
                "group_title": getattr(ch, 'group_title', ''),
                "id": getattr(ch, 'tvg_id', ''),
                "logo": getattr(ch, 'tvg_logo', ''),
                "latency": getattr(ch, 'latency', 9999),
                "video_codec": getattr(ch, 'video_codec', ''),
                "ip_info": getattr(ch, 'ip_info', None)
            }
        classified[cat].append(ch_dict)
    
    # 分类显示顺序
    category_order = ["央视", "卫视", "地方", "体育", "动漫", "新闻", "影视", "音乐", "教育", "纪录片", "其他"]
    result = {}
    for cat in category_order:
        if cat not in classified:
            result[cat] = []
            continue
        if cat == "央视":
            def ctv_key(ch):
                name = ch["name"]
                for idx, std in enumerate(CCTV_ORDER):
                    if std.lower() in name.lower() or name.lower() in std.lower():
                        return idx
                return len(CCTV_ORDER)
            result[cat] = sorted(classified[cat], key=ctv_key)
        else:
            result[cat] = sorted(classified[cat], key=lambda x: x["name"])
    
    print("📊 分类统计：")
    for cat, lst in result.items():
        if lst:
            print(f"  {cat}: {len(lst)} 个频道")
    return result
