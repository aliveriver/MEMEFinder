#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查打包结果脚本
用于诊断打包后ZIP文件未生成的问题
"""

import os
from pathlib import Path

def check_build_results():
    """检查打包结果"""
    print("=" * 60)
    print("MEMEFinder 打包结果检查")
    print("=" * 60)
    print()
    
    # 检查dist目录
    dist_dir = Path('dist')
    print(f"[1] 检查 dist 目录: {dist_dir.absolute()}")
    if dist_dir.exists():
        print(f"    ✓ dist 目录存在")
    else:
        print(f"    ✗ dist 目录不存在")
        print("    请先运行打包脚本")
        return
    
    # 检查MEMEFinder目录
    memefinder_dir = dist_dir / 'MEMEFinder'
    print(f"\n[2] 检查 MEMEFinder 目录: {memefinder_dir.absolute()}")
    if memefinder_dir.exists():
        print(f"    ✓ MEMEFinder 目录存在")
        
        # 检查文件
        exe_file = memefinder_dir / 'MEMEFinder.exe'
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"    ✓ MEMEFinder.exe 存在 ({size_mb:.2f} MB)")
        else:
            print(f"    ✗ MEMEFinder.exe 不存在")
        
        # 统计文件
        file_count = sum(1 for _ in memefinder_dir.rglob('*') if _.is_file())
        print(f"    ✓ 总文件数: {file_count}")
    else:
        print(f"    ✗ MEMEFinder 目录不存在")
        print("    打包可能未完成")
        return
    
    # 检查ZIP文件
    zip_files = list(dist_dir.glob('*.zip'))
    print(f"\n[3] 检查 ZIP 文件:")
    if zip_files:
        for zip_file in zip_files:
            size_mb = zip_file.stat().st_size / (1024 * 1024)
            print(f"    ✓ {zip_file.name} ({size_mb:.2f} MB)")
    else:
        print(f"    ✗ 未找到 ZIP 文件")
        print(f"    尝试创建 ZIP 文件...")
        create_zip_manually(memefinder_dir, dist_dir)
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)


def create_zip_manually(source_dir, output_dir):
    """手动创建ZIP文件"""
    import shutil
    
    try:
        output_name = 'MEMEFinder-v1.0.0-Windows-x64'
        zip_base = output_dir / output_name
        zip_path = Path(f'{zip_base}.zip')
        
        print(f"\n正在创建: {zip_path.absolute()}")
        
        # 如果已存在，先删除
        if zip_path.exists():
            zip_path.unlink()
            print("    删除已存在的ZIP文件")
        
        # 创建ZIP
        shutil.make_archive(
            str(zip_base.absolute()),
            'zip',
            str(output_dir.absolute()),
            'MEMEFinder'
        )
        
        if zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"    ✓ ZIP文件创建成功: {zip_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"    ✗ ZIP文件创建失败")
            print(f"    请检查权限和磁盘空间")
            
    except Exception as e:
        print(f"    ✗ 创建ZIP时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_build_results()
    input("\n按回车键退出...")


