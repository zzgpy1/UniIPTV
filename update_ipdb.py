#!/usr/bin/env python3
# IP 数据库自动更新模块（使用 qqwry 镜像源的稳定版本）
import os
import sys
import requests
import gzip
import shutil
from io import BytesIO
import time

# 备用的下载源（GitCode 镜像：https://gitcode.com/qqwry/qqwry.dat）
QQWRY_MIRROR_URL = "https://gitcode.com/qqwry/qqwry.dat/raw/main/qqwry.dat"

# 配置重试参数
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

def download_file_with_retry(url, filename, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    带重试机制的文件下载函数
    增强的网络容错性，在 GitHub Actions 等网络不稳定的环境中也能稳定工作
    """
    for attempt in range(max_retries):
        try:
            print(f"正在从 {url} 下载... (尝试 {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 检查内容类型，排除错误页面
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type and '404' in response.text[:100]:
                raise Exception("下载链接返回了404错误页面，可能URL已失效")
            
            # 写入文件
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 验证文件有效性（简单的文件大小检查）
            if os.path.getsize(filename) < 1024 * 1024:  # 小于1MB，可能有问题
                raise Exception("下载的文件过小，可能无效")
                
            print(f"✅ 成功下载: {filename}")
            return True
        except Exception as e:
            print(f"⚠️ 下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                return False
    return False

def update_ip_database():
    """从多个源尝试更新 IP 数据库（优先使用在线镜像，回退到本地）"""
    
    # 1. 尝试从在线镜像源下载最新数据库
    print("🔄 尝试从 qqwry 镜像源下载最新数据库...")
    
    if download_file_with_retry(QQWRY_MIRROR_URL, "qqwry.dat"):
        return True, None
    
    print("⚠️ 在线下载失败，将使用本地备份策略")
    return False, "所有在线源均不可用，请检查网络连接或稍后重试"

def check_database_exists() -> bool:
    """检查 IP 数据库是否存在"""
    return os.path.exists("qqwry.dat")

def get_database_info() -> dict:
    """获取 IP 数据库信息"""
    if not check_database_exists():
        return {"exists": False}
    
    try:
        from qqwry import QQwry
        q = QQwry()
        if q.load_file("qqwry.dat", loadindex=False):
            version = q.get_lastone()
            size = os.path.getsize("qqwry.dat")
            return {"exists": True, "version": version, "size": size}
    except Exception:
        pass
    
    return {"exists": True, "version": "未知", "size": os.path.getsize("qqwry.dat")}

if __name__ == "__main__":
    print("=" * 50)
    print("纯真 IP 数据库更新工具")
    print("=" * 50)
    
    # 显示现有数据库信息
    info = get_database_info()
    if info["exists"]:
        print(f"当前数据库: {info.get('version', '未知版本')}, 大小: {info.get('size', 0)} 字节")
    else:
        print("当前无 IP 数据库文件")
    
    # 尝试更新数据库
    success, err = update_ip_database()
    if not success:
        print(f"\n⚠️ IP 数据库更新失败: {err}")
        if check_database_exists():
            print("  已有数据库文件可用，将继续使用旧版本。")
        else:
            print("  没有可用数据库文件，IP 归属地解析功能将不可用。")
        sys.exit(0)   # 更新失败但不中断工作流
    else:
        print("\n✅ 数据库已成功更新")
        sys.exit(0)
