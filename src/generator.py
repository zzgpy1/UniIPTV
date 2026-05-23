# src/generator.py
# 输出生成：M3U 和 TXT 格式（支持多源合并后的频道对象）

import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

def generate_m3u(classified: dict, output_path: str):
    """
    生成标准 M3U 文件，支持一个频道多个 URL（备源）
    classified 格式：{分类名称: [channel_dict, ...]}
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # 获取 URL 列表（兼容旧格式单个 url 或新格式 urls 列表）
                if "urls" in ch and isinstance(ch["urls"], list):
                    urls = ch["urls"]
                elif "url" in ch:
                    urls = [ch["url"]]
                else:
                    urls = []
                
                for idx, url in enumerate(urls):
                    if idx == 0:
                        # 第一个源使用完整信息
                        extinf = f'#EXTINF:-1'
                        if ch.get("id"):
                            extinf += f' tvg-id="{ch["id"]}"'
                        if ch.get("logo"):
                            extinf += f' tvg-logo="{ch["logo"]}"'
                        if category:
                            extinf += f' group-title="{category}"'
                        extinf += f',{ch["name"]}\n'
                        f.write(extinf)
                    else:
                        # 备用源简写，便于播放器识别
                        f.write(f'#EXTINF:-1 group-title="{category}",{ch["name"]} (备{idx})\n')
                    f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    """
    生成 TXT 格式（分类注释 + URL 列表）
    注意：TXT 格式无法表达多源，只输出每个频道的第一个 URL
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
                # 取第一个可用 URL
                if "urls" in ch and ch["urls"]:
                    url = ch["urls"][0]
                elif "url" in ch:
                    url = ch["url"]
                else:
                    continue
                f.write(f"{url}\n")

def generate_outputs(classified: dict):
    """生成所有输出文件，并确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
