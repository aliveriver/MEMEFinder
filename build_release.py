#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder Release 打包脚本
完整处理PaddleX依赖的版本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def clean_build():
    """清理构建目录"""
    print_header("清理旧文件")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"删除: {dir_name}/")
            shutil.rmtree(dir_name)
    
    # 删除 spec 文件
    for spec in Path('.').glob('*.spec'):
        print(f"删除: {spec}")
        spec.unlink()
    
    print("✓ 清理完成")


def build_exe():
    """使用PyInstaller打包"""
    print_header("开始打包")
    
    # PyInstaller 命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--name=MEMEFinder',
        '--windowed',
        
        # 添加数据文件
        '--add-data=src;src',
        '--add-data=README.md;.',
        '--add-data=paddlex_patch.py;.',  # 添加补丁文件
        
        # 关键：收集PaddleX的所有数据文件
        '--collect-all=paddlex',
        '--collect-all=paddle',
        '--collect-all=paddleocr',
        '--collect-all=paddlenlp',
        '--collect-all=pypdfium2',
        '--collect-submodules=paddlex',
        '--collect-submodules=paddle',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddlenlp',
        '--collect-submodules=pypdfium2',
        
        # 必需的隐藏导入
        '--hidden-import=unittest',
        '--hidden-import=unittest.mock',
        '--hidden-import=doctest',
        '--hidden-import=paddleocr',
        '--hidden-import=paddlenlp',
        '--hidden-import=paddle',
        '--hidden-import=paddlex',
        '--hidden-import=paddlex.inference',
        '--hidden-import=paddlex.inference.pipelines',
        '--hidden-import=paddlex.inference.pipelines.ocr',
        '--hidden-import=paddlex.inference.models',
        '--hidden-import=paddlex.modules',
        '--hidden-import=paddlex.inference.common',
        '--hidden-import=paddlex.inference.common.reader',
        '--hidden-import=paddlex.inference.common.reader.image_reader',
        '--hidden-import=cv2',
        '--hidden-import=cv2.cv2',  # 确保 OpenCV 的核心模块
        '--hidden-import=PIL',
        '--hidden-import=numpy',
        '--hidden-import=pandas',  # PaddleX需要
        '--hidden-import=tkinter',
        '--hidden-import=sqlite3',
        '--hidden-import=sklearn',
        '--hidden-import=scipy',
        '--hidden-import=pypdfium2',
        
        # 只排除开发工具（不排除任何科学计算库）
        '--exclude-module=pytest',
        '--exclude-module=IPython',
        
        'main.py'
    ]
    
    print("执行命令:")
    print(' '.join(cmd))
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n✗ 打包失败")
        return False
    
    print("\n✓ 打包成功")
    return True


def check_output():
    """检查输出文件"""
    print_header("检查输出")
    
    exe_path = Path('dist/MEMEFinder/MEMEFinder.exe')
    
    if not exe_path.exists():
        print("✗ 找不到 MEMEFinder.exe")
        return False
    
    # 计算大小
    total_size = 0
    file_count = 0
    
    dist_dir = Path('dist/MEMEFinder')
    for file in dist_dir.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
            file_count += 1
    
    size_mb = total_size / (1024 * 1024)
    
    print(f"✓ 可执行文件: {exe_path}")
    print(f"✓ 总文件数: {file_count}")
    print(f"✓ 总大小: {size_mb:.2f} MB")
    
    return True


def create_release_package():
    """创建发布包"""
    print_header("创建发布包")
    
    dist_dir = Path('dist/MEMEFinder')
    
    # 复制README到dist
    readme_src = Path('README.md')
    if readme_src.exists():
        shutil.copy2(readme_src, dist_dir / 'README.txt')
        print("✓ 复制 README.md")
    
    # 创建启动批处理
    launcher_bat = dist_dir / '启动MEMEFinder.bat'
    launcher_bat.write_text(
        '@echo off\n'
        'start MEMEFinder.exe\n',
        encoding='utf-8'
    )
    print("✓ 创建 启动MEMEFinder.bat")
    
    # 创建ZIP包
    print("\n正在创建 ZIP 压缩包...")
    output_name = 'MEMEFinder-v1.0.0-Windows-x64'
    
    shutil.make_archive(
        str(Path('dist') / output_name),
        'zip',
        'dist',
        'MEMEFinder'
    )
    
    zip_path = Path(f'dist/{output_name}.zip')
    if zip_path.exists():
        zip_size = zip_path.stat().st_size / (1024 * 1024)
        print(f"✓ ZIP包: {zip_path} ({zip_size:.2f} MB)")
    
    print("\n✓ 发布包创建完成")


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MEMEFinder Release 打包工具" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"\n✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("\n✗ 未安装 PyInstaller")
        print("请运行: pip install pyinstaller")
        input("\n按回车退出...")
        sys.exit(1)
    
    # 执行构建流程
    try:
        # 1. 清理
        clean_build()
        
        # 2. 打包
        if not build_exe():
            input("\n按回车退出...")
            sys.exit(1)
        
        # 3. 检查
        if not check_output():
            input("\n按回车退出...")
            sys.exit(1)
        
        # 4. 创建发布包
        create_release_package()
        
        # 完成
        print_header("打包完成")
        print("输出目录: dist/MEMEFinder/")
        print("发布包: dist/MEMEFinder-v1.0.0-Windows-x64.zip")
        print("\n后续步骤:")
        print("1. 测试 dist/MEMEFinder/MEMEFinder.exe")
        print("2. 确认程序可以正常运行")
        print("3. 上传 ZIP 包到 GitHub Releases")
        
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")


if __name__ == '__main__':
    main()
