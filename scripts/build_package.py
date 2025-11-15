#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目打包脚本 - 一键打包包含所有模型的可执行程序
"""

import subprocess
import sys
from pathlib import Path
import shutil


def check_requirements():
    """检查打包环境"""
    print("=" * 70)
    print("🔍 检查打包环境")
    print("=" * 70)
    print()
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("   请运行: pip install pyinstaller")
        return False
    
    # 检查 RapidOCR
    try:
        import rapidocr_onnxruntime
        print("✓ RapidOCR 已安装")
    except ImportError:
        print("❌ RapidOCR 未安装")
        print("   请运行: pip install rapidocr-onnxruntime")
        return False
    
    # 检查 models 目录
    models_dir = Path("models")
    if not models_dir.exists():
        print("❌ models 目录不存在")
        print("   请先运行: python copy_models.py")
        return False
    
    # 检查模型文件
    onnx_files = list(models_dir.glob("*.onnx"))
    if len(onnx_files) < 3:
        print(f"⚠️  models 目录只有 {len(onnx_files)} 个模型文件（应该至少3个）")
        print("   请先运行: python copy_models.py")
        return False
    else:
        print(f"✓ 找到 {len(onnx_files)} 个模型文件")
        for f in onnx_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   - {f.name} ({size_mb:.2f} MB)")
    
    print()
    return True


def clean_build():
    """清理旧的构建文件"""
    print("=" * 70)
    print("🧹 清理旧的构建文件")
    print("=" * 70)
    print()
    
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"删除: {dir_name}/")
            shutil.rmtree(dir_path)
        else:
            print(f"跳过: {dir_name}/ (不存在)")
    
    print()


def build_exe():
    """使用 PyInstaller 打包"""
    print("=" * 70)
    print("📦 开始打包程序")
    print("=" * 70)
    print()
    
    # 使用 .spec 文件打包
    spec_file = "MEMEFinder.spec"
    
    if not Path(spec_file).exists():
        print(f"❌ 未找到 {spec_file}")
        return False
    
    print(f"使用配置文件: {spec_file}")
    print()
    
    # 运行 PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--clean"]
    
    print("执行命令:")
    print(f"  {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 打包过程出错: {e}")
        return False


def verify_build():
    """验证打包结果"""
    print("\n" + "=" * 70)
    print("🔍 验证打包结果")
    print("=" * 70)
    print()
    
    dist_dir = Path("dist/MEMEFinder")
    if not dist_dir.exists():
        print("❌ dist/MEMEFinder 目录不存在")
        return False
    
    # 检查可执行文件
    exe_file = dist_dir / "MEMEFinder.exe"
    if not exe_file.exists():
        print("❌ MEMEFinder.exe 不存在")
        return False
    
    exe_size = exe_file.stat().st_size / (1024 * 1024)
    print(f"✓ 可执行文件: MEMEFinder.exe ({exe_size:.2f} MB)")
    
    # 检查 models 目录
    models_dir = dist_dir / "models"
    if models_dir.exists():
        onnx_files = list(models_dir.glob("*.onnx"))
        print(f"✓ models 目录: {len(onnx_files)} 个模型文件")
        
        total_size = sum(f.stat().st_size for f in onnx_files) / (1024 * 1024)
        print(f"   模型总大小: {total_size:.2f} MB")
    else:
        print("⚠️  models 目录不存在（运行时可能需要下载模型）")
    
    # 计算总大小
    total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    print()
    print(f"📊 打包目录总大小: {total_size_mb:.2f} MB")
    print(f"📁 输出目录: {dist_dir.absolute()}")
    
    return True


def create_readme():
    """创建发布说明"""
    print("\n" + "=" * 70)
    print("📝 创建发布说明")
    print("=" * 70)
    print()
    
    readme_content = """# MEMEFinder - 表情包查找器

## 简介

MEMEFinder 是一款基于 OCR 和情绪分析的表情包管理工具。

## 功能特点

- 📸 **图片扫描**: 自动扫描指定文件夹中的图片
- 🔍 **OCR识别**: 使用 RapidOCR 提取图片中的文字
- 😊 **情绪分析**: 分析图片文字的情绪倾向（正向/负向/中性）
- 🔎 **智能搜索**: 支持文字内容和情绪搜索
- 💾 **本地数据库**: 使用 SQLite 存储图片信息

## 使用方法

1. 运行 `MEMEFinder.exe`
2. 在"图源管理"页添加图片文件夹
3. 点击"扫描新图片"导入图片
4. 在"图片处理"页处理图片（OCR识别）
5. 在"图片搜索"页搜索表情包

## GPU 加速

程序支持 GPU 加速（如果系统有 NVIDIA 显卡）。

- 自动检测并使用 GPU
- 如需强制使用 CPU，设置环境变量: `MEMEFINDER_USE_GPU=0`

## 技术栈

- **OCR引擎**: RapidOCR (ONNX Runtime)
- **情绪分析**: SnowNLP (可选)
- **GUI框架**: Tkinter
- **数据库**: SQLite

## 系统要求

- Windows 10 或更高版本
- 内存: 建议 4GB 以上
- 硬盘: 至少 500MB 可用空间

## 许可证

详见 LICENSE 文件

## 更新日志

### v1.0.0
- 初始版本发布
- 支持 OCR 文字识别
- 支持情绪分析
- 支持智能搜索
"""
    
    readme_file = Path("dist/MEMEFinder/README.txt")
    readme_file.write_text(readme_content, encoding='utf-8')
    
    print(f"✓ 创建 README.txt")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 MEMEFinder 打包工具")
    print("=" * 70)
    print()
    
    # 1. 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，请先完成上述步骤")
        return 1
    
    # 2. 清理旧文件
    clean_build()
    
    # 3. 打包
    if not build_exe():
        print("\n❌ 打包失败")
        return 1
    
    # 4. 验证
    if not verify_build():
        print("\n❌ 验证失败")
        return 1
    
    # 5. 创建说明文件
    create_readme()
    
    # 完成
    print("=" * 70)
    print("🎉 打包完成！")
    print("=" * 70)
    print()
    print("输出目录: dist/MEMEFinder/")
    print()
    print("下一步:")
    print("  1. 测试运行: dist\\MEMEFinder\\MEMEFinder.exe")
    print("  2. 如需分发，可以压缩整个 dist/MEMEFinder 文件夹")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
