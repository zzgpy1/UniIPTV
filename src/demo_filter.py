#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 频道列表筛选模块（增强版）
支持别名匹配，将频道名标准化后与 demo 列表比对
"""

import re
import os
from typing import Set, List, Dict, Any
from src.alias_matcher import get_alias_matcher
from src.config import DEMO_FILE, ENABLE_DEMO_FILTER, ENABLE_ALIAS

def load_demo_channels(demo_file: str = DEMO_FILE) -> Set[str]:
    """
    从 demo.txt 加载期望的频道名称列表
    返回标准化名称集合（小写，去除特殊字符）
    """
    if not os.path.exists(demo_file):
        print(f"⚠️ Demo 文件不存在: {demo_file}，将跳过筛选")
        return set()
    
    demos = set()
    with open(demo_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 标准化 demo 名称（与频道名匹配时使用的标准化函数一致）
            normalized = normalize_name(line)
            demos.add(normalized)
    print(f"📋 已加载 {len(demos)} 个 Demo 频道")
    return demos

def normalize_name(name: str) -> str:
    """
    标准化频道名，用于匹配
    - 转小写
    - 去除分辨率标签、括号内容
    - 去除特殊符号
    """
    name = name.lower()
    # 去除清晰度标签
    name = re.sub(r'\s*(?:1080[pi]|720[pi]|4k|8k|hd|高清|超清|标清|流畅|付费)\s*', '', name, flags=re.IGNORECASE)
    # 去除括号及内容
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 去除多余空格和特殊符号（保留字母数字中文）
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name.strip()

def filter_by_demo(channels: List[Any], demo_file: str = DEMO_FILE) -> List[Any]:
    """
    根据 demo.txt 筛选频道
    优先使用别名匹配，若无别名则使用标准化名称匹配
    """
    if not ENABLE_DEMO_FILTER:
        print("⚙️ Demo 筛选未启用")
        return channels
    
    demo_set = load_demo_channels(demo_file)
    if not demo_set:
        print("⚠️ Demo 列表为空，保留所有频道")
        return channels
    
    alias_matcher = get_alias_matcher() if ENABLE_ALIAS else None
    
    filtered = []
    for ch in channels:
        # 获取频道名称
        if hasattr(ch, 'name'):
            name = ch.name
        elif isinstance(ch, dict) and 'name' in ch:
            name = ch['name']
        else:
            filtered.append(ch)
            continue
        
        # 尝试别名匹配
        matched = False
        if alias_matcher:
            standard_name = alias_matcher.match(name)
            if standard_name and normalize_name(standard_name) in demo_set:
                matched = True
        
        # 降级使用标准化名称匹配
        if not matched:
            norm_name = normalize_name(name)
            if norm_name in demo_set:
                matched = True
        
        if matched:
            filtered.append(ch)
    
    print(f"🎯 Demo 筛选：{len(channels)} -> {len(filtered)} 个频道")
    return filtered
