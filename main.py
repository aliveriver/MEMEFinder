#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder - 表情包查找器
主程序入口 (使用 RapidOCR)
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

import tkinter as tk
from src.gui import MemeFinderGUI
from src.gui.loading_window import ModelLoadingWindow


def main():
    """主函数"""
    # 创建并显示加载窗口
    loading_window = ModelLoadingWindow()
    
    # 用于存储OCR实例和主窗口
    ocr_instance = [None]
    main_window = [None]
    
    def on_load_complete():
        """模型加载完成回调"""
        # 保存OCR实例
        if hasattr(loading_window, '_ocr_instance'):
            ocr_instance[0] = loading_window._ocr_instance
        
        # 关闭加载窗口
        loading_window.close()
        
        # 创建主窗口
        root = tk.Tk()
        main_window[0] = root
        app = MemeFinderGUI(root)
        
        # 将预加载的OCR实例传递给ProcessTab
        if ocr_instance[0]:
            app.process_tab.ocr_processor = ocr_instance[0]
            app.process_tab._ocr_initialized = True
        
        # 启动主循环
        root.mainloop()
    
    def on_load_error(error_msg):
        """模型加载失败回调"""
        from tkinter import messagebox
        
        # 关闭加载窗口
        loading_window.close()
        
        # 显示错误
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "初始化失败",
            f"模型加载失败:\n{error_msg}\n\n程序将继续运行，但OCR功能可能不可用。"
        )
        root.deiconify()
        
        # 创建主窗口
        app = MemeFinderGUI(root)
        root.mainloop()
    
    # 开始加载模型（不使用异步线程，直接在加载窗口的事件循环中）
    loading_window.check_and_load_models(on_load_complete, on_load_error, run_async=True)
    
    # 运行加载窗口的事件循环
    loading_window.window.mainloop()


if __name__ == "__main__":
    main()
