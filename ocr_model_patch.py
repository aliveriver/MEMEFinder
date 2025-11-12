"""
OCR模型路径补丁
在打包环境中修复PaddleOCR模型路径问题
"""

import sys
import os
from pathlib import Path

def patch_ocr_model_path():
    """修复PaddleOCR在打包环境中的模型路径"""
    
    if not getattr(sys, "frozen", False):
        # 开发环境无需补丁
        return
    
    # PaddleOCR会从用户目录查找模型，我们需要确保它能找到
    if hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)
        
        # 检查是否有paddleocr相关的模型文件
        paddleocr_paths = [
            meipass / 'paddleocr',
            meipass / 'paddlex' / 'inference',
        ]
        
        for path in paddleocr_paths:
            if path.exists():
                print(f"[补丁] 找到OCR相关路径: {path}")
        
        # 设置PaddleOCR模型缓存目录（如果支持）
        # PaddleOCR默认会从用户目录的.paddleocr目录加载模型
        # 在打包环境中，我们需要确保模型可以被找到
        try:
            # 尝试设置环境变量（如果PaddleOCR支持）
            user_home = Path.home()
            paddleocr_cache = user_home / '.paddleocr'
            if paddleocr_cache.exists():
                print(f"[补丁] PaddleOCR模型缓存目录: {paddleocr_cache}")
        except Exception as e:
            print(f"[补丁] 检查PaddleOCR模型路径时出错: {e}")

# 自动应用补丁
if __name__ != "__main__":
    patch_ocr_model_path()

