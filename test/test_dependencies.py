#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依赖测试脚本
验证所有必需的依赖是否正确安装
"""

import sys


def test_import(module_name, description=""):
    """测试导入模块"""
    try:
        __import__(module_name)
        print(f"✓ {module_name:30s} - {description}")
        return True
    except ImportError as e:
        print(f"✗ {module_name:30s} - 失败: {e}")
        return False
    except Exception as e:
        print(f"⚠ {module_name:30s} - 警告: {e}")
        return True  # 可能是配置问题，不是导入问题


def main():
    """主函数"""
    print("=" * 70)
    print("MEMEFinder 依赖检查")
    print("=" * 70)
    print()
    
    # 应用补丁
    print("应用补丁...")
    try:
        import paddlex_patch
        print()
    except Exception as e:
        print(f"警告: 补丁加载失败 - {e}\n")
    
    # 核心依赖
    print("核心依赖:")
    results = []
    results.append(test_import("paddle", "PaddlePaddle"))
    results.append(test_import("paddleocr", "PaddleOCR"))
    results.append(test_import("paddlex", "PaddleX"))
    results.append(test_import("paddlenlp", "PaddleNLP"))
    
    print("\nPDF支持:")
    results.append(test_import("pypdfium2", "PDF阅读器"))
    
    print("\n图像处理:")
    results.append(test_import("cv2", "OpenCV"))
    results.append(test_import("PIL", "Pillow"))
    
    print("\n科学计算:")
    results.append(test_import("numpy", "NumPy"))
    
    print("\nGUI:")
    results.append(test_import("tkinter", "Tkinter"))
    
    print("\n数据库:")
    results.append(test_import("sqlite3", "SQLite3"))
    
    print("\n" + "=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有依赖检查通过 ({passed}/{total})")
        print("\n可以开始打包！")
        return 0
    else:
        print(f"✗ 依赖检查失败 ({passed}/{total} 通过)")
        print("\n请安装缺失的依赖:")
        print("pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
