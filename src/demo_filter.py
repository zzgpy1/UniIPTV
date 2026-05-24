#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 频道列表筛选模块（修正版）
- 正确解析 demo.txt，忽略分类行（以 ,#genre# 结尾的行）
- 使用宽松的标准化匹配（去除清晰度、括号、空格等）
- 支持别名映射（可选）
"""

import re
import os
from typing import Set, List, Any
from src.alias_matcher import get_alias_matcher
from src.config import DEMO_FILE, ENABLE_DEMO_FILTER, ENABLE_ALIAS

def load_demo_channels(demo_file: str = DEMO_FILE) -> Set[str]:
    """
    从 demo.txt 加载期望的频道名称集合
    忽略分类行（以 ,#genre# 结尾的行），只保留纯频道名
    """
    if not os.path.exists(demo_file):
        print(f"⚠️ Demo 文件不存在: {demo_file}，将跳过筛选")
        return set()
    
    demos = set()
    with open(demo_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 跳过分类行（如 "📺央视频道,#genre#"）
            if line.endswith(",#genre#"):
                continue
            # 跳过注释行
            if line.startswith('#'):
                continue
            # 标准化频道名（用于后续匹配）
            normalized = normalize_name(line)
            if normalized:
                demos.add(normalized)
    print(f"📋 已加载 {len(demos)} 个 Demo 频道（来自 {demo_file}）")
    return demos

def normalize_name(name: str) -> str:
    """
    标准化频道名，用于匹配 demo 列表
    规则：
    - 转小写
    - 去除分辨率标签（1080p、720p、4K、HD等）
    - 去除括号及其内容
    - 去除多余空格和特殊符号（保留字母、数字、中文、连字符、点）
    """
    if not name:
        return ""
    name = name.lower()
    # 去除常见清晰度标签
    name = re.sub(r'\b(?:1080[pi]|720[pi]|4k|8k|hd|uhd|高清|超清|标清|流畅|付费|备\d*)\b', '', name, flags=re.IGNORECASE)
    # 去除括号及其内容（包括中英文括号）
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 去除末尾无意义的符号
    name = re.sub(r'[ _\-]+$', '', name)
    # 保留字母、数字、中文、连字符、点、空格（但后续会压缩空格）
    name = re.sub(r'[^\w\u4e00-\u9fa5\-. ]', '', name)
    # 压缩多个空格为单个空格
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def filter_by_demo(channels: List[Any], demo_file: str = DEMO_FILE) -> List[Any]:
    """
    根据 demo.txt 筛选频道
    优先级：别名匹配（若启用） > 标准化名称匹配
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
        # 获取频道名称（兼容对象和字典）
        if hasattr(ch, 'name'):
            name = ch.name
        elif isinstance(ch, dict) and 'name' in ch:
            name = ch['name']
        else:
            continue
        
        matched = False
        
        # 1. 尝试别名匹配
        if alias_matcher:
            standard_name = alias_matcher.match(name)
            if standard_name:
                std_norm = normalize_name(standard_name)
                if std_norm in demo_set:
                    matched = True
        
        # 2. 降级使用标准化名称匹配
        if not matched:
            norm_name = normalize_name(name)
            if norm_name in demo_set:
                matched = True
        
        if matched:
            filtered.append(ch)
    
    print(f"🎯 Demo 筛选：原始 {len(channels)} 个频道 -> 保留 {len(filtered)} 个频道")
    return filtered
