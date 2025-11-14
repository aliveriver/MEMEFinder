#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR处理模块 - 基于 ocr_cli.py 的成功实现

本文件对原始实现进行了格式化和缩进修复，但保持逻辑不变。
"""

import re
import tempfile
import gc
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from PIL import Image
import cv2

# RapidOCR - 轻量级OCR引擎，易于打包
from rapidocr_onnxruntime import RapidOCR

# 导入日志和资源监控
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.resource_monitor import get_resource_monitor

logger = get_logger()
resource_monitor = get_resource_monitor()


class OCRProcessor:
    """OCR处理器 - 使用 RapidOCR（轻量级，易于打包）"""

    def __init__(self, lang: str = 'ch', use_gpu: bool = False, det_side: int = 1536, use_senta: bool = True):
        """
        初始化OCR处理器

        Args:
            lang: 语言，默认'ch'（中文）- RapidOCR会忽略此参数，因为它已内置多语言支持
            use_gpu: 是否使用GPU - RapidOCR ONNX版本已优化，CPU性能很好
            det_side: 检测侧边长度，默认1536（可降低以减少内存）
            use_senta: 是否使用情绪分析模型，默认True（优先使用 SnowNLP，快速且准确）
        """
        logger.info("=" * 60)
        logger.info("初始化 OCR 处理器（RapidOCR）...")
        
        self.lang = lang
        self.det_side = det_side
        
        # 处理计数器（用于定期清理内存）
        self._process_count = 0
        self._gc_interval = 10  # 每处理10张图片执行一次垃圾回收

        # 初始化 RapidOCR
        logger.info("正在初始化 RapidOCR...")
        try:
            # RapidOCR 初始化非常简单，无需复杂配置
            # use_cuda=True 可以启用GPU加速（如果支持）
            # use_angle_cls=True 启用文本方向分类
            # print_verbose=False 不打印详细日志
            self.ocr = RapidOCR(
                det_use_cuda=use_gpu,  # 检测模型是否使用CUDA
                cls_use_cuda=use_gpu,  # 方向分类是否使用CUDA  
                rec_use_cuda=use_gpu   # 识别模型是否使用CUDA
            )
            
            if self.ocr is None:
                raise Exception("RapidOCR 初始化返回 None")
            
            device_type = "GPU" if use_gpu else "CPU"
            logger.info(f"✓ RapidOCR 初始化成功（{device_type} 模式）")
            logger.info("RapidOCR 优势：轻量级、易打包、无复杂依赖")
            
        except Exception as e:
            error_msg = f"RapidOCR 初始化失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # 初始化 Senta 情绪分析（可选）
        self._senta = None
        self._use_senta = False
        if use_senta:
            self._init_senta()
        
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
            
            # 1. OCR识别（使用 ocr_cli.py 的实现）
            ocr_result = self._ocr_with_padding(image_path, pad_ratio)
            
            # 检查OCR结果 - 确保ocr_result是字典
            if not isinstance(ocr_result, dict):
                logger.error(f"OCR结果格式错误，期望dict，得到{type(ocr_result)}")
                ocr_result = {'items': []}
            
            items = ocr_result.get('items', [])
            items_count = len(items)
            logger.debug(f"OCR识别完成，识别到 {items_count} 个文本区域")

            # 2. 提取文本
            ocr_text = self._extract_text(items)
            logger.debug(f"OCR文本提取完成，提取到 {len(ocr_text)} 字符")
            if ocr_text:
                logger.debug(f"提取的文本预览: {ocr_text[:100]}")

            # 3. 过滤文本
            filtered_text = self.filter_text(ocr_text)
            if filtered_text:
                logger.debug(f"文本过滤完成: {filtered_text[:50]}...")

            # 4. 情绪分析
            emotion, pos_score, neg_score = self.analyze_emotion(filtered_text)
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

    # ==================== OCR识别核心功能（来自 ocr_cli.py）====================

    def _ocr_with_padding(self, img_path: Path, pad_ratio: float = 0.10) -> Dict[str, Any]:
        """
        带画布外扩的OCR识别（与 ocr_cli.py 一致）
        
        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        td_ctx = None
        try:
            # 创建外扩图片
            td_ctx, feed_path, (px, py), (orig_w, orig_h) = self._make_padded_tmp(
                img_path, pad_ratio
            )

            # OCR识别
            result = self._ocr_single(feed_path)
            
            # 确保result是字典
            if not isinstance(result, dict):
                logger.error(f"OCR结果格式错误，期望dict，得到{type(result)}")
                result = {"image": str(img_path), "items": []}

            # 坐标回退到原图
            items = self._shift_items_to_original(
                result.get("items", []), px, py, (orig_w, orig_h)
            )

            return {"image": str(img_path), "items": items}

        finally:
            if td_ctx is not None:
                td_ctx.cleanup()

    def _make_padded_tmp(self, img_path: Path, pad_ratio: float, pad_color=(0, 0, 0)) -> Tuple:
        """创建外扩的临时图片（与 ocr_cli.py 一致，优化内存使用）"""
        # 使用 Image.open 上下文管理器，自动关闭文件
        with Image.open(img_path) as img:
            # 转换为RGB（如果需要）
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            w, h = img.size

            if pad_ratio <= 0:
                return None, img_path, (0, 0), (w, h)

            px = max(1, int(round(w * pad_ratio)))
            py = max(1, int(round(h * pad_ratio)))
            canvas = Image.new("RGB", (w + 2 * px, h + 2 * py), pad_color)
            canvas.paste(img, (px, py))

            td = tempfile.TemporaryDirectory()
            outp = Path(td.name) / f"{img_path.stem}.padded.png"
            canvas.save(outp)
            
            # 显式释放canvas
            del canvas

        return td, outp, (px, py), (w, h)

    def _shift_items_to_original(self, items: List[Dict[str, Any]], dx: int, dy: int, orig_wh=None) -> List[Dict[str, Any]]:
        """将坐标回退到原图（与 ocr_cli.py 一致）"""
        W, H = orig_wh if orig_wh else (None, None)
        shifted = []

        for it in items:
            box = [[p[0] - dx, p[1] - dy] for p in it["box"]]
            if W is not None and H is not None:
                box = [[max(0, min(W - 1, x)), max(0, min(H - 1, y))] for x, y in box]
            shifted.append({**it, "box": box})

        return shifted

    def _ocr_single(self, img_path: Path) -> Dict[str, Any]:
        """
        单张图片OCR识别（使用 RapidOCR）

        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        try:
            # RapidOCR 返回格式: 
            # - 成功时: (result_list, elapse) 其中 result_list = [[box, text, score], ...]
            # - 失败时: (None, elapse) 或 ([], elapse)
            result = self.ocr(str(img_path))
            
            if result is None:
                logger.warning(f"OCR识别失败，未返回结果: {img_path.name}")
                return {"image": str(img_path), "items": []}
            
            # RapidOCR 返回 (result_list, elapse_time)
            if isinstance(result, tuple) and len(result) == 2:
                result_list, elapse = result
                # elapse 可能是数字或列表
                if isinstance(elapse, (list, tuple)):
                    logger.debug(f"OCR耗时: {elapse}")
                else:
                    logger.debug(f"OCR耗时: {elapse:.2f}ms")
            else:
                result_list = result
            
            # 解析 RapidOCR 结果
            items = []
            
            if result_list:
                for item in result_list:
                    # item 格式: [box, text, score]
                    # box: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    if len(item) >= 2:  # 至少有 box 和 text
                        box = item[0]
                        text = item[1]
                        score = item[2] if len(item) > 2 else 1.0
                        
                        items.append({
                            "box": box.tolist() if hasattr(box, 'tolist') else box,
                            "text": str(text),
                            "score": float(score)
                        })
                
                logger.debug(f"OCR识别完成，识别到 {len(items)} 个文本区域")
                if len(items) > 0:
                    logger.debug(f"第一个文本区域: {items[0].get('text', '')[:50]}")
            
            return {"image": str(img_path), "items": items}
            
        except Exception as e:
            logger.error(f"OCR识别异常: {e}")
            import traceback
            logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return {"image": str(img_path), "items": []}



    def _extract_text(self, ocr_result: List[Dict[str, Any]]) -> str:
        """从OCR结果中提取文本"""
        texts = [item['text'] for item in ocr_result if item.get('text')]
        return ' '.join(texts)

    # ==================== 文本过滤 ====================

    def filter_text(self, text: str) -> str:
        """
        过滤水印和网址

        规则：
        1. 过滤网址（http, https, www, .com, .cn等）
        2. 过滤常见水印词汇
        3. 过滤特殊符号
        """
        if not text:
            return ''

        # 1. 过滤网址
        url_patterns = [
            r'https?://[^\s]+',          # http:// 或 https://
            r'www\.[^\s]+',              # www.开头
            r'[a-zA-Z0-9-]+\.(com|cn|net|org|cc|tv|info|top|xyz|vip)[^\s]*',  # 域名
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
        text = re.sub(r'\s+', ' ', text)  # 多个空格替换为单个
        text = re.sub(r'[\_\-\|]{3,}', '', text)  # 连续的下划线、横线

        # 4. 去除首尾空格
        text = text.strip()

        return text

    # ==================== 情绪分析模型初始化（支持多种方案）====================

    def _init_senta(self):
        """
        初始化情绪分析模型
        
        支持的模型（按优先级尝试）：
        1. SnowNLP（轻量级，中文情感分析）
        2. TextBlob（英文情感分析，如果有英文需求）
        3. 关键词方法（默认回退方案）
        """
        # 方案1：尝试使用 SnowNLP（推荐，轻量且准确）
        try:
            from snownlp import SnowNLP
            logger.info("正在初始化 SnowNLP 情绪分析模型...")
            
            # 测试模型是否正常工作
            test = SnowNLP("这是一个测试")
            _ = test.sentiments
            
            self._senta = 'snownlp'
            self._use_senta = True
            logger.info("SnowNLP 初始化成功（轻量级中文情感分析）")
            return
        except ImportError:
            logger.info("SnowNLP 未安装，尝试其他方案...")
            logger.info("如需使用 SnowNLP，请运行: pip install snownlp")
        except Exception as e:
            logger.warning(f"SnowNLP 初始化失败: {e}")

        # 方案2：尝试使用 TextBlob（适合英文）
        try:
            from textblob import TextBlob
            logger.info("正在初始化 TextBlob 情绪分析模型...")
            
            # 测试模型
            test = TextBlob("This is a test")
            _ = test.sentiment.polarity
            
            self._senta = 'textblob'
            self._use_senta = True
            logger.info("TextBlob 初始化成功（适合英文情感分析）")
            return
        except ImportError:
            logger.info("TextBlob 未安装，尝试其他方案...")
            logger.info("如需使用 TextBlob，请运行: pip install textblob")
        except Exception as e:
            logger.warning(f"TextBlob 初始化失败: {e}")

        # 回退到关键词方法
        logger.info("将使用关键词方法进行情绪分析（快速且有效）")
        self._senta = None
        self._use_senta = False

    def _senta_analyze(self, text: str) -> Tuple[str, float, float]:
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

    # ==================== 情绪分析 ====================

    def analyze_emotion(self, text: str) -> Tuple[str, float, float]:
        """
        情绪分析：优先使用 PaddleNLP Senta（如果已启用），否则使用关键词匹配

        Args:
            text: 文本内容

        Returns:
            (emotion, pos_score, neg_score)
            emotion: '正向', '负向', '中性', '未分类'
        """
        # 1. 优先尝试使用 Senta（如果已初始化）
        if self._use_senta and self._senta:
            senta_result = self._senta_analyze(text)
            if senta_result is not None:
                return senta_result

        # 2. 回退到关键词匹配方法
        if not text or len(text.strip()) < 2:
            return ('未分类', 0.0, 0.0)

        # 基于简单关键词判断
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
