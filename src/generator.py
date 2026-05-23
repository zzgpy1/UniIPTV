# src/generator.py
# 输出生成：M3U 和 TXT 格式（清理频道名，只输出最优源）

import os
import re
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

def clean_channel_name(name: str) -> str:
    """
    清理频道名：去掉分辨率标签（720p、1080p、4K等）、去掉多余空格、去掉备用源后缀
    例如: "CCTV-1 1080p" -> "CCTV-1"
         "湖南卫视(备1)" -> "湖南卫视"
    """
    # 去除常见的清晰度标签
    name = re.sub(r'\s*(?:1080[pi]|720[pi]|4K|8K|HD|高清|超清|标清|流畅|付费|备\d*)\s*', '', name, flags=re.IGNORECASE)
    # 去除括号及内容（如“(HD)”）
    name = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 去除多余空格
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def generate_m3u(classified: dict, output_path: str):
    """
    生成标准 M3U 文件，每个频道只输出最优的一个源（无备用源后缀，无分辨率标签）
    classified 格式：{分类名称: [channel_dict, ...]}
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # 获取最优 URL（第一个即为合并排序后的最优）
                if "urls" in ch and ch["urls"]:
                    url = ch["urls"][0]
                elif "url" in ch:
                    url = ch["url"]
                else:
                    continue
                
                # 清理频道名
                clean_name = clean_channel_name(ch["name"])
                
                extinf = f'#EXTINF:-1'
                if ch.get("id"):
                    extinf += f' tvg-id="{ch["id"]}"'
                if ch.get("logo"):
                    extinf += f' tvg-logo="{ch["logo"]}"'
                if category:
                    extinf += f' group-title="{category}"'
                extinf += f',{clean_name}\n'
                f.write(extinf)
                f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    """
    生成 TXT 格式（分类注释 + URL 列表），只输出最优源
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
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
