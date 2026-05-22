# 工具函数（暂未使用，可扩展）
import re

def is_valid_url(url: str) -> bool:
    """简单检查 URL 格式"""
    return url.startswith(("http://", "https://", "rtmp://", "rtsp://"))

def safe_filename(name: str) -> str:
    """将频道名转为安全的文件名"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)
