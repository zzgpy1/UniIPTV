#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 黑名单过滤模块
从 blacklist.txt 加载关键字，过滤包含这些关键字的 URL
"""

import os
from typing import List

class BlacklistFilter:
    """黑名单过滤器"""
    
    def __init__(self, blacklist_file: str = "blacklist.txt"):
        self.blacklist_file = blacklist_file
        self.keywords: List[str] = []
        self._load()
    
    def _load(self):
        """加载黑名单关键字"""
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
        """检查 URL 是否命中黑名单"""
        url_lower = url.lower()
        for kw in self.keywords:
            if kw in url_lower:
                return True
        return False
    
    def filter_channels(self, channels: list) -> list:
        """过滤频道列表，移除 URL 命中黑名单的频道"""
        original_count = len(channels)
        filtered = []
        for ch in channels:
            # 兼容 Channel 对象和字典
            if hasattr(ch, 'url'):
                url = ch.url
            elif isinstance(ch, dict) and 'url' in ch:
                url = ch['url']
            else:
                # 尝试 urls 列表（取第一个）
                if hasattr(ch, 'urls') and ch.urls:
                    url = ch.urls[0]
                elif isinstance(ch, dict) and 'urls' in ch and ch['urls']:
                    url = ch['urls'][0]
                else:
                    filtered.append(ch)
                    continue
            
            if not self.is_blacklisted(url):
                filtered.append(ch)
        
        print(f"🛡️ 黑名单过滤：{original_count} -> {len(filtered)} 个频道")
        return filtered

# 全局单例
_filter = None

def get_blacklist_filter() -> BlacklistFilter:
    global _filter
    if _filter is None:
        _filter = BlacklistFilter()
    return _filter
