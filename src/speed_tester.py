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
from collections import defaultdict

logger = logging.getLogger(__name__)


class SpeedTester:
    """测速器（含缓存机制）"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / 'speed_cache.pkl'
        self.cache = self._load_cache()
        self.DEFAULT_TIMEOUT = 5
        self.MIN_SPEED = 0.5
    
    def _load_cache(self) -> Dict:
        """加载测速缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """保存测速缓存"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
            logger.info(f"测速缓存已保存: {len(self.cache)} 条记录")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")
    
    async def _test_single_url(self, session: aiohttp.ClientSession, 
                               stream: Dict) -> Dict:
        """测试单个URL的延迟"""
        url = stream.get('url', '')
        name = stream.get('name', '')
        cache_key = f"{name}|{url}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # 缓存有效期为 12 小时
            if time.time() - cached.get('timestamp', 0) < 12 * 3600:
                logger.debug(f"缓存命中: {name[:30]}...")
                stream['delay'] = cached.get('delay', float('inf'))
                stream['is_alive'] = cached.get('is_alive', False)
                return stream
        
        # 实际测速
        try:
            retry_options = aiohttp_retry.RetryOptions(
                attempts=2,
                statuses={408, 429, 500, 502, 503, 504}
            )
            retry_client = aiohttp_retry.RetryClient(
                client=session,
                retry_options=retry_options
            )
            
            start_time = time.time()
            async with retry_client.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as resp:
                delay = time.time() - start_time
                
                if resp.status == 200:
                    stream['delay'] = delay
                    stream['is_alive'] = True
                    
                    # 更新缓存
                    self.cache[cache_key] = {
                        'delay': delay,
                        'is_alive': True,
                        'timestamp': time.time()
                    }
                    logger.debug(f"✅ {name[:30]}... {delay:.2f}s")
                else:
                    stream['delay'] = float('inf')
                    stream['is_alive'] = False
                    logger.debug(f"❌ {name[:30]}... HTTP {resp.status}")
            
            await retry_client.close()
            
        except asyncio.TimeoutError:
            stream['delay'] = float('inf')
            stream['is_alive'] = False
            logger.debug(f"⏱️ {name[:30]}... 超时")
        except Exception as e:
            stream['delay'] = float('inf')
            stream['is_alive'] = False
            logger.debug(f"⚠️ {name[:30]}... 错误: {type(e).__name__}")
        
        return stream
    
    async def test(self, streams: List[Dict]) -> List[Dict]:
        """批量测速"""
        if not streams:
            return []
        
        logger.info(f"开始测速，共 {len(streams)} 个源")
        
        # 控制并发数
        semaphore = asyncio.Semaphore(20)
        
        async def test_with_semaphore(session, stream):
            async with semaphore:
                return await self._test_single_url(session, stream)
        
        async with aiohttp.ClientSession() as session:
            tasks = [test_with_semaphore(session, stream) for stream in streams]
            results = await asyncio.gather(*tasks)
        
        # 保存缓存
        self._save_cache()
        
        # 过滤有效的源
        valid_streams = [s for s in results if s.get('is_alive', False)]
        logger.info(f"测速完成: {len(valid_streams)}/{len(streams)} 个源有效")
        
        return valid_streams
    
    def sort_by_delay(self, streams: List[Dict]) -> List[Dict]:
        """按延迟排序"""
        if not streams:
            return []
        
        sorted_streams = sorted(streams, key=lambda x: x.get('delay', float('inf')))
        
        # 延迟统计
        delays = [s.get('delay', 0) for s in sorted_streams if s.get('delay', 0) < float('inf')]
        if delays:
            avg_delay = sum(delays) / len(delays)
            min_delay = min(delays)
            logger.info(f"测速统计: 平均 {avg_delay:.2f}s, 最快 {min_delay:.2f}s")
        
        return sorted_streams
