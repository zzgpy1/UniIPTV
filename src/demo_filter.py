# src/demo_filter.py
# 根据 demo.txt 筛选和排序频道

import os
import re
from typing import Dict, List, Any

def parse_demo_file(file_path: str = "demo.txt") -> Dict[str, List[str]]:
    """
    解析 demo.txt，返回期望的分类和频道名列表（原始顺序）
    格式示例：
        📺央视频道,#genre#
        CCTV-1
        CCTV-2
        ...
        📡卫视频道,#genre#
        湖南卫视
        ...
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
        # 匹配分类行：以任意字符开头，末尾为 ",#genre#"
        if line.endswith(",#genre#"):
            current_cat = line[:-7]  # 去掉末尾的 ,#genre#
            categories[current_cat] = []
        elif current_cat is not None:
            # 频道名行（排除注释）
            if not line.startswith("#"):
                categories[current_cat].append(line)

    print(f"📋 从 demo.txt 加载了 {len(categories)} 个分类，共 {sum(len(v) for v in categories.values())} 个期望频道")
    return categories

def normalize_name(name: str) -> str:
    """标准化频道名用于匹配（去除清晰度、括号、特殊符号）"""
    # 去除分辨率标签
    name = re.sub(r'\s*(?:1080[pi]|720[pi]|4K|8K|HD|高清|超清|标清|流畅|付费)\s*', '', name, flags=re.IGNORECASE)
    # 去除括号及内容
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 去除多余空格
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def filter_and_reorder_by_demo(classified: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    根据 demo.txt 筛选和重排分类及频道
    输入：classify_all 返回的分类字典
    输出：仅包含 demo 中指定频道的分类字典，顺序与 demo.txt 一致
    """
    demo_cats = parse_demo_file()
    if not demo_cats:
        print("⚠️ 未加载到 demo 数据，将跳过筛选")
        return classified

    # 构建期望频道集合（标准化后）
    expected_channels = {}
    for cat, ch_list in demo_cats.items():
        for ch in ch_list:
            norm = normalize_name(ch)
            expected_channels[norm] = (cat, ch)  # 存储期望的分类和原始名称

    # 从现有分类中提取频道
    all_channels = []
    for cat, channels in classified.items():
        for ch in channels:
            all_channels.append(ch)

    # 匹配并收集
    matched = {}  # {标准化名: channel_dict}
    for ch in all_channels:
        name = ch.get("name", "")
        norm = normalize_name(name)
        if norm in expected_channels:
            # 使用 demo 中的原始名称（可选，保持统一）
            # ch["name"] = expected_channels[norm][1]  # 取消注释可强制使用 demo 中的名称
            matched[norm] = ch

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
    for cat, lst in result.items():
        if lst:
            print(f"   {cat}: {len(lst)} 个")

    return result
