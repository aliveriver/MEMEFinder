#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本过滤模块 - 过滤水印、网址等无关内容
"""

import re


class TextFilter:
    """文本过滤器"""
    
    def __init__(self):
        """初始化文本过滤器"""
        # 网址模式
        self.url_patterns = [
            r'https?://[^\s]+',          # http:// 或 https://
            r'www\.[^\s]+',              # www.开头
            r'[a-zA-Z0-9-]+\.(com|cn|net|org|cc|tv|info|top|xyz|vip)[^\s]*',  # 域名
        ]
        
        # 水印关键词
        self.watermark_keywords = [
            '微信', 'wechat', 'WeChat',
            '抖音', 'douyin', 'tiktok', 'TikTok',
            '快手', 'kuaishou',
            '小红书', 'xiaohongshu',
            '水印', '原创', '版权',
            '@', '#',
        ]
    
    def filter(self, text: str) -> str:
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
        for pattern in self.url_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 2. 过滤常见水印关键词
        for keyword in self.watermark_keywords:
            text = text.replace(keyword, '')
        
        # 3. 过滤多余空格和特殊字符
        text = re.sub(r'\s+', ' ', text)  # 多个空格替换为单个
        text = re.sub(r'[\_\-\|]{3,}', '', text)  # 连续的下划线、横线
        
        # 4. 去除首尾空格
        text = text.strip()
        
        return text
