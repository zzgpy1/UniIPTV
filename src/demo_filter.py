# src/demo_filter.py
# 根据 demo.txt 筛选和排序频道，支持别名匹配

import os
import re
from typing import Dict, List, Any
from src.alias_matcher import get_alias_matcher

def parse_demo_file(file_path: str = "demo.txt") -> Dict[str, List[str]]:
    """
    解析 demo.txt，返回期望的分类和频道名列表（原始顺序）
    """
    if not os.path.exists(file_path):
        print(f"⚠️ demo.txt 文件不存在: {file_path}，将跳过筛选")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    categories = {}
    current_cat = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.endswith(",#genre#"):
            current_cat = line[:-7]
            categories[current_cat] = []
        elif current_cat is not None:
            if not line.startswith("#"):
                categories[current_cat].append(line)

    print(f"📋 从 demo.txt 加载了 {len(categories)} 个分类，共 {sum(len(v) for v in categories.values())} 个期望频道")
    return categories

def normalize_name(name: str) -> str:
    """标准化频道名用于匹配（去除清晰度、括号、特殊符号）"""
    name = re.sub(r'\s*(?:1080[pi]|720[pi]|4K|8K|HD|高清|超清|标清|流畅|付费)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def filter_and_reorder_by_demo(classified: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    根据 demo.txt 筛选和重排分类及频道，支持别名匹配
    """
    demo_cats = parse_demo_file()
    if not demo_cats:
        print("⚠️ 未加载到 demo 数据，将跳过筛选")
        return classified

    # 获取别名匹配器
    alias_matcher = get_alias_matcher()

    # 构建期望频道集合（标准化后）
    expected_channels = {}  # {标准化名: (分类, 原始名称)}
    for cat, ch_list in demo_cats.items():
        for ch in ch_list:
            norm = normalize_name(ch)
            expected_channels[norm] = (cat, ch)

    # 从现有分类中提取频道
    all_channels = []
    for cat, channels in classified.items():
        for ch in channels:
            all_channels.append(ch)

    # 匹配并收集
    matched = {}  # {标准化名: channel_dict}
    alias_matched_count = 0
    for ch in all_channels:
        name = ch.get("name", "")
        norm_original = normalize_name(name)

        # 首先尝试直接匹配
        if norm_original in expected_channels:
            matched[norm_original] = ch
            continue

        # 应用别名转换后再匹配
        transformed = alias_matcher.apply_for_matching(name)
        if transformed != name:
            norm_transformed = normalize_name(transformed)
            if norm_transformed in expected_channels:
                # 匹配成功，将原频道的名称替换为转换后的名称（可选，保持输出一致性）
                ch["original_name"] = name  # 保存原始名
                ch["name"] = transformed    # 替换为别名后的名称
                matched[norm_transformed] = ch
                alias_matched_count += 1
                continue

    # 按 demo 分类和顺序组织输出
    result = {}
    for cat, ch_list in demo_cats.items():
        result[cat] = []
        for demo_name in ch_list:
            norm = normalize_name(demo_name)
            if norm in matched:
                result[cat].append(matched[norm])

    # 统计
    total_matched = sum(len(v) for v in result.values())
    print(f"🎯 Demo 筛选完成：匹配 {total_matched} 个频道（期望 {len(expected_channels)} 个）")
    if alias_matched_count > 0:
        print(f"   其中通过别名匹配成功: {alias_matched_count} 个")
    for cat, lst in result.items():
        if lst:
            print(f"   {cat}: {len(lst)} 个")

    return result
