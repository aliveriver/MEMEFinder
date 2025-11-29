#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProcessTab UI组件模块
负责创建和布局所有UI控件
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class ProcessTabUI:
    """ProcessTab的UI组件管理器"""
    
    def __init__(self, parent_frame):
        """
        初始化UI组件
        
        Args:
            parent_frame: 父框架
        """
        self.frame = parent_frame
        
        # UI组件引用
        self.thread_spinbox = None
        self.multithread_var = None
        self.enable_ocr_var = None
        self.enable_sentiment_var = None
        self.gpu_checkbox = None
        self.gpu_status_label = None
        self.cuda_path_btn = None
        self.progress_var = None
        self.progress_bar = None
        self.progress_label = None
        self.log_text = None
        
    def create_all_widgets(self, callbacks, initial_values):
        """
        创建所有UI组件
        
        Args:
            callbacks: 回调函数字典 {
                'start_processing': func,
                'pause_processing': func,
                'stop_processing': func,
                'check_model_status': func,
                'on_ocr_toggle': func,
                'on_sentiment_toggle': func,
                'on_gpu_toggle': func,
                'configure_cuda_path': func,
                'download_ocr_models': func,
                'download_sentiment_model': func
            }
            initial_values: 初始值字典 {
                'max_workers': int,
                'use_multithread': bool
            }
        """
        # 创建顶部按钮区
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 第一行:基本控制按钮
        self._create_control_row1(btn_frame, callbacks, initial_values)
        
        # 第二行:模型管理按钮
        self._create_control_row2(btn_frame, callbacks)
        
        # 第三行:GPU相关控件
        self._create_control_row3(btn_frame, callbacks)
        
        # 进度信息
        self._create_progress_section()
        
        # 日志输出
        self._create_log_section()
        
    def _create_control_row1(self, parent, callbacks, initial_values):
        """创建第一行控制按钮"""
        control_row1 = ttk.Frame(parent)
        control_row1.pack(fill=tk.X, pady=2)
        
        # 处理控制按钮
        ttk.Button(control_row1, text="▶️ 开始处理", 
                  command=callbacks['start_processing']).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row1, text="⏸️ 暂停", 
                  command=callbacks['pause_processing']).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row1, text="⏹️ 停止", 
                  command=callbacks['stop_processing']).pack(side=tk.LEFT, padx=5)
        
        # 多线程设置
        thread_frame = ttk.Frame(control_row1)
        thread_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(thread_frame, text="并行线程数:").pack(side=tk.LEFT, padx=5)
        self.thread_spinbox = ttk.Spinbox(thread_frame, from_=1, to=16, width=5)
        self.thread_spinbox.set(initial_values['max_workers'])
        self.thread_spinbox.pack(side=tk.LEFT, padx=5)
        
        self.multithread_var = tk.BooleanVar(value=initial_values['use_multithread'])
        ttk.Checkbutton(thread_frame, text="启用混合模式", 
                       variable=self.multithread_var).pack(side=tk.LEFT, padx=5)
    
    def _create_control_row2(self, parent, callbacks):
        """创建第二行:模型管理按钮"""
        control_row2 = ttk.Frame(parent)
        control_row2.pack(fill=tk.X, pady=2)
        
        # 模型状态检查
        ttk.Button(control_row2, text="🔍 检查模型状态", 
                  command=callbacks['check_model_status']).pack(side=tk.LEFT, padx=5)
        
        # OCR开关
        self.enable_ocr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_row2, text="启用OCR", 
                       variable=self.enable_ocr_var,
                       command=callbacks['on_ocr_toggle']).pack(side=tk.LEFT, padx=5)
        
        # 情感分析开关
        self.enable_sentiment_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_row2, text="启用情感分析", 
                       variable=self.enable_sentiment_var,
                       command=callbacks['on_sentiment_toggle']).pack(side=tk.LEFT, padx=5)
        
        # 下载模型按钮
        ttk.Button(control_row2, text="📥 下载OCR模型", 
                  command=callbacks['download_ocr_models']).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row2, text="📥 下载情感分析模型", 
                  command=callbacks['download_sentiment_model']).pack(side=tk.LEFT, padx=5)
    
    def _create_control_row3(self, parent, callbacks):
        """创建第三行:GPU相关控件"""
        control_row3 = ttk.Frame(parent)
        control_row3.pack(fill=tk.X, pady=2)
        
        # GPU加速开关
        self.gpu_enabled_var = tk.BooleanVar(value=False)
        self.gpu_checkbox = ttk.Checkbutton(
            control_row3, 
            text="GPU加速", 
            variable=self.gpu_enabled_var,
            command=callbacks['on_gpu_toggle']
        )
        self.gpu_checkbox.pack(side=tk.LEFT, padx=5)
        
        # GPU状态标签
        self.gpu_status_label = ttk.Label(
            control_row3,
            text="GPU: 检测中...",
            foreground="gray"
        )
        self.gpu_status_label.pack(side=tk.LEFT, padx=5)
        
        # CUDA路径设置按钮(默认隐藏)
        self.cuda_path_btn = ttk.Button(
            control_row3,
            text="⚙️ 设置 CUDA 路径",
            command=callbacks['configure_cuda_path']
        )
        # 默认不pack,由GPU管理器根据情况显示
    
    def _create_progress_section(self):
        """创建进度信息区域"""
        progress_frame = ttk.LabelFrame(self.frame, text="处理进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack()
    
    def _create_log_section(self):
        """创建日志输出区域"""
        log_frame = ttk.LabelFrame(self.frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def get_thread_count(self):
        """获取线程数设置"""
        try:
            return int(self.thread_spinbox.get())
        except:
            return 4
    
    def get_multithread_enabled(self):
        """获取是否启用混合模式（子进程+多线程）"""
        return self.multithread_var.get()
