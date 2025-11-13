#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder - 表情包查找器
主程序入口
"""

import sys
import os
from pathlib import Path

# === 最最早期的环境变量设置（必须在任何导入之前）===
# 禁用 PaddleX 的依赖检查（打包环境中必需）
os.environ['PADDLEX_DISABLE_DEPS_CHECK'] = '1'
os.environ['PADDLEX_SKIP_PLUGIN_CHECK'] = '1'
os.environ['PADDLEX_SKIP_SERVING_CHECK'] = '1'
os.environ['DISABLE_IMPORTLIB_METADATA_CHECK'] = '1'
# 禁用 PaddleOCR 调用 PaddleX（核心修复）
os.environ['PPOCR_DISABLE_PADDLEX'] = '1'
os.environ['ENABLE_MKLDNN'] = '0'

# 在打包环境中应用补丁
# 首先修复 stdout/stderr 为 None 的问题（必须在所有其他补丁之前）
try:
    import stdout_stderr_patch  # 标准输出/错误流补丁 - 必须在最前面
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import paddlex_runtime_patch  # PaddleX运行时补丁 - 修复依赖检查问题
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import cv2_patch  # cv2补丁
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import snownlp_patch  # snownlp数据文件补丁
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import pyclipper_patch  # pyclipper运行时补丁
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import ocr_model_patch  # OCR模型路径补丁
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import paddlex_patch  # 必须在导入PaddleOCR之前
except ImportError:
    pass  # 开发环境可能没有这个文件

try:
    import paddle_runtime_patch  # paddle运行时补丁
except ImportError:
    pass  # 开发环境可能没有这个文件

# 提前导入关键模块，确保PyInstaller能够检测到
# 必须在导入paddlex/paddleocr之前导入，因为它们的内部模块会使用这些模块
try:
    import cv2  # OpenCV - paddlex内部会使用，必须提前导入
    print(f"[调试] cv2模块已导入")
except ImportError as e:
    print(f"[警告] cv2模块导入失败: {e}")

try:
    import numpy  # NumPy - 多个模块依赖
    print(f"[调试] numpy模块已导入")
except ImportError as e:
    print(f"[警告] numpy模块导入失败: {e}")

# 提前导入pyclipper，确保被PyInstaller收集（PaddleOCR必需）
try:
    import pyclipper
    print(f"[调试] pyclipper模块已导入")
except ImportError as e:
    print(f"[警告] pyclipper模块导入失败: {e}")
    print("[警告] OCR功能可能无法正常工作")

try:
    import paddle  # 确保paddle模块被PyInstaller收集
    print(f"[调试] paddle模块已导入: {paddle.__file__ if hasattr(paddle, '__file__') else '已导入'}")
except ImportError as e:
    print(f"[警告] paddle模块导入失败: {e}")
    # 在打包环境中，这会导致后续错误，但我们需要让PyInstaller检测到
    pass

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
