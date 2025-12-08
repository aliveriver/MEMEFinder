#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR处理器 - 主入口
整合 OCR引擎、文本处理、情感分析功能
"""

import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from .ocr_engine import OCREngine
from .text_processor import TextProcessor
from .sentiment_analyzer import SentimentAnalyzer
from ...utils.logger import get_logger
from ...utils.resource_monitor import get_resource_monitor
from ...utils.gpu_detector import should_use_gpu, detect_gpu, has_onnxruntime_gpu

logger = get_logger()
resource_monitor = get_resource_monitor()


class OCRProcessor:
    """OCR处理器 - 使用 RapidOCR（轻量级，易于打包）"""
    
    def __init__(self, lang: str = 'ch', use_gpu: Optional[bool] = None, 
                 det_side: int = 1536, use_senta: bool = True, 
                 model_dir: Optional[Path] = None, lazy_load: bool = False):
        """
        初始化OCR处理器
        
        Args:
            lang: 语言，默认'ch'（中文）
            use_gpu: 是否使用GPU，None表示自动检测
            det_side: 检测侧边长度，默认1536
            use_senta: 是否使用情绪分析模型，默认True
            model_dir: 模型存储目录，None表示使用默认路径
            lazy_load: 是否延迟加载，True时不立即加载模型
        """
        logger.info("=" * 60)
        logger.info("初始化 OCR 处理器（RapidOCR）...")
        
        self.lang = lang
        self.det_side = det_side
        self._lazy_load = lazy_load
        self._ocr_loaded = False
        
        # 处理计数器
        self._process_count = 0
        self._gc_interval = 10
        
        # 线程锁
        self._load_lock = threading.Lock()
        
        # 设置模型目录
        if model_dir is None:
            from ...utils.model_manager import get_model_manager
            model_manager = get_model_manager()
            model_dir = model_manager.get_model_dir()
        
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir = model_dir
        
        logger.info(f"模型存储路径: {model_dir}")
        
        # 初始化各个组件
        self.text_processor = TextProcessor()
        self.sentiment_analyzer = SentimentAnalyzer(use_senta=use_senta)
        
        # 保存参数供延迟加载使用
        self.use_gpu = use_gpu
        self._use_senta_flag = use_senta
        self._use_senta = use_senta
        
        # 如果是延迟加载模式，跳过OCR初始化
        if lazy_load:
            logger.info("延迟加载模式：OCR模型将在首次使用时加载")
            self.ocr_engine = None
            logger.info("OCR 处理器初始化完成（延迟加载模式）")
            logger.info("=" * 60)
            return
        
        # 检查GPU
        use_gpu = self._detect_gpu(use_gpu)
        self.use_gpu = use_gpu
        
        # 初始化 OCR 引擎
        self.ocr_engine = OCREngine(use_gpu, model_dir)
        if not self.ocr_engine.initialize():
            raise Exception("OCR引擎初始化失败")
        
        self._ocr_loaded = True
        
        # 记录资源状态
        resource_monitor.log_resource_status()
        logger.info("OCR 处理器初始化完成")
        logger.info("=" * 60)
    
    def _detect_gpu(self, use_gpu: Optional[bool]) -> bool:
        """
        检测和配置GPU
        
        Args:
            use_gpu: 用户指定的GPU设置
        
        Returns:
            最终的GPU使用设置
        """
        # 检查环境变量
        force_cpu = os.environ.get('MEMEFINDER_FORCE_CPU', '').lower() in ('1', 'true', 'yes')
        if force_cpu:
            logger.info("检测到环境变量 MEMEFINDER_FORCE_CPU，强制使用 CPU 模式")
            return False
        
        # 自动检测
        if use_gpu is None:
            has_gpu, gpu_info = detect_gpu()
            use_gpu = should_use_gpu()
            if has_gpu and use_gpu:
                logger.info(f"✓ 检测到GPU: {gpu_info}")
                logger.info(f"  将使用GPU加速模式")
            else:
                logger.info("✗ 未检测到可用GPU或已禁用，将使用CPU模式")
        else:
            # 手动指定
            if use_gpu:
                if not has_onnxruntime_gpu():
                    logger.warning("⚠ 请求使用GPU，但未检测到 onnxruntime-gpu 包")
                    logger.warning("  自动回退到 CPU 模式")
                    use_gpu = False
                else:
                    has_gpu, gpu_info = detect_gpu()
                    if has_gpu:
                        logger.info(f"✓ 手动启用GPU模式: {gpu_info}")
                    else:
                        logger.warning("⚠ 手动启用了GPU，但未检测到硬件，尝试使用")
            else:
                logger.info("手动禁用GPU，使用CPU模式")
        
        return use_gpu
    
    def load_ocr_model(self) -> bool:
        """
        加载OCR模型（用于延迟加载）
        使用线程锁确保多线程环境下只加载一次
        
        Returns:
            是否加载成功
        """
        if self._ocr_loaded and self.ocr_engine is not None:
            return True
        
        with self._load_lock:
            if self._ocr_loaded and self.ocr_engine is not None:
                logger.info("OCR模型已由其他线程加载")
                return True
            
            logger.info("开始加载OCR模型...")
            
            # 初始化OCR引擎
            self.ocr_engine = OCREngine(self.use_gpu, self.model_dir)
            if not self.ocr_engine.initialize():
                return False
            
            self._ocr_loaded = True
            
            # 初始化情感分析
            if self._use_senta_flag:
                self._use_senta = True
                logger.info("情感分析已启用（使用SnowNLP）")
            
            return True
    
    def process_image(self, image_path: Path, pad_ratio: float = 0.10) -> Dict[str, Any]:
        """
        处理单张图片（主入口）
        
        Args:
            image_path: 图片路径
            pad_ratio: 画布外扩比例，默认0.10
        
        Returns:
            {
                'ocr_text': str,
                'filtered_text': str,
                'emotion': str,
                'emotion_positive': float,
                'emotion_negative': float
            }
        """
        try:
            # 延迟加载检查
            if self._lazy_load and not self._ocr_loaded:
                if not self.load_ocr_model():
                    logger.error("OCR模型加载失败，无法处理图片")
                    return self._empty_result()
            
            # 定期GC
            self._process_count += 1
            if self._process_count % self._gc_interval == 0:
                resource_monitor.force_garbage_collection()
                logger.debug(f"已处理 {self._process_count} 张图片，执行垃圾回收")
            
            # 记录内存
            if self._process_count % 5 == 0:
                mem_usage = resource_monitor.get_memory_usage()
                logger.debug(f"当前内存使用: {mem_usage['rss_mb']:.2f} MB ({mem_usage['percent']:.1f}%)")
            
            logger.debug(f"开始处理图片: {image_path.name}")
            
            # 1. OCR识别
            ocr_result = self.ocr_engine.process_with_padding(image_path, pad_ratio)
            
            if not isinstance(ocr_result, dict):
                logger.error(f"OCR结果格式错误，期望dict，得到{type(ocr_result)}")
                ocr_result = {'items': []}
            
            items = ocr_result.get('items', [])
            logger.debug(f"OCR识别完成，识别到 {len(items)} 个文本区域")
            
            # 2. 提取文本
            ocr_text = self.text_processor.extract_text(items)
            logger.debug(f"OCR文本提取完成，提取到 {len(ocr_text)} 字符")
            if ocr_text:
                logger.debug(f"提取的文本预览: {ocr_text[:100]}")
            
            # 3. 过滤文本
            filtered_text = self.text_processor.filter_text(ocr_text)
            if filtered_text:
                logger.debug(f"文本过滤完成: {filtered_text[:50]}...")
            
            # 4. 情绪分析
            emotion, pos_score, neg_score = self.sentiment_analyzer.analyze(filtered_text)
            logger.debug(f"情绪分析: {emotion} (正:{pos_score:.2f}, 负:{neg_score:.2f})")
            
            # 5. 计算图片哈希值和颜色特征（PHash + HSV + K-Means颜色）
            try:
                from ..image_hash import calculate_image_hashes
                phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v, histogram_bytes = calculate_image_hashes(image_path)
                logger.debug(f"图片特征计算完成: PHash={phash[:8]}..., HSV=({hsv_h},{hsv_s},{hsv_v}), 色相索引={hue_idx}, 明度={lightness}")
            except Exception as e:
                logger.warning(f"计算图片特征失败: {e}")
                phash = '0' * 16
                hsv_h, hsv_s, hsv_v = -1, 0, 0
                hue_idx, lightness = -1, 0
                histogram_bytes = None
            
            return {
                'ocr_text': ocr_text,
                'filtered_text': filtered_text,
                'emotion': emotion,
                'emotion_positive': pos_score,
                'emotion_negative': neg_score,
                'phash': phash,
                'hsv_h': hsv_h,
                'hsv_s': hsv_s,
                'hsv_v': hsv_v,
                'hue_idx': hue_idx,
                'lightness': lightness,
                'histogram': histogram_bytes
            }
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'ocr_text': '',
            'filtered_text': '',
            'emotion': '未分类',
            'emotion_positive': 0.0,
            'emotion_negative': 0.0,
            'phash': '0' * 16,
            'hsv_h': -1,
            'hsv_s': 0,
            'hsv_v': 0,
            'hue_idx': -1,
            'lightness': 0,
            'histogram': None
        }
    
    # 保留向后兼容的属性访问
    @property
    def ocr(self):
        """向后兼容：返回OCR引擎的ocr对象"""
        if self.ocr_engine:
            return self.ocr_engine.ocr
        return None
    
    @ocr.setter
    def ocr(self, value):
        """向后兼容：设置OCR引擎的ocr对象"""
        if self.ocr_engine:
            self.ocr_engine.ocr = value
        # 如果ocr_engine为None，忽略设置操作
    
    @ocr.deleter
    def ocr(self):
        """向后兼容：删除OCR引擎的ocr对象"""
        if self.ocr_engine and hasattr(self.ocr_engine, 'ocr'):
            self.ocr_engine.ocr = None
    
    def filter_text(self, text: str) -> str:
        """向后兼容：文本过滤"""
        return self.text_processor.filter_text(text)
    
    def analyze_emotion(self, text: str):
        """向后兼容：情感分析"""
        return self.sentiment_analyzer.analyze(text)
