#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR处理模块 - 基于 ocr_cli.py 的成功实现

本文件对原始实现进行了格式化和缩进修复，但保持逻辑不变。
"""

import re
import tempfile
import gc
import os
import threading
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

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
from utils.gpu_detector import should_use_gpu, detect_gpu

logger = get_logger()
resource_monitor = get_resource_monitor()


def _init_rapidocr_with_timeout(kwargs_dict, result_container, timeout=30):
    """
    在单独线程中初始化RapidOCR，带超时控制
    
    Args:
        kwargs_dict: RapidOCR初始化参数
        result_container: 用于存储结果的字典 {'ocr': None, 'error': None}
        timeout: 超时时间（秒）
    """
    try:
        ocr_instance = RapidOCR(**kwargs_dict)
        result_container['ocr'] = ocr_instance
    except Exception as e:
        result_container['error'] = e


class OCRProcessor:
    """OCR处理器 - 使用 RapidOCR（轻量级，易于打包）"""

    def __init__(self, lang: str = 'ch', use_gpu: Optional[bool] = None, det_side: int = 1536, use_senta: bool = True, model_dir: Optional[Path] = None):
        """
        初始化OCR处理器

        Args:
            lang: 语言，默认'ch'（中文）- RapidOCR会忽略此参数，因为它已内置多语言支持
            use_gpu: 是否使用GPU，None表示自动检测
            det_side: 检测侧边长度，默认1536（可降低以减少内存）
            use_senta: 是否使用情绪分析模型，默认True（优先使用 SnowNLP，快速且准确）
            model_dir: 模型存储目录，None表示使用默认路径（根目录的models文件夹）
        """
        logger.info("=" * 60)
        logger.info("初始化 OCR 处理器（RapidOCR）...")
        
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
        
        # RapidOCR模型存储路径设置
        # RapidOCR会将模型下载到用户目录下的.rapidocr文件夹
        # 我们需要通过环境变量或符号链接来重定向到我们的目录
        # 设置RAPIDOCR_HOME环境变量（如果RapidOCR支持）
        os.environ['RAPIDOCR_HOME'] = str(model_dir)
        
        # 也尝试设置可能的其他环境变量
        os.environ['RAPIDOCR_MODEL_DIR'] = str(model_dir)
        
        logger.info(f"模型存储路径: {model_dir}")
        logger.info(f"环境变量 RAPIDOCR_HOME: {os.environ.get('RAPIDOCR_HOME', '未设置')}")

        # 检查是否通过环境变量强制使用 CPU 模式
        force_cpu = os.environ.get('MEMEFINDER_FORCE_CPU', '').lower() in ('1', 'true', 'yes')
        if force_cpu:
            logger.info("检测到环境变量 MEMEFINDER_FORCE_CPU，强制使用 CPU 模式")
            use_gpu = False

        # 自动检测GPU（如果未指定）
        if use_gpu is None:
            has_gpu, gpu_info = detect_gpu()
            use_gpu = should_use_gpu()
            if has_gpu:
                logger.info(f"✓ 检测到GPU: {gpu_info}")
                logger.info(f"  将使用GPU加速模式")
            else:
                logger.info("✗ 未检测到GPU，将使用CPU模式")
                if gpu_info and "不可用" in str(gpu_info):
                    # GPU 硬件存在但初始化测试失败
                    logger.warning(f"  原因: {gpu_info}")
                    logger.info("  为了程序稳定性，已自动切换到CPU模式")
                else:
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
        
        # 初始化 RapidOCR
        logger.info("正在初始化 RapidOCR...")
        try:
            # 确保模型目录存在
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查models目录下是否已有模型文件
            existing_models = list(model_dir.rglob('*.onnx'))
            if existing_models:
                # 如果已有模型文件，尝试使用它们
                model_names = {f.name.lower(): f for f in existing_models}
                det_model = None
                rec_model = None
                cls_model = None
                
                # 查找检测模型
                for name, path in model_names.items():
                    if 'det' in name and 'infer' in name:
                        det_model = path
                        break
                
                # 查找识别模型
                for name, path in model_names.items():
                    if 'rec' in name and 'infer' in name:
                        rec_model = path
                        break
                
                # 查找分类模型（可选）
                for name, path in model_names.items():
                    if 'cls' in name and 'infer' in name:
                        cls_model = path
                        break
                
                if det_model and rec_model:
                    logger.info(f"✓ 找到本地模型文件，使用本地模型")
                    logger.info(f"  检测模型: {det_model.name}")
                    logger.info(f"  识别模型: {rec_model.name}")
                    if cls_model:
                        logger.info(f"  方向分类: {cls_model.name}")
                else:
                    logger.info(f"模型文件不完整，RapidOCR将自动下载缺失的模型")
                    det_model = None
                    rec_model = None
                    cls_model = None
            else:
                logger.info(f"模型文件不存在，RapidOCR将在首次使用时自动下载到: {model_dir}")
                det_model = None
                rec_model = None
                cls_model = None
            
            # 构建RapidOCR初始化参数
            # 注意：GPU模式可能导致初始化失败，需要做好异常处理
            rapidocr_kwargs = {
                'det_use_cuda': use_gpu,  # 检测模型是否使用CUDA
                'cls_use_cuda': use_gpu,   # 方向分类是否使用CUDA  
                'rec_use_cuda': use_gpu,   # 识别模型是否使用CUDA
            }
            
            # 如果启用GPU，尝试验证CUDA是否可用
            if use_gpu:
                try:
                    import onnxruntime as ort
                    available_providers = ort.get_available_providers()
                    if 'CUDAExecutionProvider' not in available_providers:
                        logger.warning("⚠ CUDA不可用，将自动切换到CPU模式")
                        logger.warning(f"  可用提供者: {available_providers}")
                        use_gpu = False
                        rapidocr_kwargs['det_use_cuda'] = False
                        rapidocr_kwargs['cls_use_cuda'] = False
                        rapidocr_kwargs['rec_use_cuda'] = False
                except Exception as e:
                    logger.warning(f"⚠ 检查CUDA可用性失败: {e}")
                    logger.warning("  将尝试使用GPU模式，如失败将回退到CPU")
            
            # 设置模型文件的标准路径（如果还没有找到本地模型）
            if not det_model:
                det_model = model_dir / 'ch_PP-OCRv4_det_infer.onnx'
            if not rec_model:
                rec_model = model_dir / 'ch_PP-OCRv4_rec_infer.onnx'
            if not cls_model:
                # 注意文件名可能有两种格式
                cls_model_v2 = model_dir / 'ch_ppocr_mobile_v2.0_cls_infer.onnx'
                cls_model_old = model_dir / 'ch_ppocr_mobile_v2_cls_infer.onnx'
                if cls_model_v2.exists():
                    cls_model = cls_model_v2
                elif cls_model_old.exists():
                    cls_model = cls_model_old
                else:
                    cls_model = cls_model_v2  # 默认使用v2.0版本
            
            # 检查模型文件是否存在，如果不存在则给出明确提示
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
            
            # 直接传递模型文件的绝对路径给RapidOCR
            # 注意：这里不使用params参数，而是直接传递路径参数
            rapidocr_kwargs['det_model_path'] = str(det_model)
            rapidocr_kwargs['rec_model_path'] = str(rec_model)
            rapidocr_kwargs['cls_model_path'] = str(cls_model)
            
            logger.info(f"模型路径配置:")
            logger.info(f"  检测模型: {det_model}")
            logger.info(f"  识别模型: {rec_model}")
            logger.info(f"  方向分类: {cls_model}")
            
            # 尝试初始化 RapidOCR，如果GPU模式失败则自动回退到CPU
            ocr_initialized = False
            last_error = None
            
            try:
                logger.info(f"尝试初始化 RapidOCR ({'GPU' if use_gpu else 'CPU'} 模式)...")
                
                # 使用超时机制初始化RapidOCR（特别针对GPU模式可能卡住的问题）
                if use_gpu:
                    logger.info("使用超时保护机制（30秒）防止GPU初始化卡死...")
                    logger.warning("  如果初始化超时，程序将自动切换到CPU模式")
                    
                    result_container = {'ocr': None, 'error': None}
                    thread = threading.Thread(
                        target=_init_rapidocr_with_timeout, 
                        args=(rapidocr_kwargs, result_container),
                        daemon=True  # 设置为守护线程，主程序退出时自动终止
                    )
                    thread.start()
                    thread.join(timeout=30)  # 30秒超时
                    
                    if thread.is_alive():
                        # 超时了，线程还在运行
                        logger.error("✗ GPU模式初始化超时（30秒）")
                        logger.warning("  GPU 初始化线程仍在运行，将被放弃")
                        logger.warning("  这通常是由于打包后的程序缺少CUDA相关的DLL文件")
                        logger.warning("  或者GPU驱动存在问题")
                        # 不抛出异常，而是设置错误让后面的逻辑处理
                        result_container['error'] = TimeoutError("RapidOCR GPU初始化超时")
                    
                    if result_container['error']:
                        raise result_container['error']
                    
                    self.ocr = result_container['ocr']
                    
                    if self.ocr is None:
                        raise Exception("RapidOCR GPU 初始化返回 None")
                else:
                    # CPU模式，直接初始化
                    self.ocr = RapidOCR(**rapidocr_kwargs)
                
                if self.ocr is None:
                    raise Exception("RapidOCR 初始化返回 None")
                
                # 尝试进行一个简单的测试以确保OCR真的可用
                # 这可以捕获一些延迟的初始化错误
                ocr_initialized = True
                logger.info("✓ RapidOCR 对象创建成功")
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.error(f"✗ RapidOCR 初始化失败: {error_msg}")
                
                # 分析错误原因并给出建议
                if use_gpu:
                    logger.warning("=" * 60)
                    logger.warning("⚠ GPU模式初始化失败")
                    logger.warning("=" * 60)
                    
                    # 分析具体错误
                    if "Timeout" in error_msg or "超时" in error_msg:
                        logger.warning("错误类型: 初始化超时")
                        logger.warning("可能原因:")
                        logger.warning("  1. 打包后的程序缺少CUDA相关的DLL文件")
                        logger.warning("  2. GPU驱动存在问题或版本不兼容")
                        logger.warning("  3. onnxruntime-gpu加载CUDA库时卡住")
                        logger.warning("")
                        logger.warning("说明:")
                        logger.warning("  这是打包程序在某些GPU环境下的已知问题")
                        logger.warning("  程序将自动切换到CPU模式，不影响使用")
                    elif "CUDA" in error_msg or "cuda" in error_msg:
                        logger.warning("错误类型: CUDA相关")
                        logger.warning("可能原因:")
                        logger.warning("  1. CUDA版本与onnxruntime-gpu不匹配")
                        logger.warning("  2. 缺少cuDNN库")
                        logger.warning("  3. CUDA驱动损坏")
                        logger.warning("")
                        logger.warning("修复建议:")
                        logger.warning("  1. 检查CUDA版本: nvidia-smi")
                        logger.warning("  2. 重新安装onnxruntime-gpu:")
                        logger.warning("     pip uninstall onnxruntime onnxruntime-gpu")
                        logger.warning("     pip install onnxruntime-gpu")
                        logger.warning("  3. 或者使用CPU模式（稳定可靠）")
                    elif "DLL" in error_msg or "load" in error_msg:
                        logger.warning("错误类型: 库文件加载失败")
                        logger.warning("可能原因:")
                        logger.warning("  1. 缺少必要的DLL文件")
                        logger.warning("  2. Visual C++ 运行库未安装")
                        logger.warning("")
                        logger.warning("修复建议:")
                        logger.warning("  1. 安装 Visual C++ Redistributable")
                        logger.warning("  2. 使用CPU模式")
                    else:
                        logger.warning("错误类型: 未知")
                        logger.warning("建议使用CPU模式以保证程序稳定运行")
                    
                    logger.warning("=" * 60)
                    logger.warning("正在自动切换到CPU模式...")
                    logger.warning("=" * 60)
                    
                    try:
                        # 切换到CPU模式
                        rapidocr_kwargs['det_use_cuda'] = False
                        rapidocr_kwargs['cls_use_cuda'] = False
                        rapidocr_kwargs['rec_use_cuda'] = False
                        use_gpu = False
                        
                        logger.info("重新尝试初始化 RapidOCR (CPU 模式)...")
                        self.ocr = RapidOCR(**rapidocr_kwargs)
                        
                        if self.ocr is None:
                            raise Exception("RapidOCR 初始化返回 None")
                        
                        ocr_initialized = True
                        logger.info("✓ CPU模式初始化成功")
                        
                    except Exception as cpu_error:
                        logger.error(f"✗ CPU模式也初始化失败: {cpu_error}")
                        raise Exception(f"RapidOCR 初始化完全失败 - GPU错误: {last_error}, CPU错误: {cpu_error}")
                else:
                    # 如果本来就是CPU模式，直接抛出错误
                    raise
            
            if not ocr_initialized or self.ocr is None:
                raise Exception("RapidOCR 初始化失败")
            
            # 验证实际使用的设备
            actual_device = "未知"
            try:
                # 尝试从OCR对象获取设备信息
                if hasattr(self.ocr, 'det_model') and hasattr(self.ocr.det_model, 'session'):
                    providers = self.ocr.det_model.session.get_providers()
                    if 'CUDAExecutionProvider' in providers:
                        actual_device = "GPU (CUDA)"
                    elif 'DmlExecutionProvider' in providers:
                        actual_device = "GPU (DirectML)"
                    else:
                        actual_device = "CPU"
            except:
                # 如果无法获取，使用我们设置的use_gpu值
                actual_device = "GPU" if use_gpu else "CPU"
            
            device_type = "GPU" if use_gpu else "CPU"
            logger.info(f"✓ RapidOCR 初始化成功")
            logger.info(f"  配置模式: {device_type}")
            logger.info(f"  实际设备: {actual_device}")
            logger.info("RapidOCR 优势：轻量级、易打包、无复杂依赖")
            
            # 检查模型文件位置（初始化后再次检查）
            self._check_model_location(model_dir)
            
        except Exception as e:
            error_msg = f"RapidOCR 初始化失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # 保存模型目录路径供后续使用
        self.model_dir = model_dir
        
        # 初始化 Senta 情绪分析（可选）
        self._senta = None
        self._use_senta = False
        if use_senta:
            self._init_senta()
        
        # 记录初始化后的资源状态
        resource_monitor.log_resource_status()
        logger.info("OCR 处理器初始化完成")
        logger.info("=" * 60)
    
    def _check_model_location(self, target_dir: Path):
        """
        检查模型文件位置
        
        Args:
            target_dir: 目标模型目录
        """
        try:
            # 检查目标目录是否有模型文件
            target_onnx = list(target_dir.rglob('*.onnx'))
            if target_onnx:
                total_size = sum(f.stat().st_size for f in target_onnx) / (1024 * 1024)
                logger.info(f"✓ 模型文件已在目标目录: {target_dir}")
                logger.info(f"  找到 {len(target_onnx)} 个模型文件，总大小: {total_size:.2f} MB")
                
                # 列出主要模型文件
                main_models = ['det', 'rec', 'cls']
                for model_type in main_models:
                    model_files = [f for f in target_onnx if model_type.lower() in f.name.lower()]
                    if model_files:
                        logger.info(f"    - {model_type.upper()}: {model_files[0].name}")
                return
            
            # 如果目标目录没有模型，检查是否在下载中
            logger.info(f"模型文件将在首次使用时自动下载到: {target_dir}")
            logger.info("  下载完成后，模型将保存在此目录，无需再次下载")
                
        except Exception as e:
            logger.warning(f"检查模型位置时出错: {e}")

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
