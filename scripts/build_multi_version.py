"""
多版本打包脚本 - 为不同用户需求构建不同版本

版本说明:
1. CPU版本 - 适用于所有用户，无需GPU
2. GPU-CUDA11版本 - 适用于CUDA 11.x用户（GTX 10/16/20系列）
3. GPU-CUDA12版本 - 适用于CUDA 12.x用户（RTX 30/40系列）

使用方法:
    python scripts/build_multi_version.py --version cpu
    python scripts/build_multi_version.py --version gpu-cuda11
    python scripts/build_multi_version.py --version gpu-cuda12
    python scripts/build_multi_version.py --all  # 构建所有版本
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MultiVersionBuilder:
    """多版本打包构建器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.output_dir = self.project_root / "releases"
        
    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        print("✅ 清理完成")
        
    def install_dependencies(self, version_type):
        """安装对应版本的依赖"""
        print(f"📦 安装 {version_type} 依赖...")
        
        # 基础依赖
        base_deps = [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "opencv-python>=4.8",
            "pillow>=10.0",
            "numpy>=1.24,<2.1",
            "snownlp>=0.12.3",
            "python-dateutil>=2.8.0",
            "pyinstaller>=6.0.0"
        ]
        
        # OCR依赖
        if version_type == "cpu":
            ocr_deps = ["rapidocr-onnxruntime>=1.3.0"]
        elif version_type == "gpu-cuda11":
            # 卸载CPU版本，安装CUDA 11版本
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "rapidocr-onnxruntime"], 
                         capture_output=True)
            ocr_deps = [
                "onnxruntime-gpu==1.16.3",  # CUDA 11.8
                "rapidocr-onnxruntime>=1.3.0"
            ]
        elif version_type == "gpu-cuda12":
            # 卸载CPU版本，安装CUDA 12版本
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "rapidocr-onnxruntime"], 
                         capture_output=True)
            ocr_deps = [
                "onnxruntime-gpu==1.17.0",  # CUDA 12.x
                "rapidocr-onnxruntime>=1.3.0"
            ]
        else:
            raise ValueError(f"未知版本类型: {version_type}")
        
        # 安装依赖
        all_deps = base_deps + ocr_deps
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + all_deps)
        print("✅ 依赖安装完成")
        
    def create_version_config(self, version_type):
        """创建版本配置文件"""
        config = {
            "version_type": version_type,
            "gpu_enabled": version_type.startswith("gpu"),
            "cuda_version": version_type.split("-")[-1] if version_type.startswith("gpu") else None,
            "build_time": None  # 将在打包时添加
        }
        
        config_file = self.project_root / "src" / "version_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ 版本配置已创建: {version_type}")
        
    def build_version(self, version_type):
        """构建特定版本"""
        print(f"\n{'='*60}")
        print(f"🚀 开始构建 {version_type.upper()} 版本")
        print(f"{'='*60}\n")
        
        # 1. 清理构建目录
        self.clean_build()
        
        # 2. 安装依赖
        self.install_dependencies(version_type)
        
        # 3. 创建版本配置
        self.create_version_config(version_type)
        
        # 4. 选择对应的spec文件或修改spec
        spec_file = self.create_spec_for_version(version_type)
        
        # 5. 运行PyInstaller
        print(f"📦 正在打包 {version_type} 版本...")
        subprocess.check_call([
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ])
        
        # 6. 重命名输出
        self.rename_output(version_type)
        
        # 7. 创建版本说明
        self.create_version_readme(version_type)
        
        print(f"\n✅ {version_type.upper()} 版本构建完成！")
        
    def create_spec_for_version(self, version_type):
        """为特定版本创建spec文件"""
        spec_template = self.project_root / "MEMEFinder.spec"
        spec_file = self.project_root / f"MEMEFinder_{version_type}.spec"
        
        # 读取模板
        with open(spec_template, "r", encoding="utf-8") as f:
            spec_content = f.read()
        
        # 修改输出名称
        spec_content = spec_content.replace(
            "name='MEMEFinder'",
            f"name='MEMEFinder_{version_type}'"
        )
        
        # GPU版本需要额外的DLL收集逻辑
        if version_type.startswith("gpu"):
            # spec文件已经包含GPU DLL收集逻辑，无需修改
            pass
        
        # 写入新spec文件
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(spec_content)
        
        return spec_file
        
    def rename_output(self, version_type):
        """重命名输出文件"""
        # 创建releases目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 源文件夹
        source_dir = self.dist_dir / f"MEMEFinder_{version_type}"
        if not source_dir.exists():
            source_dir = self.dist_dir / "MEMEFinder"
        
        if not source_dir.exists():
            print(f"⚠️ 警告: 找不到输出目录 {source_dir}")
            return
        
        # 目标文件夹
        target_dir = self.output_dir / f"MEMEFinder_{version_type}"
        
        # 如果目标已存在，删除
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        # 移动文件
        shutil.move(str(source_dir), str(target_dir))
        print(f"✅ 输出已保存到: {target_dir}")
        
    def create_version_readme(self, version_type):
        """创建版本说明文件"""
        target_dir = self.output_dir / f"MEMEFinder_{version_type}"
        readme_file = target_dir / "版本说明.txt"
        
        version_info = {
            "cpu": {
                "name": "CPU通用版",
                "description": "适用于所有用户，无需GPU，兼容性最好",
                "requirements": "无特殊要求",
                "performance": "识别速度较慢，但稳定可靠",
                "recommended": "推荐给普通用户和没有NVIDIA显卡的用户"
            },
            "gpu-cuda11": {
                "name": "GPU加速版 (CUDA 11.x)",
                "description": "适用于CUDA 11.x用户，提供GPU加速",
                "requirements": "需要NVIDIA显卡 + CUDA 11.x运行时",
                "performance": "识别速度快，适合大量图片处理",
                "recommended": "推荐给GTX 10/16/20系列显卡用户"
            },
            "gpu-cuda12": {
                "name": "GPU加速版 (CUDA 12.x)",
                "description": "适用于CUDA 12.x用户，提供GPU加速",
                "requirements": "需要NVIDIA显卡 + CUDA 12.x运行时",
                "performance": "识别速度最快，支持最新显卡特性",
                "recommended": "推荐给RTX 30/40系列显卡用户"
            }
        }
        
        info = version_info[version_type]
        
        content = f"""
========================================
MEMEFinder - {info['name']}
========================================

版本类型: {version_type}
构建时间: 自动生成

【版本说明】
{info['description']}

【系统要求】
{info['requirements']}

【性能表现】
{info['performance']}

【推荐用户】
{info['recommended']}

【使用方法】
1. 直接运行 MEMEFinder_{version_type}.exe
2. 程序会自动打开浏览器界面
3. 如果浏览器未自动打开，请访问: http://localhost:5000

【GPU版本说明】
- 如果GPU初始化失败，程序会自动切换到CPU模式
- 您可以使用 启动_CPU模式.bat 强制使用CPU模式
- 检查GPU支持: 运行后查看日志文件

【常见问题】
1. GPU版本无法启动？
   - 检查是否安装了对应的CUDA运行时
   - 尝试使用CPU版本

2. 如何确认我的CUDA版本？
   - 打开命令提示符，运行: nvidia-smi
   - 查看右上角的CUDA Version

3. 程序闪退？
   - 查看logs目录下的日志文件
   - 尝试使用CPU版本

【技术支持】
如有问题，请查看项目文档或提交Issue
"""
        
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(content.strip())
        
        print(f"✅ 版本说明已创建")
        
    def build_all(self):
        """构建所有版本"""
        versions = ["cpu", "gpu-cuda11", "gpu-cuda12"]
        
        print(f"\n{'='*60}")
        print("🚀 开始构建所有版本")
        print(f"{'='*60}\n")
        
        success = []
        failed = []
        
        for version in versions:
            try:
                self.build_version(version)
                success.append(version)
            except Exception as e:
                print(f"\n❌ {version} 构建失败: {e}")
                failed.append(version)
        
        # 总结
        print(f"\n{'='*60}")
        print("📊 构建总结")
        print(f"{'='*60}")
        print(f"✅ 成功: {len(success)} 个版本")
        for v in success:
            print(f"   - {v}")
        
        if failed:
            print(f"\n❌ 失败: {len(failed)} 个版本")
            for v in failed:
                print(f"   - {v}")
        
        print(f"\n📁 所有版本已保存到: {self.output_dir}")
        
    def create_launcher_script(self):
        """创建启动脚本和版本选择器"""
        # 创建版本选择脚本
        selector_script = self.output_dir / "选择版本.bat"
        selector_content = """@echo off
chcp 65001 >nul
echo ========================================
echo MEMEFinder 版本选择器
echo ========================================
echo.
echo 请选择适合您系统的版本:
echo.
echo [1] CPU通用版 (推荐，兼容所有系统)
echo [2] GPU加速版 - CUDA 11.x (GTX 10/16/20系列)
echo [3] GPU加速版 - CUDA 12.x (RTX 30/40系列)
echo [0] 退出
echo.
set /p choice="请输入选项 (0-3): "

if "%choice%"=="1" (
    echo.
    echo 启动 CPU通用版...
    cd MEMEFinder_cpu
    start MEMEFinder_cpu.exe
) else if "%choice%"=="2" (
    echo.
    echo 启动 GPU加速版 (CUDA 11.x)...
    cd MEMEFinder_gpu-cuda11
    start MEMEFinder_gpu-cuda11.exe
) else if "%choice%"=="3" (
    echo.
    echo 启动 GPU加速版 (CUDA 12.x)...
    cd MEMEFinder_gpu-cuda12
    start MEMEFinder_gpu-cuda12.exe
) else if "%choice%"=="0" (
    exit
) else (
    echo 无效选项，请重新运行
    pause
)
"""
        
        with open(selector_script, "w", encoding="utf-8") as f:
            f.write(selector_content)
        
        print(f"✅ 版本选择器已创建: {selector_script}")


def main():
    parser = argparse.ArgumentParser(description="MEMEFinder 多版本打包工具")
    parser.add_argument("--version", choices=["cpu", "gpu-cuda11", "gpu-cuda12"],
                       help="指定要构建的版本")
    parser.add_argument("--all", action="store_true",
                       help="构建所有版本")
    
    args = parser.parse_args()
    
    builder = MultiVersionBuilder()
    
    if args.all:
        builder.build_all()
        builder.create_launcher_script()
    elif args.version:
        builder.build_version(args.version)
    else:
        parser.print_help()
        print("\n示例:")
        print("  python scripts/build_multi_version.py --version cpu")
        print("  python scripts/build_multi_version.py --all")


if __name__ == "__main__":
    main()
