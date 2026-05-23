# src/generator.py
import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

def generate_m3u(classified: dict, output_path: str):
    """生成支持多源（备源）的 M3U 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch_dict in channels:
                # 获取 url 列表（优先 urls，否则退化为单元素列表）
                urls = ch_dict.get('urls', [ch_dict.get('url', '')])
                if not urls:
                    continue
                for idx, url in enumerate(urls):
                    if idx == 0:
                        # 第一个源使用完整的 #EXTINF 标签
                        extinf = f'#EXTINF:-1'
                        if ch_dict.get('id'):
                            extinf += f' tvg-id="{ch_dict["id"]}"'
                        if ch_dict.get('logo'):
                            extinf += f' tvg-logo="{ch_dict["logo"]}"'
                        if category:
                            extinf += f' group-title="{category}"'
                        extinf += f',{ch_dict["name"]}\n'
                        f.write(extinf)
                    else:
                        # 备用源：也可使用相同频道名，播放器会尝试
                        extinf = f'#EXTINF:-1 group-title="{category}",备用{idx}:{ch_dict["name"]}\n'
                        f.write(extinf)
                    f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    """生成 TXT 格式（分类注释 + URL 列表）"""
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch_dict in channels:
                # TXT 格式只输出主源（或所有源）
                urls = ch_dict.get('urls', [ch_dict.get('url', '')])
                for url in urls:
                    f.write(f"{url}\n")

def generate_outputs(classified: dict):
    """生成所有输出文件，并确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
