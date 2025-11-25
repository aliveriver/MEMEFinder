#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProcessTab 图片处理模块
负责图片的OCR识别和情感分析处理
"""

import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core.ocr_processor import OCRProcessor
from ..utils.logger import get_logger

logger = get_logger()


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self, db, log_callback, ui_updaters, ui_vars):
        """
        初始化图片处理器
        
        Args:
            db: 数据库实例
            log_callback: 日志记录回调
            ui_updaters: UI更新回调字典 {
                'progress': func(value),
                'progress_label': func(text),
                'stats': func()
            }
            ui_vars: UI变量字典 {
                'enable_ocr_var': var,
                'enable_sentiment_var': var,
                'gpu_enabled_var': var
            }
        """
        self.db = db
        self.log_message = log_callback
        self.ui_updaters = ui_updaters
        self.ui_vars = ui_vars
        
        # OCR处理器
        self.ocr_processor = None
        self._ocr_initialized = False
        
        # 处理状态
        self.processing = False
        
    def initialize_ocr(self):
        """初始化OCR处理器"""
        if self._ocr_initialized and self.ocr_processor:
            self.log_message("[INFO] OCR 处理器已初始化,跳过重复初始化")
            logger.info("OCR processor already initialized")
            return True
        
        if self.ocr_processor is None:
            try:
                use_gpu = self.ui_vars['gpu_enabled_var'].get()
                use_sentiment = self.ui_vars['enable_sentiment_var'].get()
                mode_str = "GPU模式" if use_gpu else "CPU模式"
                sentiment_str = "启用" if use_sentiment else "禁用"
                
                self.log_message(f"[INFO] 正在初始化 OCR 处理器...")
                self.log_message(f"  - 运行模式: {mode_str}")
                self.log_message(f"  - 情感分析: {sentiment_str}")
                logger.info(f"Initializing OCR processor: GPU={use_gpu}, Sentiment={use_sentiment}")
                
                from ..utils.model_manager import get_model_manager
                model_manager = get_model_manager()
                model_dir = model_manager.get_model_dir()
                
                self.log_message(f"  - 模型目录: {model_dir}")
                logger.info(f"Model directory: {model_dir}")
                
                self.ocr_processor = OCRProcessor(
                    use_gpu=use_gpu, 
                    model_dir=model_dir, 
                    lazy_load=True,
                    use_senta=use_sentiment
                )
                self._ocr_initialized = True
                self.log_message(f"[INFO] ✓ OCR 处理器初始化完成")
                logger.info("OCR processor initialized successfully")
                return True
            except Exception as e:
                error_msg = f"OCR 初始化失败: {e}"
                self.log_message(f"[错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                traceback_str = traceback.format_exc()
                logger.debug(traceback_str)
                self.log_message(f"[错误] 详细信息已记录到日志文件")
                return False
        else:
            self._ocr_initialized = True
            self.log_message("[INFO] 使用预加载的 OCR 处理器")
            logger.info("Using pre-loaded OCR processor")
            return True
    
    def reset_ocr(self):
        """重置OCR处理器"""
        self.ocr_processor = None
        self._ocr_initialized = False
    
    def process_single_image(self, img_info):
        """处理单张图片"""
        img_id = img_info['id']
        img_path = img_info['file_path']
        
        try:
            if not Path(img_path).exists():
                error_msg = f"文件不存在: {img_path}"
                logger.warning(error_msg)
                return {
                    'success': False,
                    'id': img_id,
                    'path': img_path,
                    'error': '文件不存在'
                }
            
            enable_ocr = self.ui_vars['enable_ocr_var'].get()
            enable_sentiment = self.ui_vars['enable_sentiment_var'].get()
            
            if not enable_ocr:
                logger.debug(f"OCR disabled, skipping image {img_id}")
                self.db.update_image_data(
                    image_id=img_id,
                    ocr_text='',
                    filtered_text='',
                    emotion='未处理',
                    pos_score=0.0,
                    neg_score=0.0
                )
                return {
                    'success': True,
                    'id': img_id,
                    'path': img_path,
                    'result': {
                        'ocr_text': '',
                        'filtered_text': '',
                        'emotion': '未处理',
                        'emotion_positive': 0.0,
                        'emotion_negative': 0.0
                    }
                }
            
            assert self.ocr_processor is not None, "OCR处理器未初始化"
            
            logger.debug(f"Processing image {img_id}: {Path(img_path).name}")
            
            if not enable_sentiment:
                original_use_senta = self.ocr_processor._use_senta
                self.ocr_processor._use_senta = False
                try:
                    result = self.ocr_processor.process_image(Path(img_path))
                    logger.debug(f"Image {img_id} processed (OCR only)")
                finally:
                    self.ocr_processor._use_senta = original_use_senta
            else:
                result = self.ocr_processor.process_image(Path(img_path))
                logger.debug(f"Image {img_id} processed (OCR + Sentiment)")
            
            self.db.update_image_data(
                image_id=img_id,
                ocr_text=result['ocr_text'],
                filtered_text=result['filtered_text'],
                emotion=result['emotion'],
                pos_score=result['emotion_positive'],
                neg_score=result['emotion_negative']
            )
            
            logger.debug(f"Image {img_id} data saved to database")
            
            return {
                'success': True,
                'id': img_id,
                'path': img_path,
                'result': result
            }
            
        except Exception as e:
            error_msg = f"Error processing image {img_id} ({Path(img_path).name}): {e}"
            logger.error(error_msg)
            import traceback
            logger.debug(traceback.format_exc())
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': str(e)
            }
    
    def process_images_multithread(self, unprocessed, max_workers, finish_callback):
        """多线程处理图片"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        progress_lock = threading.Lock()
        
        self.log_message("=" * 50)
        self.log_message(f"多线程处理模式: {max_workers} 个工作线程")
        self.log_message(f"待处理图片总数: {total}")
        self.log_message("=" * 50)
        
        logger.info(f"Starting multithread processing: {total} images with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_img = {
                executor.submit(self.process_single_image, img_info): (idx, img_info)
                for idx, img_info in enumerate(unprocessed, 1)
            }
            
            self.log_message(f"已提交 {len(future_to_img)} 个处理任务到线程池")
            logger.info(f"Submitted {len(future_to_img)} tasks to thread pool")
            
            for future in as_completed(future_to_img):
                if not self.processing:
                    self.log_message("[暂停] 处理已暂停，取消剩余任务...")
                    logger.info("Processing paused, cancelling remaining tasks")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                idx, img_info = future_to_img[future]
                img_path = img_info['file_path']
                
                try:
                    task_result = future.result()
                    
                    with progress_lock:
                        if task_result['success']:
                            processed_count += 1
                        else:
                            error_count += 1
                        completed = processed_count + error_count
                    
                    progress = (completed / total) * 100
                    self.ui_updaters['progress'](progress)
                    self.ui_updaters['progress_label'](
                        f"正在处理: {completed}/{total} (成功:{processed_count}, 失败:{error_count})"
                    )
                    
                    if task_result['success']:
                        result = task_result['result']
                        filename = Path(img_path).name
                        self.log_message(f"[{completed}/{total}] ✓ {filename}")
                        if result['filtered_text']:
                            preview = result['filtered_text'][:50]
                            if len(result['filtered_text']) > 50:
                                preview += "..."
                            self.log_message(f"  文本: {preview}")
                            self.log_message(f"  情绪: {result['emotion']} (正:{result['emotion_positive']:.2f}, 负:{result['emotion_negative']:.2f})")
                        else:
                            self.log_message(f"  未识别到文本")
                    else:
                        error = task_result.get('error', '未知错误')
                        filename = Path(img_path).name
                        self.log_message(f"[{completed}/{total}] ✗ {filename}")
                        self.log_message(f"  错误: {error}")
                    
                    if completed % 5 == 0:
                        self.ui_updaters['stats']()
                    
                    if completed % 10 == 0:
                        self.log_message(f"--- 进度: {completed}/{total} ({progress:.1f}%) | 成功: {processed_count} | 失败: {error_count} ---")
                        logger.info(f"Progress: {completed}/{total} ({progress:.1f}%) - Success: {processed_count}, Failed: {error_count}")
                    
                except Exception as e:
                    with progress_lock:
                        error_count += 1
                        completed = processed_count + error_count
                    
                    filename = Path(img_path).name
                    self.log_message(f"[{completed}/{total}] ✗ {filename}")
                    self.log_message(f"  异常: {str(e)}")
                    logger.error(f"处理图片失败 [{filename}]: {e}")
        
        logger.info(f"Multithread processing completed: {processed_count} successful, {error_count} failed")
        finish_callback(processed_count, error_count)
    
    def process_images_singlethread(self, unprocessed, finish_callback):
        """单线程处理图片"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        logger.info(f"Starting singlethread processing: {total} images")
        
        for idx, img_info in enumerate(unprocessed, 1):
            if not self.processing:
                self.log_message("[暂停] 处理已暂停")
                logger.info("Processing paused")
                break
            
            img_id = img_info['id']
            img_path = img_info['file_path']
            
            try:
                progress = (idx / total) * 100
                self.ui_updaters['progress'](progress)
                self.ui_updaters['progress_label'](f"正在处理: {idx}/{total}")
                
                task_result = self.process_single_image(img_info)
                
                if task_result['success']:
                    result = task_result['result']
                    filename = Path(img_path).name
                    self.log_message(f"[{idx}/{total}] ✓ {filename}")
                    if result['filtered_text']:
                        preview = result['filtered_text'][:50]
                        if len(result['filtered_text']) > 50:
                            preview += "..."
                        self.log_message(f"  - 文本: {preview}")
                        self.log_message(f"  - 情绪: {result['emotion']}")
                    else:
                        self.log_message(f"  - 未识别到文本")
                    
                    processed_count += 1
                else:
                    error_msg = f"处理图片失败 [{Path(img_path).name}]: {task_result.get('error', '未知错误')}"
                    self.log_message(f"  [错误] {error_msg}")
                    logger.error(error_msg)
                    error_count += 1
                
                if idx % 5 == 0:
                    self.ui_updaters['stats']()
                
                if idx % 10 == 0:
                    logger.info(f"Singlethread progress: {idx}/{total} - Success: {processed_count}, Failed: {error_count}")
                    
            except Exception as e:
                error_msg = f"处理图片失败 [{Path(img_path).name}]: {e}"
                self.log_message(f"  [错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                traceback_str = traceback.format_exc()
                logger.debug(traceback_str)
                error_count += 1
                continue
        
        logger.info(f"Singlethread processing completed: {processed_count} successful, {error_count} failed")
        finish_callback(processed_count, error_count)
