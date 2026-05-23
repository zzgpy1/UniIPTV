import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE, CATEGORY_ORDER

def generate_m3u(classified: dict, output_path: str):
    """生成支持多源（备胎）的 M3U 文件，按指定分类顺序输出"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category in CATEGORY_ORDER:
            if category not in classified:
                continue
            channels = classified[category]
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                urls = getattr(ch, 'urls', [ch.url]) if hasattr(ch, 'urls') else [ch.url if not isinstance(ch, dict) else ch['url']]
                for idx, url in enumerate(urls):
                    if idx == 0:
                        extinf = f'#EXTINF:-1'
                        tvg_id = getattr(ch, 'tvg_id', '') if not isinstance(ch, dict) else ch.get('tvg_id', '')
                        if tvg_id:
                            extinf += f' tvg-id="{tvg_id}"'
                        if category:
                            extinf += f' group-title="{category}"'
                        channel_name = getattr(ch, 'name', '') if not isinstance(ch, dict) else ch.get('name', '')
                        extinf += f',{channel_name}\n'
                        f.write(extinf)
                    else:
                        f.write(f'#EXTINF:-1 group-title="{category}",备用源{idx}:{channel_name}\n')
                    f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    """生成 TXT 格式，按分类顺序输出"""
    with open(output_path, "w", encoding="utf-8") as f:
        for category in CATEGORY_ORDER:
            if category not in classified:
                continue
            channels = classified[category]
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
                urls = getattr(ch, 'urls', [ch.url]) if hasattr(ch, 'urls') else [ch.url if not isinstance(ch, dict) else ch['url']]
                for url in urls:
                    f.write(f"{url}\n")

def generate_outputs(classified: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
