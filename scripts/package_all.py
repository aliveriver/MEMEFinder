#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder GPU 版本打包脚本
功能：
1. 打包支持 GPU 加速的版本（自动降级 CPU）
2. 包含 cuDNN 和 CUDA 运行时库
3. 自动清理构建缓存
4. 整理发布文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import time

# 导入CUDA清理脚本
sys.path.insert(0, str(Path(__file__).parent))
from clean_cuda import clean_cuda_dlls

# 确保在项目根目录运行
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
os.chdir(PROJECT_ROOT)

def print_color(text, color="green"):
    """打印带颜色的文本 (简单的 ANSI 转义码)"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    # Windows 10+ 支持 ANSI，旧版可能不支持，这里简单处理
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass
    
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def clean_build():
    """清理构建目录"""
    print_color("\n[1/4] 正在清理构建环境...", "yellow")
    dirs = ['build', 'dist']
    for d in dirs:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  - 已删除 {d}/")
            except Exception as e:
                print_color(f"  ! 删除 {d} 失败: {e}", "red")

def generate_spec(version_name, console=False):
    """
    生成 Spec 文件内容
    version_name: 'cpu', 'gpu-cuda11', 'gpu-cuda12'
    """
    app_name = "MEMEFinder"  # 统一使用MEMEFinder作为应用名称
    
    # 基础 hidden imports
    hidden_imports = [
        'unittest', 'unittest.mock', 'doctest',
        'rapidocr_onnxruntime', 'onnxruntime',
        'snownlp', 'cv2', 'PIL', 'numpy', 
        'tkinter', 'sqlite3', 'flask', 'flask_cors',
        'pypdfium2', 'pyclipper', 'shapely', 'imgaug',
        # 不包含sklearn（太大），颜色聚类已用纯numpy实现
    ]
    
    # 基础数据文件
    datas = [
        ('src', 'src'),
        ('assets', 'assets'),  # 打包 assets 目录（包含 icon.ico）
        ('README.md', '.'),
        ('LICENSE', '.'),
        # 打包模型文件
        ('models/mobilenetv3_small_feature.onnx', 'models'),  # 深度学习特征提取模型（4.73MB）
    ]
    
    # 补丁文件检测
    patch_files = [
        'paddlex_patch.py', 'paddle_runtime_patch.py', 'cv2_patch.py',
        'snownlp_patch.py', 'snownlp_runtime_patch.py', 'ocr_model_patch.py',
        'pyclipper_patch.py', 'stdout_stderr_patch.py'
    ]
    for patch in patch_files:
        if os.path.exists(patch):
            datas.append((patch, '.'))

    # 构建 Spec 文件内容
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# 动态收集依赖
datas = {datas}
binaries = []
hiddenimports = {hidden_imports}

# 收集 RapidOCR
try:
    tmp_ret = collect_all('rapidocr_onnxruntime')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f\"[SPEC] 收集 RapidOCR: {{len(tmp_ret[0])}} 数据文件, {{len(tmp_ret[1])}} 二进制文件, {{len(tmp_ret[2])}} 隐藏导入\")
except: pass

# 收集 ONNX Runtime
try:
    tmp_ret = collect_all('onnxruntime')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
except: pass

# 收集 SnowNLP
try:
    tmp_ret = collect_all('snownlp')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
except: pass

# 收集 OpenCV
try:
    tmp_ret = collect_all('cv2')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
except: pass

# 手动添加 conda 环境中的必需 DLL（pyexpat 等依赖）
import sys
import sysconfig
try:
    # 获取 conda 环境路径
    conda_prefix = sys.prefix
    library_bin = os.path.join(conda_prefix, 'Library', 'bin')
    
    # 需要包含的 DLL 列表
    required_dlls = ['libexpat.dll', 'expat.dll']
    
    for dll_name in required_dlls:
        dll_path = os.path.join(library_bin, dll_name)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
            print(f"[SPEC] 添加必需 DLL: {{dll_name}}")
except Exception as e:
    print(f"[SPEC] 警告: 添加 conda DLL 时出错: {{e}}")

# 手动添加 CUDA 和 cuDNN 库（用于 GPU 加速）
try:
    # 获取 conda 环境路径
    conda_prefix = sys.prefix
    library_bin = os.path.join(conda_prefix, 'Library', 'bin')
    
    # 需要包含的 CUDA/cuDNN DLL 列表
    cuda_dlls = [
        # cuDNN 库（深度学习优化库）
        'cudnn64_8.dll',
        'cudnn_adv_infer64_8.dll',
        'cudnn_cnn_infer64_8.dll',
        'cudnn_ops_infer64_8.dll',
        # cuBLAS 库（线性代数运算）
        'cublas64_11.dll',
        'cublasLt64_11.dll',
        # CUDA 运行时
        'cudart64_110.dll',
        'cufft64_10.dll',
        # zlib压缩库（cuDNN依赖）
        'zlibwapi.dll',
    ]
    
    collected_cuda_dlls = []
    for dll_name in cuda_dlls:
        dll_path = os.path.join(library_bin, dll_name)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
            collected_cuda_dlls.append(dll_name)
            print(f"[SPEC] 添加 GPU 加速 DLL: {{dll_name}}")
        else:
            # 不是错误，某些DLL可能不存在（取决于CUDA版本）
            pass
    
    if collected_cuda_dlls:
        print(f"[SPEC] 已收集 {{len(collected_cuda_dlls)}} 个 GPU 加速库")
        print(f"[SPEC] 打包后的程序将支持 GPU 加速（如果系统有兼容的 NVIDIA GPU）")
    else:
        print(f"[SPEC] 未找到 GPU 加速库，打包的程序将仅支持 CPU 模式")
        
except Exception as e:
    print(f"[SPEC] 警告: 添加 CUDA/cuDNN DLL 时出错: {{e}}")
    print(f"[SPEC] 打包将继续，但程序可能无法使用 GPU 加速")


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'pytest', 'IPython', 'matplotlib', 'scipy',
        # 排除不必要的大型模块以减小打包体积
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # 不使用Qt
        'wx',  # 不使用wxPython
        'tornado', 'django', 'flask_sqlalchemy',  # 不需要的Web框架
        'numba', 'sympy',  # 不需要的科学计算库
        'docutils', 'pygments',  # 文档工具
        'PIL.ImageQt',  # Qt图像支持
        # 数据处理库（项目未使用）
        'pyarrow',  # Arrow/Parquet支持 - 约79MB
        'pandas',  # 数据分析框架 - 约17MB
        'sklearn', 'scikit-learn',  # 机器学习库 - 约30MB，已用纯numpy实现
        'skimage', 'scikit-image',  # 图像处理库 - 约20MB，已用OpenCV替代
        # 深度学习框架（项目不使用）
        'paddle', 'paddlepaddle', 'paddlex',  # PaddlePaddle框架 - 约783MB！
        'torch', 'pytorch', 'torchvision', 'torchaudio',  # PyTorch框架 - 约310MB
        'tensorflow', 'tf',  # TensorFlow框架
        'jax', 'flax',  # JAX框架
        # Hugging Face 生态（项目不使用）
        'transformers',  # Transformers库 - 约50MB
        'datasets',  # Datasets库
        'tokenizers',  # 分词器
        # 其他不必要的库
        'dask',  # 并行计算库
        'xarray',  # 多维数组库
        'zarr',  # 数组存储格式
        'h5py',  # HDF5文件支持
        'tables',  # PyTables（HDF5支持）
        'fastparquet',  # Parquet文件支持
        # 注意：不能排除snownlp本身，但可以通过hooks排除其数据文件
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
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={str(console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)
"""
    return spec_content

