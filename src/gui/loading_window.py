#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
加载窗口 - macOS风格的优雅加载界面
用于显示模型下载和加载进度
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from pathlib import Path
from typing import Optional, Callable


class LoadingWindow:
    """
    macOS风格的加载窗口
    
    特点：
    - 简洁优雅的设计
    - 圆角效果（通过样式实现）
    - 柔和的颜色
    - 流畅的动画
    - 半透明效果
    """
    
    def __init__(self, parent=None, title: str = "加载中", message: str = "正在准备..."):
        """
        初始化加载窗口
        
        Args:
            parent: 父窗口，如果为None则创建独立窗口
            title: 窗口标题
            message: 初始消息
        """
        # 创建顶层窗口
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
        
        self.window.title(title)
        
        # 设置窗口大小和位置（小巧精致）
        window_width = 400
        window_height = 200
        
        # 居中显示
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 窗口设置
        self.window.resizable(False, False)
        self.window.overrideredirect(False)  # 保留标题栏，更符合Windows习惯
        
        # 设置为模态窗口
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        # macOS风格的颜色方案
        self.colors = {
            'bg': '#F5F5F7',           # 浅灰背景
            'fg': '#1D1D1F',           # 深灰文字
            'accent': '#007AFF',       # 蓝色强调
            'progress_bg': '#E5E5E7',  # 进度条背景
            'progress_fg': '#007AFF',  # 进度条前景
            'secondary': '#86868B',    # 次要文字
        }
        
        # 设置背景色
        self.window.configure(bg=self.colors['bg'])
        
        # 状态变量
        self.is_downloading = False
        self.progress_value = 0.0
        self.message_text = message
        self.detail_text = ""
        
        # 创建界面
        self._create_widgets()
        
        # 更新UI
        self.window.update()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器 - 增加内边距
        main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # 标题/消息标签（大号）
        self.message_label = tk.Label(
            main_frame,
            text=self.message_text,
            font=('SF Pro Display', 16, 'normal'),  # macOS系统字体
            fg=self.colors['fg'],
            bg=self.colors['bg'],
            anchor='center'
        )
        self.message_label.pack(pady=(0, 20))
        
        # 进度条容器
        progress_container = tk.Frame(main_frame, bg=self.colors['bg'])
        progress_container.pack(fill=tk.X, pady=(0, 15))
        
        # 配置进度条样式
        style = ttk.Style()
        
        # macOS风格的进度条
        style.theme_use('default')
        style.configure(
            'macOS.Horizontal.TProgressbar',
            troughcolor=self.colors['progress_bg'],
            background=self.colors['progress_fg'],
            bordercolor=self.colors['bg'],
            lightcolor=self.colors['progress_fg'],
            darkcolor=self.colors['progress_fg'],
            thickness=6  # 较细的进度条
        )
        
        # 进度条 - 使用determinate模式以显示具体进度
        self.progress_bar = ttk.Progressbar(
            progress_container,
            style='macOS.Horizontal.TProgressbar',
            mode='determinate',
            maximum=100,
            value=0
        )
        self.progress_bar.pack(fill=tk.X, ipady=3)
        
        # 进度百分比标签
        self.percent_label = tk.Label(
            main_frame,
            text="0%",
            font=('SF Pro Display', 12),
            fg=self.colors['secondary'],
            bg=self.colors['bg']
        )
        self.percent_label.pack(pady=(0, 10))
        
        # 详细信息标签（小号，次要文字）
        self.detail_label = tk.Label(
            main_frame,
            text=self.detail_text,
            font=('SF Pro Display', 10),
            fg=self.colors['secondary'],
            bg=self.colors['bg'],
            wraplength=340,  # 自动换行
            justify='center'
        )
        self.detail_label.pack()
    
    def set_message(self, message: str):
        """
        设置主要消息
        
        Args:
            message: 消息文本
        """
        self.message_text = message
        self.message_label.config(text=message)
        self.window.update()
    
    def set_detail(self, detail: str):
        """
        设置详细信息
        
        Args:
            detail: 详细信息文本
        """
        self.detail_text = detail
        self.detail_label.config(text=detail)
        self.window.update()
    
    def set_progress(self, value: float, message: str = None, detail: str = None):
        """
        设置进度值
        
        Args:
            value: 进度值（0-100）
            message: 可选的消息文本
            detail: 可选的详细信息
        """
        self.progress_value = max(0, min(100, value))
        self.progress_bar['value'] = self.progress_value
        self.percent_label.config(text=f"{int(self.progress_value)}%")
        
        if message:
            self.set_message(message)
        
        if detail:
            self.set_detail(detail)
        
        self.window.update()
    
    def set_indeterminate(self, message: str = "正在加载..."):
        """
        设置为不确定模式（循环动画）
        
        Args:
            message: 消息文本
        """
        self.set_message(message)
        self.progress_bar.configure(mode='indeterminate')
        self.progress_bar.start(10)  # 开始动画
        self.percent_label.config(text="")  # 隐藏百分比
        self.window.update()
    
    def set_determinate(self):
        """设置为确定模式（显示具体进度）"""
        self.progress_bar.stop()  # 停止动画
        self.progress_bar.configure(mode='determinate')
        self.percent_label.config(text=f"{int(self.progress_value)}%")
        self.window.update()
    
    def close(self):
        """关闭窗口"""
        try:
            if self.window:
                self.window.destroy()
        except:
            pass
    
    def show(self):
        """显示窗口"""
        self.window.deiconify()
        self.window.update()


