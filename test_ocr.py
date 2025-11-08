#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试OCR功能
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.ocr_processor import OCRProcessor


def test_ocr():
    """测试OCR功能"""
    print("=" * 60)
    print("OCR功能测试")
    print("=" * 60)
    
    # 初始化OCR
    print("\n[步骤1] 初始化OCR处理器...")
    try:
        ocr = OCRProcessor(lang='ch', use_gpu=False, det_side=1536)
        print("✓ OCR初始化成功")
    except Exception as e:
        print(f"✗ OCR初始化失败: {e}")
        print("\n请先运行: python download_ocr_models.py")
        return False
    
    # 查找测试图片
    print("\n[步骤2] 查找测试图片...")
    imgs_dir = Path("imgs")
    
    if not imgs_dir.exists():
        print(f"✗ 图片目录不存在: {imgs_dir}")
        return False
    
    test_images = list(imgs_dir.glob("*.jpg"))[:5]  # 测试前5张
    
    if not test_images:
        print(f"✗ 未找到测试图片")
        return False
    
    print(f"✓ 找到 {len(test_images)} 张测试图片")
    
    # 测试OCR
    print("\n[步骤3] 开始OCR识别...")
    print("-" * 60)
    
    for idx, img_path in enumerate(test_images, 1):
        print(f"\n[{idx}/{len(test_images)}] {img_path.name}")
        
        try:
            result = ocr.process_image(img_path, pad_ratio=0.10)
            
            print(f"  原始文本: {result['ocr_text'][:80] if result['ocr_text'] else '(无)'}")
            print(f"  过滤文本: {result['filtered_text'][:80] if result['filtered_text'] else '(无)'}")
            print(f"  情绪分类: {result['emotion']}")
            print(f"  情绪分数: 正向={result['emotion_positive']:.2f}, 负向={result['emotion_negative']:.2f}")
            
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("✓ OCR功能测试完成")
    print("=" * 60)
    
    return True


def test_text_filter():
    """测试文本过滤功能"""
    print("\n" + "=" * 60)
    print("文本过滤功能测试")
    print("=" * 60)
    
    ocr = OCRProcessor()
    
    test_cases = [
        "这是一个表情包 www.example.com",
        "http://example.com/image.jpg 快乐每一天",
        "微信扫一扫 关注我们 @username",
        "抖音号：123456 #热门",
        "今天天气真好，心情很棒！",
    ]
    
    print()
    for idx, text in enumerate(test_cases, 1):
        filtered = ocr.filter_text(text)
        print(f"[{idx}] 原始: {text}")
        print(f"    过滤: {filtered}")
        print()
    
    print("=" * 60)


def test_emotion_analysis():
    """测试情绪分析功能"""
    print("\n" + "=" * 60)
    print("情绪分析功能测试")
    print("=" * 60)
    
    ocr = OCRProcessor()
    
    test_cases = [
        "今天天气真好，心情很棒！",
        "太难过了，想哭",
        "这个很一般吧",
        "超级开心，笑死我了哈哈哈",
        "讨厌，真烦人",
    ]
    
    print()
    for idx, text in enumerate(test_cases, 1):
        emotion, pos, neg = ocr.analyze_emotion(text)
        print(f"[{idx}] 文本: {text}")
        print(f"    情绪: {emotion} (正向={pos:.2f}, 负向={neg:.2f})")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR功能测试")
    parser.add_argument('--filter', action='store_true', help="测试文本过滤")
    parser.add_argument('--emotion', action='store_true', help="测试情绪分析")
    args = parser.parse_args()
    
    if args.filter:
        test_text_filter()
    elif args.emotion:
        test_emotion_analysis()
    else:
        test_ocr()
