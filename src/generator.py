# src/generator.py
import os
from src.config import OUTPUT_DIR, M3U_FILE, TXT_FILE

# 定义输出分类顺序：央视 → 卫视 → 各省份（按拼音顺序） → 动漫
# 省份列表（按拼音排序，可根据需要调整）
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

def get_category_order(category: str) -> int:
    """返回分类的排序权重"""
    if category == "央视":
        return 0
    if category == "卫视":
        return 1
    if category in PROVINCES:
        # 省份权重从 2 开始
        return 2 + PROVINCES.index(category)
    if category == "动漫":
        return 1000
    # 其他未列入的分类（但未被过滤）放在最后
    return 2000

def filter_and_sort_categories(classified: dict) -> dict:
    """过滤不需要的分类，并按自定义顺序排序"""
    # 过滤
    filtered = {k: v for k, v in classified.items() if k not in FILTER_CATEGORIES}
    # 排序
    sorted_items = sorted(filtered.items(), key=lambda item: get_category_order(item[0]))
    return dict(sorted_items)

def generate_m3u(classified: dict, output_path: str):
    """生成 M3U 文件，按分类顺序输出"""
    # 先过滤和排序
    classified = filter_and_sort_categories(classified)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# 分类: {category}\n")
            for ch in channels:
                # ch 是字典，包含 name, urls, url, 等
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
    """生成 TXT 文件，也按分类顺序输出"""
    classified = filter_and_sort_categories(classified)
    with open(output_path, "w", encoding="utf-8") as f:
        for category, channels in classified.items():
            if not channels:
                continue
            f.write(f"\n# {category}\n")
            for ch in channels:
                # TXT 只输出第一个 URL
                url = ch.get("urls", [ch.get("url")])[0]
                f.write(f"{url}\n")

def generate_outputs(classified: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, M3U_FILE)
    txt_path = os.path.join(OUTPUT_DIR, TXT_FILE)
    generate_m3u(classified, m3u_path)
    generate_txt(classified, txt_path)
    print(f"📄 输出已生成：\n  - {m3u_path}\n  - {txt_path}")
