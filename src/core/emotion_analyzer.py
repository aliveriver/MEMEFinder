#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情绪分析模块 - 支持多种分析方法
"""

from typing import Tuple, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class EmotionAnalyzer:
    """情绪分析器"""
    
    def __init__(self, use_senta: bool = True, model_dir: Optional[Path] = None):
        """
        初始化情绪分析器
        
        Args:
            use_senta: 是否使用深度学习模型（SnowNLP等），默认True
            model_dir: 模型目录（用于存储SnowNLP模型）
        """
        self._senta = None
        self._use_senta = False
        self._model_dir = model_dir
        
        if use_senta:
            self._init_senta()
        
        # 关键词方法的词库
        self.positive_keywords = [
            '开心', '快乐', '高兴', '喜欢', '爱', '好', '棒', '赞', '哈哈', '笑',
            '牛', '强', '优秀', '完美', '美好', '幸福', '温暖', '可爱'
        ]
        
        self.negative_keywords = [
            '难过', '伤心', '生气', '讨厌', '恨', '差', '烂', '哭', '呜呜',
            '痛', '累', '烦', '糟', '坏', '丑', '悲伤', '失望'
        ]
    
    def _init_senta(self):
        """
        初始化情绪分析模型
        
        支持的模型（按优先级尝试）：
        1. SnowNLP（轻量级，中文情感分析）
        2. TextBlob（英文情感分析，如果有英文需求）
        3. 关键词方法（默认回退方案）
        """
        # 方案1：尝试使用 SnowNLP（推荐，轻量且准确）
        if self._try_init_snownlp():
            return
        
        # 方案2：尝试使用 TextBlob（适合英文）
        if self._try_init_textblob():
            return
        
        # 回退到关键词方法
        logger.info("将使用关键词方法进行情绪分析（快速且有效）")
        self._senta = None
        self._use_senta = False
    
    def _try_init_snownlp(self) -> bool:
        """尝试初始化 SnowNLP"""
        try:
            from snownlp import SnowNLP
            import os
            
            logger.info("正在初始化 SnowNLP 情绪分析模型...")
            
            # 如果指定了模型目录，尝试设置SnowNLP的数据目录
            if self._model_dir:
                snownlp_data_dir = self._model_dir / 'snownlp'
                if snownlp_data_dir.exists():
                    # SnowNLP会从这个目录加载模型
                    os.environ['SNOWNLP_DATA_PATH'] = str(snownlp_data_dir)
                    logger.info(f"设置 SnowNLP 数据路径: {snownlp_data_dir}")
            
            # 测试模型是否正常工作
            test = SnowNLP("这是一个测试")
            _ = test.sentiments
            
            self._senta = 'snownlp'
            self._use_senta = True
            logger.info("✓ SnowNLP 初始化成功（轻量级中文情感分析）")
            return True
            
        except ImportError:
            logger.info("SnowNLP 未安装，尝试其他方案...")
            logger.info("如需使用 SnowNLP，请运行: pip install snownlp")
            return False
        except Exception as e:
            logger.warning(f"SnowNLP 初始化失败: {e}")
            return False
    
    def _try_init_textblob(self) -> bool:
        """尝试初始化 TextBlob"""
        try:
            from textblob import TextBlob
            
            logger.info("正在初始化 TextBlob 情绪分析模型...")
            
            # 测试模型
            test = TextBlob("This is a test")
            _ = test.sentiment.polarity
            
            self._senta = 'textblob'
            self._use_senta = True
            logger.info("✓ TextBlob 初始化成功（适合英文情感分析）")
            return True
            
        except ImportError:
            logger.info("TextBlob 未安装，尝试其他方案...")
            logger.info("如需使用 TextBlob，请运行: pip install textblob")
            return False
        except Exception as e:
            logger.warning(f"TextBlob 初始化失败: {e}")
            return False
    
    def analyze(self, text: str) -> Tuple[str, float, float]:
        """
        分析文本情绪
        
        Args:
            text: 文本内容
            
        Returns:
            (emotion, pos_score, neg_score)
            emotion: '正向', '负向', '中性', '未分类'
            pos_score: 正向分数 (0.0-1.0)
            neg_score: 负向分数 (0.0-1.0)
        """
        # 1. 优先尝试使用深度学习模型（如果已初始化）
        if self._use_senta and self._senta:
            result = self._analyze_with_model(text)
            if result is not None:
                return result
        
        # 2. 回退到关键词匹配方法
        return self._analyze_with_keywords(text)
    
    def _analyze_with_model(self, text: str) -> Optional[Tuple[str, float, float]]:
        """
        使用深度学习模型进行情绪分析
        
        Args:
            text: 文本内容
            
        Returns:
            (emotion, pos_score, neg_score) 或 None（如果分析失败）
        """
        try:
            if not text or len(text.strip()) == 0:
                return ('未分类', 0.0, 0.0)
            
            # 方案1：使用 SnowNLP
            if self._senta == 'snownlp':
                from snownlp import SnowNLP
                s = SnowNLP(text)
                score = s.sentiments  # 返回 0-1 之间的分数，越接近1越积极
                
                # 转换为正向/负向分数
                pos_score = round(score, 4)
                neg_score = round(1.0 - score, 4)
                
                # 判断情绪类别
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
                polarity = blob.sentiment.polarity  # 返回 -1 到 1 之间的分数
                
                # 转换为 0-1 区间
                normalized = (polarity + 1) / 2  # 映射到 0-1
                pos_score = round(normalized, 4)
                neg_score = round(1.0 - normalized, 4)
                
                # 判断情绪类别
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
        使用关键词匹配方法进行情绪分析
        
        Args:
            text: 文本内容
            
        Returns:
            (emotion, pos_score, neg_score)
        """
        if not text or len(text.strip()) < 2:
            return ('未分类', 0.0, 0.0)
        
        # 基于简单关键词判断
        text_lower = text.lower()
        pos_count = sum(1 for kw in self.positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in self.negative_keywords if kw in text_lower)
        
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
