#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV 频道缓存管理器
- 支持数据库持久化
- 智能判断是否需要更新
- 带时效性判断
- 支持多源展开保存
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
        """判断是否需要执行完整采集更新"""
        if self.stats["total_channels"] == 0:
            print("📦 数据库为空，需要执行完整采集")
            return True
        if self.db.is_stale():
            print(f"⏰ 缓存数据已超过 {DATA_EXPIRY_SECONDS // 3600} 小时，需要执行完整采集")
            return True
        print(f"✅ 缓存数据有效（上次更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.db.get_last_update_time()))}），跳过完整采集")
        return False

    def load_from_cache(self):
        """从缓存加载频道数据（返回字典列表，每个字典有 url 字段）"""
        channels = self.db.load_valid_channels(skip_old=False)
        print(f"📂 从缓存加载了 {len(channels)} 个频道（每个 URL 一条记录）")
        return channels

    def save_to_cache(self, channels):
        """
        保存频道数据到缓存
        channels: 列表，每个元素可以是：
            - 包含 urls 列表的字典（合并后的频道）
            - 包含 url 字符串的字典（普通频道）
        自动展开为每个 URL 一条记录
        """
        records = []
        for ch in channels:
            if isinstance(ch, dict):
                # 检查是否有 urls 列表
                if 'urls' in ch and isinstance(ch['urls'], list):
                    for url in ch['urls']:
                        record = {
                            "name": ch.get("name", ""),
                            "url": url,
                            "group_title": ch.get("group_title", ""),
                            "id": ch.get("id", ""),
                            "logo": ch.get("logo", ""),
                            "latency": ch.get("latency", 9999),
                            "video_codec": ch.get("video_codec", ""),
                            "ip_info": ch.get("ip_info")
                        }
                        records.append(record)
                elif 'url' in ch:
                    # 单个 URL
                    records.append(ch)
            else:
                # 对象形式（不常用，但兼容）
                if hasattr(ch, 'urls') and ch.urls:
                    for url in ch.urls:
                        record = {
                            "name": ch.name,
                            "url": url,
                            "group_title": getattr(ch, 'group_title', ''),
                            "id": getattr(ch, 'tvg_id', ''),
                            "logo": getattr(ch, 'tvg_logo', ''),
                            "latency": getattr(ch, 'latency', 9999),
                            "video_codec": getattr(ch, 'video_codec', ''),
                            "ip_info": getattr(ch, 'ip_info', None)
                        }
                        records.append(record)
                elif hasattr(ch, 'url'):
                    records.append({
                        "name": ch.name,
                        "url": ch.url,
                        "group_title": getattr(ch, 'group_title', ''),
                        "id": getattr(ch, 'tvg_id', ''),
                        "logo": getattr(ch, 'tvg_logo', ''),
                        "latency": getattr(ch, 'latency', 9999),
                        "video_codec": getattr(ch, 'video_codec', ''),
                        "ip_info": getattr(ch, 'ip_info', None)
                    })
        if records:
            self.db.save_channels(records)
            self.db.set_last_update_time()
            print(f"💾 已保存 {len(records)} 条记录（来自 {len(channels)} 个合并频道）到缓存")
        else:
            print("⚠️ 没有可保存的记录")

    def get_cache_age(self) -> int:
        """获取缓存数据时效（剩余有效秒数）"""
        last_update = self.db.get_last_update_time()
        if last_update is None:
            return 0
        elapsed = int(time.time()) - last_update
        return max(0, DATA_EXPIRY_SECONDS - elapsed)