class ModelLoadingWindow(LoadingWindow):
    """
    模型加载专用窗口
    
    功能：
    1. 检查模型是否存在
    2. 如果不存在，显示下载进度
    3. 如果存在，显示加载进度
    """
    
    def __init__(self, parent=None):
        """初始化模型加载窗口"""
        super().__init__(parent, title="初始化模型", message="正在检查模型...")
        
        self.download_thread = None
        self.load_thread = None
        self.on_complete_callback = None
        self.on_error_callback = None
    
    def check_and_load_models(
        self,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable[[str], None]] = None,
        run_async: bool = True
    ):
        """
        检查并加载模型
        
        Args:
            on_complete: 完成回调函数
            on_error: 错误回调函数（参数为错误消息）
            run_async: 是否在后台线程运行（True），还是在主线程运行（False）
        """
        self.on_complete_callback = on_complete
        self.on_error_callback = on_error
        
        if run_async:
            # 在单独线程中执行，避免阻塞UI
            thread = threading.Thread(target=self._check_and_load_thread, daemon=True)
            thread.start()
        else:
            # 在主线程中执行（用于启动时加载）
            self._check_and_load_thread()
    
    def _check_and_load_thread(self):
        """检查和加载线程"""
        try:
            # 步骤1：检查PaddleOCR模型
            self.set_progress(10, "正在检查模型...", "检查 PaddleOCR 模型是否已下载")
            
            models_exist = self._check_models_exist()
            
            if not models_exist:
                # 需要下载模型
                self.set_progress(20, "正在下载模型...", "首次使用需要下载 OCR 模型，请稍候...")
                self._download_models()
            else:
                # 模型已存在
                self.set_progress(30, "模型已就绪", "开始加载模型...")
            
            # 步骤2：加载OCR模型
            self._load_ocr_model()
            
            # 步骤3：加载情感分析模型（可选）
            self._load_sentiment_model()
            
            # 完成
            self.set_progress(100, "加载完成", "模型已就绪")
            time.sleep(0.5)  # 短暂显示完成状态
            
            # 执行完成回调
            if self.on_complete_callback:
                self.window.after(100, self.on_complete_callback)
            
        except Exception as e:
            error_msg = f"模型加载失败: {str(e)}"
            self.set_message("加载失败")
            self.set_detail(error_msg)
            
            if self.on_error_callback:
                self.window.after(100, lambda: self.on_error_callback(error_msg))
            
            # 延迟关闭，让用户看到错误信息
            time.sleep(3)
    
    def _check_models_exist(self) -> bool:
        """
        检查模型是否已下载
        
        Returns:
            bool: 模型是否存在
        """
        try:
            # 检查PaddleOCR默认模型路径
            # PaddleOCR会将模型下载到用户目录下的 .paddleocr 文件夹
            from pathlib import Path
            import os
            
            # 获取用户主目录
            home_dir = Path.home()
            paddleocr_dir = home_dir / '.paddleocr'
            
            # 检查常见的模型目录
            model_paths = [
                paddleocr_dir / '2.6' / 'ocr' / 'det' / 'ch',  # 检测模型
                paddleocr_dir / '2.6' / 'ocr' / 'rec' / 'ch',  # 识别模型
                paddleocr_dir / 'whl',  # 其他模型
            ]
            
            # 如果任何一个路径存在且包含文件，则认为模型已下载
            for model_path in model_paths:
                if model_path.exists() and any(model_path.iterdir()):
                    return True
            
            return False
            
        except Exception as e:
            # 如果检查失败，假设模型不存在
            return False
    
    def _download_models(self):
        """下载模型（模拟进度）"""
        # 注意：实际下载会在PaddleOCR初始化时自动进行
        # 这里只是模拟进度显示
        
        progress_steps = [
            (30, "正在下载检测模型...", "下载 ch_PP-OCRv3_det"),
            (50, "正在下载识别模型...", "下载 ch_PP-OCRv3_rec"),
            (70, "正在下载方向分类器...", "下载 ch_ppocr_mobile_v2.0_cls"),
        ]
        
        for progress, message, detail in progress_steps:
            self.set_progress(progress, message, detail)
            time.sleep(0.5)  # 模拟下载时间
    
    def _load_ocr_model(self):
        """加载OCR模型"""
        try:
            self.set_progress(75, "正在加载 OCR 模型...", "初始化 PaddleOCR")
            
            # 实际加载OCR模型
            from ..core.ocr_processor import OCRProcessor
            import os
            
            # 检查是否启用GPU
            env_use_gpu = os.environ.get('MEMEFINDER_USE_GPU', '').lower()
            use_gpu = env_use_gpu in ('1', 'true', 'yes', 'on')
            
            # 创建OCR处理器实例（这会触发实际的模型加载）
            self._ocr_instance = OCRProcessor(use_gpu=use_gpu)
            
            self.set_progress(90, "OCR 模型加载完成", "")
            
        except Exception as e:
            raise Exception(f"OCR模型加载失败: {e}")
    
    def _load_sentiment_model(self):
        """加载情感分析模型（可选）"""
        try:
            self.set_progress(95, "正在检查情感分析模型...", "SnowNLP / TextBlob")
            
            # 检查是否安装了情感分析库
            has_snownlp = False
            has_textblob = False
            
            try:
                import snownlp
                has_snownlp = True
            except ImportError:
                pass
            
            try:
                import textblob
                has_textblob = True
            except ImportError:
                pass
            
            if has_snownlp:
                self.set_detail("使用 SnowNLP 进行情感分析")
            elif has_textblob:
                self.set_detail("使用 TextBlob 进行情感分析")
            else:
                self.set_detail("使用关键词方法进行情感分析")
            
            time.sleep(0.5)
            
        except Exception as e:
            # 情感分析失败不影响主流程
            pass


def show_model_loading(parent=None, on_complete=None, on_error=None):
    """
    便捷函数：显示模型加载窗口
    
    Args:
        parent: 父窗口
        on_complete: 完成回调
        on_error: 错误回调
    
    Returns:
        ModelLoadingWindow: 加载窗口实例
    """
    window = ModelLoadingWindow(parent)
    window.check_and_load_models(on_complete, on_error)
    return window


# 测试代码
if __name__ == "__main__":
    def on_complete():
        print("模型加载完成！")
    
    def on_error(error_msg):
        print(f"错误: {error_msg}")
    
    # 创建测试窗口
    window = ModelLoadingWindow()
    window.check_and_load_models(on_complete, on_error)
    window.window.mainloop()
