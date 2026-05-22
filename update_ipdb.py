#!/usr/bin/env python3
# IP 数据库自动更新模块（多源策略）
import os
import sys
import requests
import time

# 定义多个可靠的 qqwry.dat 下载源（按优先级排序）
QQWRY_SOURCES = [
    "https://github.com/metowolf/qqwry.dat/releases/latest/download/qqwry.dat",                # GitHub 源[reference:2]
    "https://cdn.1008.site/gh/nmgliangwei/qqwry@main/qqwry.dat",                               # GitHub 镜像源[reference:3]
    "https://raw.githubusercontent.com/FW27623/qqwry/main/qqwry.dat"                          # GitHub 镜像源[reference:4]
]

# 配置重试参数
MAX_RETRIES = 2
RETRY_DELAY = 3  # 秒

def download_file_with_retry(url, filename):
    """带重试机制的文件下载函数。成功返回 True，失败返回 False。"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"正在从 {url} 下载... (尝试 {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # 简单的文件大小验证，避免保存错误页面
            if int(response.headers.get('content-length', 0)) < 1024 * 1024:
                raise Exception("下载的文件过小，可能无效")

            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"✅ 成功下载: {filename}，大小: {os.path.getsize(filename)} 字节")
            return True
        except Exception as e:
            print(f"⚠️ 下载失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                return False
    return False

def update_ip_database():
    """从多个源尝试更新 IP 数据库。"""
    print("🔄 尝试从多个在线源下载最新数据库...")

    for source_url in QQWRY_SOURCES:
        if download_file_with_retry(source_url, "qqwry.dat"):
            return True, None

    print("⚠️ 所有在线源均下载失败，将使用本地备份策略")
    return False, "所有在线源均不可用，请检查网络连接或稍后重试"

def check_database_exists() -> bool:
    """检查 IP 数据库是否存在。"""
    return os.path.exists("qqwry.dat")

def get_database_info() -> dict:
    """获取 IP 数据库信息。"""
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
        sys.exit(0)   # 更新失败但不中断工作流
    else:
        print("\n✅ 数据库已成功更新")
        sys.exit(0)
