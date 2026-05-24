# src/blacklist.py
import os
import re
from typing import List, Optional

class Blacklist:
    _instance = None
    _keywords: List[str] = []
    _compiled_patterns: List[re.Pattern] = []
    _file_path: Optional[str] = None
    _last_mtime: float = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, file_path: str = "blacklist.txt"):
        """加载黑名单文件，如果文件已修改则重新加载"""
        self._file_path = file_path
        if not os.path.exists(file_path):
            if self._keywords:  # 之前加载过，现在文件不见了
                print(f"⚠️ 黑名单文件不存在: {file_path}，清空黑名单")
                self._keywords = []
                self._compiled_patterns = []
            else:
                print(f"⚠️ 黑名单文件不存在: {file_path}，跳过黑名单过滤")
            return

        # 检查文件修改时间，如果未变更则跳过
        mtime = os.path.getmtime(file_path)
        if mtime == self._last_mtime and self._compiled_patterns:
            return

        keywords = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keywords.append(line)

        if keywords:
            self._keywords = keywords
            self._compiled_patterns = [re.compile(kw, re.IGNORECASE) for kw in keywords]
            print(f"🚫 黑名单已加载: {len(keywords)} 个关键字")
        else:
            self._keywords = []
            self._compiled_patterns = []
            print("🚫 黑名单文件为空，不进行过滤")
        self._last_mtime = mtime

    def is_blacklisted(self, url: str) -> bool:
        """检查 URL 是否匹配黑名单中的任一关键字"""
        # 确保已加载（懒加载）
        if self._file_path is None:
            self.load()
        if not self._compiled_patterns:
            return False
        for pattern in self._compiled_patterns:
            if pattern.search(url):
                return True
        return False

    def reload(self):
        """重新加载黑名单"""
        if self._file_path:
            self._last_mtime = 0  # 强制重新加载
            self.load(self._file_path)

# 全局单例
_blacklist = None

def get_blacklist() -> Blacklist:
    global _blacklist
    if _blacklist is None:
        _blacklist = Blacklist()
    return _blacklist

def is_blacklisted(url: str) -> bool:
    return get_blacklist().is_blacklisted(url)

def reload_blacklist():
    get_blacklist().reload()
