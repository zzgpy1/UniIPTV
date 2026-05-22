#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EPGIntegrator:
    """EPG 节目单整合器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.epg_sources = self._load_epg_sources()
    
    def _load_epg_sources(self) -> List[Dict]:
        """加载 EPG 源配置"""
        epg_file = self.config_dir / 'epg_sources.json'
        if epg_file.exists():
            with open(epg_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        # 默认 EPG 源（提供中文 EPG 数据）
        return [
            {
                "name": "51zmt",
                "url": "https://epg.51zmt.top:8000/api/",
                "type": "api"
            },
            {
                "name": "epg.pw",
                "url": "https://epg.pw/api/",
                "type": "api"
            }
        ]
    
    async def fetch_epg(self, streams: List[Dict]) -> Dict[str, Any]:
        """获取 EPG 数据"""
        epg_data = {}
        
        if not streams:
            return epg_data
        
        # 提取频道名称列表
        channel_names = list(set([s.get('name', '') for s in streams if s.get('name')]))
        logger.info(f"为 {len(channel_names)} 个频道获取 EPG 数据...")
        
        async with aiohttp.ClientSession() as session:
            for epg_source in self.epg_sources:
                try:
                    # 简单实现：调用 EPG API
                    # 完整实现可以解析 XMLTV 格式
                    async with session.get(
                        f"{epg_source['url']}channels",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # 将 EPG 数据关联到频道
                            for channel_name in channel_names:
                                if channel_name in data:
                                    epg_data[channel_name] = data[channel_name]
                            logger.info(f"从 {epg_source['name']} 获取到 EPG 数据")
                except Exception as e:
                    logger.warning(f"EPG 源 {epg_source['name']} 获取失败: {e}")
        
        return epg_data
