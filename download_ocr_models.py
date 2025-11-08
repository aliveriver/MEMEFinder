#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaddleOCR 模型下载和初始化脚本
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.ocr_processor import OCRProcessor


def download_models():
    """
    下载PaddleOCR模型
    首次运行会自动下载模型到 ~/.paddleocr/
    """
    print("=" * 60)
    print("PaddleOCR 模型下载和初始化")
    print("=" * 60)
    print()
    print("首次使用会自动下载以下模型：")
    print("  1. 文本检测模型 (PP-OCRv4/v5)")
    print("  2. 文本识别模型 (PP-OCRv4/v5)")
    print("  3. 方向分类器模型")
    print()
    print("模型将下载到: ~/.paddleocr/")
    print("约需要: 30-50MB 空间")
    print()
    
    try:
        print("[步骤1] 初始化中文OCR模型...")
        ocr = OCRProcessor(lang='ch', use_gpu=False, det_side=1536)
        print("✓ 中文OCR模型初始化成功")
        print()
        
        # 测试OCR
        print("[步骤2] 测试OCR功能...")
        test_imgs = list(Path("imgs").glob("*.jpg"))
        
        if test_imgs:
            test_img = test_imgs[0]
            print(f"  测试图片: {test_img.name}")
            
            result = ocr.process_image(test_img)
            
            print(f"  ✓ OCR识别成功")
            print(f"    原始文本: {result['ocr_text'][:100] if result['ocr_text'] else '(无)'}")
            print(f"    过滤文本: {result['filtered_text'][:100] if result['filtered_text'] else '(无)'}")
            print(f"    情绪分类: {result['emotion']}")
            print(f"    正向分数: {result['emotion_positive']:.2f}")
            print(f"    负向分数: {result['emotion_negative']:.2f}")
        else:
            print("  - 未找到测试图片，跳过测试")
        
        print()
        print("=" * 60)
        print("✓ 模型下载和初始化完成！")
        print("=" * 60)
        print()
        print("现在可以运行主程序:")
        print("  python main.py")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ 初始化失败！")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        print("可能的原因:")
        print("  1. 未安装 paddleocr: pip install paddleocr")
        print("  2. 网络连接问题，无法下载模型")
        print("  3. 磁盘空间不足")
        print()
        return False


def show_model_info():
    """显示模型信息"""
    import os
    
    print("\n" + "=" * 60)
    print("模型存储位置")
    print("=" * 60)
    
    home = Path.home()
    paddle_dir = home / ".paddleocr"
    
    if paddle_dir.exists():
        print(f"✓ 模型目录: {paddle_dir}")
        
        # 统计模型文件
        model_files = list(paddle_dir.rglob("*.pd*"))
        if model_files:
            total_size = sum(f.stat().st_size for f in model_files) / (1024 * 1024)
            print(f"  模型文件数: {len(model_files)}")
            print(f"  总大小: {total_size:.2f} MB")
        else:
            print("  - 未找到模型文件")
    else:
        print(f"✗ 模型目录不存在: {paddle_dir}")
        print("  请先运行本脚本下载模型")
    
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PaddleOCR 模型管理")
    parser.add_argument('--info', action='store_true', help="显示模型信息")
    args = parser.parse_args()
    
    if args.info:
        show_model_info()
    else:
        if download_models():
            show_model_info()
