#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模块化结构测试脚本
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import ImageDatabase, ImageScanner, OCRProcessor


def test_modules():
    """测试各个模块"""
    print("=" * 60)
    print("MEMEFinder 模块化结构测试")
    print("=" * 60)
    
    # 测试1: 数据库模块
    print("\n[测试1] 数据库模块 (core/database.py)")
    try:
        db = ImageDatabase("test_structure.db")
        print("  ✓ ImageDatabase 导入成功")
        print(f"  ✓ 数据库文件: test_structure.db")
        
        # 测试添加图源
        test_folder = str(Path("./imgs").absolute())
        if db.add_source(test_folder):
            print(f"  ✓ 添加图源成功: {test_folder}")
        else:
            print(f"  ✓ 图源已存在: {test_folder}")
        
        # 测试获取图源
        sources = db.get_sources()
        print(f"  ✓ 获取图源成功: {len(sources)} 个")
        
        # 测试统计
        stats = db.get_statistics()
        print(f"  ✓ 统计信息: 总图片 {stats['total']}, 已处理 {stats['processed']}")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False
    
    # 测试2: 扫描模块
    print("\n[测试2] 扫描模块 (core/scanner.py)")
    try:
        scanner = ImageScanner()
        print("  ✓ ImageScanner 导入成功")
        
        # 测试扫描
        imgs_folder = Path("./imgs")
        if imgs_folder.exists():
            images = scanner.scan_folder(str(imgs_folder))
            print(f"  ✓ 扫描文件夹: {imgs_folder}")
            print(f"  ✓ 发现图片: {len(images)} 张")
            
            # 测试哈希计算
            if images:
                img_hash = scanner.calculate_file_hash(images[0])
                print(f"  ✓ 计算哈希: {img_hash[:16]}...")
        else:
            print("  - 跳过: imgs文件夹不存在")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False
    
    # 测试3: OCR处理模块
    print("\n[测试3] OCR处理模块 (core/ocr_processor.py)")
    try:
        ocr = OCRProcessor()
        print("  ✓ OCRProcessor 导入成功")
        print("  - OCR功能待实现")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False
    
    # 测试4: GUI模块导入
    print("\n[测试4] GUI模块导入")
    try:
        from src.gui import MemeFinderGUI
        print("  ✓ MemeFinderGUI 导入成功")
        
        from src.gui.source_tab import SourceTab
        print("  ✓ SourceTab 导入成功")
        
        from src.gui.process_tab import ProcessTab
        print("  ✓ ProcessTab 导入成功")
        
        from src.gui.search_tab import SearchTab
        print("  ✓ SearchTab 导入成功")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("所有模块测试通过！✨")
    print("=" * 60)
    
    # 清理测试数据库
    import os
    if os.path.exists("test_structure.db"):
        os.remove("test_structure.db")
        print("\n✓ 测试数据库已清理")
    
    return True


def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 60)
    print("文件结构检查")
    print("=" * 60)
    
    required_files = [
        "main.py",
        "src/__init__.py",
        "src/core/__init__.py",
        "src/core/database.py",
        "src/core/scanner.py",
        "src/core/ocr_processor.py",
        "src/gui/__init__.py",
        "src/gui/main_window.py",
        "src/gui/source_tab.py",
        "src/gui/process_tab.py",
        "src/gui/search_tab.py",
    ]
    
    all_exist = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✓ {file:40} ({size:>6} bytes)")
        else:
            print(f"  ✗ {file:40} 不存在")
            all_exist = False
    
    if all_exist:
        print("\n✓ 所有必需文件都存在")
    else:
        print("\n✗ 部分文件缺失")
    
    return all_exist


def show_code_stats():
    """显示代码统计"""
    print("\n" + "=" * 60)
    print("代码统计")
    print("=" * 60)
    
    files = {
        "main.py": Path("main.py"),
        "core/database.py": Path("src/core/database.py"),
        "core/scanner.py": Path("src/core/scanner.py"),
        "core/ocr_processor.py": Path("src/core/ocr_processor.py"),
        "gui/main_window.py": Path("src/gui/main_window.py"),
        "gui/source_tab.py": Path("src/gui/source_tab.py"),
        "gui/process_tab.py": Path("src/gui/process_tab.py"),
        "gui/search_tab.py": Path("src/gui/search_tab.py"),
    }
    
    total_lines = 0
    print(f"\n{'文件':<30} {'行数':>10}")
    print("-" * 42)
    
    for name, path in files.items():
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            total_lines += lines
            print(f"{name:<30} {lines:>10}")
    
    print("-" * 42)
    print(f"{'总计':<30} {total_lines:>10}")
    print(f"\n平均每个文件: {total_lines // len(files)} 行")


if __name__ == "__main__":
    print("\n🚀 开始测试模块化结构...\n")
    
    # 测试文件结构
    if not test_file_structure():
        print("\n❌ 文件结构检查失败")
        sys.exit(1)
    
    # 测试模块功能
    if not test_modules():
        print("\n❌ 模块功能测试失败")
        sys.exit(1)
    
    # 显示代码统计
    show_code_stats()
    
    print("\n" + "=" * 60)
    print("🎉 模块化结构优化成功！")
    print("=" * 60)
    print("\n主要改进:")
    print("  ✓ 代码按功能模块化")
    print("  ✓ 每个文件平均 ~100 行")
    print("  ✓ 职责单一，易于维护")
    print("  ✓ 便于团队协作开发")
    print("\n可以运行以下命令启动程序:")
    print("  python main.py")
    print("  或双击: 启动程序.bat")
    print()
