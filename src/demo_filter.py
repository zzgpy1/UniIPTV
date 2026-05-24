#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 频道筛选与排序模块
兼容对象和字典类型的频道输入
"""

import re
import os
from typing import List, Tuple, Any

def parse_demo_order(demo_file: str = "demo.txt") -> List[Tuple[str, str]]:
    """解析 demo.txt，返回有序列表 [(分类名, 频道名), ...]"""
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
            if line.endswith(",#genre#"):
                current_category = line[:-7]
                continue
            if line.startswith('#'):
                continue
            if current_category is not None:
                order.append((current_category, line))
            else:
                order.append(("其他", line))
    print(f"📋 从 demo.txt 解析到 {len(order)} 个有序频道，共 {len(set(cat for cat, _ in order))} 个分类")
    return order

def normalize_name(name: str) -> str:
    """标准化频道名用于匹配"""
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

def get_channel_name(channel: Any) -> str:
    """兼容获取频道名：支持对象（有 name 属性）或字典（有 name 键）"""
    if hasattr(channel, 'name'):
        return channel.name
    elif isinstance(channel, dict):
        return channel.get('name', '')
    return ''

def match_channel_name(channel_name: str, demo_name: str) -> bool:
    """判断采集到的频道名是否匹配 demo 中的频道名"""
    std_c = normalize_name(channel_name)
    std_d = normalize_name(demo_name)
    if std_c == std_d:
        return True
    if std_d in std_c or std_c in std_d:
        return True
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
    channels: 采集到的频道列表（元素可以是对象或字典，需有 name 属性/键）
    返回：按 demo 顺序排列的频道列表（保持原类型）
    """
    demo_order = parse_demo_order(demo_file)
    if not demo_order:
        print("⚠️ demo.txt 为空或不存在，保留原顺序")
        return channels

    # 构建标准化名 -> 频道索引列表的映射
    index = {}
    for idx, ch in enumerate(channels):
        name = get_channel_name(ch)
        if not name:
            continue
        norm = normalize_name(name)
        if norm not in index:
            index[norm] = []
        index[norm].append((idx, ch))

    matched_channels = []
    used = set()

    for category, demo_name in demo_order:
        norm_demo = normalize_name(demo_name)
        matched = False
        # 精确匹配
        if norm_demo in index:
            for idx, ch in index[norm_demo]:
                if idx not in used:
                    matched_channels.append(ch)
                    used.add(idx)
                    matched = True
                    break
        if not matched:
            # 模糊匹配
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

    print(f"🎯 Demo 筛选：原始 {len(channels)} 个频道 -> 匹配 {len(matched_channels)} 个频道（按 demo 顺序）")
    return matched_channels
