#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from typing import List, Any, Union

class BlacklistFilter:
    def __init__(self, blacklist_file: str = "blacklist.txt"):
        self.blacklist_file = blacklist_file
        self.patterns: List[Union[str, re.Pattern]] = []
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
                if re.search(r'[\.\*\?\+\[\]\(\)\{\}\\]', line):
                    try:
                        pattern = re.compile(line, re.IGNORECASE)
                        self.patterns.append(pattern)
                    except re.error as e:
                        print(f"⚠️ 正则错误: {line} -> {e}")
                else:
                    self.patterns.append(line.lower())
        print(f"✅ 已加载 {len(self.patterns)} 条黑名单规则（支持正则）")

    def is_blacklisted(self, url: str) -> bool:
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
        urls = []
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
        original_count = len(channels)
        filtered = [ch for ch in channels if not self.channel_should_be_filtered(ch)]
        print(f"🛡️ 黑名单过滤：{original_count} -> {len(filtered)} 个频道")
        return filtered

_filter = None

def get_blacklist_filter() -> BlacklistFilter:
    global _filter
    if _filter is None:
        _filter = BlacklistFilter()
    return _filter
