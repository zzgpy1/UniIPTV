#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
别名匹配模块
从 alias.txt 加载正则表达式映射，将频道名标准化为统一名称
"""

import re
import os
from typing import Dict, Optional

class AliasMatcher:
    """别名匹配器"""
    
    def __init__(self, alias_file: str = "alias.txt"):
        self.alias_file = alias_file
        self.mappings: Dict[re.Pattern, str] = {}
        self._load()
    
    def _load(self):
        """加载别名映射文件"""
        if not os.path.exists(self.alias_file):
            print(f"⚠️ 别名文件不存在: {self.alias_file}")
            return
        
        with open(self.alias_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # 格式：正则表达式|标准化名称
                if '|' not in line:
                    print(f"⚠️ 别名文件第 {line_num} 行格式错误，跳过: {line}")
                    continue
                pattern_str, target = line.split('|', 1)
                pattern_str = pattern_str.strip()
                target = target.strip()
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    self.mappings[pattern] = target
                except re.error as e:
                    print(f"⚠️ 别名文件第 {line_num} 行正则错误: {e}")
        
        print(f"✅ 已加载 {len(self.mappings)} 条别名规则")
    
    def match(self, channel_name: str) -> Optional[str]:
        """
        匹配别名，返回标准化后的名称；若无匹配返回 None
        """
        for pattern, target in self.mappings.items():
            if pattern.search(channel_name):
                return target
        return None
    
    def get_all_standard_names(self) -> set:
        """获取所有标准化名称集合（用于 demo 匹配）"""
        return set(self.mappings.values())

# 全局单例
_matcher = None

def get_alias_matcher() -> AliasMatcher:
    global _matcher
    if _matcher is None:
        _matcher = AliasMatcher()
    return _matcher
