# IP 归属地和运营商解析模块（基于纯真 IP 数据库）
import socket
import re
from urllib.parse import urlparse
from typing import Optional, Tuple
import os

# 尝试导入 qqwry 库
try:
    from qqwry import QQwry
    QQWRY_AVAILABLE = True
except ImportError:
    QQWRY_AVAILABLE = False
    print("⚠️ qqwry-py3 未安装，IP 归属地解析功能将不可用")

class IPResolver:
    """IP 归属地和运营商解析器"""
    
    _instance = None
    _qqwry = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_resolver()
        return cls._instance
    
    def _init_resolver(self):
        """初始化解析器，加载 IP 数据库"""
        self._loaded = False
        if not QQWRY_AVAILABLE:
            return
        
        # 尝试加载 IP 数据库
        db_paths = ["qqwry.dat", "data/qqwry.dat", "../qqwry.dat"]
        for path in db_paths:
            if os.path.exists(path):
                self._db_path = path
                break
        else:
            print("⚠️ 未找到 qqwry.dat 文件，IP 归属地解析功能不可用")
            return
        
        try:
            self._qqwry = QQwry()
            if self._qqwry.load_file(self._db_path, loadindex=False):
                self._loaded = True
                version = self._qqwry.get_lastone()
                if version:
                    print(f"✅ IP 数据库加载成功: {self._db_path}, 版本: {version}")
                else:
                    print(f"✅ IP 数据库加载成功: {self._db_path}")
            else:
                print(f"⚠️ IP 数据库加载失败: {self._db_path}")
        except Exception as e:
            print(f"⚠️ IP 数据库加载异常: {e}")
    
    def extract_ip_from_url(self, url: str) -> Optional[str]:
        """从 URL 中提取 IP 地址"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return None
            # 检查是否为 IP 地址格式
            ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
            if ip_pattern.match(hostname):
                return hostname
            # 尝试解析域名
            try:
                ip = socket.gethostbyname(hostname)
                return ip
            except socket.gaierror:
                return None
        except Exception:
            return None
    
    def lookup(self, ip: str) -> Optional[Tuple[str, str]]:
        """查询 IP 归属地，返回 (位置, 运营商)"""
        if not self._loaded or not self._qqwry:
            return None
        try:
            result = self._qqwry.lookup(ip)
            if result and len(result) >= 2:
                # 纯真 IP 库返回格式: (位置, 运营商)
                # 例如: ("广东省广州市", "电信") 或 ("中国", "北京 鹏博士")
                location = result[0] or ""
                isp = result[1] or ""
                # 清理数据：去除多余空格
                location = location.strip()
                isp = isp.strip()
                return (location, isp)
            return None
        except Exception:
            return None
    
    def resolve_channel_ip(self, channel) -> Optional[dict]:
        """解析频道的 IP 归属地信息"""
        if not self._loaded:
            return None
        
        ip = self.extract_ip_from_url(channel.url)
        if not ip:
            return None
        
        result = self.lookup(ip)
        if not result:
            return None
        
        location, isp = result
        # 提取省份和城市
        province, city = self._parse_location(location)
        
        return {
            "ip": ip,
            "location_raw": location,
            "province": province,
            "city": city,
            "isp": isp
        }
    
    def _parse_location(self, location: str) -> Tuple[str, str]:
        """解析位置字符串，提取省份和城市"""
        if not location:
            return ("", "")
        
        # 常见省份/直辖市列表
        provinces = [
            "北京", "天津", "上海", "重庆",
            "河北", "山西", "辽宁", "吉林", "黑龙江",
            "江苏", "浙江", "安徽", "福建", "江西", "山东",
            "河南", "湖北", "湖南", "广东", "海南", "四川",
            "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
            "内蒙古", "广西", "西藏", "宁夏", "新疆",
            "香港", "澳门"
        ]
        
        province = ""
        city = ""
        
        # 提取省份
        for p in provinces:
            if p in location:
                province = p
                # 提取城市（省份后的部分）
                remaining = location.split(p, 1)[-1]
                if remaining and remaining.startswith(("省", "市")):
                    remaining = remaining[1:]
                if remaining:
                    # 简单提取城市名（取第一个逗号或空格前的内容）
                    import re
                    city_match = re.match(r'^[^市,\s]+', remaining)
                    if city_match:
                        city = city_match.group()
                break
        
        # 如果没有匹配到省份，可能 location 本身就是城市名
        if not province and location:
            province = location
        
        return (province, city)
    
    @property
    def is_available(self) -> bool:
        """检查解析器是否可用"""
        return self._loaded

# 全局单例
_resolver = None

def get_resolver() -> IPResolver:
    """获取 IPResolver 单例"""
    global _resolver
    if _resolver is None:
        _resolver = IPResolver()
    return _resolver


def matches_region(channel_info: dict, preferred_locations: list, preferred_isps: list) -> bool:
    """
    检查频道是否匹配指定的地域和运营商筛选条件
    
    Args:
        channel_info: 包含 province, city, isp 的字典
        preferred_locations: 优先地域列表（省份/城市）
        preferred_isps: 优先运营商列表
    
    Returns:
        True 如果匹配任一条件（或条件为空则返回 True）
    """
    if not preferred_locations and not preferred_isps:
        return True
    
    province = channel_info.get("province", "")
    city = channel_info.get("city", "")
    isp = channel_info.get("isp", "")
    
    # 匹配地域（省份或城市）
    location_match = False
    if preferred_locations:
        for loc in preferred_locations:
            if loc in province or loc in city:
                location_match = True
                break
    else:
        location_match = True
    
    # 匹配运营商
    isp_match = False
    if preferred_isps:
        for i in preferred_isps:
            if i in isp:
                isp_match = True
                break
    else:
        isp_match = True
    
    return location_match and isp_match
