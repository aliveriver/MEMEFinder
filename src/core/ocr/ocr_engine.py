#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR 引擎模块
负责与 RapidOCR 的交互和图片识别
"""

import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image

from rapidocr_onnxruntime import RapidOCR
from ...utils.logger import get_logger

logger = get_logger()


class OCREngine:
    """OCR 引擎封装"""
    
    def __init__(self, use_gpu: bool, model_dir: Path):
        """
        初始化 OCR 引擎
        
        Args:
            use_gpu: 是否使用GPU
            model_dir: 模型目录
        """
        self.use_gpu = use_gpu
        self.model_dir = model_dir
        self.ocr = None
        
    def initialize(self) -> bool:
        """
        初始化 RapidOCR
        
        Returns:
            是否初始化成功
        """
        try:
            # 检查模型文件
            det_model = self.model_dir / 'ch_PP-OCRv4_det_infer.onnx'
            rec_model = self.model_dir / 'ch_PP-OCRv4_rec_infer.onnx'
            cls_model_v2 = self.model_dir / 'ch_ppocr_mobile_v2.0_cls_infer.onnx'
            cls_model = cls_model_v2 if cls_model_v2.exists() else self.model_dir / 'ch_ppocr_mobile_v2_cls_infer.onnx'
            
            missing_models = []
            if not det_model.exists():
                missing_models.append(f"检测模型: {det_model.name}")
            if not rec_model.exists():
                missing_models.append(f"识别模型: {rec_model.name}")
            if not cls_model.exists():
                missing_models.append(f"方向分类: {cls_model.name}")
            
            if missing_models:
                logger.error("=" * 60)
                logger.error("缺少以下模型文件:")
                for model in missing_models:
                    logger.error(f"  - {model}")
                logger.error("")
                logger.error("请通过界面的\"下载模型\"功能下载OCR模型")
                logger.error("=" * 60)
                return False
            
            # 构建初始化参数
            rapidocr_kwargs: Dict[str, Any] = {
                'det_use_cuda': self.use_gpu,
                'cls_use_cuda': self.use_gpu,
                'rec_use_cuda': self.use_gpu,
                'det_model_path': str(det_model),
                'rec_model_path': str(rec_model),
                'cls_model_path': str(cls_model),
            }
            
            # 初始化 RapidOCR
            self.ocr = RapidOCR(**rapidocr_kwargs)
            
            if self.ocr is None:
                raise Exception("RapidOCR 初始化返回 None")
            
            logger.info("✓ OCR模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ OCR模型加载失败: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def recognize(self, img_input) -> Dict[str, Any]:
        """
        单张图片OCR识别
        
        Args:
            img_input: PIL Image 对象或图片路径
        
        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        try:
            if self.ocr is None:
                logger.error("OCR引擎未初始化")
                return {"image": "", "items": []}
            
            result = self.ocr(img_input)
            
            if result is None:
                logger.warning(f"OCR识别失败，未返回结果")
                return {"image": "", "items": []}
            
            # RapidOCR 返回 (result_list, elapse_time)
            if isinstance(result, tuple) and len(result) == 2:
                result_list, elapse = result
                if elapse is not None:
                    if isinstance(elapse, (list, tuple)):
                        logger.debug(f"OCR耗时: {elapse}")
                    else:
                        logger.debug(f"OCR耗时: {elapse:.2f}ms")
            else:
                result_list = result
            
            # 解析结果
            items = []
            
            if result_list:
                for item in result_list:
                    if len(item) >= 2:
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
            
            return {"image": "", "items": items}
            
        except Exception as e:
            logger.error(f"OCR识别异常: {e}")
            logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return {"image": "", "items": []}
    
    def process_with_padding(self, image_path: Path, pad_ratio: float = 0.10) -> Dict[str, Any]:
        """
        带画布外扩的OCR识别
        
        Args:
            image_path: 图片路径
            pad_ratio: 外扩比例
        
        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        feed_img = None
        try:
            # 创建外扩图片
            feed_img, (px, py), (orig_w, orig_h) = self._make_padded_image(
                image_path, pad_ratio
            )
            
            # OCR识别
            result = self.recognize(feed_img)
            
            if not isinstance(result, dict):
                logger.error(f"OCR结果格式错误，期望dict，得到{type(result)}")
                result = {"image": str(image_path), "items": []}
            
            # 坐标回退到原图
            items = self._shift_coordinates(
                result.get("items", []), px, py, (orig_w, orig_h)
            )
            
            return {"image": str(image_path), "items": items}
            
        except Exception as e:
            logger.error(f"OCR识别异常: {e}")
            return {"image": str(image_path), "items": []}
        finally:
            if feed_img is not None:
                try:
                    feed_img.close()
                    del feed_img
                except Exception:
                    pass
            
            import gc
            gc.collect()
    
    def _make_padded_image(self, img_path: Path, pad_ratio: float, pad_color=(0, 0, 0)) -> Tuple:
        """创建外扩的临时图片"""
        img = None
        canvas = None
        try:
            MAX_SIZE = 2048
            
            img = Image.open(img_path)
            
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            w, h = img.size
            
            if max(w, h) > MAX_SIZE:
                ratio = MAX_SIZE / max(w, h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                w, h = new_w, new_h
                logger.debug(f"图片尺寸过大，已缩小至: {w}x{h}")
            
            if pad_ratio <= 0:
                return img, (0, 0), (w, h)
            
            px = max(1, int(round(w * pad_ratio)))
            py = max(1, int(round(h * pad_ratio)))
            canvas = Image.new("RGB", (w + 2 * px, h + 2 * py), pad_color)
            canvas.paste(img, (px, py))
            
            img.close()
            del img
            
            return canvas, (px, py), (w, h)
            
        except Exception as e:
            if img:
                try:
                    img.close()
                except:
                    pass
            if canvas:
                try:
                    canvas.close()
                except:
                    pass
            raise
    
    def _shift_coordinates(self, items: List[Dict[str, Any]], dx: int, dy: int, orig_wh=None) -> List[Dict[str, Any]]:
        """将坐标回退到原图"""
        W, H = orig_wh if orig_wh else (None, None)
        shifted = []
        
        for it in items:
            box = [[p[0] - dx, p[1] - dy] for p in it["box"]]
            if W is not None and H is not None:
                box = [[max(0, min(W - 1, x)), max(0, min(H - 1, y))] for x, y in box]
            shifted.append({**it, "box": box})
        
        return shifted
