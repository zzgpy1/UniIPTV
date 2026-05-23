# src/generator.py
import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

def generate_m3u(classified: dict, output_path: str):
    """生成支持多源（备胎）的 M3U 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # 判断是合并后的频道（有 urls 属性）还是普通频道
                if hasattr(ch, 'urls') and isinstance(ch.urls, list):
                    urls = ch.urls
                elif hasattr(ch, 'url'):
                    urls = [ch.url]
                else:
                    continue
                
                for idx, url in enumerate(urls):
                    if idx == 0:
                        # 第一个源使用完整的 #EXTINF 标签
                        extinf = f'#EXTINF:-1'
                        if hasattr(ch, 'tvg_id') and ch.tvg_id:
                            extinf += f' tvg-id="{ch.tvg_id}"'
                        if hasattr(ch, 'tvg_logo') and ch.tvg_logo:
                            extinf += f' tvg-logo="{ch.tvg_logo}"'
                        if category:
                            extinf += f' group-title="{category}"'
                        extinf += f',{ch.name}\n'
                        f.write(extinf)
                    else:
                        # 备用源：也可以写成一个简洁的标签，便于播放器识别
                        f.write(f'#EXTINF:-1 group-title="{category}",备用{idx}:{ch.name}\n')
                    f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    """生成 TXT 格式（分类注释 + URL 列表），多源时会分行列出所有源"""
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
                if hasattr(ch, 'urls') and isinstance(ch.urls, list):
                    for url in ch.urls:
                        f.write(f"{url}\n")
                elif hasattr(ch, 'url'):
                    f.write(f"{ch.url}\n")

def generate_outputs(classified: dict):
    """生成所有输出文件，并确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
