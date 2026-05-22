#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import aiohttp
import asyncio
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class AIDiscovery:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    async def discover(self) -> List[Dict]:
        """调用AI API发现潜在的直播源"""
        if not self.api_key:
            logger.warning("未设置 DEEPSEEK_API_KEY 环境变量，跳过AI发现")
            return []

        prompt = """请提供10个可能有效的中国央视或省级卫视的直播流地址，以JSON数组格式返回。每个元素包含"name"和"url"字段。只输出JSON，不要有其他文字。示例:
[{"name": "CCTV1", "url": "http://example.com/cctv1.m3u8"}]
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        # 提取JSON部分
                        json_start = content.find('[')
                        json_end = content.rfind(']') + 1
                        if json_start != -1 and json_end != 0:
                            json_str = content[json_start:json_end]
                            candidates = json.loads(json_str)
                            # 添加来源标记
                            for c in candidates:
                                c['source'] = 'AI_Discovery'
                                c['ai'] = True
                            logger.info(f"AI 发现 {len(candidates)} 个候选源")
                            return candidates
        except Exception as e:
            logger.error(f"AI 发现源失败: {e}")
        return []
