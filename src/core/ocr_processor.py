#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR处理模块 - 基于 ocr_cli.py 的成功实现

本文件对原始实现进行了格式化和缩进修复，但保持逻辑不变。
"""

import re
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from PIL import Image
import paddle
# PaddleOCR
from paddleocr import PaddleOCR


class OCRProcessor:
    """OCR处理器 - 与 ocr_cli.py 完全兼容的实现"""

    def __init__(self, lang: str = 'ch', use_gpu: bool = False, det_side: int = 1536, use_senta: bool = True):
        """
        初始化OCR处理器

        Args:
            lang: 语言，默认'ch'（中文）
            use_gpu: 是否使用GPU
            det_side: 检测侧边长度，默认1536
            use_senta: 是否使用 PaddleNLP Senta 进行情绪分析，默认True（启用深度学习模型，如不可用则回退到关键词方法）
        """
        self.lang = lang
        self.det_side = det_side

        # 设置设备
        if use_gpu:
            try:
                if self._cuda_compiled():
                    paddle.set_device('gpu')
                    print("[INFO] 使用GPU进行OCR识别")
                else:
                    paddle.set_device('cpu')
                    print("[WARN] GPU不可用，使用CPU")
            except Exception as e:
                paddle.set_device('cpu')
                print(f"[WARN] GPU设置失败({e})，使用CPU")
        else:
            paddle.set_device('cpu')
            print("[INFO] 使用CPU进行OCR识别")

        # 初始化OCR（与 ocr_cli.py 完全一致的配置）
        print(f"[INFO] 正在初始化 PaddleOCR (lang={lang}, det_side={det_side})...")
        self.ocr = PaddleOCR(
            lang=lang,
            use_textline_orientation=True,
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            text_det_limit_side_len=det_side,
            text_det_limit_type="max",
            text_det_box_thresh=0.30,
            text_det_unclip_ratio=2.30,
        )
        print("[INFO] PaddleOCR 初始化完成")

        # 初始化 Senta 情绪分析（可选）
        self._senta = None
        self._use_senta = False
        if use_senta:
            self._init_senta()

    @staticmethod
    def _cuda_compiled() -> bool:
        """检查CUDA是否可用"""
        try:
            # 在新版 Paddle 中优先使用 paddle.is_compiled_with_cuda
            if hasattr(paddle, 'is_compiled_with_cuda'):
                return bool(paddle.is_compiled_with_cuda())
            # 兼容性：如果没有该函数，则认为不可用
            return False
        except Exception:
            return False

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
            # 1. OCR识别（使用 ocr_cli.py 的实现）
            ocr_result = self._ocr_with_padding(image_path, pad_ratio)

            # 2. 提取文本
            ocr_text = self._extract_text(ocr_result)

            # 3. 过滤文本
            filtered_text = self.filter_text(ocr_text)

            # 4. 情绪分析
            emotion, pos_score, neg_score = self.analyze_emotion(filtered_text)

            return {
                'ocr_text': ocr_text,
                'filtered_text': filtered_text,
                'emotion': emotion,
                'emotion_positive': pos_score,
                'emotion_negative': neg_score
            }
        except Exception as e:
            print(f"[ERROR] 处理图片失败 {image_path}: {e}")
            return {
                'ocr_text': '',
                'filtered_text': '',
                'emotion': '未分类',
                'emotion_positive': 0.0,
                'emotion_negative': 0.0
            }

    # ==================== OCR识别核心功能（来自 ocr_cli.py）====================

    def _ocr_with_padding(self, img_path: Path, pad_ratio: float = 0.10) -> List[Dict[str, Any]]:
        """
        带画布外扩的OCR识别（与 ocr_cli.py 一致）
        """
        td_ctx = None
        try:
            # 创建外扩图片
            td_ctx, feed_path, (px, py), (orig_w, orig_h) = self._make_padded_tmp(
                img_path, pad_ratio
            )

            # OCR识别
            result = self._ocr_single(feed_path)

            # 坐标回退到原图
            items = self._shift_items_to_original(
                result.get("items", []), px, py, (orig_w, orig_h)
            )

            return items

        finally:
            if td_ctx is not None:
                td_ctx.cleanup()

    def _make_padded_tmp(self, img_path: Path, pad_ratio: float, pad_color=(0, 0, 0)) -> Tuple:
        """创建外扩的临时图片（与 ocr_cli.py 一致）"""
        img = Image.open(img_path).convert("RGB")
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
        单张图片OCR识别（与 ocr_cli.py 完全一致）

        Returns:
            {"image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...]}
        """
        res = None
        try:
            # 尝试使用 predict 方法
            try:
                res = self.ocr.predict(str(img_path))
            except TypeError:
                tmp = self.ocr.predict([str(img_path)])
                res = tmp[0] if isinstance(tmp, (list, tuple)) and len(tmp) == 1 else tmp
        except Exception:
            res = None

        if not res:
            try:
                res = self.ocr.ocr(str(img_path))
            except Exception:
                res = None

        if not res:
            items = []
            return {"image": str(img_path), "items": items}

        # 解析结果（使用 ocr_cli.py 的解析逻辑）
        items = self._parse_ocr_result(res, img_path)

        return {"image": str(img_path), "items": items}

    def _parse_ocr_result(self, res, img_path: Path) -> List[Dict[str, Any]]:
        """
        解析OCR结果（与 ocr_cli.py 完全一致的解析逻辑）
        """
        items: List[Dict[str, Any]] = []

        def _tolist(x):
            try:
                return x.tolist() if hasattr(x, "tolist") else x
            except Exception:
                return x

        def _find_inner_res(d):
            # 递归查找包含 rec_texts + (rec_polys|dt_polys) 的层
            if isinstance(d, dict):
                if "res" in d and isinstance(d["res"], dict):
                    v = d["res"]
                    ks = v.keys()
                    if ("rec_texts" in ks) and (("rec_polys" in ks) or ("dt_polys" in ks)):
                        return v
                ks = d.keys()
                if ("rec_texts" in ks) and (("rec_polys" in ks) or ("dt_polys" in ks)):
                    return d
                for v in d.values():
                    inner = _find_inner_res(v)
                    if inner is not None:
                        return inner
            elif isinstance(d, (list, tuple)):
                for v in d:
                    inner = _find_inner_res(v)
                    if inner is not None:
                        return inner
            return None

        inner = _find_inner_res(res)
        if inner is not None:
            texts = list(inner.get("rec_texts") or [])
            scores = list(inner.get("rec_scores") or [])
            polys = _tolist(inner.get("rec_polys") or inner.get("dt_polys"))
            n = len(texts)
            for i in range(n):
                text = str(texts[i])
                score = float(scores[i]) if i < len(scores) else 0.0
                if polys is not None and i < len(polys):
                    box = _tolist(polys[i])
                    if isinstance(box, (list, tuple)) and len(box) == 4 and all(
                        isinstance(p, (list, tuple)) and len(p) == 2 for p in box
                    ):
                        items.append({"box": box, "text": text, "score": score})
            return items

        # 旧风格解析
        def _num(x):
            return isinstance(x, (int, float, np.integer, np.floating))

        def _pt(p):
            return isinstance(p, (list, tuple, np.ndarray)) and len(p) == 2 and _num(p[0]) and _num(p[1])

        def _box(b):
            if hasattr(b, "tolist"):
                try:
                    b = b.tolist()
                except Exception:
                    return None
            return b if (isinstance(b, (list, tuple)) and len(b) == 4 and all(_pt(p) for p in b)) else None

        def _ts(v):
            return (isinstance(v, (list, tuple)) and len(v) >= 2 and isinstance(v[0], str) and _num(v[1]))

        if isinstance(res, (list, tuple)) and len(res) > 0:
            first = res[0]
            if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)):
                for line in first:
                    if not (isinstance(line, (list, tuple)) and len(line) >= 2):
                        continue
                    b = _box(line[0])
                    ts = line[1]
                    if b is not None and _ts(ts):
                        items.append({"box": b, "text": ts[0], "score": float(ts[1])})
                if items:
                    return items

            ok = False
            for line in res:
                if not (isinstance(line, (list, tuple)) and len(line) >= 2):
                    continue
                b = _box(line[0])
                ts = line[1]
                if b is not None and _ts(ts):
                    items.append({"box": b, "text": ts[0], "score": float(ts[1])})
                    ok = True
            if ok:
                return items

        if (
            isinstance(res, (list, tuple)) and len(res) == 2
            and isinstance(res[0], (list, tuple)) and isinstance(res[1], (list, tuple))
        ):
            det_boxes, recs = res[0], res[1]
            n = min(len(det_boxes), len(recs))
            for i in range(n):
                b = _box(det_boxes[i])
                ts = recs[i]
                if b is not None and _ts(ts):
                    items.append({"box": b, "text": ts[0], "score": float(ts[1])})
            if items:
                return items

        seq = res if isinstance(res, (list, tuple)) else [res]
        took = False
        for d in seq:
            if not isinstance(d, dict):
                continue
            b = _box(d.get("box") or d.get("bbox") or d.get("points") or d.get("poly") or d.get("det"))
            ts = d.get("rec")
            text = d.get("text") or d.get("transcription") or d.get("label")
            score = d.get("score") or d.get("confidence") or d.get("prob")
            if ts and _ts(ts):
                text, score = ts[0], ts[1]
            if b is not None and isinstance(text, str):
                items.append({"box": b, "text": text, "score": float(score or 0.0)})
                took = True
        if took:
            return items

        return []

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

    # ==================== Senta 情绪分析（可选）====================

    def _init_senta(self):
        """
        初始化 PaddleNLP Senta 情绪分析模型
        如果初始化失败，将回退到关键词方法
        """
        try:
            from paddlenlp import Taskflow
            print("[INFO] 正在初始化 PaddleNLP Senta 情绪分析模型...")
            self._senta = Taskflow("sentiment_analysis")
            self._use_senta = True
            print("[INFO] PaddleNLP Senta 初始化完成")
        except ImportError:
            print("[WARN] PaddleNLP 未安装，将使用关键词方法进行情绪分析")
            print("[WARN] 如需使用 Senta，请运行: pip install paddlenlp")
            self._senta = None
            self._use_senta = False
        except Exception as e:
            print(f"[WARN] PaddleNLP Senta 初始化失败: {e}")
            print("[WARN] 将使用关键词方法进行情绪分析")
            self._senta = None
            self._use_senta = False

    def _senta_analyze(self, text: str) -> Tuple[str, float, float]:
        """
        使用 PaddleNLP Senta 进行情绪分析

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

            # 调用 Senta 进行情绪分析
            result = self._senta(text)
            
            if not result:
                return ('中性', 0.5, 0.5)

            # 解析结果
            item = result[0] if isinstance(result, list) else result
            
            if isinstance(item, dict):
                label = item.get('label', '').lower()
                score = float(item.get('score', 0.0))
                
                # PaddleNLP Senta 返回格式：
                # {'label': 'positive', 'score': 0.9xxx} 或 {'label': 'negative', 'score': 0.9xxx}
                if 'pos' in label or label == '1':
                    # 正向情绪
                    pos_score = min(0.99, max(0.5, score))
                    neg_score = 1.0 - pos_score
                    return ('正向', round(pos_score, 4), round(neg_score, 4))
                elif 'neg' in label or label == '0':
                    # 负向情绪
                    neg_score = min(0.99, max(0.5, score))
                    pos_score = 1.0 - neg_score
                    return ('负向', round(pos_score, 4), round(neg_score, 4))
                else:
                    # 中性或未知
                    return ('中性', 0.5, 0.5)
            
            return ('中性', 0.5, 0.5)

        except Exception as e:
            print(f"[WARN] Senta 分析失败: {e}，回退到关键词方法")
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
