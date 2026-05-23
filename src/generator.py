# src/generator.py
# 输出生成：支持多源的 M3U 和 TXT 格式

import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE


def generate_m3u(classified: dict, output_path: str):
    """
    生成标准 M3U 文件，支持多源（每个频道多个备选URL）
    classified 格式: {分类名: [MergedChannel 对象列表]}
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # 处理 MergedChannel 对象
                if hasattr(ch, 'urls'):
                    # MergedChannel 对象
                    urls = ch.urls
                    name = ch.name
                    tvg_id = getattr(ch, 'tvg_id', '')
                    tvg_logo = getattr(ch, 'tvg_logo', '')
                else:
                    # 字典类型（兼容旧格式）
                    urls = ch.get('urls') if ch.get('urls') else [ch.get('url', '')]
                    name = ch.get('name', '')
                    tvg_id = ch.get('id', '')
                    tvg_logo = ch.get('logo', '')
                
                if not urls:
                    continue
                
                # 第一个源使用完整标签
                extinf = f'#EXTINF:-1'
                if tvg_id:
                    extinf += f' tvg-id="{tvg_id}"'
                if tvg_logo:
                    extinf += f' tvg-logo="{tvg_logo}"'
                if category:
                    extinf += f' group-title="{category}"'
                extinf += f',{name}\n'
                f.write(extinf)
                f.write(f"{urls[0]}\n")
                
                # 备用源（每个备用源单独一行）
                for idx, url in enumerate(urls[1:], start=1):
                    f.write(f'#EXTINF:-1 group-title="{category}",备用源{idx}:{name}\n')
                    f.write(f"{url}\n")


def generate_txt(classified: dict, output_path: str):
    """
    生成 TXT 格式（分类注释 + URL 列表）
    为简化，只输出每个频道的第一个 URL（最佳源）
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
                # 处理 MergedChannel 对象
                if hasattr(ch, 'urls'):
                    url = ch.urls[0] if ch.urls else ''
                else:
                    url = ch.get('urls', [ch.get('url', '')])[0]
                if url:
                    f.write(f"{url}\n")


def generate_outputs(classified: dict):
    """生成所有输出文件，并确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
