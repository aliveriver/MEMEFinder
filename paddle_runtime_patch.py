"""
Paddle运行时补丁
在打包环境中确保paddle模块可以被正确导入
注意：设备选择（CPU/GPU）由 OCRProcessor 根据实际情况决定
"""

import sys
import os
from pathlib import Path

def patch_paddle_import():
    """在打包环境中修复paddle模块导入"""
    
    is_frozen = getattr(sys, "frozen", False)
    
    # 在打包环境中，默认设置CPU模式（防止在没有GPU的环境中尝试加载CUDA库）
    # 但如果用户有GPU且想要使用，OCRProcessor会清除这些环境变量
    if is_frozen:
        # 先设置CPU模式作为默认值，避免CUDA错误
        # 如果用户有GPU且想使用，OCRProcessor会清除这些设置
        if 'CUDA_VISIBLE_DEVICES' not in os.environ:
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
        if 'FLAGS_selected_gpus' not in os.environ:
            os.environ['FLAGS_selected_gpus'] = ''
    
    # 在打包环境中，paddle可能位于_internal目录
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller临时目录
        meipass = Path(sys._MEIPASS)
        
        # 尝试添加paddle路径
        paddle_paths = [
            meipass / 'paddle',
            meipass / 'paddlepaddle',
            meipass / '_internal' / 'paddle',
        ]
        
        for paddle_path in paddle_paths:
            if paddle_path.exists() and str(paddle_path.parent) not in sys.path:
                sys.path.insert(0, str(paddle_path.parent))
                print(f"[补丁] 添加paddle路径: {paddle_path.parent}")
    
    # 尝试导入paddle（不强制设置设备，由OCRProcessor决定）
    try:
        import paddle
        # 在打包环境中，默认设置为CPU（避免CUDA错误）
        # 但如果用户有GPU，OCRProcessor会重新设置
        if is_frozen:
            try:
                paddle.set_device('cpu')
                print(f"[补丁] paddle模块导入成功（打包环境，默认CPU模式）")
            except Exception as e:
                print(f"[补丁] 警告: 设置CPU模式失败: {e}")
        else:
            print(f"[补丁] paddle模块导入成功（开发环境）")
        print(f"[补丁] paddle模块路径: {paddle.__file__ if hasattr(paddle, '__file__') else '已导入'}")
    except ImportError as e:
        print(f"[补丁] 警告: paddle模块导入失败: {e}")
        print(f"[补丁] sys.path: {sys.path[:5]}")  # 只显示前5个路径
        # 不抛出异常，让程序继续运行，后续会报错

# 自动应用补丁
if __name__ != "__main__":
    patch_paddle_import()

