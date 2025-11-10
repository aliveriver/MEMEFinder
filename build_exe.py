#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本 - 创建 Windows 可执行文件
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def clean_build_dirs():
    """清理之前的构建目录"""
    print("清理旧的构建文件...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_name}")
    
    # 清理 .spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  已删除: {spec_file}")


def create_pyinstaller_spec():
    """创建 PyInstaller 配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析所有的依赖
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('README.md', '.'),
    ],
    collect_data=['paddlex'],  # 收集 PaddleX 的数据文件（包括 .version）
    hiddenimports=[
        'paddleocr',
        'paddlenlp',
        'paddle',
        'cv2',
        'PIL',
        'numpy',
        'tkinter',
        'sqlite3',
        'unittest',  # 修复 PaddlePaddle 依赖
        'unittest.mock',
        'doctest',
        'flask',
        'flask_cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 开发工具
        'pytest', 'pytest_cov', 'coverage', 'hypothesis',
        # 文档工具
        'sphinx', 'docutils', 'jinja2',
        # Jupyter相关
        'IPython', 'jupyter', 'notebook', 'nbconvert', 'nbformat',
        # 数据科学库（pandas需要保留，PaddleX依赖）
        'matplotlib', 'scipy', 'seaborn',
        # Web框架（保留flask因为可能需要）
        'django', 'tornado', 'aiohttp',
        # 其他不需要的
        'PIL.ImageQt', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标可以在这里指定
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
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
    print("\n开始打包...")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--clean',
        str(spec_path)
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False


def copy_additional_files():
    """复制额外的文件到 dist 目录"""
    print("\n复制额外文件...")
    
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        print(f"✗ 找不到输出目录: {dist_dir}")
        return False
    
    # 需要复制的文件
    files_to_copy = [
        'README.md',
        'requirements.txt',
    ]
    
    # 需要复制的目录
    dirs_to_copy = [
        'docs',
    ]
    
    # 复制文件
    for file_name in files_to_copy:
        src = Path(file_name)
        if src.exists():
            dst = dist_dir / file_name
            shutil.copy2(src, dst)
            print(f"  ✓ 已复制: {file_name}")
    
    # 复制目录
    for dir_name in dirs_to_copy:
        src = Path(dir_name)
        if src.exists():
            dst = dist_dir / dir_name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  ✓ 已复制目录: {dir_name}")
    
    # 创建空的目录
    empty_dirs = ['logs', 'models']
    for dir_name in empty_dirs:
        (dist_dir / dir_name).mkdir(exist_ok=True)
        print(f"  ✓ 已创建目录: {dir_name}")
    
    return True


def create_release_readme():
    """创建发布版本的 README"""
    readme_content = '''# MEMEFinder - 表情包智能管理工具

🎭 基于 OCR 和情绪分析的表情包搜索与管理系统

---

## 📦 开箱即用版本说明

这是 MEMEFinder 的 **Windows 独立发布版本**，无需安装 Python 环境即可使用！

---

## 🚀 快速开始

### 1️⃣ 首次运行（必需）

**重要**: 首次使用前，必须下载 AI 模型！

双击运行：`下载模型.bat`

这将下载：
- PaddleOCR 文字识别模型（必需）
- PaddleNLP 情绪分析模型（可选，如果失败将使用关键词方法）

下载时间取决于网速，大约需要 5-15 分钟。

### 2️⃣ 启动程序

双击运行：`MEMEFinder.exe`

或者使用快捷方式：`启动程序.bat`

### 3️⃣ 使用流程

1. **添加图源**
   - 点击"图源管理"标签
   - 点击"添加文件夹"
   - 选择包含表情包的文件夹

2. **处理图片**
   - 切换到"处理"标签
   - 点击"开始处理"
   - 等待 OCR 识别完成

3. **搜索表情包**
   - 切换到"搜索"标签
   - 输入关键词
   - 选择情绪类型（可选）
   - 点击搜索

---

## 📁 目录结构

```
MEMEFinder/
├── MEMEFinder.exe       # 主程序（双击运行）
├── 下载模型.bat          # 首次运行必需
├── 启动程序.bat          # 启动快捷方式
├── README.md            # 本说明文件
├── docs/                # 详细文档
├── logs/                # 日志文件
├── models/              # AI 模型缓存
└── meme_finder.db       # 数据库（自动创建）
```

---

## ⚙️ 系统要求

### 最低配置
- **操作系统**: Windows 10 64位 或更高
- **内存**: 4GB RAM
- **磁盘空间**: 3GB（包括模型文件）
- **网络**: 首次下载模型需要联网

### 推荐配置
- **操作系统**: Windows 10/11 64位
- **内存**: 8GB RAM 或更多
- **磁盘空间**: 5GB 或更多
- **处理器**: 4核心或更多（提升处理速度）

---

## 🔧 常见问题

### 1. 程序无法启动
- 确保您使用的是 Windows 10 或更高版本
- 尝试以管理员身份运行
- 检查杀毒软件是否阻止了程序

### 2. OCR 识别失败
- 确保已运行 `下载模型.bat` 下载模型
- 检查图片格式（支持 jpg, png, bmp, gif）
- 查看 `logs/` 目录下的日志文件

### 3. 内存占用过高
- 每次处理的图片数量较少时分批处理
- 关闭其他占用内存的程序
- 重启程序释放内存

### 4. 搜索速度慢
- 首次处理图片需要时间，后续搜索会很快
- 定期清理不需要的图源
- 考虑使用 SSD 硬盘

---

## 📊 性能优化建议

1. **分批处理**: 建议每次处理 100-500 张图片
2. **定期清理**: 删除不需要的图源和数据
3. **关闭其他程序**: 处理时关闭浏览器等占用内存的程序
4. **使用 SSD**: SSD 硬盘可以显著提升数据库查询速度

---

## 📝 更新日志

### v1.0.0 (2025-11-10)
- ✨ 首次发布
- ✅ OCR 文字识别
- ✅ 情绪分析
- ✅ 关键词搜索
- ✅ 批量处理
- ✅ 数据持久化

---

## 🆘 获取帮助

- 查看 `docs/` 目录下的详细文档
- 查看 `logs/` 目录下的日志文件
- 提交 Issue 到 GitHub

---

## 📄 许可证

MIT License

---

**祝您使用愉快！** 🎉
'''
    
    dist_dir = Path('dist/MEMEFinder')
    if dist_dir.exists():
        readme_path = dist_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"  ✓ 已创建发布版 README")
        return True
    return False


def create_model_download_script():
    """创建模型下载脚本（用于发布版）"""
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        return False
    
    # 复制 download_models.py
    src = Path('download_models.py')
    if src.exists():
        dst = dist_dir / 'download_models.py'
        shutil.copy2(src, dst)
        print(f"  ✓ 已复制: download_models.py")
    
    # 创建批处理脚本
    bat_content = '''@echo off
chcp 65001 > nul
echo ========================================
echo MEMEFinder - 模型下载工具
echo ========================================
echo.

MEMEFinder.exe download_models.py

echo.
echo ========================================
echo 下载完成！
echo ========================================
pause
'''
    
    bat_path = dist_dir / '下载模型.bat'
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"  ✓ 已创建: 下载模型.bat")
    
    return True


def create_startup_script():
    """创建启动脚本"""
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        return False
    
    bat_content = '''@echo off
chcp 65001 > nul
echo 正在启动 MEMEFinder...
start MEMEFinder.exe
'''
    
    bat_path = dist_dir / '启动程序.bat'
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"  ✓ 已创建: 启动程序.bat")
    
    return True


def create_release_package():
    """创建发布包（ZIP）"""
    print("\n创建发布包...")
    
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        print(f"✗ 找不到输出目录: {dist_dir}")
        return False
    
    # 创建 ZIP 文件
    output_name = 'MEMEFinder-v1.0.0-Windows-x64'
    output_path = Path('dist') / output_name
    
    print(f"  正在打包: {output_name}.zip")
    shutil.make_archive(str(output_path), 'zip', 'dist', 'MEMEFinder')
    
    zip_file = Path(f'{output_path}.zip')
    if zip_file.exists():
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ 发布包已创建: {zip_file} ({size_mb:.2f} MB)")
        return True
    
    return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "MEMEFinder 打包工具 (PyInstaller)" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 1. 清理旧文件
    clean_build_dirs()
    
    # 2. 创建配置文件
    spec_path = create_pyinstaller_spec()
    
    # 3. 运行打包
    if not run_pyinstaller(spec_path):
        print("\n✗ 打包失败！")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 4. 复制额外文件
    copy_additional_files()
    
    # 5. 创建发布版 README
    create_release_readme()
    
    # 6. 创建模型下载脚本
    create_model_download_script()
    
    # 7. 创建启动脚本
    create_startup_script()
    
    # 8. 创建发布包
    create_release_package()
    
    # 完成
    print("\n" + "=" * 60)
    print("打包完成！")
    print("=" * 60)
    print(f"\n输出目录: dist/MEMEFinder/")
    print(f"发布包: dist/MEMEFinder-v1.0.0-Windows-x64.zip")
    print("\n后续步骤:")
    print("1. 将发布包上传到 GitHub Releases")
    print("2. 解压后首次运行 '下载模型.bat'")
    print("3. 然后双击 'MEMEFinder.exe' 启动程序")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
