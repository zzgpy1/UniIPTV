#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 频道筛选与排序模块
- 解析 demo.txt，提取分类和频道顺序
- 筛选采集到的频道，只保留 demo 中出现的频道
- 按 demo 顺序输出频道列表
"""

import re
import os
from typing import List, Tuple, Dict, Any, Optional

def parse_demo_order(demo_file: str = "demo.txt") -> List[Tuple[str, str]]:
    """
    解析 demo.txt，返回有序列表 [(分类名, 频道名), ...]
    分类名来自行如 "📺央视频道,#genre#"，频道名是后续行直到下一个分类
    """
    if not os.path.exists(demo_file):
        print(f"⚠️ Demo 文件不存在: {demo_file}")
        return []

    order = []
    current_category = None
    with open(demo_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 分类行格式：任意文字,#genre#
            if line.endswith(",#genre#"):
                # 提取分类名（去掉末尾的 ,#genre#）
                current_category = line[:-7]
                continue
            # 跳过注释行（以 # 开头但不是分类行）
            if line.startswith('#'):
                continue
            # 普通频道名行
            if current_category is not None:
                order.append((current_category, line))
            else:
                # 没有分类行时，归类为“其他”
                order.append(("其他", line))
    print(f"📋 从 demo.txt 解析到 {len(order)} 个有序频道，共 {len(set(cat for cat, _ in order))} 个分类")
    return order

def normalize_name(name: str) -> str:
    """标准化频道名用于匹配（与之前版本一致）"""
    if not name:
        return ""
    name = name.lower()
    # 去除清晰度标签
    name = re.sub(r'\b(?:1080[pi]|720[pi]|4k|8k|hd|uhd|高清|超清|标清|流畅|付费|备\d*)\b', '', name, flags=re.IGNORECASE)
    # 去除括号内容
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 保留字母数字中文连字符点空格
    name = re.sub(r'[^\w\u4e00-\u9fa5\-. ]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def match_channel_name(channel_name: str, demo_name: str) -> bool:
    """
    判断采集到的频道名是否匹配 demo 中的频道名
    支持：
    - 标准化后完全匹配
    - demo 名包含在采集名中（如 demo="CCTV-1", 采集="CCTV-1 高清"）
    - 采集名包含在 demo 名中（如 demo="CCTV-1综合", 采集="CCTV-1"）
    """
    std_c = normalize_name(channel_name)
    std_d = normalize_name(demo_name)
    if std_c == std_d:
        return True
    if std_d in std_c or std_c in std_d:
        return True
    # 额外处理常见变体：去除连字符
    if std_d.replace('-', '') == std_c.replace('-', ''):
        return True
    return False

def filter_and_order_by_demo(
    channels: List[Any],
    demo_file: str = "demo.txt",
    alias_matcher=None
) -> List[Any]:
    """
    根据 demo.txt 筛选并排序频道
    channels: 采集到的频道列表（每个元素可以是对象或字典，需有 name 属性）
    返回：按 demo 顺序排列的频道列表（每个频道保留原有属性）
    """
    demo_order = parse_demo_order(demo_file)
    if not demo_order:
        print("⚠️ demo.txt 为空或不存在，保留原顺序")
        return channels

    # 构建 name -> 频道的映射（优先使用第一个匹配，保留多源信息）
    # 注意：同一个频道名可能对应多个采集到的频道（不同源），我们只保留最好的那个（已在合并时处理好）
    # 这里简化：每个 demo 条目最多匹配一个采集频道
    matched_channels = []  # 按 demo 顺序存放匹配到的频道对象
    used = set()  # 记录已使用的采集频道索引

    # 为提高效率，先将采集频道按 name 建立索引（标准化名 -> 频道列表）
    index = {}
    for idx, ch in enumerate(channels):
        name = ch.name if hasattr(ch, 'name') else ch.get('name', '')
        if not name:
            continue
        norm = normalize_name(name)
        if norm not in index:
            index[norm] = []
        index[norm].append((idx, ch))

    # 按 demo 顺序逐一匹配
    for category, demo_name in demo_order:
        matched = False
        norm_demo = normalize_name(demo_name)
        # 首先尝试直接匹配标准化名
        if norm_demo in index:
            # 取第一个未使用的
            for idx, ch in index[norm_demo]:
                if idx not in used:
                    matched_channels.append(ch)
                    used.add(idx)
                    matched = True
                    break
        if not matched:
            # 尝试模糊匹配（遍历所有未使用的）
            for norm_key, ch_list in index.items():
                if match_channel_name(norm_key, norm_demo):
                    for idx, ch in ch_list:
                        if idx not in used:
                            matched_channels.append(ch)
                            used.add(idx)
                            matched = True
                            break
                if matched:
                    break
        # 如果没有匹配到，跳过该频道（不保留）

    print(f"🎯 Demo 筛选：原始 {len(channels)} 个频道 -> 匹配 {len(matched_channels)} 个频道（按 demo 顺序）")
    return matched_channels
