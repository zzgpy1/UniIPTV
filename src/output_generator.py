#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputGenerator:
    """输出文件生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def generate(self, streams: List[Dict], epg_data: Dict = None) -> Dict:
        """生成所有输出文件"""
        stats = {
            'txt_count': 0,
            'm3u_count': 0,
            'm3u8_count': 0
        }
        
        # 1. 生成 TXT 格式（简单 URL 列表）
        txt_file = self.output_dir / 'tv.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            for stream in streams:
                if stream.get('url'):
                    f.write(f"{stream['url']}\n")
                    stats['txt_count'] += 1
        
        logger.info(f"生成 TXT 文件: {txt_file}, {stats['txt_count']} 条")
        
        # 2. 生成 M3U 格式（标准播放列表）
        m3u_file = self.output_dir / 'tv.m3u'
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            
            for stream in streams:
                name = stream.get('name', 'Unknown')
                url = stream.get('url', '')
                group = stream.get('group', 'Other')
                tvg_id = stream.get('tvg_id', '')
                tvg_logo = stream.get('tvg_logo', '')
                delay = stream.get('delay', 0)
                
                if not url:
                    continue
                
                # 构建 EXTINF 行
                extinf_parts = [f'-1']
                if tvg_id:
                    extinf_parts.append(f'tvg-id="{tvg_id}"')
                if tvg_logo:
                    extinf_parts.append(f'tvg-logo="{tvg_logo}"')
                extinf_parts.append(f'group-title="{group}"')
                
                extinf_line = '#EXTINF:' + ','.join(extinf_parts) + f',{name}'
                f.write(f'{extinf_line}\n{url}\n')
                stats['m3u_count'] += 1
        
        logger.info(f"生成 M3U 文件: {m3u_file}, {stats['m3u_count']} 条")
        
        # 3. 生成 M3U8 格式（同 M3U，便于兼容）
        m3u8_file = self.output_dir / 'tv.m3u8'
        with open(m3u8_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write(f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            for stream in streams:
                url = stream.get('url', '')
                if url and not url.endswith('.m3u8'):
                    url = url.replace('.m3u', '.m3u8')
                if url:
                    name = stream.get('name', 'Unknown')
                    f.write(f'#EXTINF:-1,{name}\n{url}\n')
                    stats['m3u8_count'] += 1
        
        logger.info(f"生成 M3U8 文件: {m3u8_file}, {stats['m3u8_count']} 条")
        
        return stats
