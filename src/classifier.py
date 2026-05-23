# src/classifier.py
# 智能分类模块（支持字典和对象输入，增强地方频道识别）

from src.config import CATEGORY_KEYWORDS, CCTV_ORDER

# 中国所有省份/自治区/直辖市名称（用于匹配地方频道）
PROVINCES = [
    "北京", "天津", "上海", "重庆",
    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "海南", "四川",
    "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆",
    "香港", "澳门"
]

# 市级名称常见后缀
CITY_SUFFIX = ["市", "州", "地区", "盟"]

def get_channel_attribute(ch, attr, default=""):
    """兼容获取频道属性（支持字典和对象）"""
    if isinstance(ch, dict):
        return ch.get(attr, default)
    else:
        return getattr(ch, attr, default)

def classify_channel(channel) -> str:
    """根据 group-title 或频道名匹配分类（兼容字典和对象）"""
    name = get_channel_attribute(channel, 'name', '')
    group = get_channel_attribute(channel, 'group_title', '')
    
    # 优先使用 group-title
    if group:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == "其他":
                continue
            for kw in keywords:
                if kw.lower() in group.lower():
                    return cat
    
    # 降级使用频道名匹配
    # 先匹配央视
    for kw in CATEGORY_KEYWORDS.get("央视", []):
        if kw.lower() in name.lower():
            return "央视"
    
    # 匹配卫视（频道名中包含“卫视”）
    if "卫视" in name:
        return "卫视"
    
    # 匹配地方：检查频道名中是否包含省份名称或“市”、“州”等
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
    """
    将所有频道分类，返回 {分类名称: [channel_dict, ...]}
    分类顺序：央视、卫视、地方、体育、动漫、新闻、影视、音乐、教育、纪录片、其他
    """
    # 初始化分类字典
    classified = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    classified["其他"] = []
    
    for ch in channels:
        cat = classify_channel(ch)
        if cat not in classified:
            classified[cat] = []
        
        # 转换为统一字典格式（确保有 name, url, urls, group_title 等字段）
        if isinstance(ch, dict):
            ch_dict = ch.copy()
            # 确保 urls 字段存在（如果没有，则用 url 构造）
            if "urls" not in ch_dict:
                ch_dict["urls"] = [ch_dict.get("url", "")]
        else:
            # 对象转字典
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
    
    # 定义分类显示顺序
    category_order = ["央视", "卫视", "地方", "体育", "动漫", "新闻", "影视", "音乐", "教育", "纪录片", "其他"]
    
    # 对每个分类内的频道进行排序
    result = {}
    for cat in category_order:
        if cat not in classified:
            result[cat] = []
            continue
        
        if cat == "央视":
            def ctv_key(ch):
                name = ch.get("name", "")
                for idx, standard_name in enumerate(CCTV_ORDER):
                    if standard_name.lower() in name.lower() or name.lower() in standard_name.lower():
                        return idx
                return len(CCTV_ORDER)
            result[cat] = sorted(classified[cat], key=ctv_key)
        else:
            result[cat] = sorted(classified[cat], key=lambda x: x.get("name", ""))
    
    # 输出统计
    print("📊 分类统计：")
    for cat, lst in result.items():
        if lst:
            print(f"  {cat}: {len(lst)} 个频道")
        else:
            print(f"  {cat}: 0 个频道")
    return result
