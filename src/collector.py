#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import aiohttp
import aiohttp_retry
import asyncio
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SourceCollector:
    """多源直播流采集器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.sources = self._load_sources()
        self.streams = []
    
    def _load_sources(self) -> List[Dict]:
        """加载采集源配置"""
        sources_file = self.config_dir / 'sources.json'
        if sources_file.exists():
            with open(sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        # 默认配置
        return [
            {
                "name": "collect_iptv_api",
                "url": "https://raw.githubusercontent.com/Guovin/iptv-api/main/output/result.m3u",
                "type": "m3u"
            },
            {
                "name": "collect_best_sorted",
                "url": "https://raw.githubusercontent.com/zilong7728/Collect-IPTV/main/best_sorted.m3u",
                "type": "m3u"
            },
            {
                "name": "collect_iptv_org",
                "url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/CN.m3u",
                "type": "m3u"
            }
        ]
    
    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """异步获取URL内容"""
        retry_options = aiohttp_retry.RetryOptions(
            attempts=3,
            statuses={408, 429, 500, 502, 503, 504}
        )
        retry_client = aiohttp_retry.RetryClient(
            client=session, 
            retry_options=retry_options
        )
        try:
            async with retry_client.get(url, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    logger.warning(f"请求失败 {url}: HTTP {resp.status}")
                    return ""
        except Exception as e:
            logger.error(f"获取 {url} 失败: {e}")
            return ""
        finally:
            await retry_client.close()
    
    async def _parse_m3u(self, content: str, source_name: str) -> List[Dict]:
        """解析 M3U 格式内容"""
        streams = []
        lines = content.strip().split('\n')
        
        current_tvg_id = None
        current_tvg_name = None
        current_group = None
        current_logo = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # 解析 EXTINF 标签
                current_tvg_id = None
                current_tvg_name = None
                current_group = None
                current_logo = None
                
                # 提取 tvg-id
                if 'tvg-id="' in line:
                    start = line.find('tvg-id="') + 8
                    end = line.find('"', start)
                    if end > start:
                        current_tvg_id = line[start:end]
                
                # 提取 tvg-name
                if 'tvg-name="' in line:
                    start = line.find('tvg-name="') + 10
                    end = line.find('"', start)
                    if end > start:
                        current_tvg_name = line[start:end]
                
                # 提取 group-title
                if 'group-title="' in line:
                    start = line.find('group-title="') + 13
                    end = line.find('"', start)
                    if end > start:
                        current_group = line[start:end]
                
                # 提取 tvg-logo
                if 'tvg-logo="' in line:
                    start = line.find('tvg-logo="') + 10
                    end = line.find('"', start)
                    if end > start:
                        current_logo = line[start:end]
                
                # 提取频道名（最后一个逗号后的内容）
                parts = line.split(',')
                if len(parts) >= 2:
                    channel_name = parts[-1].strip()
                else:
                    channel_name = current_tvg_name or "Unknown"
                
                current_tvg_name = channel_name
                
            elif line and not line.startswith('#') and current_tvg_name:
                # 这是 URL 行
                streams.append({
                    'name': current_tvg_name,
                    'url': line,
                    'tvg_id': current_tvg_id,
                    'tvg_logo': current_logo,
                    'group': current_group or 'Uncategorized',
                    'source': source_name
                })
                current_tvg_name = None
        
        return streams
    
    async def collect_all(self) -> List[Dict]:
        """采集所有配置源"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in self.sources:
                tasks.append(self._fetch_url(session, source['url']))
            
            contents = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_streams = []
            for i, content in enumerate(contents):
                source = self.sources[i]
                if isinstance(content, Exception) or not content:
                    logger.warning(f"源 {source['name']} 采集失败")
                    continue
                
                streams = await self._parse_m3u(content, source['name'])
                logger.info(f"从 {source['name']} 采集到 {len(streams)} 个源")
                all_streams.extend(streams)
            
            return all_streams
