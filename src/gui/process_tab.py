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

from ..core.database import ImageDatabase
from ..core.ocr_processor import OCRProcessor


class ProcessTab:
    """图片处理标签页"""
    
    def __init__(self, parent, db: ImageDatabase, stats_callback=None):
        self.parent = parent
        self.db = db
        self.stats_callback = stats_callback  # 用于更新统计信息的回调函数
        
        # OCR处理器（延迟初始化）
        self.ocr_processor = None
        self._ocr_initialized = False
        
        # 处理状态
        self.processing = False
        self.processing_thread = None
        
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
                self.log_message(f"[错误] OCR 初始化失败: {e}")
                messagebox.showerror("错误", f"OCR 初始化失败: {e}")
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
            unprocessed = self.db.get_unprocessed_images(limit=1000)
            
            if not unprocessed:
                self.log_message("[INFO] 没有待处理的图片")
                self.processing = False
                return
            
            total = len(unprocessed)
            self.log_message(f"[INFO] 开始处理 {total} 张图片...")
            
            processed_count = 0
            error_count = 0
            
            for idx, img_info in enumerate(unprocessed, 1):
                if not self.processing:
                    self.log_message("[暂停] 处理已暂停")
                    break
                
                img_id = img_info['id']
                img_path = img_info['file_path']
                
                try:
                    # 更新进度（线程安全）
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
                    
                    # 更新统计信息（调用回调函数）
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
                    self.log_message(f"  [错误] {e}")
                    error_count += 1
                    continue
            
            # 完成
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
            
            # 线程安全地更新UI
            self.frame.after(0, lambda: self.progress_var.set(100))
            self.frame.after(0, lambda: self.progress_label.config(
                text=f"处理完成: 成功 {processed_count}, 失败 {error_count}"))
            self.log_message("=" * 50)
            self.log_message(f"[完成] 处理结束")
            self.log_message(f"  成功: {processed_count} 张")
            self.log_message(f"  失败: {error_count} 张")
            self.log_message("=" * 50)
            
        except Exception as e:
            self.processing = False
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
            self.log_message(f"[错误] 处理线程异常: {e}")
            import traceback
            self.log_message(traceback.format_exc())
    
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
