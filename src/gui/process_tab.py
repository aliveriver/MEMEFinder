#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理标签页
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from pathlib import Path
import threading
import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

from ..core.database import ImageDatabase
from ..core.ocr_processor import OCRProcessor
from ..utils.logger import get_logger

logger = get_logger()


class ProcessTab:
    """图片处理标签页"""
    
    def __init__(self, parent, db: ImageDatabase, stats_callback=None):
        self.parent = parent
        self.db = db
        self.stats_callback = stats_callback  # 用于更新统计信息的回调函数
        
        # OCR处理器（延迟初始化）
        self.ocr_processor: Optional[OCRProcessor] = None
        self._ocr_initialized = False
        
        # 处理状态
        self.processing = False
        self.processing_thread = None
        
        # 多线程配置
        self.max_workers = 4  # 默认4个工作线程
        self.use_multithread = True  # 是否启用多线程
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def _should_use_gpu(self) -> bool:
        """
        检查是否应该使用GPU
        
        优先级：
        1. 环境变量 MEMEFINDER_USE_GPU (1/true/yes 启用，0/false/no 禁用)
        2. 自动检测GPU是否可用
        
        Returns:
            bool: 是否使用GPU
        """
        from ..utils.gpu_detector import should_use_gpu
        return should_use_gpu()
    
    def create_widgets(self):
        """创建界面组件"""
        # 顶部按钮区
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="▶️ 开始处理", 
                  command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏸️ 暂停", 
                  command=self.pause_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹️ 停止", 
                  command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        
        # 多线程设置
        thread_frame = ttk.Frame(btn_frame)
        thread_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(thread_frame, text="并行线程数:").pack(side=tk.LEFT, padx=5)
        self.thread_spinbox = ttk.Spinbox(thread_frame, from_=1, to=16, width=5)
        self.thread_spinbox.set(self.max_workers)
        self.thread_spinbox.pack(side=tk.LEFT, padx=5)
        
        self.multithread_var = tk.BooleanVar(value=self.use_multithread)
        ttk.Checkbutton(thread_frame, text="启用多线程", 
                       variable=self.multithread_var).pack(side=tk.LEFT, padx=5)
        
        # 进度信息
        progress_frame = ttk.LabelFrame(self.frame, text="处理进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack()
        
        # 日志输出
        log_frame = ttk.LabelFrame(self.frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _initialize_ocr(self):
        """初始化OCR处理器（如果尚未初始化）"""
        if self._ocr_initialized and self.ocr_processor:
            return True
        
        # 如果没有预加载的实例，则现在加载
        if self.ocr_processor is None:
            try:
                self.log_message("[INFO] 正在初始化 OCR 模型...")
                from pathlib import Path
                
                # 获取项目根目录的models文件夹
                project_root = Path(__file__).parent.parent.parent
                model_dir = project_root / 'models'
                
                # 使用自动GPU检测和指定的模型目录
                self.ocr_processor = OCRProcessor(use_gpu=None, model_dir=model_dir)
                self._ocr_initialized = True
                self.log_message("[INFO] OCR 模型加载完成")
                return True
            except Exception as e:
                error_msg = f"OCR 初始化失败: {e}"
                self.log_message(f"[错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                logger.debug(traceback.format_exc())
                messagebox.showerror("错误", error_msg)
                return False
        else:
            # 已经有预加载的实例
            self._ocr_initialized = True
            self.log_message("[INFO] 使用预加载的 OCR 模型")
            return True
    
    def start_processing(self):
        """开始处理图片"""
        if self.processing:
            messagebox.showinfo("提示", "正在处理中...")
            return
        
        unprocessed = self.db.get_unprocessed_images(limit=1)
        if not unprocessed:
            messagebox.showinfo("提示", "没有待处理的图片")
            return
        
        # 首次运行时初始化OCR
        if not self._ocr_initialized:
            if not self._initialize_ocr():
                return  # 初始化失败，不继续处理
        
        # 标记应用状态为正在运行（用于断点恢复）
        try:
            self.db.set_app_state('processing_state', 'running')
        except Exception:
            pass
         
        self.processing = True
        self.log_message("=" * 50)
        self.log_message("开始处理图片...")
        self.log_message("=" * 50)
        
        # 在单独线程中处理
        self.processing_thread = threading.Thread(target=self.process_images_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def pause_processing(self):
        """暂停处理"""
        if self.processing:
            self.processing = False
            self.log_message("[暂停] 处理已暂停")
            try:
                self.db.set_app_state('processing_state', 'paused')
            except Exception:
                pass
     
    def stop_processing(self):
        """停止处理"""
        if self.processing:
            self.processing = False
            self.log_message("[停止] 处理已停止")
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
    
    def process_images_thread(self):
        """处理图片的线程"""
        try:
            # 获取未处理的图片
            unprocessed = self.db.get_unprocessed_images(limit=10000)
            
            if not unprocessed:
                self.log_message("[INFO] 没有待处理的图片")
                self.processing = False
                return
            
            total = len(unprocessed)
            
            # 读取用户设置的线程数
            try:
                max_workers = int(self.thread_spinbox.get())
                max_workers = max(1, min(16, max_workers))  # 限制在1-16之间
            except:
                max_workers = self.max_workers
            
            use_multithread = self.multithread_var.get()
            
            if use_multithread and max_workers > 1:
                self.log_message(f"[INFO] 使用多线程模式，{max_workers} 个并行工作线程")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self._process_images_multithread(unprocessed, max_workers)
            else:
                self.log_message(f"[INFO] 使用单线程模式")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self._process_images_singlethread(unprocessed)
            
        except Exception as e:
            self.processing = False
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
            error_msg = f"处理线程异常: {e}"
            self.log_message(f"[错误] {error_msg}")
            logger.error(error_msg)
            import traceback
            traceback_str = traceback.format_exc()
            self.log_message(traceback_str)
            logger.debug(traceback_str)
    
    def _process_single_image(self, img_info):
        """处理单张图片的工作函数"""
        img_id = img_info['id']
        img_path = img_info['file_path']
        
        try:
            # 检查文件是否存在
            if not Path(img_path).exists():
                return {
                    'success': False,
                    'id': img_id,
                    'path': img_path,
                    'error': '文件不存在'
                }
            
            # OCR识别和情绪分析
            assert self.ocr_processor is not None, "OCR处理器未初始化"
            result = self.ocr_processor.process_image(Path(img_path))
            
            # 更新数据库
            self.db.update_image_data(
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
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': str(e)
            }
    
    def _process_images_multithread(self, unprocessed, max_workers):
        """多线程处理图片"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        # 用于跟踪任务提交和完成的计数器
        import threading
        progress_lock = threading.Lock()
        
        self.log_message("=" * 50)
        self.log_message(f"多线程处理模式: {max_workers} 个工作线程")
        self.log_message(f"待处理图片总数: {total}")
        self.log_message("=" * 50)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_img = {
                executor.submit(self._process_single_image, img_info): (idx, img_info)
                for idx, img_info in enumerate(unprocessed, 1)
            }
            
            self.log_message(f"已提交 {len(future_to_img)} 个处理任务到线程池")
            
            # 处理完成的任务
            for future in as_completed(future_to_img):
                if not self.processing:
                    self.log_message("[暂停] 处理已暂停，取消剩余任务...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                idx, img_info = future_to_img[future]
                img_path = img_info['file_path']
                
                try:
                    task_result = future.result()
                    
                    # 线程安全地更新计数器
                    with progress_lock:
                        if task_result['success']:
                            processed_count += 1
                        else:
                            error_count += 1
                        completed = processed_count + error_count
                    
                    # 更新进度
                    progress = (completed / total) * 100
                    self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                    self.frame.after(0, lambda t=f"正在处理: {completed}/{total} (成功:{processed_count}, 失败:{error_count})": 
                                    self.progress_label.config(text=t))
                    
                    if task_result['success']:
                        result = task_result['result']
                        
                        # 日志输出
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
                    
                    # 定期更新统计信息
                    if completed % 5 == 0 and self.stats_callback:
                        try:
                            self.frame.after(0, self.stats_callback)
                        except Exception:
                            pass
                    
                    # 每处理10张图片输出一次进度摘要
                    if completed % 10 == 0:
                        self.log_message(f"--- 进度: {completed}/{total} ({progress:.1f}%) | 成功: {processed_count} | 失败: {error_count} ---")
                    
                except Exception as e:
                    with progress_lock:
                        error_count += 1
                        completed = processed_count + error_count
                    
                    filename = Path(img_path).name
                    self.log_message(f"[{completed}/{total}] ✗ {filename}")
                    self.log_message(f"  异常: {str(e)}")
                    logger.error(f"处理图片失败 [{filename}]: {e}")
        
        # 完成处理
        self._finish_processing(processed_count, error_count)
    
    def _process_images_singlethread(self, unprocessed):
        """单线程处理图片（原有逻辑）"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        for idx, img_info in enumerate(unprocessed, 1):
            if not self.processing:
                self.log_message("[暂停] 处理已暂停")
                break
            
            img_id = img_info['id']
            img_path = img_info['file_path']
            
            try:
                # 更新进度
                progress = (idx / total) * 100
                self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                self.frame.after(0, lambda t=f"正在处理: {idx}/{total} - {Path(img_path).name}": 
                                self.progress_label.config(text=t))
                
                self.log_message(f"[{idx}/{total}] 处理: {Path(img_path).name}")
                
                # 检查文件是否存在
                if not Path(img_path).exists():
                    self.log_message(f"  [跳过] 文件不存在: {img_path}")
                    error_count += 1
                    continue
                
                # OCR识别和情绪分析
                assert self.ocr_processor is not None, "OCR处理器未初始化"
                result = self.ocr_processor.process_image(Path(img_path))
                
                # 更新数据库
                self.db.update_image_data(
                    image_id=img_id,
                    ocr_text=result['ocr_text'],
                    filtered_text=result['filtered_text'],
                    emotion=result['emotion'],
                    pos_score=result['emotion_positive'],
                    neg_score=result['emotion_negative']
                )
                
                # 更新统计信息
                if self.stats_callback:
                    try:
                        self.frame.after(0, self.stats_callback)
                    except Exception:
                        pass
                
                # 日志输出
                if result['filtered_text']:
                    self.log_message(f"  ✓ 识别文本: {result['filtered_text'][:50]}")
                    self.log_message(f"  ✓ 情绪分类: {result['emotion']} (正:{result['emotion_positive']:.2f}, 负:{result['emotion_negative']:.2f})")
                else:
                    self.log_message(f"  - 未识别到文本")
                
                processed_count += 1
                
            except Exception as e:
                error_msg = f"处理图片失败 [{Path(img_path).name}]: {e}"
                self.log_message(f"  [错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                logger.debug(traceback.format_exc())
                error_count += 1
                continue
        
        # 完成处理
        self._finish_processing(processed_count, error_count)
    
    def _finish_processing(self, processed_count, error_count):
        """完成处理的收尾工作"""
        self.processing = False
        try:
            self.db.set_app_state('processing_state', 'idle')
        except Exception:
            pass
        
        # 最后一次更新统计信息
        if self.stats_callback:
            try:
                self.frame.after(0, self.stats_callback)
            except Exception:
                pass
        
        # 更新UI
        self.frame.after(0, lambda: self.progress_var.set(100))
        self.frame.after(0, lambda: self.progress_label.config(
            text=f"处理完成: 成功 {processed_count}, 失败 {error_count}"))
        self.log_message("=" * 50)
        self.log_message(f"[完成] 处理结束")
        self.log_message(f"  成功: {processed_count} 张")
        self.log_message(f"  失败: {error_count} 张")
        self.log_message("=" * 50)
    
    def log_message(self, message: str):
        """添加日志消息（线程安全）"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
        
        # 如果在主线程中，直接执行；否则使用 after 调度到主线程
        try:
            self.frame.after(0, _log)
        except:
            # 如果 after 失败，尝试直接执行（可能是在主线程中）
            try:
                _log()
            except:
                pass  # 静默失败，避免崩溃
