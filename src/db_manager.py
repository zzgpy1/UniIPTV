#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV 频道缓存数据库管理器
- 存储验证通过的频道数据
- 支持按需增量更新
- 时效性判断机制
"""

import sqlite3
import json
import time
import os
from typing import List, Dict, Optional, Any

# 数据库路径
DB_PATH = "iptv_cache.db"

# 数据时效性配置：3天（单位：秒）
DATA_EXPIRY_SECONDS = 3 * 24 * 3600

# 源连续失效阈值：连续 N 次验证失败后才标记为无效
CONSECUTIVE_FAILURE_THRESHOLD = 3

class IPTVDatabase:
    """IPTV 频道缓存数据库管理类"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建主数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    group_title TEXT,
                    tvg_id TEXT,
                    tvg_logo TEXT,
                    latency INTEGER DEFAULT 9999,
                    video_codec TEXT,
                    ip_info TEXT,
                    last_verified INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    UNIQUE(name, url)
                )
            ''')
            # 创建元数据表，存储版本和更新时间
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()
            print("✅ 数据库初始化完成")

    def get_last_update_time(self) -> Optional[int]:
        """获取上次数据库更新时间（时间戳）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = 'last_update'")
            row = cursor.fetchone()
            if row:
                return int(row[0])
        return None

    def set_last_update_time(self, timestamp: int = None):
        """设置数据库更新时间"""
        if timestamp is None:
            timestamp = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                ("last_update", str(timestamp))
            )
            conn.commit()

    def save_channels(self, channels: List[Dict[str, Any]]):
        """保存或更新频道数据"""
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for ch in channels:
                name = ch.get("name", "")
                url = ch.get("url", "")
                group_title = ch.get("group_title", "")
                tvg_id = ch.get("id", "")
                tvg_logo = ch.get("logo", "")
                latency = ch.get("latency", 9999)
                video_codec = ch.get("video_codec", "")
                ip_info = json.dumps(ch.get("ip_info")) if ch.get("ip_info") else None

                cursor.execute('''
                    INSERT OR REPLACE INTO channels
                    (name, url, group_title, tvg_id, tvg_logo, latency, video_codec, ip_info, last_verified, failure_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (name, url, group_title, tvg_id, tvg_logo, latency, video_codec, ip_info, now))
            conn.commit()
            print(f"💾 数据库已保存 {len(channels)} 个频道")

    def load_valid_channels(self, skip_old: bool = True) -> List[Dict[str, Any]]:
        """
        从数据库加载有效频道
        - skip_old=True: 跳过超过时效的数据
        - 返回频道列表
        """
        now = int(time.time())
        expiry_threshold = now - DATA_EXPIRY_SECONDS
        channels = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if skip_old:
                cursor.execute('''
                    SELECT * FROM channels
                    WHERE last_verified >= ?
                    ORDER BY name, latency
                ''', (expiry_threshold,))
            else:
                cursor.execute('SELECT * FROM channels ORDER BY name, latency')

            for row in cursor.fetchall():
                ch = dict(row)
                # 恢复 JSON 字段
                if ch.get("ip_info"):
                    ch["ip_info"] = json.loads(ch["ip_info"])
                else:
                    ch["ip_info"] = None
                channels.append(ch)

        return channels

    def mark_failed(self, url: str) -> int:
        """
        标记某个链接验证失败
        返回当前失败次数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE channels SET failure_count = failure_count + 1 WHERE url = ?", (url,))
            conn.commit()
            cursor.execute("SELECT failure_count FROM channels WHERE url = ?", (url,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def is_stale(self) -> bool:
        """
        检查缓存数据是否已过期（超过设定的时效）
        """
        last_update = self.get_last_update_time()
        if last_update is None:
            return True
        return (int(time.time()) - last_update) > DATA_EXPIRY_SECONDS

    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM channels")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM channels WHERE failure_count >= ?", (CONSECUTIVE_FAILURE_THRESHOLD,))
            failed = cursor.fetchone()[0]
        return {"total_channels": total, "failed_threshold": failed}
