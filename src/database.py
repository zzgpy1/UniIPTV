import sqlite3
import json
from src.config import DATABASE_PATH

class IPTVDatabase:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    latency INTEGER,
                    province TEXT,
                    city TEXT,
                    isp TEXT,
                    video_codec TEXT,
                    group_title TEXT,
                    tvg_id TEXT,
                    tvg_logo TEXT,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_valid BOOLEAN DEFAULT 1
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_name ON channels(name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_valid ON channels(is_valid)')

    def save_channel(self, channel_info: dict):
        """保存或更新频道信息（基于URL唯一）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO channels 
                (name, url, latency, province, city, isp, video_codec, group_title, tvg_id, tvg_logo, last_checked, is_valid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (
                channel_info.get('name'),
                channel_info.get('url'),
                channel_info.get('latency'),
                channel_info.get('province'),
                channel_info.get('city'),
                channel_info.get('isp'),
                channel_info.get('video_codec'),
                channel_info.get('group_title'),
                channel_info.get('tvg_id'),
                channel_info.get('tvg_logo'),
                1 if channel_info.get('is_valid', True) else 0
            ))

    def get_all_valid_channels(self) -> list:
        """获取所有有效频道（去重保留每个URL的最新记录）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT name, url, latency, province, city, isp, video_codec, group_title, tvg_id, tvg_logo
                FROM channels
                WHERE is_valid = 1
                ORDER BY name, latency
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def mark_invalid(self, url: str):
        """将指定URL标记为无效"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE channels SET is_valid = 0 WHERE url = ?', (url,))

    def clear_invalid(self):
        """清理无效记录（可选）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM channels WHERE is_valid = 0')

    def is_url_exists(self, url: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT 1 FROM channels WHERE url = ?', (url,))
            return cursor.fetchone() is not None

    def get_last_check_time(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT MAX(last_checked) FROM channels')
            row = cursor.fetchone()
            return row[0] if row and row[0] else None
