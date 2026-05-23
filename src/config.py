# src/config.py
# 配置文件：源地址、分类关键词、全局参数、数据库配置

import os

# ==================== IPTV 源列表 ====================
IPTV_SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/gh-pages/countries/cn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv4.m3u",
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv4.txt",
    "https://raw.githubusercontent.com/zzgpy1/Collect-IPTV/main/best_sorted.m3u",
    "https://raw.githubusercontent.com/dogwalkerg/IPTV-collect-tv-txt/main/others_output.txt",
    "https://raw.githubusercontent.com/zzgpy1/iptv-hybrid/main/iptv.m3u",
]

# ==================== 性能配置 ====================
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))      # 并发线程数
TIMEOUT = int(os.getenv("TIMEOUT", 10))              # 超时时间（秒）

# ==================== 验证配置 ====================
FFMPEG_ENABLE = os.getenv("FFMPEG_ENABLE", "true").lower() == "true"
FFMPEG_STRICT = os.getenv("FFMPEG_STRICT", "false").lower() == "true"
ENABLE_RETRY = os.getenv("ENABLE_RETRY", "true").lower() == "true"

# ==================== HTTP 请求头 ====================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== 分类关键词映射 ====================
# 用于智能分类，优先级：group-title > 频道名匹配
CATEGORY_KEYWORDS = {
    "央视": ["CCTV", "cctv", "央视", "中央电视", "中央-", "中央台", "CNTV", "CCTV-"],
    "卫视": ["卫视", "卫星", "TV", "HD", "Satellite", "湖南", "浙江", "江苏", "东方", "北京", "深圳", "广东卫视", "上海卫视"],
    "地方": ["地方", "综合", "频道", "县", "市", "省台", "城市", "生活", "新闻", "经济"],
    "体育": ["体育", "sport", "运动", "健身", "赛事", "ESPN", "CCTV5", "五星体育", "高尔夫"],
    "动漫": ["动漫", "动画", "卡通", "anime", "cartoon", "kids", "少儿", "宝贝", "玩具"],
    "新闻": ["新闻", "news", "资讯", "财经", "CCTV13", "报道"],
    "影视": ["电影", "影院", "剧集", "电视剧", "movie", "film", "series", "影视频道", "剧场"],
    "音乐": ["音乐", "music", "综艺", "娱乐", "entertainment", "MV", "歌舞"],
    "教育": ["教育", "教育频道", "学习", "CCTV10", "科技", "教学"],
    "纪录片": ["纪实", "记录", "documentary", "CCTV9", "探索", "发现"],
    "其他": []   # 默认分类
}

# 央视频道固定顺序（用于输出排序）
CCTV_ORDER = [
    "CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5", "CCTV-5+", "CCTV-6",
    "CCTV-7", "CCTV-8", "CCTV-9", "CCTV-10", "CCTV-11", "CCTV-12", "CCTV-13",
    "CCTV-14", "CCTV-15", "CCTV-16", "CCTV-17", "CCTV-4K", "CCTV-8K",
    "CCTV世界地理", "CCTV央视台球", "CCTV女性时尚", "CCTV怀旧剧场",
    "CCTV第一剧场", "CCTV风云足球", "CCTV老故事", "CGTN", "CGTN俄语",
    "CGTN法语", "CGTN纪录", "CGTN西语", "CGTN阿语"
]

# ==================== 输出配置 ====================
OUTPUT_DIR = "output"
M3U_FILE = "tv.m3u"
TXT_FILE = "tv.txt"

# ==================== 重试配置 ====================
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_MAX_WAIT = 60

# ==================== Demo 文件（已废弃，保留兼容）====================
DEMO_FILE = "demo.txt"

# ==================== IP 解析与地域筛选 ====================
IP_DATABASE_FILE = "qqwry.dat"
ENABLE_IP_RESOLVE = os.getenv("ENABLE_IP_RESOLVE", "true").lower() == "true"
ENABLE_REGION_FILTER = os.getenv("ENABLE_REGION_FILTER", "false").lower() == "true"
PREFERRED_LOCATION = os.getenv("PREFERRED_LOCATION", "")   # 多个用逗号分隔
PREFERRED_ISP = os.getenv("PREFERRED_ISP", "")             # 多个用逗号分隔

# ==================== 数据库配置 ====================
# 用于存储历史检测结果，减少重复工作
DATABASE_ENABLE = os.getenv("DATABASE_ENABLE", "true").lower() == "true"
DATABASE_PATH = os.getenv("DATABASE_PATH", "iptv_cache.db")   # SQLite 数据库文件路径
DATABASE_TABLE = "channel_cache"

# ==================== 频道合并配置 ====================
MAX_SOURCES_PER_CHANNEL = 5      # 每个频道最多保留几个源
PREFER_H264 = True               # 是否优先保留 H.264 编码的源
PREFER_LOCAL_ISP = True          # 是否优先选择同运营商源（需要 IP 解析支持）
