#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包前检查脚本
确保所有必需的模块都已安装
"""

import sys

def check_module(module_name, package_name=None):
    """检查模块是否已安装"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✓ {package_name} 已安装")
        return True
    except ImportError:
        print(f"✗ {package_name} 未安装")
        print(f"  请运行: pip install {package_name}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("打包前依赖检查")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # 检查关键模块
    print("[1] 检查核心依赖...")
    all_ok &= check_module('paddle', 'paddlepaddle')
    all_ok &= check_module('paddleocr')
    all_ok &= check_module('cv2', 'opencv-contrib-python')
    all_ok &= check_module('PIL', 'pillow')
    all_ok &= check_module('numpy')
    print()
    
    print("[2] 检查可选依赖...")
    try:
        import paddlenlp
        print("✓ paddlenlp 已安装")
    except ImportError:
        print("⚠ paddlenlp 未安装（可选，情绪分析将使用关键词方法）")
    print()
    
    print("[3] 检查打包工具...")
    all_ok &= check_module('PyInstaller')
    print()
    
    if all_ok:
        print("=" * 60)
        print("✓ 所有必需的依赖已安装，可以开始打包")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("✗ 部分依赖缺失，请先安装缺失的模块")
        print("=" * 60)
        print("\n建议运行:")
        print("  pip install -r requirements.txt")
        print("  pip install pyinstaller")
        return 1

if __name__ == '__main__':
    sys.exit(main())

