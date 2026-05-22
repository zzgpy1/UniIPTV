# 根据 demo 列表过滤和重排频道
import re
from src.demo_parser import parse_demo_file
from src.config import DEMO_FILE

def normalize_name(name: str) -> str:
    """
    标准化频道名用于匹配：
    - 转小写
    - 去除括号内容（如 “（HD）”）
    - 去除常见修饰词：“高清”、“HD”、“超清”、“4K”、“标清”、“频道”、“卫视”、“综合”
    - 去除多余空格、特殊符号（保留字母数字、中文、-、+）
    """
    if not name:
        return ""
    # 转小写
    n = name.lower()
    # 去除括号及内容
    n = re.sub(r'[（(][^）)]*[）)]', '', n)
    # 去除常见后缀
    remove_words = ['高清', 'hd', '超清', '4k', '标清', '频道', '卫视', '综合']
    for w in remove_words:
        n = n.replace(w, '')
    # 只保留字母数字中文 - + 空格（空格后续去除）
    n = re.sub(r'[^a-z0-9\u4e00-\u9fa5\-+]', '', n)
    # 去除首尾空格和内部多余空格
    n = ' '.join(n.split())
    return n.strip()

def build_demo_map(demo_file=DEMO_FILE):
    """
    构建期望频道集合和分类顺序映射
    返回：
        expected_set: set of normalized names
        category_order: list of category names (顺序)
        category_channels: dict {category: [original_name1, ...]}（原始顺序）
        normalized_to_original: dict {normalized_name: original_name}
    """
    cat_dict = parse_demo_file(demo_file)
    expected_set = set()
    category_order = []
    category_channels = {}
    normalized_to_original = {}
    for cat, ch_list in cat_dict.items():
        category_order.append(cat)
        category_channels[cat] = []
        for ch in ch_list:
            norm = normalize_name(ch)
            expected_set.add(norm)
            normalized_to_original[norm] = ch   # 保留原始写法用于输出
            category_channels[cat].append(norm)
    return expected_set, category_order, category_channels, normalized_to_original

def filter_and_reorder(channels_dict, demo_file=DEMO_FILE):
    """
    输入：classify_all 返回的字典 {分类: [{name, url, ...}]}
    输出：按 demo 分类和顺序重新组织的字典
    """
    expected_set, category_order, demo_cat_channels, norm_to_orig = build_demo_map(demo_file)
    
    # 构建原始频道映射： normalized_name -> channel_dict
    original_map = {}
    for cat, ch_list in channels_dict.items():
        for ch in ch_list:
            norm = normalize_name(ch["name"])
            if norm in expected_set:
                # 保留第一次出现（去重）
                if norm not in original_map:
                    original_map[norm] = ch
    
    # 按 demo 分类重新组织
    result = {}
    for cat in category_order:
        result[cat] = []
        for norm_name in demo_cat_channels[cat]:
            if norm_name in original_map:
                # 输出时使用原始频道名（保留原样）
                ch = original_map[norm_name].copy()
                # 可选：将 name 替换为 demo 中的原始名称（保持统一）
                # ch["name"] = norm_to_orig[norm_name]
                result[cat].append(ch)
    
    # 打印统计
    total_matched = sum(len(v) for v in result.values())
    print(f"🎯 Demo 过滤完成：匹配 {total_matched} 个频道（期望总数 {len(expected_set)}）")
    for cat, lst in result.items():
        print(f"   {cat}: {len(lst)} 个")
    return result
