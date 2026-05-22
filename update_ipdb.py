#!/usr/bin/env python3
# IP 数据库自动更新模块（从纯真网络获取最新 qqwry.dat）
import os
import sys

def update_ip_database():
    """从纯真网络更新 IP 数据库"""
    try:
        from qqwry import updateQQwry
    except ImportError:
        print("❌ qqwry-py3 未安装，无法更新 IP 数据库")
        print("   请运行: pip install qqwry-py3")
        return False
    
    print("🔄 正在更新 IP 数据库...")
    try:
        # 下载并保存到当前目录
        result = updateQQwry("qqwry.dat")
        if isinstance(result, int) and result > 0:
            print(f"✅ IP 数据库更新成功！文件大小: {result} 字节")
            return True
        else:
            print(f"⚠️ IP 数据库更新失败，错误码: {result}")
            return False
    except Exception as e:
        print(f"⚠️ IP 数据库更新异常: {e}")
        return False

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
            return {
                "exists": True,
                "version": version,
                "size": size
            }
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
    
    print("\n开始更新...")
    if update_ip_database():
        print("\n更新完成！")
    else:
        print("\n更新失败，请检查网络连接")
        sys.exit(1)
