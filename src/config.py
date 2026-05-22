# 配置文件：源地址、分类关键词、全局参数
import os

# IPTV 源列表（用户提供的6个及以上）
IPTV_SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/gh-pages/countries/cn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv4.m3u",
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv4.txt",
    "https://raw.githubusercontent.com/zzgpy1/Collect-IPTV/main/best_sorted.m3u",
    "https://raw.githubusercontent.com/dogwalkerg/IPTV-collect-tv-txt/main/others_output.txt",
]

# 并发线程数 / 超时（秒）
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))
TIMEOUT = int(os.getenv("TIMEOUT", 10))
FFMPEG_ENABLE = os.getenv("FFMPEG_ENABLE", "true").lower() == "true"
ENABLE_RETRY = os.getenv("ENABLE_RETRY", "true").lower() == "true"

# HTTP 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 分类关键词映射（支持 group-title 和频道名）
CATEGORY_KEYWORDS = {
    "央视": ["CCTV", "cctv", "央视", "中央电视", "中央-", "中央台", "CNTV"],
    "卫视": ["卫视", "卫星", "TV", "HD", "Satellite", "湖南", "浙江", "江苏", "东方", "北京", "深圳"],
    "地方": ["地方", "综合", "频道", "县", "市", "省台", "城市"],
    "体育": ["体育", "sport", "运动", "健身", "赛事", "ESPN", "CCTV5", "五星体育"],
    "动漫": ["动漫", "动画", "卡通", "anime", "cartoon", "kids", "少儿", "宝贝"],
    "新闻": ["新闻", "news", "资讯", "财经", "CCTV13"],
    "影视": ["电影", "影院", "剧集", "电视剧", "movie", "film", "series", "影视频道"],
    "音乐": ["音乐", "music", "综艺", "娱乐", "entertainment", "MV"],
    "教育": ["教育", "教育频道", "学习", "CCTV10"],
    "纪录片": ["纪实", "记录", "documentary", "CCTV9"],
    "其他": []  # 默认分类
}

# 输出目录
OUTPUT_DIR = "output"
M3U_FILE = "tv.m3u"
TXT_FILE = "tv.txt"

# 重试配置（指数退避）
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_MAX_WAIT = 60
