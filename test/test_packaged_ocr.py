#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试打包后的OCR功能
用于验证打包程序是否能正常工作
"""

import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("测试打包环境OCR功能")
print("=" * 60)

# 测试1: 导入基础模块
print("\n[测试1] 导入基础模块...")
try:
    import cv2
    print(f"✓ cv2 已导入: {cv2.__version__}")
except Exception as e:
    print(f"✗ cv2 导入失败: {e}")
    sys.exit(1)

try:
    import numpy as np
    print(f"✓ numpy 已导入: {np.__version__}")
except Exception as e:
    print(f"✗ numpy 导入失败: {e}")
    sys.exit(1)

try:
    import paddle
    print(f"✓ paddle 已导入")
except Exception as e:
    print(f"✗ paddle 导入失败: {e}")
    sys.exit(1)

# 测试2: 导入PaddleOCR
print("\n[测试2] 导入PaddleOCR...")
try:
    from paddleocr import PaddleOCR
    print("✓ PaddleOCR 已导入")
except Exception as e:
    print(f"✗ PaddleOCR 导入失败: {e}")
    sys.exit(1)

# 测试3: 创建OCR实例
print("\n[测试3] 创建OCR实例...")
try:
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    print("✓ OCR 实例创建成功")
except Exception as e:
    print(f"✗ OCR 实例创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: 测试OCR处理器
print("\n[测试4] 测试OCR处理器...")
try:
    from src.core.ocr_processor import OCRProcessor
    print("✓ OCRProcessor 模块导入成功")
    
    processor = OCRProcessor(use_gpu=False)
    print("✓ OCRProcessor 实例创建成功")
except Exception as e:
    print(f"✗ OCRProcessor 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("所有测试通过！OCR功能正常")
print("=" * 60)
