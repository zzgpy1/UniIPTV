#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
别名匹配模块
从 alias.txt 加载映射，格式：标准名称,别名1,别名2,...
支持正则表达式别名（以 re: 开头）
"""

import re
import os
from typing import Dict, Optional, Union

class AliasMatcher:
    def __init__(self, alias_file: str = "alias.txt"):
        self.alias_file = alias_file
        self.mappings: Dict[Union[str, re.Pattern], str] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.alias_file):
            print(f"⚠️ 别名文件不存在: {self.alias_file}")
            return
        with open(self.alias_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # 使用逗号分隔（修复：原来错误使用了竖线）
                parts = line.split(',')
                if len(parts) < 2:
                    print(f"⚠️ 别名文件第 {line_num} 行格式错误（至少需要标准名和一个别名），跳过: {line}")
                    continue
                standard = parts[0].strip()
                aliases = parts[1:]
                for alias in aliases:
                    alias = alias.strip()
                    if not alias:
                        continue
                    if alias.startswith('re:'):
                        # 正则表达式别名
                        pattern_str = alias[3:].strip()
                        try:
                            pattern = re.compile(pattern_str, re.IGNORECASE)
                            self.mappings[pattern] = standard
                        except re.error as e:
                            print(f"⚠️ 别名文件第 {line_num} 行正则错误: {e}")
                    else:
                        # 普通字符串别名（转小写用于不区分大小写匹配）
                        self.mappings[alias.lower()] = standard
        print(f"✅ 已加载 {len(self.mappings)} 条别名规则")

    def match(self, channel_name: str) -> Optional[str]:
        if not channel_name:
            return None
        name_lower = channel_name.lower()
        # 优先匹配普通字符串（精确子串）
        for alias, standard in self.mappings.items():
            if isinstance(alias, str):
                if alias in name_lower:
                    return standard
        # 再匹配正则表达式
        for pattern, standard in self.mappings.items():
            if isinstance(pattern, re.Pattern):
                if pattern.search(channel_name):
                    return standard
        return None

    def get_all_standard_names(self) -> set:
        return set(self.mappings.values())

_matcher = None

def get_alias_matcher() -> AliasMatcher:
    global _matcher
    if _matcher is None:
        _matcher = AliasMatcher()
    return _matcher
