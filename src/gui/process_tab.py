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
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        
        # 检查是否启用GPU（通过环境变量或配置）
        use_gpu = self._should_use_gpu()
        self.ocr_processor = OCRProcessor(use_gpu=use_gpu)
        
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
        2. 默认 False (使用CPU)
        
        Returns:
            bool: 是否使用GPU
        """
        # 检查环境变量
        env_use_gpu = os.environ.get('MEMEFINDER_USE_GPU', '').lower()
        if env_use_gpu in ('1', 'true', 'yes', 'on'):
            return True
        elif env_use_gpu in ('0', 'false', 'no', 'off', ''):
            return False
        
        # 默认使用CPU
        return False
    
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
    
    def start_processing(self):
        """开始处理图片"""
        if self.processing:
            messagebox.showinfo("提示", "正在处理中...")
            return
        
        unprocessed = self.db.get_unprocessed_images(limit=1)
        if not unprocessed:
            messagebox.showinfo("提示", "没有待处理的图片")
            return
        
        # 标记应用状态为正在运行（用于断点恢复）
        try:
            self.db.set_app_state('processing_state', 'running')
        except Exception:
            pass
         
        self.processing = True
        self.log_message("=" * 50)
        self.log_message("准备开始处理图片...")
        self.log_message("注意: OCR和情绪分析功能将在下一步实现")
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
                    # 更新进度
                    progress = (idx / total) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"正在处理: {idx}/{total} - {Path(img_path).name}")
                    
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
            self.progress_var.set(100)
            self.progress_label.config(text=f"处理完成: 成功 {processed_count}, 失败 {error_count}")
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
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
