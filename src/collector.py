#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import aiohttp
import aiohttp_retry
import asyncio
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SourceCollector:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.sources = self._load_sources()
        self.proxies = [
            lambda u: u,
            lambda u: f"https://gh-proxy.com/{u}",
            lambda u: f"https://ghproxy.net/{u}",
            lambda u: f"https://ghproxy.homeboyc.cn/{u}",
            # 如果你想使用 gh-proxy.19860519.xyz，取消下一行注释
            # lambda u: f"https://gh-proxy.19860519.xyz/{u}",
        ]

    def _load_sources(self) -> List[Dict]:
        sources_file = self.config_dir / 'sources.json'
        if sources_file.exists():
            with open(sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        # 默认源
        return [
            {
                "name": "zilong7728_best",
                "url": "https://raw.githubusercontent.com/zilong7728/Collect-IPTV/main/best_sorted.m3u",
                "type": "m3u",
                "enabled": True
            },
            {
                "name": "fanmingming_ipv6",
                "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
                "type": "m3u",
                "enabled": True
            }
        ]

    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        for proxy_func in self.proxies:
            try:
                target_url = proxy_func(url)
                retry_options = aiohttp_retry.RetryOptions(
                    attempts=2, statuses={408, 429, 500, 502, 503, 504}
                )
                retry_client = aiohttp_retry.RetryClient(
                    client=session, retry_options=retry_options
                )
                async with retry_client.get(target_url, timeout=30) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if content.strip():
                            logger.info(f"✅ 从 {url} 获取数据 (代理: {target_url[:50]}...)")
                            await retry_client.close()
                            return content
                await retry_client.close()
            except Exception:
                continue
        logger.error(f"所有代理均失败，无法获取 {url}")
        return ""

    async def _parse_m3u(self, content: str, source_name: str) -> List[Dict]:
        streams = []
        lines = content.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                channel = {}
                # 提取频道名
                if ',' in line:
                    channel['name'] = line.split(',')[-1].strip()
                else:
                    channel['name'] = "Unknown"
                # 提取 tvg-id, group-title
                for attr in ['tvg-id', 'group-title']:
                    if f'{attr}="' in line:
                        start = line.find(f'{attr}="') + len(f'{attr}="')
                        end = line.find('"', start)
                        if end > start:
                            channel[attr.replace('-', '_')] = line[start:end]
                # 下一行应为 URL
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()
                    if url_line and not url_line.startswith('#'):
                        channel['url'] = url_line
                        channel['source'] = source_name
                        channel.setdefault('group', channel.get('group_title', 'Uncategorized'))
                        streams.append(channel)
                        i += 1
            i += 1
        logger.info(f"从 {source_name} 解析到 {len(streams)} 个源")
        return streams

    async def collect_all(self) -> List[Dict]:
        all_streams = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_url(session, src['url']) for src in self.sources if src.get('enabled', True)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, content in enumerate(results):
                if isinstance(content, Exception) or not content:
                    logger.warning(f"源 {self.sources[i]['name']} 采集失败")
                    continue
                streams = await self._parse_m3u(content, self.sources[i]['name'])
                all_streams.extend(streams)
        logger.info(f"总计采集到 {len(all_streams)} 个原始源")
        return all_streams
