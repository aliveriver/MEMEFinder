#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR处理模块 - 重构版

将原有的大文件拆分为多个模块：
- ocr_engine.py: OCR引擎封装
- text_filter.py: 文本过滤
- emotion_analyzer.py: 情绪分析

本文件作为统一接口，整合所有功能。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# 导入拆分后的模块
from .ocr_engine import OCREngine
from .text_filter import TextFilter
from .emotion_analyzer import EmotionAnalyzer

# 导入日志和资源监控
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.resource_monitor import get_resource_monitor
from utils.gpu_detector import should_use_gpu, detect_gpu

logger = get_logger()
resource_monitor = get_resource_monitor()


class OCRProcessor:
    """OCR处理器 - 统一接口"""

    def __init__(self, lang: str = 'ch', use_gpu: Optional[bool] = None, 
                 det_side: int = 1536, use_senta: bool = True, 
                 model_dir: Optional[Path] = None):
        """
        初始化OCR处理器

        Args:
            lang: 语言，默认'ch'（中文）
            use_gpu: 是否使用GPU，None表示自动检测
            det_side: 检测侧边长度，默认1536（可降低以减少内存）
            use_senta: 是否使用情绪分析模型，默认True
            model_dir: 模型存储目录，None表示使用默认路径（根目录的models文件夹）
        """
        logger.info("=" * 60)
        logger.info("初始化 OCR 处理器（重构版）...")
        
        self.lang = lang
        self.det_side = det_side
        
        # 处理计数器（用于定期清理内存）
        self._process_count = 0
        self._gc_interval = 10  # 每处理10张图片执行一次垃圾回收

        # 设置模型存储路径
        if model_dir is None:
            # 默认使用项目根目录的models文件夹
            project_root = Path(__file__).parent.parent.parent
            model_dir = project_root / 'models'
        
        # 确保模型目录存在
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"模型存储路径: {model_dir}")

        # 自动检测GPU（如果未指定）
        if use_gpu is None:
            has_gpu, gpu_info = detect_gpu()
            use_gpu = should_use_gpu()
            if has_gpu:
                logger.info(f"✓ 检测到GPU: {gpu_info}")
                logger.info(f"  将使用GPU加速模式")
            else:
                logger.info("✗ 未检测到GPU，将使用CPU模式")
                logger.info("  提示: 如需使用GPU，请确保已安装 onnxruntime-gpu")
        else:
            # 手动指定了GPU使用
            if use_gpu:
                has_gpu, gpu_info = detect_gpu()
                if has_gpu:
                    logger.info(f"✓ 手动启用GPU模式: {gpu_info}")
                else:
                    logger.warning("⚠ 手动启用了GPU，但系统可能不支持，将尝试使用GPU")
            else:
                logger.info("手动禁用GPU，使用CPU模式")
        
        # 初始化各个组件
        logger.info("正在初始化 OCR 引擎...")
        try:
            self.ocr_engine = OCREngine(use_gpu=use_gpu, model_dir=model_dir)
            logger.info("✓ OCR 引擎初始化成功")
        except Exception as e:
            error_msg = f"OCR 引擎初始化失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 初始化文本过滤器
        logger.info("初始化文本过滤器...")
        self.text_filter = TextFilter()
        logger.info("✓ 文本过滤器初始化成功")
        
        # 初始化情绪分析器
        logger.info("初始化情绪分析器...")
        self.emotion_analyzer = EmotionAnalyzer(use_senta=use_senta, model_dir=model_dir)
        logger.info("✓ 情绪分析器初始化成功")
        
        # 保存模型目录路径供后续使用
        self.model_dir = model_dir
        
        # 记录初始化后的资源状态
        resource_monitor.log_resource_status()
        logger.info("OCR 处理器初始化完成")
        logger.info("=" * 60)

    def process_image(self, image_path: Path, pad_ratio: float = 0.10) -> Dict[str, Any]:
        """
        处理单张图片（主入口）

        Args:
            image_path: 图片路径
            pad_ratio: 画布外扩比例，默认0.10

        Returns:
            {
                'ocr_text': str,           # 原始OCR文本
                'filtered_text': str,      # 过滤后的文本
                'emotion': str,            # 情绪分类
                'emotion_positive': float, # 正向分数
                'emotion_negative': float  # 负向分数
            }
        """
        try:
            # 定期执行垃圾回收以释放内存
            self._process_count += 1
            if self._process_count % self._gc_interval == 0:
                freed = resource_monitor.force_garbage_collection()
                logger.debug(f"已处理 {self._process_count} 张图片，执行垃圾回收")
            
            # 检查内存使用情况
            if self._process_count % 5 == 0:
                mem_usage = resource_monitor.get_memory_usage()
                logger.debug(f"当前内存使用: {mem_usage['rss_mb']:.2f} MB ({mem_usage['percent']:.1f}%)")
            
            logger.debug(f"开始处理图片: {image_path.name}")
            
            # 1. OCR识别（使用带外扩的识别）
            ocr_result = self.ocr_engine.recognize_with_padding(image_path, pad_ratio)
            
            items = ocr_result.get('items', [])
            items_count = len(items)
            logger.debug(f"OCR识别完成，识别到 {items_count} 个文本区域")

            # 2. 提取文本
            ocr_text = self._extract_text(items)
            logger.debug(f"OCR文本提取完成，提取到 {len(ocr_text)} 字符")
            if ocr_text:
                logger.debug(f"提取的文本预览: {ocr_text[:100]}")

            # 3. 过滤文本
            filtered_text = self.text_filter.filter(ocr_text)
            if filtered_text:
                logger.debug(f"文本过滤完成: {filtered_text[:50]}...")

            # 4. 情绪分析
            emotion, pos_score, neg_score = self.emotion_analyzer.analyze(filtered_text)
            logger.debug(f"情绪分析: {emotion} (正:{pos_score:.2f}, 负:{neg_score:.2f})")

            return {
                'ocr_text': ocr_text,
                'filtered_text': filtered_text,
                'emotion': emotion,
                'emotion_positive': pos_score,
                'emotion_negative': neg_score
            }
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {e}")
            return {
                'ocr_text': '',
                'filtered_text': '',
                'emotion': '未分类',
                'emotion_positive': 0.0,
                'emotion_negative': 0.0
            }

    def _extract_text(self, ocr_result: list) -> str:
        """从OCR结果中提取文本"""
        texts = [item['text'] for item in ocr_result if item.get('text')]
        return ' '.join(texts)
    
    # 向后兼容的方法（保留原有接口）
    def filter_text(self, text: str) -> str:
        """过滤文本（向后兼容）"""
        return self.text_filter.filter(text)
    
    def analyze_emotion(self, text: str) -> tuple:
        """分析情绪（向后兼容）"""
        return self.emotion_analyzer.analyze(text)