def build_version(version_name):
    """构建指定版本"""
    print_color(f"\n[2/4] 正在构建版本: {version_name} ...", "green")
    
    spec_filename = "MEMEFinder.spec"  # 统一使用MEMEFinder.spec
    
    # 1. 生成 Spec 文件
    print(f"  - 生成配置文件: {spec_filename}")
    spec_content = generate_spec(version_name)
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)
        
    # 2. 运行 PyInstaller
    print(f"  - 开始打包 (这可能需要几分钟)...")
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--distpath', 'releases',  # 输出到 releases 目录
        '--workpath', 'build',
        spec_filename
    ]
    
    try:
        subprocess.check_call(cmd)
        print_color(f"  ✓ {version_name} 打包成功!", "green")
        
        # 清理CUDA DLLs
        dist_path = Path('releases') / "MEMEFinder"
        if dist_path.exists():
            clean_cuda_dlls(dist_path)
        
        return True
    except subprocess.CalledProcessError:
        print_color(f"  ✗ {version_name} 打包失败!", "red")
        return False

def create_launcher(version_name, dist_dir):
    """创建启动脚本"""
    print(f"  - 创建启动脚本...")
    
    exe_name = "MEMEFinder.exe"  # 统一使用MEMEFinder.exe
    bat_path = dist_dir / "启动程序.bat"
    
    content = f"""@echo off
chcp 65001 > nul
title MEMEFinder ({version_name})
cd /d "%~dp0"
if not exist "{exe_name}" (
    echo 错误: 找不到 {exe_name}
    pause
    exit /b 1
)
start "" "{exe_name}"
"""
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print_color("="*60)
    print_color("       MEMEFinder GPU 版本打包工具", "green")
    print_color("="*60)
    
    # 1. 清理
    clean_build()
    
    # 确保 releases 目录存在
    if not os.path.exists('releases'):
        os.makedirs('releases')
        
    # 只打包 GPU 版本（包含 cuDNN 和 CUDA 运行时库）
    versions = ['gpu']
    results = {}
    
    # 2. 逐个构建
    for ver in versions:
        success = build_version(ver)
        results[ver] = success
        
        if success:
            # 3. 后处理 (创建启动脚本等)
            dist_path = Path('releases') / "MEMEFinder"
            if dist_path.exists():
                create_launcher(ver, dist_path)
    
    # 4. 总结
    print_color("\n[4/4] 打包结果汇总", "yellow")
    print("-" * 30)
    all_success = True
    for ver, success in results.items():
        status = "成功" if success else "失败"
        color = "green" if success else "red"
        print_color(f"{ver:<15}: {status}", color)
        if not success:
            all_success = False
            
    if all_success:
        print_color("\n✨ 所有版本打包完成！文件位于 releases/ 目录下。", "green")
    else:
        print_color("\n⚠️ 部分版本打包失败，请检查日志。", "red")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print_color(f"\n发生未预期的错误: {e}", "red")
        import traceback
        traceback.print_exc()
