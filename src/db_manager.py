# src/db_manager.py
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "iptv_cache.db"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        # 源数据哈希表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_hash (
                source_url TEXT PRIMARY KEY,
                content_hash TEXT,
                last_updated TIMESTAMP
            )
        ''')
        # 频道缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT,
                latency INTEGER,
                video_codec TEXT,
                group_title TEXT,
                tvg_id TEXT,
                ip_info TEXT,
                last_verified TIMESTAMP,
                UNIQUE(name, url)
            )
        ''')
        self.conn.commit()

    def get_source_hash(self, source_url: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT content_hash FROM source_hash WHERE source_url=?", (source_url,))
        row = cursor.fetchone()
        return row[0] if row else None

    def update_source_hash(self, source_url: str, content_hash: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO source_hash (source_url, content_hash, last_updated)
            VALUES (?, ?, ?)
        ''', (source_url, content_hash, datetime.now().isoformat()))
        self.conn.commit()

    def save_channels(self, channels: List[Any]):
        cursor = self.conn.cursor()
        for ch in channels:
            ip_info_json = json.dumps(getattr(ch, 'ip_info', None) or {})
            cursor.execute('''
                INSERT OR REPLACE INTO channels
                (name, url, latency, video_codec, group_title, tvg_id, ip_info, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ch.name, ch.url, getattr(ch, 'latency', 9999),
                getattr(ch, 'video_codec', ''),
                getattr(ch, 'group_title', ''),
                getattr(ch, 'tvg_id', ''),
                ip_info_json,
                datetime.now().isoformat()
            ))
        self.conn.commit()

    def load_all_channels(self) -> List[Any]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name, url, latency, video_codec, group_title, tvg_id, ip_info
            FROM channels
        ''')
        rows = cursor.fetchall()
        channels = []
        for row in rows:
            # 创建一个简单的对象
            ch = type('Channel', (), {})()
            ch.name = row[0]
            ch.url = row[1]
            ch.latency = row[2]
            ch.video_codec = row[3]
            ch.group_title = row[4]
            ch.tvg_id = row[5]
            ch.ip_info = json.loads(row[6]) if row[6] else None
            channels.append(ch)
        return channels

    def clear_cache(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM channels")
        cursor.execute("DELETE FROM source_hash")
        self.conn.commit()
