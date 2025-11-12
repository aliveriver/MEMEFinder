#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder - 表情包查找器
主程序入口
"""

import sys
from pathlib import Path

# 在打包环境中应用补丁
# 首先修复 stdout/stderr 为 None 的问题（必须在所有其他补丁之前）
try:
    import stdout_stderr_patch  # 标准输出/错误流补丁 - 必须在最前面
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


def main():
    """主函数"""
    root = tk.Tk()
    app = MemeFinderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
