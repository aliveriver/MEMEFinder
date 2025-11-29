#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感分析模块
支持多种情感分析方案：SnowNLP、TextBlob、关键词匹配
"""

from typing import Tuple, Optional
from ...utils.logger import get_logger

logger = get_logger()


class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self, use_senta: bool = True):
        """
        初始化情感分析器
        
        Args:
            use_senta: 是否使用深度学习模型（SnowNLP）
        """
        self._use_senta = use_senta
        self._senta = None
    
    def analyze(self, text: str) -> Tuple[str, float, float]:
        """
        情感分析：优先使用 SnowNLP（懒加载），否则使用关键词匹配
        
        Args:
            text: 文本内容
        
        Returns:
            (emotion, pos_score, neg_score)
            emotion: '正向', '负向', '中性', '未分类'
        """
        # 1. 如果启用了情感分析且SnowNLP未加载，尝试懒加载
        if self._use_senta and self._senta is None:
            self._lazy_load_snownlp()
        
        # 2. 优先尝试使用 SnowNLP（如果已加载）
        if self._use_senta and self._senta:
            senta_result = self._analyze_with_model(text)
            if senta_result is not None:
                return senta_result
        
        # 3. 回退到关键词匹配方法
        return self._analyze_with_keywords(text)
    
    def _lazy_load_snownlp(self):
        """懒加载 SnowNLP"""
        try:
            logger.info("首次使用情感分析，正在加载SnowNLP...")
            from snownlp import SnowNLP
            # 测试是否正常
            test = SnowNLP("测试")
            _ = test.sentiments
            self._senta = 'snownlp'
            logger.info("✓ SnowNLP加载成功（懒加载，节省初始内存385MB）")
        except ImportError:
            logger.warning("SnowNLP未安装，将使用关键词匹配")
            self._senta = None
            self._use_senta = False
        except Exception as e:
            logger.warning(f"SnowNLP加载失败: {e}，将使用关键词匹配")
            self._senta = None
            self._use_senta = False
    
    def _analyze_with_model(self, text: str) -> Optional[Tuple[str, float, float]]:
        """
        使用深度学习模型进行情绪分析
        
        Args:
            text: 文本内容
        
        Returns:
            (emotion, pos_score, neg_score) 或 None（如果分析失败）
        """
        if not self._use_senta or not self._senta:
            return None
        
        try:
            if not text or len(text.strip()) == 0:
                return ('未分类', 0.0, 0.0)
            
            # 方案1：使用 SnowNLP
            if self._senta == 'snownlp':
                from snownlp import SnowNLP
                s = SnowNLP(text)
                score = s.sentiments
                
                pos_score = round(score, 4)
                neg_score = round(1.0 - score, 4)
                
                if score > 0.6:
                    emotion = '正向'
                elif score < 0.4:
                    emotion = '负向'
                else:
                    emotion = '中性'
                
                return (emotion, pos_score, neg_score)
            
            # 方案2：使用 TextBlob
            elif self._senta == 'textblob':
                from textblob import TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                normalized = (polarity + 1) / 2
                pos_score = round(normalized, 4)
                neg_score = round(1.0 - normalized, 4)
                
                if polarity > 0.2:
                    emotion = '正向'
                elif polarity < -0.2:
                    emotion = '负向'
                else:
                    emotion = '中性'
                
                return (emotion, pos_score, neg_score)
            
            return None
            
        except Exception as e:
            logger.warning(f"情绪分析模型失败: {e}，回退到关键词方法")
            return None
    
    def _analyze_with_keywords(self, text: str) -> Tuple[str, float, float]:
        """
        使用关键词匹配进行情绪分析
        
        Args:
            text: 文本内容
        
        Returns:
            (emotion, pos_score, neg_score)
        """
        if not text or len(text.strip()) < 2:
            return ('未分类', 0.0, 0.0)
        
        positive_keywords = ['开心', '快乐', '高兴', '喜欢', '爱', '好', '棒', '赞', '哈哈', '笑',
                             '牛', '强', '优秀', '完美', '美好', '幸福', '温暖', '可爱']
        negative_keywords = ['难过', '伤心', '生气', '讨厌', '恨', '差', '烂', '哭', '呜呜',
                             '痛', '累', '烦', '糟', '坏', '丑', '悲伤', '失望']
        
        text_lower = text.lower()
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if pos_count > neg_count and pos_count > 0:
            pos_score = min(0.9, 0.5 + pos_count * 0.1)
            neg_score = 1.0 - pos_score
            return ('正向', pos_score, neg_score)
        elif neg_count > pos_count and neg_count > 0:
            neg_score = min(0.9, 0.5 + neg_count * 0.1)
            pos_score = 1.0 - neg_score
            return ('负向', pos_score, neg_score)
        else:
            return ('中性', 0.5, 0.5)
