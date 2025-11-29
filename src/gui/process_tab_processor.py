#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProcessTab 图片处理模块
负责图片的OCR识别和情感分析处理
"""

import gc
import threading
import tracemalloc  # 内存分析
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
        
        # OCR处理器 - 完全延迟加载，启动时不初始化
        self.ocr_processor = None
        self._ocr_initialized = False
        
        # 处理状态
        self.processing = False
        
        # 自动释放模型定时器
        self._unload_timer = None
        
        # 内存分析配置（生产环境建议关闭以节省600-700MB内存）
        # 开发调试时设为True，生产环境设为False
        self._memory_profiling = False  # 默认关闭，节省内存
        if self._memory_profiling:
            tracemalloc.start()
            logger.info("内存分析已启动")
            self._print_memory_status("程序启动")
        
        logger.info("ImageProcessor 初始化完成（延迟加载模式，未加载OCR模型）")

        
    def initialize_ocr(self):
        """初始化OCR处理器（延迟加载）"""
        if self._ocr_initialized and self.ocr_processor:
            self.log_message("[INFO] OCR 处理器已初始化，跳过重复初始化")
            logger.info("OCR processor already initialized")
            return True
        
        # 首次加载提示
        self.log_message("=" * 60)
        self.log_message("[INFO] 🔄 首次加载OCR模型，请稍候...")
        self.log_message("[INFO] 这可能需要5-10秒，后续使用将自动恢复")
        self.log_message("=" * 60)
        
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
                
                # 初始化OCR处理器
                self.ocr_processor = OCRProcessor(
                    use_gpu=use_gpu,
                    use_senta=use_sentiment,
                    lazy_load=True
                )
                
                # 加载OCR模型
                if not self.ocr_processor.load_ocr_model():
                    self.log_message("[ERROR] OCR模型加载失败")
                    return False
                
                # 内存快照：OCR模型加载后
                self._print_memory_status("OCR模型加载后")
                
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
    
    def _schedule_model_unload(self):
        """
        调度模型卸载：5秒后自动释放OCR和SnowNLP模型
        节省约400MB内存（OCR ~370MB + SnowNLP ~30MB），下次使用时会自动重新加载
        """
        # 取消之前的定时器
        if self._unload_timer:
            try:
                self._unload_timer.cancel()
            except Exception:
                pass
        
        def unload_models():
            try:
                if self.ocr_processor and not self.processing:
                    self.log_message("[INFO] 5秒无活动，自动释放OCR模型以节省内存...")
                    logger.info("Auto-unloading OCR models after 5 seconds of inactivity")
                    
                    # 1. 释放ONNX Runtime会话（关键：必须显式释放）
                    if self.ocr_processor.ocr:
                        try:
                            # 尝试访问RapidOCR内部的session并释放
                            if hasattr(self.ocr_processor.ocr, 'text_det'):
                                if hasattr(self.ocr_processor.ocr.text_det, 'session'):
                                    del self.ocr_processor.ocr.text_det.session
                                del self.ocr_processor.ocr.text_det
                            
                            if hasattr(self.ocr_processor.ocr, 'text_rec'):
                                if hasattr(self.ocr_processor.ocr.text_rec, 'session'):
                                    del self.ocr_processor.ocr.text_rec.session
                                del self.ocr_processor.ocr.text_rec
                            
                            if hasattr(self.ocr_processor.ocr, 'text_cls'):
                                if hasattr(self.ocr_processor.ocr.text_cls, 'session'):
                                    del self.ocr_processor.ocr.text_cls.session
                                del self.ocr_processor.ocr.text_cls
                        except Exception as e:
                            logger.debug(f"释放ONNX会话时出错（可忽略）: {e}")
                        
                        # 删除OCR对象
                        del self.ocr_processor.ocr
                        self.ocr_processor.ocr = None
                    
                    self.ocr_processor._ocr_loaded = False
                    
                    # 2. 释放情感分析模型（强制卸载SnowNLP）
                    if hasattr(self.ocr_processor, '_senta') and self.ocr_processor._senta:
                        del self.ocr_processor._senta
                        self.ocr_processor._senta = None
                    self.ocr_processor._use_senta = False
                    
                    # 强制卸载SnowNLP模块（关键：释放385MB内存）
                    try:
                        import sys
                        snownlp_modules = [mod for mod in sys.modules.keys() if 'snownlp' in mod.lower()]
                        if snownlp_modules:
                            logger.info(f"卸载SnowNLP模块: {len(snownlp_modules)} 个模块")
                            for mod in snownlp_modules:
                                try:
                                    del sys.modules[mod]
                                except:
                                    pass
                    except Exception as e:
                        logger.debug(f"SnowNLP模块卸载失败（可忽略）: {e}")
                    
                    # 3. 清理可能的缓存
                    if hasattr(self.ocr_processor, '_process_count'):
                        self.ocr_processor._process_count = 0
                    
                    # 4. 垃圾回收（2次足够，避免过度GC影响性能）
                    import gc
                    for i in range(2):
                        collected = gc.collect()
                        logger.debug(f"GC round {i+1}: collected {collected} objects")
                    
                    # 5. 尝试释放NumPy/OpenCV缓存
                    try:
                        import numpy as np
                        # 清理NumPy内部缓存
                        np._core._get_handler_cache().clear()
                    except:
                        pass
                    
                    self.log_message("[INFO] ✓ 模型已释放，已节省约735MB内存")
                    self.log_message("[INFO]   - OCR模型: ~350MB")
                    self.log_message("[INFO]   - SnowNLP模型: ~385MB")
                    self.log_message("[INFO] 下次处理时将自动重新加载模型")
                    logger.info("Models unloaded successfully")
                    
                    # 内存状态：模型释放后
                    self._print_memory_status("模型卸载后（最终状态）")
                    
            except Exception as e:
                logger.error(f"Error unloading models: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # 5秒后执行卸载（优化后）
        self._unload_timer = threading.Timer(5.0, unload_models)
        self._unload_timer.daemon = True
        self._unload_timer.start()
        logger.info("Model auto-unload timer scheduled for 5 seconds")

    
    def _print_memory_status(self, label="内存状态"):
        """
        打印详细的内存使用状态（增强版）
        包含：实际物理内存、Python对象统计、内存分配详情
        """
        try:
            import psutil
            import os
            import gc
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            self.log_message(f"\n{'='*70}")
            self.log_message(f"📊 {label}")
            self.log_message(f"{'='*70}")
            
            # 1. 实际物理内存使用
            rss_mb = mem_info.rss / 1024 / 1024
            vms_mb = mem_info.vms / 1024 / 1024
            self.log_message(f"📦 实际物理内存 (RSS): {rss_mb:.1f} MB")
            self.log_message(f"📦 虚拟内存 (VMS): {vms_mb:.1f} MB")
            
            # 2. Python GC统计
            gc_stats = gc.get_stats()
            gc_count = gc.get_count()
            self.log_message(f"\n🗑️  垃圾回收统计:")
            self.log_message(f"  - 代数统计: Gen0={gc_count[0]}, Gen1={gc_count[1]}, Gen2={gc_count[2]}")
            
            # 3. Python对象统计
            import sys
            obj_count = len(gc.get_objects())
            self.log_message(f"  - Python对象总数: {obj_count:,}")
            
            # 4. 如果启用了tracemalloc，显示详细分配
            if self._memory_profiling and tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                # 总内存
                total = sum(stat.size for stat in top_stats)
                self.log_message(f"\n💾 Tracemalloc追踪的内存: {total / 1024 / 1024:.1f} MB")
                
                # 前10个最大分配
                self.log_message(f"\n📈 内存占用 Top 10:")
                for index, stat in enumerate(top_stats[:10], 1):
                    frame = stat.traceback[0]
                    filename = frame.filename
                    
                    # 简化路径
                    if 'MEMEFinder' in filename:
                        short_name = '...' + filename.split('MEMEFinder')[-1]
                    elif 'site-packages' in filename:
                        short_name = '...' + filename.split('site-packages')[-1]
                    else:
                        short_name = filename[-50:]
                    
                    self.log_message(
                        f"  {index}. {short_name}:{frame.lineno} - "
                        f"{stat.size / 1024 / 1024:.1f} MB ({stat.count:,} 对象)"
                    )
            
            self.log_message(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"内存状态打印失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _print_memory_snapshot(self, label="Memory Snapshot"):
        """保留兼容性的简化版本"""
        self._print_memory_status(label)

    
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
        
        # 打印处理完成时的内存状态
        self._print_memory_status("处理完成（GC前）")
        
        # 立即GC（仅1次，快速回收临时对象）
        logger.info("开始垃圾回收...")
        gc.collect()
        logger.info("内存清理完成")
        
        # 打印GC后的内存状态
        self._print_memory_status("处理完成（GC后）")
        
        # 直接调度模型卸载（无需额外延迟GC）
        self._schedule_model_unload()
        
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
        
        # 缩短延迟GC
        def delayed_gc():
            import time
            time.sleep(2)
            logger.info("开始延迟垃圾回收...")
            for _ in range(2):
                gc.collect()
            logger.info("内存清理完成")
            
            # GC完成后，启动模型自动释放定时器
            self._schedule_model_unload()
        
        threading.Thread(target=delayed_gc, daemon=True).start()
        
        finish_callback(processed_count, error_count)
