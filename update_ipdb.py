#!/usr/bin/env python3
# IP 数据库自动更新模块（从纯真网络获取最新 qqwry.dat）
import os
import sys

def update_ip_database():
    """从纯真网络更新 IP 数据库，返回 (成功标志, 错误信息)"""
    try:
        from qqwry import updateQQwry
    except ImportError:
        return False, "qqwry-py3 未安装，请运行: pip install qqwry-py3"
    
    print("🔄 正在更新 IP 数据库...")
    try:
        result = updateQQwry("qqwry.dat")
        if isinstance(result, int) and result > 0:
            print(f"✅ IP 数据库更新成功！文件大小: {result} 字节")
            return True, None
        else:
            msg = f"更新失败，错误码: {result}"
            print(f"⚠️ {msg}")
            return False, msg
    except Exception as e:
        msg = f"更新异常: {e}"
        print(f"⚠️ {msg}")
        return False, msg

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
    
    info = get_database_info()
    if info["exists"]:
        print(f"当前数据库: {info.get('version', '未知版本')}, 大小: {info.get('size', 0)} 字节")
    else:
        print("当前无 IP 数据库文件")
    
    success, err = update_ip_database()
    if not success:
        print(f"\n⚠️ IP 数据库更新失败，将使用已有的数据库（若存在）")
        # 如果已有数据库文件，返回 0（不影响构建）
        if check_database_exists():
            print("  已有数据库文件可用，继续执行。")
        else:
            print("  没有可用数据库文件，IP 归属地解析功能将不可用。")
        sys.exit(0)   # 更新失败但不中断工作流
    else:
        print("\n✅ 数据库更新完成")
        sys.exit(0)
