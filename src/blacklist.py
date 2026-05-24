# src/blacklist.py
# 黑名单过滤模块：根据 blacklist.txt 中的关键字拦截接口

import os
import re
from typing import List

class Blacklist:
    _instance = None
    _keywords: List[str] = []
    _compiled_patterns: List[re.Pattern] = []
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, file_path: str = "blacklist.txt"):
        """加载黑名单文件，每行一个关键字（支持正则表达式）"""
        if self._loaded:
            return
        if not os.path.exists(file_path):
            print(f"⚠️ 黑名单文件不存在: {file_path}，跳过黑名单过滤")
            self._loaded = True
            return

        keywords = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # 支持注释行
                    keywords.append(line)

        if keywords:
            self._keywords = keywords
            # 将关键字编译为正则表达式（不区分大小写）
            self._compiled_patterns = [re.compile(kw, re.IGNORECASE) for kw in keywords]
            print(f"🚫 黑名单已加载: {len(keywords)} 个关键字")
        else:
            print("🚫 黑名单文件为空，不进行过滤")
        self._loaded = True

    def is_blacklisted(self, url: str) -> bool:
        """检查 URL 是否匹配黑名单中的任一关键字"""
        if not self._compiled_patterns:
            return False
        for pattern in self._compiled_patterns:
            if pattern.search(url):
                return True
        return False

    def get_keywords(self) -> List[str]:
        return self._keywords

# 全局单例
_blacklist = None

def get_blacklist() -> Blacklist:
    global _blacklist
    if _blacklist is None:
        _blacklist = Blacklist()
        _blacklist.load()
    return _blacklist

def is_blacklisted(url: str) -> bool:
    """便捷函数：检查 URL 是否被黑名单拦截"""
    return get_blacklist().is_blacklisted(url)
