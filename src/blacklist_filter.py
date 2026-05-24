#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 黑名单过滤模块（支持正则表达式）
- 支持对象和字典类型的频道
- 支持单个 url 或 urls 列表
- 黑名单文件每行一个关键字，可以是普通字符串或正则表达式（自动检测）
"""

import os
import re
from typing import List, Any, Union

class BlacklistFilter:
    def __init__(self, blacklist_file: str = "blacklist.txt"):
        self.blacklist_file = blacklist_file
        self.patterns: List[Union[str, re.Pattern]] = []  # 存储原始字符串或编译后的正则
        self._load()

    def _load(self):
        if not os.path.exists(self.blacklist_file):
            print(f"⚠️ 黑名单文件不存在: {self.blacklist_file}")
            return
        with open(self.blacklist_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # 检测是否为正则表达式（包含 . * + ? [ ] ( ) { } \ 等特殊字符）
                if re.search(r'[\.\*\?\+\[\]\(\)\{\}\\]', line):
                    try:
                        pattern = re.compile(line, re.IGNORECASE)
                        self.patterns.append(pattern)
                    except re.error as e:
                        print(f"⚠️ 正则表达式错误: {line} -> {e}")
                else:
                    # 普通字符串，转为小写用于子串匹配
                    self.patterns.append(line.lower())
        print(f"✅ 已加载 {len(self.patterns)} 条黑名单规则（支持正则）")

    def is_blacklisted(self, url: str) -> bool:
        """检查 URL 是否命中黑名单"""
        url_lower = url.lower()
        for p in self.patterns:
            if isinstance(p, re.Pattern):
                if p.search(url):
                    return True
            else:
                if p in url_lower:
                    return True
        return False

    def channel_should_be_filtered(self, channel: Any) -> bool:
        """检查一个频道是否应该被过滤（任何 URL 命中黑名单则返回 True）"""
        urls = []

        # 获取所有 URL
        if hasattr(channel, 'urls') and channel.urls:
            urls = channel.urls
        elif isinstance(channel, dict) and 'urls' in channel and channel['urls']:
            urls = channel['urls']
        elif hasattr(channel, 'url') and channel.url:
            urls = [channel.url]
        elif isinstance(channel, dict) and 'url' in channel and channel['url']:
            urls = [channel['url']]

        for url in urls:
            if self.is_blacklisted(url):
                return True
        return False

    def filter_channels(self, channels: List[Any]) -> List[Any]:
        """过滤频道列表，移除命中黑名单的频道"""
        original_count = len(channels)
        filtered = [ch for ch in channels if not self.channel_should_be_filtered(ch)]
        print(f"🛡️ 黑名单过滤：{original_count} -> {len(filtered)} 个频道")
        return filtered

# 全局单例
_filter = None

def get_blacklist_filter() -> BlacklistFilter:
    global _filter
    if _filter is None:
        _filter = BlacklistFilter()
    return _filter
