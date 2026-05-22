#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collector import SourceCollector
from processor import StreamProcessor
from speed_tester import SpeedTester
from epg_integrator import EPGIntegrator
from output_generator import OutputGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('UniIPTV')


class UniIPTV:
    """UniIPTV 主控制器"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / 'config'
        self.output_dir = self.base_dir / 'output'
        self.cache_dir = self.base_dir / '.cache'
        
        # 确保目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化各模块
        self.collector = SourceCollector(self.config_dir)
        self.processor = StreamProcessor(self.config_dir)
        self.speed_tester = SpeedTester(self.cache_dir)
        self.epg_integrator = EPGIntegrator(self.config_dir)
        self.output_generator = OutputGenerator(self.output_dir)
    
    async def run(self):
        """执行完整流水线"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("UniIPTV 流水线开始执行")
        logger.info("=" * 60)
        
        try:
            # 阶段1：采集源数据
            logger.info("阶段 1/5: 采集直播源...")
            raw_streams = await self.collector.collect_all()
            logger.info(f"采集完成，共获取 {len(raw_streams)} 个原始源")
            
            # 阶段2：去重和广告过滤
            logger.info("阶段 2/5: 去重及广告过滤...")
            clean_streams = self.processor.process(raw_streams)
            logger.info(f"清洗完成，剩余 {len(clean_streams)} 个有效源")
            
            # 阶段3：测速并排序
            logger.info("阶段 3/5: 测速中（自动缓存复用）...")
            tested_streams = await self.speed_tester.test(clean_streams)
            sorted_streams = self.speed_tester.sort_by_delay(tested_streams)
            logger.info(f"测速完成，共测试 {len(tested_streams)} 个源")
            
            # 阶段4：整合 EPG
            logger.info("阶段 4/5: 整合 EPG 节目单...")
            epg_data = await self.epg_integrator.fetch_epg(sorted_streams)
            logger.info(f"EPG 整合完成，更新了 {len(epg_data)} 个频道的节目信息")
            
            # 阶段5：输出文件
            logger.info("阶段 5/5: 生成输出文件...")
            stats = self.output_generator.generate(sorted_streams, epg_data)
            logger.info(f"输出完成: TXT={stats['txt_count']}条, M3U={stats['m3u_count']}条")
            
            # 统计报告
            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"✅ 流水线执行完成！总耗时: {elapsed:.2f} 秒")
            logger.info(f"📊 最终有效源数: {len(sorted_streams)}")
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"流水线执行失败: {e}", exc_info=True)
            sys.exit(1)


def main():
    app = UniIPTV()
    asyncio.run(app.run())


if __name__ == '__main__':
    main()
