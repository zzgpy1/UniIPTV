# 解析 demo.txt，提取期望的分类和频道名列表
import re

def parse_demo_file(file_path: str) -> dict:
    """
    返回：{
        "分类名称": ["频道名1", "频道名2", ...],
        ...
    }
    保持原始顺序
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    
    categories = {}
    current_cat = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 匹配分类行：以任意字符开头，末尾为 ",#genre#"
        if line.endswith(",#genre#"):
            # 提取分类名（去掉最后的 ,#genre#）
            current_cat = line[:-7]
            categories[current_cat] = []
        elif current_cat is not None:
            # 频道名行（排除注释等）
            if not line.startswith("#"):
                categories[current_cat].append(line)
    return categories
