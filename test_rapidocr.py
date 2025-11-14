#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 RapidOCR 是否能正常工作"""

import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.core.ocr_processor import OCRProcessor

def test_rapidocr():
    """测试 RapidOCR 初始化和识别"""
    print("=" * 60)
    print("测试 RapidOCR 初始化...")
    print("=" * 60)
    
    try:
        # 初始化 OCR 处理器
        ocr = OCRProcessor(lang='ch', use_gpu=False)
        print("✓ OCR 处理器初始化成功")
        
        # 查找测试图片
        img_dir = Path(__file__).parent / 'img' / 'imgs'
        if not img_dir.exists():
            print(f"警告: 图片目录不存在: {img_dir}")
            return
        
        # 获取第一张图片进行测试
        image_files = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png'))
        if not image_files:
            print(f"警告: 没有找到测试图片在: {img_dir}")
            return
        
        test_image = image_files[0]
        print(f"\n测试图片: {test_image.name}")
        print("=" * 60)
        
        # 处理图片
        result = ocr.process_image(test_image)
        
        print("\n识别结果:")
        print(f"  OCR文本: {result['ocr_text'][:100] if result['ocr_text'] else '(无)'}")
        print(f"  过滤文本: {result['filtered_text'][:100] if result['filtered_text'] else '(无)'}")
        print(f"  情绪: {result['emotion']}")
        print(f"  正向分数: {result['emotion_positive']:.2f}")
        print(f"  负向分数: {result['emotion_negative']:.2f}")
        
        print("\n=" * 60)
        print("✓ 测试完成！RapidOCR 工作正常")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rapidocr()
