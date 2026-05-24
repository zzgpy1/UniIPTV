#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 黑名单过滤模块
- 支持对象和字典类型的频道
- 支持单个 url 或 urls 列表
- 只要任意 URL 命中黑名单，整个频道被过滤
"""

import os
from typing import List, Any

class BlacklistFilter:
    def __init__(self, blacklist_file: str = "blacklist.txt"):
        self.blacklist_file = blacklist_file
        self.keywords: List[str] = []
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
                self.keywords.append(line.lower())
        print(f"✅ 已加载 {len(self.keywords)} 条黑名单关键字")

    def is_blacklisted(self, url: str) -> bool:
        """检查单个 URL 是否命中黑名单"""
        url_lower = url.lower()
        for kw in self.keywords:
            if kw in url_lower:
                return True
        return False

    def channel_should_be_filtered(self, channel: Any) -> bool:
        """
        检查一个频道是否应该被过滤（任何 URL 命中黑名单则返回 True）
        支持：对象（有 url 或 urls 属性）或字典（有 'url' 或 'urls' 键）
        """
        urls = []

        # 1. 尝试获取 urls 列表
        if hasattr(channel, 'urls') and channel.urls:
            urls = channel.urls
        elif isinstance(channel, dict) and 'urls' in channel and channel['urls']:
            urls = channel['urls']
        # 2. 尝试获取单个 url
        elif hasattr(channel, 'url') and channel.url:
            urls = [channel.url]
        elif isinstance(channel, dict) and 'url' in channel and channel['url']:
            urls = [channel['url']]

        # 检查所有 URL
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
