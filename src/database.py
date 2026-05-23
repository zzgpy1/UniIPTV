# 数据库模块：存储频道信息，避免重复采集
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "iptv_cache.db"

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 频道表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT,
            latency INTEGER,
            video_codec TEXT,
            has_video INTEGER,
            has_audio INTEGER,
            ip_info TEXT,
            valid INTEGER DEFAULT 1,
            last_checked TIMESTAMP,
            source TEXT,
            UNIQUE(name, url)
        )
    ''')
    
    # 元数据表（记录上次更新时间、源文件hash等）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_channels(channels_list, source_hash=None):
    """保存频道列表到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先标记所有现有频道为待更新（后续会更新有效状态）
    cursor.execute("UPDATE channels SET valid = 0")
    
    now = datetime.now().isoformat()
    for ch in channels_list:
        # 检查是否已存在
        cursor.execute(
            "SELECT id FROM channels WHERE name = ? AND url = ?",
            (ch.name, ch.url)
        )
        exists = cursor.fetchone()
        
        ip_info_json = None
        if hasattr(ch, 'ip_info') and ch.ip_info:
            ip_info_json = json.dumps(ch.ip_info, ensure_ascii=False)
        
        if exists:
            cursor.execute('''
                UPDATE channels SET
                    category = ?, latency = ?, video_codec = ?,
                    has_video = ?, has_audio = ?, ip_info = ?,
                    valid = 1, last_checked = ?
                WHERE name = ? AND url = ?
            ''', (
                getattr(ch, 'category', '其他'),
                getattr(ch, 'latency', 9999),
                getattr(ch, 'video_codec', ''),
                1 if getattr(ch, 'has_video', False) else 0,
                1 if getattr(ch, 'has_audio', False) else 0,
                ip_info_json,
                now,
                ch.name, ch.url
            ))
        else:
            cursor.execute('''
                INSERT INTO channels (
                    name, url, category, latency, video_codec,
                    has_video, has_audio, ip_info, valid, last_checked, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ch.name, ch.url,
                getattr(ch, 'category', '其他'),
                getattr(ch, 'latency', 9999),
                getattr(ch, 'video_codec', ''),
                1 if getattr(ch, 'has_video', False) else 0,
                1 if getattr(ch, 'has_audio', False) else 0,
                ip_info_json,
                1,
                now,
                getattr(ch, 'source', 'unknown')
            ))
    
    # 删除长期无效的频道（可选：保留标记为无效但不删除）
    # cursor.execute("DELETE FROM channels WHERE valid = 0 AND last_checked < datetime('now', '-7 days')")
    
    # 保存源文件hash
    if source_hash:
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("source_hash", source_hash)
        )
    
    conn.commit()
    conn.close()
    print(f"💾 已保存 {len(channels_list)} 个频道到数据库")

def load_valid_channels():
    """从数据库加载所有有效的频道（返回Channel对象列表）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, url, category, latency, video_codec, has_video, has_audio, ip_info
        FROM channels WHERE valid = 1
        ORDER BY name, latency
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    # 动态创建Channel对象（简化版）
    from src.parser import Channel
    channels = []
    for row in rows:
        ch = Channel(row['name'], row['url'], row['category'] or '')
        ch.latency = row['latency']
        ch.video_codec = row['video_codec'] or ''
        ch.has_video = bool(row['has_video'])
        ch.has_audio = bool(row['has_audio'])
        if row['ip_info']:
            import json
            ch.ip_info = json.loads(row['ip_info'])
        channels.append(ch)
    
    print(f"📂 从数据库加载了 {len(channels)} 个有效频道")
    return channels

def get_source_hash():
    """获取上次保存的源文件hash"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM metadata WHERE key = 'source_hash'")
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def set_source_hash(hash_value):
    """设置源文件hash"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
        ("source_hash", hash_value)
    )
    conn.commit()
    conn.close()
