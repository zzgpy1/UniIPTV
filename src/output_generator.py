#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputGenerator:
    def __init__(self, output_dir: Path, config_dir: Path):
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.languages = self._load_languages()

    def _load_languages(self) -> Dict:
        lang_file = self.config_dir / 'languages.json'
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"en": {}, "zh": {}}

    def _translate_name(self, name: str, lang: str = 'zh') -> str:
        """根据 languages.json 映射频道名"""
        mapping = self.languages.get(lang, {})
        return mapping.get(name, name)

    def generate(self, streams: List[Dict], epg_data: Dict = None) -> Dict:
        stats = {'txt': 0, 'm3u': 0, 'm3u8': 0, 'tvbox': 0}

        # 1. TXT 输出 (每行一个URL)
        txt_file = self.output_dir / 'tv.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"# Updated: {datetime.now()}\n")
            for s in streams:
                f.write(f"{s['url']}\n")
                stats['txt'] += 1
        logger.info(f"生成 {txt_file} ({stats['txt']} 条)")

        # 2. M3U 输出 (带中文频道名)
        m3u_file = self.output_dir / 'tv.m3u'
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for s in streams:
                name = self._translate_name(s['name'], 'zh')
                group = s.get('group', 'Other')
                f.write(f'#EXTINF:-1 group-title="{group}",{name}\n{s["url"]}\n')
                stats['m3u'] += 1
        logger.info(f"生成 {m3u_file} ({stats['m3u']} 条)")

        # 3. M3U8 输出 (同M3U，但后缀为m3u8)
        m3u8_file = self.output_dir / 'tv.m3u8'
        with open(m3u8_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for s in streams:
                name = self._translate_name(s['name'], 'zh')
                url = s['url'].replace('.m3u', '.m3u8')
                f.write(f'#EXTINF:-1,{name}\n{url}\n')
                stats['m3u8'] += 1

        # 4. TVBox JSON 格式 (xc.json)
        tvbox_config = {
            "lives": [{
                "name": "UniIPTV",
                "type": 0,
                "url": "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/output/tv.m3u",
                "epg": "https://epg.112114.xyz/"
            }],
            "sites": [],
            "parses": []
        }
        # 注意：上面的 raw 链接需要你自己替换为实际的 GitHub 用户名和仓库名
        # 这里为了自动化，可以读取环境变量或使用相对路径，但推荐在说明中让用户手动修改
        json_file = self.output_dir / 'xc.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tvbox_config, f, indent=2, ensure_ascii=False)
        stats['tvbox'] = 1
        logger.info(f"生成 {json_file}")

        return stats
