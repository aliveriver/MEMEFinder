#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试：验证修复后的OCR参数
"""
import sys
import os

# 模拟打包环境
sys.frozen = True

# 设置环境变量（与main.py一致）
os.environ['PPOCR_DISABLE_PADDLEX'] = '1'
os.environ['ENABLE_MKLDNN'] = '0'

print("=" * 60)
print("测试 OCRProcessor 最小配置（模拟打包环境）")
print("=" * 60)

try:
    from src.core.ocr_processor import OCRProcessor
    print("\n✓ OCRProcessor 导入成功")
    
    print("\n正在初始化 OCRProcessor...")
    processor = OCRProcessor(use_gpu=False)
    
    print("\n✓✓✓ 成功！OCR 初始化完成，没有任何错误！")
    print(f"✓ OCR 实例: {type(processor.ocr)}")
    print("\n问题已彻底解决！可以打包了！")
    
except Exception as e:
    print(f"\n✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
