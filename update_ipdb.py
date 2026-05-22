#!/usr/bin/env python3
# IP 数据库自动更新模块（使用稳定 CDN 源）
import os
import sys
import requests
import time

# 优先使用的 CDN 源（您提供的地址）
PRIMARY_URL = "https://cdn.1008.site/gh/nmgliangwei/qqwry@main/qqwry.dat"
# 备用镜像源（Github）
BACKUP_URL = "https://raw.githubusercontent.com/FW27623/qqwry/main/qqwry.datt"

MAX_RETRIES = 3
RETRY_DELAY = 5

def download_file(url, filename):
    """下载文件，返回成功标志"""
    print(f"正在从 {url} 下载...")
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        # 简单检查内容类型是否为二进制文件
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type and '404' in response.text[:100]:
            raise Exception("返回了404错误页面")
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # 验证文件大小（至少1MB）
        if os.path.getsize(filename) < 1024 * 1024:
            raise Exception("下载的文件过小，可能无效")
        print(f"✅ 成功下载: {filename}")
        return True
    except Exception as e:
        print(f"⚠️ 下载失败: {e}")
        return False

def download_with_retry(url, filename, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """带重试的下载"""
    for attempt in range(max_retries):
        if download_file(url, filename):
            return True
        if attempt < max_retries - 1:
            print(f"等待 {delay} 秒后重试...")
            time.sleep(delay)
    return False

def update_ip_database():
    """从多个源尝试更新 IP 数据库"""
    # 优先使用主 CDN 源
    if download_with_retry(PRIMARY_URL, "qqwry.dat"):
        return True, None
    # 备用源
    print("主源失败，尝试备用源...")
    if download_with_retry(BACKUP_URL, "qqwry.dat"):
        return True, None
    return False, "所有下载源均不可用"

def check_database_exists():
    return os.path.exists("qqwry.dat")

def get_database_info():
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

    info = get_database_info()
    if info["exists"]:
        print(f"当前数据库: {info.get('version', '未知版本')}, 大小: {info.get('size', 0)} 字节")
    else:
        print("当前无 IP 数据库文件")

    success, err = update_ip_database()
    if not success:
        print(f"\n⚠️ IP 数据库更新失败: {err}")
        if check_database_exists():
            print("  已有数据库文件可用，将继续使用旧版本。")
        else:
            print("  没有可用数据库文件，IP 归属地解析功能将不可用。")
        sys.exit(0)
    else:
        print("\n✅ 数据库已成功更新")
        sys.exit(0)
