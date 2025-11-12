#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查打包后的paddle模块
用于诊断paddle模块是否被正确打包
"""

import sys
from pathlib import Path

def check_paddle_in_build():
    """检查打包后的paddle模块"""
    print("=" * 60)
    print("检查打包后的paddle模块")
    print("=" * 60)
    print()
    
    # 检查dist目录
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        print("✗ dist/MEMEFinder 目录不存在")
        print("请先运行打包脚本")
        return
    
    # 检查_internal目录
    internal_dir = dist_dir / '_internal'
    if not internal_dir.exists():
        print("✗ _internal 目录不存在")
        return
    
    print(f"检查目录: {internal_dir.absolute()}")
    print()
    
    # 查找paddle相关文件
    paddle_dirs = []
    paddle_files = []
    
    for item in internal_dir.rglob('*'):
        if 'paddle' in item.name.lower():
            if item.is_dir():
                paddle_dirs.append(item)
            else:
                paddle_files.append(item)
    
    print(f"[1] 找到 {len(paddle_dirs)} 个paddle相关目录:")
    for d in paddle_dirs[:10]:  # 只显示前10个
        rel_path = d.relative_to(internal_dir)
        print(f"    {rel_path}")
    if len(paddle_dirs) > 10:
        print(f"    ... 还有 {len(paddle_dirs) - 10} 个目录")
    
    print(f"\n[2] 找到 {len(paddle_files)} 个paddle相关文件:")
    for f in paddle_files[:20]:  # 只显示前20个
        rel_path = f.relative_to(internal_dir)
        print(f"    {rel_path}")
    if len(paddle_files) > 20:
        print(f"    ... 还有 {len(paddle_files) - 20} 个文件")
    
    # 检查是否有paddle目录
    paddle_dir = internal_dir / 'paddle'
    if paddle_dir.exists():
        print(f"\n[3] ✓ 找到paddle目录: {paddle_dir}")
        
        # 检查关键文件
        init_file = paddle_dir / '__init__.py'
        if init_file.exists():
            print(f"    ✓ __init__.py 存在")
        else:
            print(f"    ✗ __init__.py 不存在")
    else:
        print(f"\n[3] ✗ paddle目录不存在")
        print("    paddle模块可能没有被正确打包")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)
    print("\n建议:")
    if not paddle_dir.exists():
        print("1. 确保已安装paddle: pip install paddlepaddle")
        print("2. 重新运行打包脚本")
        print("3. 检查MEMEFinder.spec中的hiddenimports配置")
    else:
        print("paddle模块已找到，如果运行时仍然报错，")
        print("可能是动态导入问题，需要添加更多隐藏导入")

if __name__ == '__main__':
    check_paddle_in_build()
    input("\n按回车键退出...")

