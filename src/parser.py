# M3U / TXT 解析与去重
import re
from urllib.parse import urlparse
from src.config import HEADERS

class Channel:
    def __init__(self, name: str, url: str, group_title: str = "", tvg_id: str = "", tvg_name: str = "", tvg_logo: str = ""):
        self.name = name.strip()
        self.url = url.strip()
        self.group_title = group_title
        self.tvg_id = tvg_id
        self.tvg_name = tvg_name
        self.tvg_logo = tvg_logo
        # 新增属性：测速延迟、IP信息、视频编码等
        self.latency = None
        self.ip_info = None
        self.video_codec = None
        self.has_video = False
        self.has_audio = False

    def key(self) -> str:
        return f"{self.name}|{self.url}"

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "group_title": self.group_title,
            "id": self.tvg_id,
            "logo": self.tvg_logo,
            "latency": self.latency,
            "video_codec": self.video_codec,
            "has_video": self.has_video,
            "has_audio": self.has_audio
        }

def parse_m3u(content: str) -> list:
    """解析标准 M3U 格式"""
    channels = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            # 提取属性
            group_title = ""
            tvg_id = ""
            tvg_name = ""
            tvg_logo = ""
            # 匹配 group-title="..."
            match = re.search(r'group-title="([^"]+)"', line)
            if match:
                group_title = match.group(1)
            match = re.search(r'tvg-id="([^"]+)"', line)
            if match:
                tvg_id = match.group(1)
            match = re.search(r'tvg-name="([^"]+)"', line)
            if match:
                tvg_name = match.group(1)
            match = re.search(r'tvg-logo="([^"]+)"', line)
            if match:
                tvg_logo = match.group(1)
            # 频道名在最后一个逗号之后
            name = line.split(",")[-1].strip()
            # 下一行应该是 URL
            if i+1 < len(lines) and not lines[i+1].startswith("#"):
                url = lines[i+1].strip()
                if url.startswith(("http://", "https://", "rtmp://", "rtsp://")):
                    channels.append(Channel(name, url, group_title, tvg_id, tvg_name, tvg_logo))
            i += 2
        else:
            i += 1
    return channels

def parse_txt(content: str) -> list:
    """解析 TXT 格式（每行一个 URL，可选注释行作为频道名）"""
    channels = []
    lines = content.splitlines()
    current_name = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            if line.startswith("#") and not line.startswith("#EXT"):
                # 注释可能用作频道名
                current_name = line.lstrip("#").strip()
            continue
        if line.startswith(("http://", "https://", "rtmp://", "rtsp://")):
            name = current_name if current_name else "未知频道"
            channels.append(Channel(name, line))
            current_name = None
    return channels

def parse_and_dedupe(raw_contents: dict) -> dict:
    """解析所有源内容，合并去重，返回 {key: Channel} 字典"""
    all_channels = {}
    for url, content in raw_contents.items():
        if not content:
            continue
        # 根据内容格式选择解析器
        if content.strip().startswith("#EXTM3U"):
            channels = parse_m3u(content)
        else:
            channels = parse_txt(content)
        for ch in channels:
            key = ch.key()
            if key not in all_channels:
                all_channels[key] = ch
    print(f"✅ 解析完成，去重后共 {len(all_channels)} 个频道")
    return all_channels
