#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder - 表情包查找器
主程序入口
"""

import sys
from pathlib import Path

# 在打包环境中应用PaddleX补丁
try:
    import paddlex_patch  # 必须在导入PaddleOCR之前
except ImportError:
    pass  # 开发环境可能没有这个文件

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
