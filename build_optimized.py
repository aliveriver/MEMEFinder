#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化打包脚本 - 创建更小、更快的可执行文件
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def clean_build_dirs():
    """清理之前的构建目录"""
    print("清理旧的构建文件...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}")
    
    # 清理 .spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  已删除: {spec_file}")


def create_optimized_spec():
    """创建优化的 PyInstaller 配置"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 排除不需要的大型模块
excludes = [
    # 开发和测试工具
    'pytest', 'pytest_cov', 'coverage', 'hypothesis', 'nose', 'tox',
    # 文档工具
    'sphinx', 'docutils', 'alabaster', 'babel',
    # Jupyter 全家桶
    'IPython', 'jupyter', 'notebook', 'nbconvert', 'nbformat', 
    'ipykernel', 'ipywidgets', 'qtconsole',
    # 数据科学库（MEMEFinder 不需要）
    'matplotlib', 'scipy', 'pandas', 'seaborn', 'statsmodels',
    'scikit-learn', 'sklearn', 'sympy',
    # Web 框架（只保留可能需要的 flask）
    'django', 'tornado', 'aiohttp', 'fastapi', 'starlette',
    # GUI 框架（只用 tkinter）
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx', 'kivy',
    'PIL.ImageQt',
    # 其他大型库
    'setuptools', 'distutils', 'pip', 'wheel', 'pkg_resources',
    # 编译器和构建工具
    'Cython', 'numba', 'jinja2',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        # 核心依赖
        'paddleocr',
        'paddlenlp',
        'paddle',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'numpy',
        # GUI
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # 数据库
        'sqlite3',
        # Python 标准库（PaddlePaddle 依赖）
        'unittest',
        'unittest.mock',
        'doctest',
        # 工具库
        'logging',
        'threading',
        'queue',
        'json',
        'datetime',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉不需要的二进制文件
def filter_binaries(binaries):
    """过滤掉不需要的 DLL/SO 文件"""
    excluded_prefixes = [
        'Qt',  # Qt 相关
        'matplotlib',
        'scipy',
        'pandas',
    ]
    
    filtered = []
    for name, path, kind in binaries:
        skip = False
        for prefix in excluded_prefixes:
            if prefix.lower() in name.lower():
                skip = True
                break
        if not skip:
            filtered.append((name, path, kind))
    
    return filtered

a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MEMEFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,  # 启用 UPX 压缩
    upx_exclude=[],
    name='MEMEFinder',
)
'''
    
    spec_path = Path('MEMEFinder.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print(f"✓ 已创建 {spec_path}")
    return spec_path


def run_pyinstaller(spec_path):
    """运行 PyInstaller"""
    try:
        # 检查 PyInstaller 版本
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--version'],
            capture_output=True,
            text=True
        )
        print(f"✓ PyInstaller 版本: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ PyInstaller 未安装: {e}")
        return False
    
    print("\n开始打包...")
    print("=" * 60)
    
    # 运行 PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', str(spec_path)]
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False


def copy_extra_files():
    """复制额外的文件到 dist 目录"""
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        print("✗ dist/MEMEFinder 目录不存在")
        return False
    
    print("\n复制额外文件...")
    
    files_to_copy = {
        'README.md': 'README.md',
        'requirements.txt': 'requirements.txt',
        'download_models.py': 'download_models.py',
    }
    
    dirs_to_copy = {
        'docs': 'docs',
    }
    
    # 复制文件
    for src, dst in files_to_copy.items():
        src_path = Path(src)
        dst_path = dist_dir / dst
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"  ✓ 已复制: {src}")
        else:
            print(f"  ⚠ 文件不存在: {src}")
    
    # 复制目录
    for src, dst in dirs_to_copy.items():
        src_path = Path(src)
        dst_path = dist_dir / dst
        if src_path.exists():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            print(f"  ✓ 已复制目录: {src}")
        else:
            print(f"  ⚠ 目录不存在: {src}")
    
    # 创建空目录
    empty_dirs = ['logs', 'models']
    for dir_name in empty_dirs:
        dir_path = dist_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  ✓ 已创建目录: {dir_name}")
    
    return True


def check_size():
    """检查打包后的文件大小"""
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        return
    
    print("\n检查文件大小...")
    
    # 计算总大小
    total_size = 0
    for path in dist_dir.rglob('*'):
        if path.is_file():
            total_size += path.stat().st_size
    
    # 转换为 MB
    size_mb = total_size / (1024 * 1024)
    print(f"  总大小: {size_mb:.2f} MB")
    
    if size_mb > 1000:
        print(f"  ⚠️ 警告: 文件过大！建议检查是否包含了不必要的依赖")
    elif size_mb > 500:
        print(f"  ℹ️ 提示: 文件较大，这对于 AI 应用是正常的")
    else:
        print(f"  ✓ 文件大小合理")


def main():
    """主函数"""
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "MEMEFinder 优化打包工具" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 1. 清理旧文件
    clean_build_dirs()
    
    # 2. 创建 spec 文件
    spec_path = create_optimized_spec()
    
    # 3. 运行 PyInstaller
    if not run_pyinstaller(spec_path):
        print("\n✗ 打包失败")
        return 1
    
    # 4. 复制额外文件
    if not copy_extra_files():
        print("\n✗ 复制文件失败")
        return 1
    
    # 5. 检查大小
    check_size()
    
    print("\n" + "=" * 60)
    print("打包完成！")
    print("=" * 60)
    print()
    print("输出目录: dist/MEMEFinder/")
    print()
    print("后续步骤:")
    print("1. 测试 dist/MEMEFinder/MEMEFinder.exe")
    print("2. 使用 Inno Setup 创建安装程序（可选）")
    print()
    
    input("按回车键退出...")
    return 0


if __name__ == '__main__':
    sys.exit(main())
