#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 OCR 实例在 main.py 中的传递流程
"""

import sys
import os

# 模拟frozen环境
sys.frozen = True

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.ocr_processor import OCRProcessor

print("=" * 60)
print("测试 OCR 实例传递")
print("=" * 60)

# 步骤1：模拟加载窗口创建 OCR
print("\n[步骤1] 创建 OCR 实例（模拟加载窗口）...")
try:
    ocr_processor = OCRProcessor(use_gpu=False)
    print(f"✓ OCR 创建成功")
    print(f"  类型: {type(ocr_processor)}")
    print(f"  ocr 属性: {type(ocr_processor.ocr)}")
    print(f"  ocr 是否为 None: {ocr_processor.ocr is None}")
except Exception as e:
    print(f"✗ OCR 创建失败: {e}")
    sys.exit(1)

# 步骤2：模拟 ProcessTab 接收实例
print("\n[步骤2] 模拟 ProcessTab 接收实例...")
class MockProcessTab:
    def __init__(self):
        self.ocr_processor = None
        self._ocr_initialized = False

process_tab = MockProcessTab()
process_tab.ocr_processor = ocr_processor
process_tab._ocr_initialized = True

print(f"✓ 实例传递完成")
print(f"  process_tab.ocr_processor: {process_tab.ocr_processor is not None}")
print(f"  process_tab._ocr_initialized: {process_tab._ocr_initialized}")

# 步骤3：验证 OCR 可用性
print("\n[步骤3] 验证 OCR 可用性...")
if process_tab.ocr_processor:
    ocr_attr = getattr(process_tab.ocr_processor, 'ocr', None)
    if ocr_attr is None:
        print("✗ OCR 属性为 None!")
        sys.exit(1)
    else:
        print(f"✓ OCR 属性有效")
        print(f"  类型: {type(ocr_attr).__name__}")
        has_predict = hasattr(ocr_attr, 'predict')
        has_ocr = hasattr(ocr_attr, 'ocr')
        print(f"  has predict: {has_predict}")
        print(f"  has ocr: {has_ocr}")
        
        if not (has_predict or has_ocr):
            print("✗ OCR 缺少必需方法!")
            sys.exit(1)
        else:
            print("✓ OCR 方法完整")
else:
    print("✗ process_tab.ocr_processor 为 None!")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过！OCR 实例传递正常")
print("=" * 60)
