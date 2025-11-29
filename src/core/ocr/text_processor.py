#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本处理模块
负责文本提取和过滤
"""

import re
from typing import List, Dict, Any
from ...utils.logger import get_logger

logger = get_logger()


class TextProcessor:
    """文本处理器"""
    
    @staticmethod
    def extract_text(ocr_result: List[Dict[str, Any]]) -> str:
        """
        从OCR结果中提取文本
        
        Args:
            ocr_result: OCR识别结果列表
        
        Returns:
            提取的文本
        """
        texts = [item['text'] for item in ocr_result if item.get('text')]
        return ' '.join(texts)
    
    @staticmethod
    def filter_text(text: str) -> str:
        """
        过滤水印和网址
        
        规则：
        1. 过滤网址（http, https, www, .com, .cn等）
        2. 过滤常见水印词汇
        3. 过滤特殊符号
        
        Args:
            text: 原始文本
        
        Returns:
            过滤后的文本
        """
        if not text:
            return ''
        
        # 1. 过滤网址
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9-]+\.(com|cn|net|org|cc|tv|info|top|xyz|vip)[^\s]*',
        ]
        for pattern in url_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 2. 过滤常见水印关键词
        watermark_keywords = [
            '微信', 'wechat', 'WeChat',
            '抖音', 'douyin', 'tiktok', 'TikTok',
            '快手', 'kuaishou',
            '小红书', 'xiaohongshu',
            '水印', '原创', '版权',
            '@', '#',
        ]
        for keyword in watermark_keywords:
            text = text.replace(keyword, '')
        
        # 3. 过滤多余空格和特殊字符
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\_\-\|]{3,}', '', text)
        
        # 4. 去除首尾空格
        text = text.strip()
        
        return text
