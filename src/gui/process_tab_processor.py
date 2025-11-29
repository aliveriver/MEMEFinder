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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from ..core.ocr_processor import OCRProcessor
from ..utils.logger import get_logger

# Windows多进程支持
import multiprocessing
if __name__ != '__main__':
    # 在模块导入时设置multiprocessing为spawn模式（Windows默认）
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass  # 已经设置过了

logger = get_logger()


# 全局函数：在单个子进程中使用多线程处理所有图片
def _process_images_in_subprocess(image_list, enable_ocr, enable_sentiment, use_gpu, db_path, max_workers):
    """
    在单个子进程中使用多线程处理多张图片
    
    这是一个混合模式：
    - 使用1个子进程隔离主进程内存
    - 在子进程内使用多线程并行处理
    - OCR模型只加载一次，所有线程共享
    
    Args:
        image_list: 图片信息列表
        enable_ocr: 是否启用OCR
        enable_sentiment: 是否启用情感分析
        use_gpu: 是否使用GPU
        db_path: 数据库路径
        max_workers: 子进程内的线程数
    
    Returns:
        处理结果列表
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from ..core.database import ImageDatabase
    from ..core.ocr_processor import OCRProcessor
    import logging
    import threading
    
    # 子进程中配置日志
    logging.basicConfig(level=logging.WARNING)
    
    results = []
    ocr_processor = None
    
    try:
        # 在子进程中初始化OCR处理器（只初始化一次）
        if enable_ocr:
            ocr_processor = OCRProcessor(
                use_gpu=use_gpu,
                use_senta=enable_sentiment,
                lazy_load=True
            )
            
            if not ocr_processor.load_ocr_model():
                return [
                    {
                        'success': False,
                        'id': img['id'],
                        'path': img['file_path'],
                        'error': 'OCR模型加载失败'
                    }
                    for img in image_list
                ]
        
        # 定义线程工作函数
        def process_one_image(img_info):
            img_id = img_info['id']
            img_path = img_info['file_path']
            
            db = None  # 确保在finally中能访问
            try:
                if not Path(img_path).exists():
                    return {
                        'success': False,
                        'id': img_id,
                        'path': img_path,
                        'error': '文件不存在'
                    }
                
                if not enable_ocr:
                    # 不启用OCR时直接写入空数据
                    db = ImageDatabase(db_path)
                    db.update_image_data(
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
                
                # 使用共享的OCR处理器处理图片
                result = ocr_processor.process_image(Path(img_path))
                
                # 更新数据库（每个线程独立连接）
                db = ImageDatabase(db_path)
                db.update_image_data(
                    image_id=img_id,
                    ocr_text=result['ocr_text'],
                    filtered_text=result['filtered_text'],
                    emotion=result['emotion'],
                    pos_score=result['emotion_positive'],
                    neg_score=result['emotion_negative']
                )
                
                return {
                    'success': True,
                    'id': img_id,
                    'path': img_path,
                    'result': result
                }
                
            except Exception as e:
                import traceback
                return {
                    'success': False,
                    'id': img_id,
                    'path': img_path,
                    'error': f"{str(e)}\n{traceback.format_exc()}"
                }
            finally:
                # 关键：确保数据库连接被正确关闭
                if db is not None:
                    try:
                        db.close()
                        del db
                    except Exception:
                        pass
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_one_image, img) for img in image_list]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    import traceback
                    results.append({
                        'success': False,
                        'error': f"线程异常: {str(e)}\n{traceback.format_exc()}"
                    })
        
        # 清理OCR处理器
        if ocr_processor:
            try:
                del ocr_processor
            except Exception:
                pass
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        return results
        
    except Exception as e:
        import traceback
        return [
            {
                'success': False,
                'error': f"子进程异常: {str(e)}\n{traceback.format_exc()}"
            }
            for _ in image_list
        ]
    finally:
        # 确保清理
        try:
            if 'ocr_processor' in locals() and ocr_processor:
                del ocr_processor
        except Exception:
            pass
        
        # 最终GC
        import gc
        gc.collect()


# 原有的单图片处理函数（保留用于单进程模式）
def _process_image_worker(img_info, enable_ocr, enable_sentiment, use_gpu, db_path):
    """
    子进程中处理单张图片的工作函数
    
    Args:
        img_info: 图片信息字典
        enable_ocr: 是否启用OCR
        enable_sentiment: 是否启用情感分析
        use_gpu: 是否使用GPU
        db_path: 数据库路径
    
    Returns:
        处理结果字典
    """
    from ..core.database import ImageDatabase
    from ..core.ocr_processor import OCRProcessor
    import logging
    
    # 子进程中重新配置日志（避免与主进程冲突）
    logging.basicConfig(level=logging.WARNING)
    
    img_id = img_info['id']
    img_path = img_info['file_path']
    
    try:
        if not Path(img_path).exists():
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': '文件不存在'
            }
        
        if not enable_ocr:
            # 不启用OCR时直接写入空数据
            db = ImageDatabase(db_path)
            db.update_image_data(
                image_id=img_id,
                ocr_text='',
                filtered_text='',
                emotion='未处理',
                pos_score=0.0,
                neg_score=0.0
            )
            db.close()
            
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
        
        # 初始化OCR处理器
        ocr_processor = OCRProcessor(
            use_gpu=use_gpu,
            use_senta=enable_sentiment,
            lazy_load=True
        )
        
        # 加载OCR模型
        if not ocr_processor.load_ocr_model():
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': 'OCR模型加载失败'
            }
        
        # 处理图片
        result = ocr_processor.process_image(Path(img_path))
        
        # 更新数据库
        db = ImageDatabase(db_path)
        db.update_image_data(
            image_id=img_id,
            ocr_text=result['ocr_text'],
            filtered_text=result['filtered_text'],
            emotion=result['emotion'],
            pos_score=result['emotion_positive'],
            neg_score=result['emotion_negative']
        )
        db.close()
        
        # 清理OCR处理器
        del ocr_processor
        gc.collect()
        
        return {
            'success': True,
            'id': img_id,
            'path': img_path,
            'result': result
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'id': img_id,
            'path': img_path,
            'error': f"{str(e)}\n{traceback.format_exc()}"
        }


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
                
                # 模型目录信息只记录到日志文件
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
                
                # 内存快照：OCR模型加载后（只记录到日志文件）
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
                        # 只记录到日志文件，不显示在UI
                        logger.debug(f"GC round {i+1}: collected {collected} objects")
                    
                    # 5. 尝试释放NumPy/OpenCV缓存
                    try:
                        import numpy as np
                        # 清理NumPy内部缓存
                        np._core._get_handler_cache().clear()
                    except:
                        pass
                    
                    self.log_message("[INFO] ✓ 模型已释放，已节省约735MB内存")
                    # 详细的内存节省信息只记录到日志文件
                    logger.info("  - OCR模型: ~350MB")
                    logger.info("  - SnowNLP模型: ~385MB")
                    self.log_message("[INFO] 下次处理时将自动重新加载模型")
                    logger.info("Models unloaded successfully")
                    
                    # 内存状态：模型释放后（只记录到日志文件）
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
        注意：这些信息只记录到日志文件，不显示在UI上
        """
        try:
            import psutil
            import os
            import gc
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            # 只记录到日志文件，不显示在UI
            self.log_message(f"\n{'='*70}", show_in_ui=False, log_level='debug')
            self.log_message(f"📊 {label}", show_in_ui=False, log_level='debug')
            self.log_message(f"{'='*70}", show_in_ui=False, log_level='debug')
            
            # 1. 实际物理内存使用
            rss_mb = mem_info.rss / 1024 / 1024
            vms_mb = mem_info.vms / 1024 / 1024
            self.log_message(f"📦 实际物理内存 (RSS): {rss_mb:.1f} MB", show_in_ui=False, log_level='debug')
            self.log_message(f"📦 虚拟内存 (VMS): {vms_mb:.1f} MB", show_in_ui=False, log_level='debug')
            
            # 2. Python GC统计
            gc_stats = gc.get_stats()
            gc_count = gc.get_count()
            self.log_message(f"\n🗑️  垃圾回收统计:", show_in_ui=False, log_level='debug')
            self.log_message(f"  - 代数统计: Gen0={gc_count[0]}, Gen1={gc_count[1]}, Gen2={gc_count[2]}", show_in_ui=False, log_level='debug')
            
            # 3. Python对象统计
            import sys
            obj_count = len(gc.get_objects())
            self.log_message(f"  - Python对象总数: {obj_count:,}", show_in_ui=False, log_level='debug')
            
            # 4. 如果启用了tracemalloc，显示详细分配
            if self._memory_profiling and tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                # 总内存
                total = sum(stat.size for stat in top_stats)
                self.log_message(f"\n💾 Tracemalloc追踪的内存: {total / 1024 / 1024:.1f} MB", show_in_ui=False, log_level='debug')
                
                # 前10个最大分配
                self.log_message(f"\n📈 内存占用 Top 10:", show_in_ui=False, log_level='debug')
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
                        f"{stat.size / 1024 / 1024:.1f} MB ({stat.count:,} 对象)",
                        show_in_ui=False,
                        log_level='debug'
                    )
            
            self.log_message(f"{'='*70}\n", show_in_ui=False, log_level='debug')
            
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
        """混合模式：单子进程 + 内部多线程处理图片
        
        架构设计：
        - 主进程：GUI + 任务调度
        - 子进程：单个工作进程（内存隔离）
          └─ 多线程：max_workers个线程并行处理
        
        优势：
        1. 内存隔离：子进程与主进程内存完全隔离
        2. 模型共享：OCR模型只加载一次，线程共享
        3. 并行处理：多线程充分利用CPU
        4. 自动回收：子进程结束后内存自动释放
        """
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        self.log_message("=" * 50)
        self.log_message(f"混合处理模式: 1个子进程 + {max_workers} 个工作线程")
        self.log_message(f"待处理图片总数: {total}")
        # 架构细节只记录到日志文件
        logger.info(f"[架构] 主进程(GUI) → 子进程(OCR模型) → 多线程(并行处理)")
        logger.info(f"[优势] 内存隔离 + 模型共享 + 多线程并行")
        self.log_message("=" * 50)
        
        logger.info(f"Starting hybrid processing: 1 subprocess with {max_workers} threads for {total} images")
        
        # 获取配置参数
        enable_ocr = self.ui_vars['enable_ocr_var'].get()
        enable_sentiment = self.ui_vars['enable_sentiment_var'].get()
        use_gpu = self.ui_vars['gpu_enabled_var'].get()
        db_path = self.db.db_path if hasattr(self.db, 'db_path') else 'meme_finder.db'
        
        # 使用单个子进程处理所有图片（内部使用多线程）
        with ProcessPoolExecutor(max_workers=1) as executor:
            # 提交整个图片列表到子进程
            future = executor.submit(
                _process_images_in_subprocess,
                unprocessed,
                enable_ocr,
                enable_sentiment,
                use_gpu,
                db_path,
                max_workers
            )
            
            self.log_message(f"已启动子进程，内部使用 {max_workers} 个线程处理...")
            logger.info(f"Subprocess started with {max_workers} internal threads")
            
            # 等待子进程完成（需要实现进度反馈）
            try:
                # 简单的等待动画
                import time
                while not future.done():
                    if not self.processing:
                        self.log_message("[暂停] 正在终止子进程...")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    # 更新等待提示
                    time.sleep(0.5)
                
                if future.done() and not future.cancelled():
                    # 获取所有结果
                    results = future.result()
                    
                    # 【优化1】分批处理结果，避免一次性保留所有结果对象
                    # 每处理10个结果就释放一次，减少内存峰值
                    batch_size = 10
                    temp_results = []
                    
                    for idx, result in enumerate(results, 1):
                        if not self.processing:
                            break
                        
                        # 提取必要信息后立即释放原始result
                        success = result.get('success', False)
                        img_path = result.get('path', '')
                        filename = Path(img_path).name if img_path else f"图片{idx}"
                        
                        if success:
                            processed_count += 1
                            self.log_message(f"[{idx}/{total}] ✓ {filename}")
                            
                            # 只提取需要显示的信息，不保留整个result对象
                            if 'result' in result and result['result'].get('filtered_text'):
                                preview = result['result']['filtered_text'][:50]
                                if len(result['result']['filtered_text']) > 50:
                                    preview += "..."
                                emotion = result['result'].get('emotion', '')
                                pos = result['result'].get('emotion_positive', 0.0)
                                neg = result['result'].get('emotion_negative', 0.0)
                                self.log_message(f"  文本: {preview}")
                                self.log_message(f"  情绪: {emotion} (正:{pos:.2f}, 负:{neg:.2f})")
                            else:
                                self.log_message(f"  未识别到文本")
                        else:
                            error_count += 1
                            error = result.get('error', '未知错误')
                            # 只显示错误的前100个字符，避免过长
                            error_short = error[:100] + '...' if len(error) > 100 else error
                            self.log_message(f"[{idx}/{total}] ✗ {filename}")
                            self.log_message(f"  错误: {error_short}")
                        
                        # 更新进度
                        completed = idx
                        progress = (completed / total) * 100
                        self.ui_updaters['progress'](progress)
                        self.ui_updaters['progress_label'](
                            f"正在处理: {completed}/{total} (成功:{processed_count}, 失败:{error_count})"
                        )
                        
                        if completed % 10 == 0:
                            self.log_message(f"--- 进度: {completed}/{total} ({progress:.1f}%) | 成功: {processed_count} | 失败: {error_count} ---")
                            logger.info(f"Progress: {completed}/{total} - Success: {processed_count}, Failed: {error_count}")
                            self.ui_updaters['stats']()
                            
                            # 【优化2】每10个结果就强制GC一次，及时回收
                            import gc
                            gc.collect(0)  # 只回收第0代，速度快
                        
                        # 【优化3】显式清理result对象中的大数据
                        if 'result' in result:
                            del result['result']
                        del result
                    
                    # 【优化4】处理完立即释放整个results列表
                    del results
                    import gc
                    gc.collect()  # 完整GC
                    gc.collect(2)  # 再次GC第2代，确保彻底清理
                
            except Exception as e:
                self.log_message(f"[错误] 子进程处理失败: {e}")
                logger.error(f"Subprocess processing failed: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                error_count = total
        
        logger.info(f"Hybrid processing completed: {processed_count} successful, {error_count} failed")
        
        # 混合模式：子进程已退出，内存已释放
        self.log_message(f"\n[INFO] 混合模式处理完成")
        self.log_message(f"[INFO] 子进程已退出，所有内存已释放")
        # 技术细节只记录到日志文件
        logger.info(f"子进程内存（约600MB）已完全释放")
        logger.info(f"子进程内使用了 {max_workers} 个线程并行处理")
        logger.info(f"OCR模型仅加载一次，被所有线程共享")
        
        # 【优化5】多次强制GC，确保主进程内存彻底清理
        # GC信息只记录到日志文件
        logger.info("主进程开始强制垃圾回收...")
        
        # 先清理第0代（最快）
        collected0 = gc.collect(0)
        logger.debug(f"GC generation 0: 回收了 {collected0} 个对象")
        
        # 再清理第1代
        collected1 = gc.collect(1)
        logger.debug(f"GC generation 1: 回收了 {collected1} 个对象")
        
        # 最后清理第2代（最彻底）
        collected2 = gc.collect(2)
        logger.debug(f"GC generation 2: 回收了 {collected2} 个对象")
        
        total_collected = collected0 + collected1 + collected2
        # 只在日志文件中记录详细信息
        logger.info(f"主进程总共回收了 {total_collected} 个对象")
        
        # 打印处理完成时的内存状态（只记录到日志文件）
        self._print_memory_status("多进程处理完成（GC后）")
        
        # 如果主进程中有OCR实例，也调度卸载
        if self.ocr_processor:
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
