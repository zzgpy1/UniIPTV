# 输出生成：M3U 和 TXT 格式
import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

def generate_m3u(classified: dict, output_path: str):
    """生成标准 M3U 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # 构建 EXTINF 行
                extinf = f'#EXTINF:-1'
                if ch.get("id"):
                    extinf += f' tvg-id="{ch["id"]}"'
                if ch.get("logo"):
                    extinf += f' tvg-logo="{ch["logo"]}"'
                if category:
                    extinf += f' group-title="{category}"'
                extinf += f',{ch["name"]}\n'
                f.write(extinf)
                f.write(f"{ch['url']}\n")

def generate_txt(classified: dict, output_path: str):
    """生成 TXT 格式（分类注释 + URL 列表）"""
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            f.write(f"\n# {category}\n")
            for ch in channels:
                f.write(f"{ch['url']}\n")

def generate_outputs(classified: dict):
    """生成所有输出文件，并确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
