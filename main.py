#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder - 表情包查找器
主程序入口 (使用 RapidOCR)
"""

import sys
import os
from pathlib import Path

# 设置Windows任务栏图标（必须在创建任何窗口之前）
if sys.platform == 'win32':
    try:
        import ctypes
        # 设置应用程序ID，这样Windows会使用我们的图标
        myappid = 'aliveriver.memefinder.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

# 应用运行时补丁 - 必须在导入其他模块之前执行
try:
    # 标准输出重定向补丁（避免打包后的控制台输出问题）
    import stdout_stderr_patch
except:
    pass

try:
    # SnowNLP 数据路径补丁（确保打包后能加载情绪分析模型）
    import snownlp_runtime_patch
except:
    pass

# 添加src目录到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

import tkinter as tk
from src.gui import MemeFinderGUI


def main():
    """主函数"""
    # 直接创建主窗口，不预加载OCR模型
    # OCR模型将在用户点击"开始处理"时才加载（真正的延迟加载）
    root = tk.Tk()
    app = MemeFinderGUI(root)
    
    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    # Windows多进程支持 - 必须在主入口设置
    # 这确保子进程不会重新执行main()
    import multiprocessing
    multiprocessing.freeze_support()  # PyInstaller打包必需
    
    main()
