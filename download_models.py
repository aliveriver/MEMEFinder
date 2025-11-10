#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型下载脚本 - 下载并集成所有必需的模型
"""

import os
import sys
from pathlib import Path
import shutil


def download_paddleocr_models():
    """下载 PaddleOCR 模型"""
    print("=" * 60)
    print("正在下载 PaddleOCR 模型...")
    print("=" * 60)
    
    try:
        from paddleocr import PaddleOCR
        
        # 设置模型下载路径
        project_root = Path(__file__).parent
        models_dir = project_root / "models" / "paddleocr"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 PaddleOCR 会自动下载模型
        print("\n正在初始化 PaddleOCR（这将自动下载中文识别模型）...")
        ocr = PaddleOCR(
            lang='ch',
            use_textline_orientation=True
        )
        
        print("\n✓ PaddleOCR 模型下载完成！")
        print(f"模型已缓存到系统默认位置")
        
        # 测试模型
        print("\n正在测试模型...")
        test_result = ocr.ocr("test.png", cls=True) if Path("test.png").exists() else None
        if test_result is not None:
            print("✓ 模型测试成功！")
        else:
            print("✓ 模型下载成功（未找到测试图片，跳过测试）")
            
        return True
        
    except ImportError:
        print("✗ 错误: PaddleOCR 未安装")
        print("请先运行: pip install paddleocr")
        return False
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False


def download_paddlenlp_models():
    """下载 PaddleNLP Senta 模型"""
    print("\n" + "=" * 60)
    print("正在下载 PaddleNLP 情绪分析模型...")
    print("=" * 60)
    
    try:
        from paddlenlp import Taskflow
        
        # 设置模型下载路径
        project_root = Path(__file__).parent
        models_dir = project_root / "models" / "senta"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Senta 会自动下载模型
        print("\n正在初始化 Senta 情绪分析模型...")
        senta = Taskflow("sentiment_analysis")
        
        print("\n✓ PaddleNLP Senta 模型下载完成！")
        
        # 测试模型
        print("\n正在测试模型...")
        test_result = senta("这个表情包太好笑了")
        print(f"测试结果: {test_result}")
        print("✓ 模型测试成功！")
        
        return True
        
    except ImportError:
        print("✗ 警告: PaddleNLP 未安装")
        print("情绪分析功能将使用简单关键词方法")
        print("如需深度学习情绪分析，请运行: pip install paddlenlp")
        return False
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        print("情绪分析将回退到关键词方法")
        return False


def check_paddle_installation():
    """检查 PaddlePaddle 安装"""
    print("=" * 60)
    print("检查 PaddlePaddle 安装...")
    print("=" * 60)
    
    try:
        import paddle
        version = paddle.__version__
        print(f"✓ PaddlePaddle 版本: {version}")
        
        # 检查是否支持 GPU
        if paddle.is_compiled_with_cuda():
            print("✓ 支持 CUDA (GPU加速)")
        else:
            print("✓ CPU 版本")
            
        return True
    except ImportError:
        print("✗ PaddlePaddle 未安装")
        print("请先安装 PaddlePaddle:")
        print("  CPU 版本: pip install paddlepaddle")
        print("  GPU 版本: pip install paddlepaddle-gpu")
        return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MEMEFinder 模型下载工具" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # 检查 PaddlePaddle
    if not check_paddle_installation():
        print("\n请先安装 PaddlePaddle，然后重新运行此脚本")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 下载 PaddleOCR 模型
    ocr_success = download_paddleocr_models()
    
    # 下载 PaddleNLP 模型（可选）
    nlp_success = download_paddlenlp_models()
    
    # 总结
    print("\n" + "=" * 60)
    print("下载完成！")
    print("=" * 60)
    
    if ocr_success:
        print("✓ OCR 模型已就绪")
    else:
        print("✗ OCR 模型下载失败")
    
    if nlp_success:
        print("✓ 情绪分析模型已就绪（深度学习）")
    else:
        print("⚠ 情绪分析将使用关键词方法（无需模型）")
    
    print("\n现在可以运行 MEMEFinder 了！")
    print("运行方式: python main.py")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
