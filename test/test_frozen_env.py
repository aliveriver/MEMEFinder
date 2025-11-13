#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 模拟打包环境
用于在不打包的情况下测试补丁是否有效
"""

import sys
import os

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 模拟打包环境
sys.frozen = True
sys._MEIPASS = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("模拟打包环境测试")
print("=" * 60)

# 加载补丁
print("\n[1] 加载运行时补丁...")
try:
    import paddlex_runtime_patch
    print("✓ 补丁加载成功")
except Exception as e:
    print(f"✗ 补丁加载失败: {e}")
    import traceback
    traceback.print_exc()

# 测试导入PaddleOCR
print("\n[2] 测试导入PaddleOCR...")
try:
    from paddleocr import PaddleOCR
    print("✓ PaddleOCR 导入成功")
except Exception as e:
    print(f"✗ PaddleOCR 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试创建OCR实例
print("\n[3] 测试创建OCR实例...")
try:
    ocr = PaddleOCR(lang='ch')
    print("✓ OCR 实例创建成功")
except Exception as e:
    print(f"✗ OCR 实例创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试OCRProcessor
print("\n[4] 测试OCRProcessor...")
try:
    from src.core.ocr_processor import OCRProcessor
    processor = OCRProcessor(use_gpu=False)
    print("✓ OCRProcessor 创建成功")
except Exception as e:
    print(f"✗ OCRProcessor 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过！")
print("=" * 60)
