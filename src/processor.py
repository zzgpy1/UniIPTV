#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import logging
from typing import List, Dict, Set
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class StreamProcessor:
    """去重和广告过滤处理器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.ad_keywords = self._load_ad_keywords()
        self.user_channels = self._load_user_channels()
    
    def _load_ad_keywords(self) -> Set[str]:
        """加载广告源过滤关键词"""
        keywords = set()
        ad_file = self.config_dir / 'ad_filter.txt'
        if ad_file.exists():
            with open(ad_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        keywords.add(line.lower())
        
        # 默认广告关键词
        default_keywords = {
            'ad', '广告', '推广', '宣传', '商业', 'sponsored',
            'p2p', 'p2p://', 'tracker', 'announce',
            'localhost', '127.0.0.1', 'example.com'
        }
        keywords.update(default_keywords)
        return keywords
    
    def _load_user_channels(self) -> Dict:
        """加载用户自定义频道配置"""
        channels_file = self.config_dir / 'user_channels.json'
        if channels_file.exists():
            with open(channels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"keep": [], "remove": []}
    
    def _is_ad_source(self, stream: Dict) -> bool:
        """判断是否为广告源"""
        url_lower = stream.get('url', '').lower()
        name_lower = stream.get('name', '').lower()
        
        for keyword in self.ad_keywords:
            if keyword in url_lower or keyword in name_lower:
                return True
        return False
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式是否有效"""
        if not url or not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            return False
        if '#' in url or '?' not in url:
            pass  # 允许简单URL
        # 基础长度检查
        if len(url) < 10 or len(url) > 1000:
            return False
        return True
    
    def process(self, streams: List[Dict]) -> List[Dict]:
        """主处理流程"""
        if not streams:
            return []
        
        # 1. 广告过滤
        filtered = []
        ad_count = 0
        for stream in streams:
            if self._is_ad_source(stream):
                ad_count += 1
                continue
            if not self._is_valid_url(stream.get('url', '')):
                continue
            filtered.append(stream)
        
        logger.info(f"广告过滤: 移除 {ad_count} 个源")
        
        # 2. 去重（基于频道名+URL，同一频道保留最佳URL）
        unique_streams = self._deduplicate(filtered)
        dup_count = len(filtered) - len(unique_streams)
        logger.info(f"去重: 移除 {dup_count} 个重复源")
        
        # 3. 分组整理
        grouped = self._group_by_category(unique_streams)
        
        return grouped
    
    def _deduplicate(self, streams: List[Dict]) -> List[Dict]:
        """智能去重：同一频道保留首次出现的源"""
        seen = {}
        result = []
        
        for stream in streams:
            key = f"{stream.get('name', '').lower()}"
            if key not in seen:
                seen[key] = stream
                result.append(stream)
        
        return result
    
    def _group_by_category(self, streams: List[Dict]) -> List[Dict]:
        """按频道分类分组"""
        categories = {
            'cctv': ['cctv', '央视'],
            'weishi': ['卫视', '卫视台'],
            'local': ['地方', '都市', '频道'],
            'other': []
        }
        
        grouped = []
        for stream in streams:
            name = stream.get('name', '').lower()
            group = 'Other'
            
            for cat, keywords in categories.items():
                for kw in keywords:
                    if kw in name:
                        group = cat.capitalize()
                        break
                if group != 'Other':
                    break
            
            stream['category'] = group
            grouped.append(stream)
        
        return grouped
