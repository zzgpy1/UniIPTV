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
    """增强版多源直播流采集器，解决解析和网络问题"""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.sources = self._load_sources()
        self.streams = []

    def _load_sources(self) -> List[Dict]:
        """加载采集源配置，并包含一个已知可用的备用源"""
        sources_file = self.config_dir / 'sources.json'
        default_sources = [
            {
                "name": "zilong7728_best_sorted",
                "url": "https://raw.githubusercontent.com/zilong7728/Collect-IPTV/main/best_sorted.m3u",
                "type": "m3u",
                "enabled": True
            },
            # 备用：来自 fanmingming/live 的聚合源
            {
                "name": "fanmingming_live_ipv6",
                "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
                "type": "m3u",
                "enabled": True
            }
        ]

        if sources_file.exists():
            with open(sources_file, 'r', encoding='utf-8') as f:
                custom_sources = json.load(f)
                # 合并自定义源，确保默认源作为回退
                return custom_sources + default_sources

        logger.info("未找到sources.json，使用默认源配置。")
        return default_sources

    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """使用代理策略获取URL内容，并包含重试机制"""
        # 常用代理列表，用于绕过可能存在的网络限制
        proxies = [
            lambda u: u,  # 直接连接
            lambda u: f"https://ghproxy.net/{u}",  # ghproxy 代理
            lambda u: f"https://mirror.ghproxy.com/{u}"  # ghproxy 镜像
        ]

        for i, proxy_func in enumerate(proxies):
            try:
                target_url = proxy_func(url)
                logger.debug(f"尝试代理 {i+1}: {target_url}")

                retry_options = aiohttp_retry.RetryOptions(
                    attempts=3, statuses={408, 429, 500, 502, 503, 504}
                )
                retry_client = aiohttp_retry.RetryClient(
                    client=session, retry_options=retry_options
                )
                async with retry_client.get(target_url, timeout=30) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if content.strip():
                            logger.info(f"成功从 {url} 获取数据 (使用代理 {i+1})")
                            await retry_client.close()
                            return content
                        else:
                            logger.warning(f"从 {url} 获取到的内容为空 (使用代理 {i+1})")
                    else:
                        logger.warning(f"请求 {url} 失败: HTTP {resp.status} (使用代理 {i+1})")
                await retry_client.close()
            except asyncio.TimeoutError:
                logger.warning(f"请求 {url} 超时 (使用代理 {i+1})")
            except Exception as e:
                logger.warning(f"请求 {url} 时发生错误: {e} (使用代理 {i+1})")

        logger.error(f"所有代理尝试均告失败，无法获取 {url}")
        return ""

    async def _parse_m3u(self, content: str, source_name: str) -> List[Dict]:
        """健壮的M3U解析器，修复了跨行解析bug"""
        streams = []
        lines = content.strip().split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            # 查找以 #EXTINF 开头的行
            if line.startswith('#EXTINF:'):
                current_channel = {}
                # 解析EXTINF行中的元数据
                extinf_parts = line.split(':', 1)[1].split(',')
                if extinf_parts:
                    # 频道名是EXTINF行中最后一个逗号之后的部分
                    current_channel['name'] = extinf_parts[-1].strip()
                else:
                    current_channel['name'] = "Unknown"

                # 解析 tvg-id, tvg-name, group-title
                attr_mapping = {'tvg-id': 'tvg_id', 'tvg-name': 'tvg_name', 'group-title': 'group'}
                for attr in attr_mapping:
                    if f'{attr}="' in line:
                        start = line.find(f'{attr}="') + len(f'{attr}="')
                        end = line.find('"', start)
                        if end > start:
                            current_channel[attr_mapping[attr]] = line[start:end]

                # 下一行应该是URL
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()
                    if url_line and not url_line.startswith('#'):
                        current_channel['url'] = url_line
                        current_channel['source'] = source_name
                        # 补充缺失的元数据
                        current_channel['group'] = current_channel.get('group', 'Uncategorized')
                        streams.append(current_channel)
                        i += 1  # 跳过URL行
            i += 1

        logger.info(f"从 {source_name} 采集到 {len(streams)} 个源")
        # 调试日志：打印第一个源的结构
        if streams:
            logger.debug(f"第一个源示例: {streams[0]}")
        else:
            logger.warning(f"源 {source_name} 解析后为空，可能格式不符或内容受损。")
        return streams

    async def collect_all(self) -> List[Dict]:
        """采集所有配置源，并包含调试输出"""
        all_streams = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in self.sources:
                tasks.append(self._fetch_url(session, source['url']))

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, content in enumerate(results):
                source = self.sources[i]
                if isinstance(content, Exception):
                    logger.error(f"源 {source['name']} 采集时发生异常: {content}")
                    continue
                if not content:
                    logger.warning(f"源 {source['name']} 采集失败，内容为空。")
                    continue

                streams = await self._parse_m3u(content, source['name'])
                all_streams.extend(streams)

        logger.info(f"总计从所有源采集到 {len(all_streams)} 个原始源")
        return all_streams
