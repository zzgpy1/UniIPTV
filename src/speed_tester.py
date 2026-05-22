#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import aiohttp_retry
import pickle
import time
import logging
from typing import List, Dict
from pathlib import Path
from ip_locator import IPLocator

logger = logging.getLogger(__name__)


class SpeedTester:
    def __init__(self, cache_dir: Path, config_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / 'speed_cache.pkl'
        self.cache = self._load_cache()
        self.ip_locator = IPLocator(config_dir)
        self.DEFAULT_TIMEOUT = 5

    def _load_cache(self) -> Dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    async def _test_one(self, session: aiohttp.ClientSession, stream: Dict) -> Dict:
        url = stream.get('url', '')
        name = stream.get('name', '')
        key = f"{name}|{url}"
        # 检查缓存（12小时）
        if key in self.cache:
            cached = self.cache[key]
            if time.time() - cached.get('timestamp', 0) < 12 * 3600:
                stream['delay'] = cached['delay']
                stream['is_alive'] = cached['is_alive']
                stream['isp'] = cached.get('isp', 'Unknown')
                return stream

        # 测速
        try:
            retry_opts = aiohttp_retry.RetryOptions(attempts=2)
            retry_client = aiohttp_retry.RetryClient(client=session, retry_options=retry_opts)
            start = time.time()
            async with retry_client.get(url, timeout=self.DEFAULT_TIMEOUT) as resp:
                delay = time.time() - start
                if resp.status == 200:
                    stream['delay'] = delay
                    stream['is_alive'] = True
                    # 识别ISP
                    stream['isp'] = self.ip_locator.get_isp(url)
                    self.cache[key] = {
                        'delay': delay,
                        'is_alive': True,
                        'isp': stream['isp'],
                        'timestamp': time.time()
                    }
                    logger.debug(f"✅ {name[:30]} {delay:.2f}s {stream['isp']}")
                else:
                    stream['delay'] = float('inf')
                    stream['is_alive'] = False
            await retry_client.close()
        except Exception:
            stream['delay'] = float('inf')
            stream['is_alive'] = False

        return stream

    async def test(self, streams: List[Dict]) -> List[Dict]:
        if not streams:
            return []
        sem = asyncio.Semaphore(30)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for s in streams:
                async def wrapped(stream):
                    async with sem:
                        return await self._test_one(session, stream)
                tasks.append(wrapped(s))
            results = await asyncio.gather(*tasks)
        self._save_cache()
        valid = [r for r in results if r.get('is_alive')]
        logger.info(f"测速完成: {len(valid)}/{len(streams)} 个有效")
        return valid

    def sort_by_delay(self, streams: List[Dict]) -> List[Dict]:
        # 可以按延迟排序，也可以按运营商偏好（例如优先电信）
        # 这里简单按延迟升序
        return sorted(streams, key=lambda x: x.get('delay', float('inf')))
