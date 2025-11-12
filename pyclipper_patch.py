"""
pyclipper运行时补丁
在打包环境中确保pyclipper模块可以被正确导入
"""

import sys
import os
from pathlib import Path

def patch_pyclipper_import():
    """在打包环境中修复pyclipper模块导入"""
    
    if not getattr(sys, "frozen", False):
        # 开发环境无需补丁
        return
    
    # 在打包环境中，pyclipper可能位于_internal目录
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller临时目录
        meipass = Path(sys._MEIPASS)
        
        # 尝试添加pyclipper路径
        pyclipper_paths = [
            meipass / 'pyclipper',
            meipass / '_internal' / 'pyclipper',
        ]
        
        for pyclipper_path in pyclipper_paths:
            if pyclipper_path.exists() and str(pyclipper_path.parent) not in sys.path:
                sys.path.insert(0, str(pyclipper_path.parent))
                print(f"[补丁] 添加pyclipper路径: {pyclipper_path.parent}")
    
    # 尝试导入pyclipper
    try:
        import pyclipper
        print(f"[补丁] pyclipper模块导入成功")
    except ImportError as e:
        print(f"[补丁] 警告: pyclipper模块导入失败: {e}")
        print(f"[补丁] sys.path: {sys.path[:5]}")  # 只显示前5个路径
        # 不抛出异常，让程序继续运行，后续会报错

# 自动应用补丁
if __name__ != "__main__":
    patch_pyclipper_import()

