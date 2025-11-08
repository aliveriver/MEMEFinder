#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试OCR处理器 - 使用真实的PaddleOCR
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import OCRProcessor
from src.core import ImageScanner


def test_ocr():
    """测试OCR功能"""
    print("=" * 60)
    print("测试OCR处理器")
    print("=" * 60)
    
    # 1. 初始化OCR处理器
    print("\n[步骤1] 初始化OCR处理器...")
    try:
        ocr_processor = OCRProcessor(lang='ch', use_gpu=False, det_side=1536)
        print("  ✓ OCR处理器初始化成功")
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return False
    
    # 2. 扫描测试图片
    print("\n[步骤2] 扫描测试图片...")
    scanner = ImageScanner()
    imgs_folder = Path("./imgs")
    
    if not imgs_folder.exists():
        print("  ✗ imgs文件夹不存在")
        return False
    
    images = scanner.scan_folder(str(imgs_folder))
    print(f"  ✓ 发现 {len(images)} 张图片")
    
    if not images:
        print("  ✗ 没有找到图片")
        return False
    
    # 3. 测试OCR识别（只测试前3张）
    print("\n[步骤3] 开始OCR识别（测试前3张）...")
    test_images = images[:3]
    
    for idx, img_path in enumerate(test_images, 1):
        print(f"\n[{idx}/{len(test_images)}] 处理: {img_path.name}")
        
        try:
            result = ocr_processor.process_image(img_path, pad_ratio=0.10)
            
            print(f"  OCR原始文本: {result['ocr_text'][:100] if result['ocr_text'] else '(无)'}")
            print(f"  过滤后文本: {result['filtered_text'][:100] if result['filtered_text'] else '(无)'}")
            print(f"  情绪分类: {result['emotion']}")
            print(f"  正向分数: {result['emotion_positive']:.2f}")
            print(f"  负向分数: {result['emotion_negative']:.2f}")
            
            if result['ocr_text']:
                print("  ✓ OCR识别成功")
            else:
                print("  - 未识别到文本（可能是纯图片）")
            
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_ocr()
