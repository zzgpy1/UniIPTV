# src/generator.py
import os
import re
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

# 定义输出分类顺序：央视 → 卫视 → 各省份（按拼音顺序） → 动漫
PROVINCES = [
    "北京", "天津", "上海", "重庆",
    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "海南", "四川",
    "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆",
    "香港", "澳门"
]

# 需要过滤掉的一级分类（不输出）
FILTER_CATEGORIES = ["旅游", "国际", "游戏", "其他"]

def extract_cctv_number(name: str) -> float:
    """
    从频道名称中提取央视的数字编号，用于排序。
    支持格式：CCTV-1, CCTV1, CCTV-5+, CCTV5+, 中央1, 央视1等
    返回浮点数，特殊频道如CCTV-5+返回5.5，否则返回999
    """
    # 匹配 CCTV 后跟数字和可能的 + 号
    match = re.search(r'CCTV[- ]?(\d+)(\+?)', name, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        if match.group(2) == '+':
            return num + 0.5
        return float(num)
    # 匹配中文 央视/中央 数字
    match = re.search(r'[央视央视频道](\d+)', name)
    if match:
        return float(match.group(1))
    return 999.0  # 非央视频道放最后

def sort_channels_in_category(category: str, channels: list) -> list:
    """根据分类对频道列表进行排序"""
    if category == "央视":
        # 按央视数字排序
        channels.sort(key=lambda x: extract_cctv_number(x.get("name", "")))
    else:
        # 其他分类按频道名拼音排序
        channels.sort(key=lambda x: x.get("name", ""))
    return channels

def get_category_order(category: str) -> int:
    if category == "央视":
        return 0
    if category == "卫视":
        return 1
    if category in PROVINCES:
        return 2 + PROVINCES.index(category)
    if category == "动漫":
        return 1000
    return 2000

def filter_and_sort_categories(classified: dict) -> dict:
    filtered = {k: v for k, v in classified.items() if k not in FILTER_CATEGORIES}
    sorted_items = sorted(filtered.items(), key=lambda item: get_category_order(item[0]))
    return dict(sorted_items)

def generate_m3u(classified: dict, output_path: str):
    classified = filter_and_sort_categories(classified)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            # 在写入前对当前分类的频道进行排序
            channels = sort_channels_in_category(category, channels)
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                urls = ch.get("urls", [ch.get("url")])
                for idx, url in enumerate(urls):
                    if idx == 0:
                        extinf = f'#EXTINF:-1'
                        if ch.get("id"):
                            extinf += f' tvg-id="{ch["id"]}"'
                        if category:
                            extinf += f' group-title="{category}"'
                        extinf += f',{ch["name"]}\n'
                        f.write(extinf)
                    else:
                        f.write(f'#EXTINF:-1 group-title="{category}",备用源{idx}:{ch["name"]}\n')
                    f.write(f"{url}\n")

def generate_txt(classified: dict, output_path: str):
    classified = filter_and_sort_categories(classified)
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            channels = sort_channels_in_category(category, channels)
            f.write(f"\n# {category}\n")
            for ch in channels:
                url = ch.get("urls", [ch.get("url")])[0]
                f.write(f"{url}\n")

def generate_outputs(classified: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
