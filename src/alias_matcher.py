# src/alias_matcher.py
# 别名匹配模块：使用正则表达式将采集到的频道名映射到标准名称

import re
import os
from typing import Dict, Optional, Tuple

class AliasMatcher:
    """别名匹配器，加载 alias.txt 中的规则并应用"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_rules()
        return cls._instance

    def _load_rules(self, file_path: str = "alias.txt"):
        """加载别名规则文件，格式：正则表达式 => 替换后的标准名称"""
        self.rules = []
        if not os.path.exists(file_path):
            print(f"⚠️ alias.txt 文件不存在: {file_path}，别名匹配功能不可用")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # 支持两种格式：
                # 1. pattern => replacement
                # 2. pattern = replacement
                if "=>" in line:
                    parts = line.split("=>", 1)
                elif "=" in line:
                    parts = line.split("=", 1)
                else:
                    continue
                if len(parts) != 2:
                    continue
                pattern = parts[0].strip()
                replacement = parts[1].strip()
                if pattern and replacement:
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        self.rules.append((regex, replacement))
                    except re.error as e:
                        print(f"⚠️ 正则表达式错误: {pattern} - {e}")

        print(f"📌 加载了 {len(self.rules)} 条别名匹配规则")

    def apply(self, name: str) -> Tuple[str, bool]:
        """
        应用别名规则，返回 (新名称, 是否匹配)
        如果匹配到规则，返回替换后的名称和 True；否则返回原名称和 False
        """
        for regex, replacement in self.rules:
            if regex.search(name):
                new_name = regex.sub(replacement, name)
                return new_name, True
        return name, False

    def apply_for_matching(self, name: str) -> str:
        """
        用于匹配时应用别名，返回转换后的名称（用于与 demo 频道名比较）
        只进行转换，不关心是否匹配
        """
        for regex, replacement in self.rules:
            if regex.search(name):
                return regex.sub(replacement, name)
        return name

# 全局单例
_matcher = None

def get_alias_matcher() -> AliasMatcher:
    global _matcher
    if _matcher is None:
        _matcher = AliasMatcher()
    return _matcher
