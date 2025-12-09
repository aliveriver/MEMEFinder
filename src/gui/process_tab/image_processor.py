#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理器
负责图片的OCR识别和情感分析处理
"""

import gc
import threading
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from ...core.ocr import OCRProcessor
from ...utils.logger import get_logger
from .worker import _process_images_in_subprocess, _process_image_worker
from .memory_utils import MemoryMonitor

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
        self.paused = False  # 暂停状态
        self.stop_requested = False  # 停止请求标志
        
        # 自动释放模型定时器
        self._unload_timer = None
        
        # 内存监控器（生产环境建议关闭详细分析以节省内存）
        self.memory_monitor = MemoryMonitor(enable_profiling=False)
        self.memory_monitor.print_memory_status("程序启动", self.log_message)
        
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
                
                from ...utils.model_manager import get_model_manager
                model_manager = get_model_manager()
                model_dir = model_manager.get_model_dir()
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
                self.memory_monitor.print_memory_status("OCR模型加载后", self.log_message)
                
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
        调度模型卸载：2秒后自动释放OCR和SnowNLP模型
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
                    self.log_message("[INFO] 2秒无活动，自动释放OCR模型以节省内存...")
                    logger.info("Auto-unloading OCR models after 2 seconds of inactivity")
                    
                    # 1. 释放ONNX Runtime会话
                    if self.ocr_processor.ocr:
                        try:
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
                        
                        del self.ocr_processor.ocr
                        self.ocr_processor.ocr = None
                    
                    self.ocr_processor._ocr_loaded = False
                    
                    # 2. 释放情感分析模型
                    if hasattr(self.ocr_processor, '_senta') and self.ocr_processor._senta:
                        del self.ocr_processor._senta
                        self.ocr_processor._senta = None
                    self.ocr_processor._use_senta = False
                    
                    # 强制卸载SnowNLP模块
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
                    
                    # 3. 清理缓存
                    if hasattr(self.ocr_processor, '_process_count'):
                        self.ocr_processor._process_count = 0
                    
                    # 4. 垃圾回收
                    for i in range(2):
                        collected = gc.collect()
                        logger.debug(f"GC round {i+1}: collected {collected} objects")
                    
                    # 5. 清理NumPy/OpenCV缓存
                    self.memory_monitor.cleanup_numpy_cache()
                    
                    self.log_message("[INFO] ✓ 模型已释放")
                    self.log_message("[INFO] 下次处理时将自动重新加载模型")
                    logger.info("Models unloaded successfully")
                    
                    # 内存状态：模型释放后
                    self.memory_monitor.print_memory_status("模型卸载后（最终状态）", self.log_message)
                    
            except Exception as e:
                logger.error(f"Error unloading models: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # 2秒后执行卸载
        self._unload_timer = threading.Timer(2.0, unload_models)
        self._unload_timer.daemon = True
        self._unload_timer.start()
        logger.info("Model auto-unload timer scheduled for 2 seconds")
    
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
                    neg_score=0.0,
                    phash=None,
                    hsv_h=None
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
                neg_score=result['emotion_negative'],
                phash=result.get('phash'),
                hsv_h=result.get('hsv_h')
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
        """混合模式：单子进程 + 内部多线程处理图片"""
        from multiprocessing import Manager
        import time
        
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        self.log_message("=" * 50)
        self.log_message(f"混合处理模式: 1个子进程 + {max_workers} 个工作线程")
        self.log_message(f"待处理图片总数: {total}")
        logger.info(f"[架构] 主进程(GUI) → 子进程(OCR模型+共享DB) → 多线程(并行处理)")
        logger.info(f"[优势] 内存隔离 + 模型共享 + DB复用 + 多线程并行")
        self.log_message("=" * 50)
        
        logger.info(f"Starting hybrid processing: 1 subprocess with {max_workers} threads for {total} images")
        
        # 获取配置参数
        enable_ocr = self.ui_vars['enable_ocr_var'].get()
        enable_sentiment = self.ui_vars['enable_sentiment_var'].get()
        use_gpu = self.ui_vars['gpu_enabled_var'].get()
        db_path = self.db.db_path if hasattr(self.db, 'db_path') else 'meme_finder.db'
        
        # 创建进度队列和控制队列用于实时更新
        manager = Manager()
        progress_queue = manager.Queue()
        control_queue = manager.Queue()  # 用于发送暂停/停止命令
        
        # 使用单个子进程处理所有图片（内部使用多线程）
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _process_images_in_subprocess,
                unprocessed,
                enable_ocr,
                enable_sentiment,
                use_gpu,
                db_path,
                max_workers,
                progress_queue,
                control_queue  # 传递控制队列
            )
            
            self.log_message(f"已启动子进程，内部使用 {max_workers} 个线程处理...")
            logger.info(f"Subprocess started with {max_workers} internal threads")
            
            # 实时监听进度更新
            try:
                last_paused_state = False
                last_stop_state = False
                
                while not future.done():
                    # 检查暂停状态变化
                    if self.paused != last_paused_state:
                        if self.paused:
                            self.log_message("[暂停] 发送暂停信号到子进程...")
                            control_queue.put('pause')
                        else:
                            self.log_message("[继续] 发送继续信号到子进程...")
                            control_queue.put('resume')
                        last_paused_state = self.paused
                    
                    # 检查停止状态变化
                    if (self.stop_requested or not self.processing) and not last_stop_state:
                        self.log_message("[停止] 发送停止信号到子进程...")
                        control_queue.put('stop')
                        last_stop_state = True
                        time.sleep(0.5)
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    # 如果处于暂停状态，只等待不处理进度
                    if self.paused:
                        time.sleep(0.2)
                        continue
                    
                    # 检查进度队列
                    try:
                        while not progress_queue.empty():
                            progress_data = progress_queue.get_nowait()
                            if progress_data['type'] == 'progress':
                                index = progress_data['index']
                                total_imgs = progress_data['total']
                                result = progress_data['result']
                                
                                # 更新进度
                                if result.get('success'):
                                    processed_count += 1
                                    filename = Path(result['path']).name if result.get('path') else f"图片{index}"
                                    self.log_message(f"[{index}/{total_imgs}] ✓ {filename}")
                                    
                                    # 显示文本预览
                                    if 'result' in result and result['result'].get('filtered_text'):
                                        preview = result['result']['filtered_text'][:50]
                                        if len(result['result']['filtered_text']) > 50:
                                            preview += "..."
                                        self.log_message(f"  文本: {preview}")
                                        self.log_message(f"  情绪: {result['result']['emotion']}")
                                else:
                                    error_count += 1
                                    filename = Path(result['path']).name if result.get('path') else f"图片{index}"
                                    self.log_message(f"[{index}/{total_imgs}] ✗ {filename} - {result.get('error', '未知错误')}")
                                
                                # 更新进度条
                                progress = (index / total_imgs) * 100
                                self.ui_updaters['progress'](progress)
                                self.ui_updaters['progress_label'](f"处理进度: {index}/{total_imgs}")
                    except Exception:
                        pass
                    
                    time.sleep(0.1)
                
                # 处理子进程完成后的剩余消息
                if future.done() and not future.cancelled():
                    try:
                        while not progress_queue.empty():
                            progress_data = progress_queue.get_nowait()
                            if progress_data['type'] == 'progress':
                                index = progress_data['index']
                                total_imgs = progress_data['total']
                                result = progress_data['result']
                                
                                if result.get('success'):
                                    processed_count += 1
                                else:
                                    error_count += 1
                                
                                progress = (index / total_imgs) * 100
                                self.ui_updaters['progress'](progress)
                                self.ui_updaters['progress_label'](f"处理进度: {index}/{total_imgs}")
                    except Exception:
                        pass
                    
                    # 获取最终结果
                    results = future.result()
                    final_success = sum(1 for r in results if r.get('success'))
                    final_error = sum(1 for r in results if not r.get('success'))
                    
                    self.log_message(f"\n子进程处理完成")
                    self.log_message(f"成功: {final_success}, 失败: {final_error}")
                    
                    del results
                    gc.collect()
                
            except Exception as e:
                self.log_message(f"[错误] 子进程处理失败: {e}")
                logger.error(f"Subprocess processing failed: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # 清理进度队列
        try:
            manager.shutdown()
        except Exception:
            pass
        
        logger.info(f"Hybrid processing completed: {processed_count} successful, {error_count} failed")
        
        self.log_message(f"\n[INFO] 混合模式处理完成")
        self.log_message(f"[INFO] 成功: {processed_count}, 失败: {error_count}")
        self.log_message(f"[INFO] 子进程已退出，所有内存已释放")
        logger.info(f"子进程内存已完全释放")
        
        # 强制GC
        logger.info("主进程开始强制垃圾回收...")
        total_collected = self.memory_monitor.force_garbage_collection()
        logger.info(f"主进程总共回收了 {total_collected} 个对象")
        
        self.memory_monitor.print_memory_status("多进程处理完成（GC后）", self.log_message)
        
        if self.ocr_processor:
            self._schedule_model_unload()
        
        self.log_message("=" * 50)
        self.log_message(f"处理统计: 总数={total}, 成功={processed_count}, 失败={error_count}")
        logger.info(f"Final stats: total={total}, success={processed_count}, failed={error_count}")
        self.log_message("=" * 50)
        finish_callback(processed_count, error_count)
    
    def process_images_singlethread(self, unprocessed, finish_callback):
        """单线程处理图片"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        logger.info(f"Starting singlethread processing: {total} images")
        
        for idx, img_info in enumerate(unprocessed, 1):
            # 检查暂停状态
            while self.paused and self.processing:
                import time
                time.sleep(0.5)
            
            # 检查停止状态
            if self.stop_requested or not self.processing:
                self.log_message("[停止] 处理已停止")
                logger.info("Processing stopped")
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
        
        # 延迟GC
        def delayed_gc():
            import time
            time.sleep(2)
            logger.info("开始延迟垃圾回收...")
            for _ in range(2):
                gc.collect()
            logger.info("内存清理完成")
            self._schedule_model_unload()
        
        threading.Thread(target=delayed_gc, daemon=True).start()
        
        finish_callback(processed_count, error_count)
