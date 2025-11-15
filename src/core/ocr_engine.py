#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR引擎封装 - RapidOCR
"""

import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image

from rapidocr_onnxruntime import RapidOCR

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class OCREngine:
    """OCR引擎 - 基于 RapidOCR"""
    
    def __init__(self, use_gpu: bool = False, model_dir: Optional[Path] = None):
        """
        初始化OCR引擎
        
        Args:
            use_gpu: 是否使用GPU加速
            model_dir: 模型目录
        """
        self.use_gpu = use_gpu
        self.model_dir = model_dir
        self.ocr = None
        
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """初始化 RapidOCR"""
        try:
            # 检查模型文件
            det_model, rec_model, cls_model = self._get_model_paths()
            
            # 检查模型文件是否存在
            missing_models = []
            if not det_model.exists():
                missing_models.append(f"检测模型: {det_model.name}")
            if not rec_model.exists():
                missing_models.append(f"识别模型: {rec_model.name}")
            if not cls_model.exists():
                missing_models.append(f"方向分类: {cls_model.name}")
            
            if missing_models:
                logger.warning("=" * 60)
                logger.warning("缺少以下模型文件，请手动下载到 models 目录:")
                for model in missing_models:
                    logger.warning(f"  - {model}")
                logger.warning("")
                logger.warning("下载方法1 - 从RapidOCR包复制:")
                logger.warning("  运行: python copy_models.py")
                logger.warning("")
                logger.warning("下载方法2 - 从GitHub下载:")
                logger.warning("  https://github.com/RapidAI/RapidOCR/tree/main/python/rapidocr_onnxruntime/models")
                logger.warning("=" * 60)
                raise FileNotFoundError(f"模型文件缺失: {', '.join([m.split(':')[1].strip() for m in missing_models])}")
            
            # 构建RapidOCR初始化参数
            rapidocr_kwargs = {
                'det_use_cuda': self.use_gpu,
                'cls_use_cuda': self.use_gpu,
                'rec_use_cuda': self.use_gpu,
                'det_model_path': str(det_model),
                'rec_model_path': str(rec_model),
                'cls_model_path': str(cls_model),
            }
            
            logger.info(f"模型路径配置:")
            logger.info(f"  检测模型: {det_model}")
            logger.info(f"  识别模型: {rec_model}")
            logger.info(f"  方向分类: {cls_model}")
            
            self.ocr = RapidOCR(**rapidocr_kwargs)
            
            if self.ocr is None:
                raise Exception("RapidOCR 初始化返回 None")
            
            # 验证实际使用的设备
            actual_device = self._get_actual_device()
            device_type = "GPU" if self.use_gpu else "CPU"
            
            logger.info(f"✓ RapidOCR 初始化成功")
            logger.info(f"  配置模式: {device_type}")
            logger.info(f"  实际设备: {actual_device}")
            
        except Exception as e:
            logger.error(f"RapidOCR 初始化失败: {e}")
            raise
    
    def _get_model_paths(self) -> Tuple[Path, Path, Path]:
        """获取模型文件路径"""
        if not self.model_dir:
            raise ValueError("未指定模型目录")
        
        # 检测模型
        det_model = self.model_dir / 'ch_PP-OCRv4_det_infer.onnx'
        
        # 识别模型
        rec_model = self.model_dir / 'ch_PP-OCRv4_rec_infer.onnx'
        
        # 方向分类模型（可能有两种文件名）
        cls_model_v2 = self.model_dir / 'ch_ppocr_mobile_v2.0_cls_infer.onnx'
        cls_model_old = self.model_dir / 'ch_ppocr_mobile_v2_cls_infer.onnx'
        
        if cls_model_v2.exists():
            cls_model = cls_model_v2
        elif cls_model_old.exists():
            cls_model = cls_model_old
        else:
            cls_model = cls_model_v2  # 默认使用v2.0版本
        
        return det_model, rec_model, cls_model
    
    def _get_actual_device(self) -> str:
        """获取实际使用的设备"""
        try:
            if hasattr(self.ocr, 'det_model') and hasattr(self.ocr.det_model, 'session'):
                providers = self.ocr.det_model.session.get_providers()
                if 'CUDAExecutionProvider' in providers:
                    return "GPU (CUDA)"
                elif 'DmlExecutionProvider' in providers:
                    return "GPU (DirectML)"
                else:
                    return "CPU"
        except:
            pass
        
        return "GPU" if self.use_gpu else "CPU"
    
    def recognize(self, img_path: Path) -> Dict[str, Any]:
        """
        识别图片中的文本
        
        Args:
            img_path: 图片路径
            
        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        try:
            # RapidOCR 返回格式: (result_list, elapse)
            result = self.ocr(str(img_path))
            
            if result is None:
                logger.warning(f"OCR识别失败，未返回结果: {img_path.name}")
                return {"image": str(img_path), "items": []}
            
            # 解析结果
            if isinstance(result, tuple) and len(result) == 2:
                result_list, elapse = result
                if isinstance(elapse, (list, tuple)):
                    logger.debug(f"OCR耗时: {elapse}")
                else:
                    logger.debug(f"OCR耗时: {elapse:.2f}ms")
            else:
                result_list = result
            
            # 转换为标准格式
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
            
            return {"image": str(img_path), "items": items}
            
        except Exception as e:
            logger.error(f"OCR识别异常: {e}")
            import traceback
            logger.debug(f"错误详情:\n{traceback.format_exc()}")
            return {"image": str(img_path), "items": []}
    
    def recognize_with_padding(self, img_path: Path, pad_ratio: float = 0.10) -> Dict[str, Any]:
        """
        带画布外扩的OCR识别（提高边缘文本识别率）
        
        Args:
            img_path: 图片路径
            pad_ratio: 外扩比例，默认0.10
            
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
            result = self.recognize(feed_path)
            
            # 坐标回退到原图
            items = self._shift_items_to_original(
                result.get("items", []), px, py, (orig_w, orig_h)
            )
            
            return {"image": str(img_path), "items": items}
            
        finally:
            if td_ctx is not None:
                td_ctx.cleanup()
    
    def _make_padded_tmp(self, img_path: Path, pad_ratio: float, 
                         pad_color=(0, 0, 0)) -> Tuple:
        """创建外扩的临时图片"""
        with Image.open(img_path) as img:
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
            
            del canvas
        
        return td, outp, (px, py), (w, h)
    
    def _shift_items_to_original(self, items: List[Dict[str, Any]], 
                                  dx: int, dy: int, orig_wh=None) -> List[Dict[str, Any]]:
        """将坐标回退到原图"""
        W, H = orig_wh if orig_wh else (None, None)
        shifted = []
        
        for it in items:
            box = [[p[0] - dx, p[1] - dy] for p in it["box"]]
            if W is not None and H is not None:
                box = [[max(0, min(W - 1, x)), max(0, min(H - 1, y))] for x, y in box]
            shifted.append({**it, "box": box})
        
        return shifted
