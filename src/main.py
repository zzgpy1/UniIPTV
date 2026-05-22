#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import time
import logging
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collector import SourceCollector
from processor import StreamProcessor
from speed_tester import SpeedTester
from epg_integrator import EPGIntegrator
from output_generator import OutputGenerator
from ai_discovery import AIDiscovery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('UniIPTV')


class UniIPTV:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / 'config'
        self.output_dir = self.base_dir / 'output'
        self.cache_dir = self.base_dir / '.cache'

        self.output_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        self.collector = SourceCollector(self.config_dir)
        self.processor = StreamProcessor(self.config_dir)
        self.speed_tester = SpeedTester(self.cache_dir, self.config_dir)
        self.epg_integrator = EPGIntegrator(self.config_dir)
        self.output_generator = OutputGenerator(self.output_dir, self.config_dir)
        self.ai_discovery = AIDiscovery(self.config_dir)

    async def run(self):
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("UniIPTV 流水线开始执行")
        logger.info("=" * 60)

        try:
            # 1. 采集常规源
            logger.info("阶段 1/6: 采集直播源...")
            raw_streams = await self.collector.collect_all()

            # 2. AI 发现源（可选）
            logger.info("阶段 2/6: AI 智能发现新源...")
            ai_streams = await self.ai_discovery.discover()
            if ai_streams:
                logger.info(f"AI 发现 {len(ai_streams)} 个候选源，将进行测速验证")
                raw_streams.extend(ai_streams)

            logger.info(f"总原始源数: {len(raw_streams)}")

            # 3. 去重 & 广告过滤
            logger.info("阶段 3/6: 去重及广告过滤...")
            clean_streams = self.processor.process(raw_streams)
            logger.info(f"清洗后剩余 {len(clean_streams)} 个有效源")

            # 4. 测速 & IP 识别 & 排序
            logger.info("阶段 4/6: 测速 + IP 归属地识别...")
            tested_streams = await self.speed_tester.test(clean_streams)
            sorted_streams = self.speed_tester.sort_by_delay(tested_streams)
            logger.info(f"测速完成，有效源 {len(sorted_streams)} 个")

            # 5. EPG 整合
            logger.info("阶段 5/6: 整合 EPG 节目单...")
            epg_data = await self.epg_integrator.fetch_epg(sorted_streams)

            # 6. 输出多格式文件
            logger.info("阶段 6/6: 生成输出文件...")
            stats = self.output_generator.generate(sorted_streams, epg_data)
            logger.info(f"输出统计: {stats}")

            elapsed = time.time() - start_time
            logger.info(f"✅ 流水线完成，耗时 {elapsed:.2f} 秒")
        except Exception as e:
            logger.error(f"流水线失败: {e}", exc_info=True)
            sys.exit(1)


def main():
    app = UniIPTV()
    asyncio.run(app.run())


if __name__ == '__main__':
    main()
