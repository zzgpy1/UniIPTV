#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV 频道缓存管理器
- 支持数据库持久化
- 智能判断是否需要更新
- 带时效性判断
"""

import time
import os
from src.db_manager import IPTVDatabase, DATA_EXPIRY_SECONDS

class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.db = IPTVDatabase()
        self.stats = self.db.get_stats()

    def should_update(self) -> bool:
        """
        判断是否需要执行完整采集更新：
        1. 数据库为空 → 需要更新
        2. 数据已超过时效 → 需要更新
        3. 否则 → 不需要更新
        """
        # 检查数据库是否有数据
        if self.stats["total_channels"] == 0:
            print("📦 数据库为空，需要执行完整采集")
            return True

        # 检查数据是否过期
        if self.db.is_stale():
            print(f"⏰ 缓存数据已超过 {DATA_EXPIRY_SECONDS // 3600} 小时，需要执行完整采集")
            return True

        print(f"✅ 缓存数据有效（上次更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.db.get_last_update_time()))}），跳过完整采集")
        return False

    def load_from_cache(self):
        """从缓存加载频道数据"""
        channels = self.db.load_valid_channels(skip_old=False)
        print(f"📂 从缓存加载了 {len(channels)} 个频道")
        return channels

    def save_to_cache(self, channels):
        """保存频道数据到缓存"""
        self.db.save_channels(channels)
        self.db.set_last_update_time()
        print(f"💾 已保存 {len(channels)} 个频道到缓存")

    def get_cache_age(self) -> int:
        """获取缓存数据时效（剩余有效秒数）"""
        last_update = self.db.get_last_update_time()
        if last_update is None:
            return 0
        elapsed = int(time.time()) - last_update
        return max(0, DATA_EXPIRY_SECONDS - elapsed)
