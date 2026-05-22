#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import logging
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class StreamProcessor:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.ad_keywords = self._load_ad_keywords()
        self.user_channels = self._load_user_channels()

    def _load_ad_keywords(self) -> Set[str]:
        keywords = set()
        ad_file = self.config_dir / 'ad_filter.txt'
        if ad_file.exists():
            with open(ad_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith('#'):
                        keywords.add(line)
        default = {'ad', '广告', '推广', 'localhost', '127.0.0.1', 'tracker', 'announce'}
        keywords.update(default)
        return keywords

    def _load_user_channels(self) -> Dict:
        ch_file = self.config_dir / 'user_channels.json'
        if ch_file.exists():
            with open(ch_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"keep": [], "remove": [], "priority_channels": []}

    def _is_ad(self, stream: Dict) -> bool:
        name = stream.get('name', '').lower()
        url = stream.get('url', '').lower()
        for kw in self.ad_keywords:
            if kw in name or kw in url:
                return True
        return False

    def _is_valid_url(self, url: str) -> bool:
        return url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')) and 10 < len(url) < 1000

    def process(self, streams: List[Dict]) -> List[Dict]:
        if not streams:
            return []
        # 广告过滤 + URL 有效性
        filtered = [s for s in streams if not self._is_ad(s) and self._is_valid_url(s.get('url', ''))]
        logger.info(f"广告过滤后剩余 {len(filtered)} 个")

        # 去重（按频道名去重，保留第一个）
        seen = set()
        unique = []
        for s in filtered:
            key = s.get('name', '').lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        logger.info(f"去重后剩余 {len(unique)} 个")

        # 按用户配置保留频道（如果配置了 keep 列表，只保留在列表中的频道）
        keep_list = self.user_channels.get('keep', [])
        if keep_list:
            keep_lower = [k.lower() for k in keep_list]
            unique = [s for s in unique if s.get('name', '').lower() in keep_lower]
            logger.info(f"按用户白名单过滤后剩余 {len(unique)} 个")

        return unique
