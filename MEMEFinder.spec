# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from pathlib import Path
import os
import sys

# 数据文件列表
datas = [
    ('src', 'src'), 
    ('README.md', '.'), 
    ('LICENSE', '.'),
]

# 添加models目录（如果存在）
models_dir = Path('models')
if models_dir.exists():
    # 检查是否有onnx模型文件或snownlp数据
    onnx_files = list(models_dir.glob('*.onnx'))
    snownlp_dir = models_dir / 'snownlp'
    has_snownlp = snownlp_dir.exists() and any(snownlp_dir.rglob('*.marshal'))
    
    if onnx_files or has_snownlp:
        if onnx_files:
            print(f"[SPEC] 找到 {len(onnx_files)} 个ONNX模型文件")
        if has_snownlp:
            snownlp_files = len(list(snownlp_dir.rglob('*')))
            print(f"[SPEC] 找到 SnowNLP 数据文件 ({snownlp_files} 个文件)")
        print(f"[SPEC] 将打包 models 目录到应用中")
        # 添加models目录（包括所有子目录和文件）
        datas.append(('models', 'models'))
    else:
        print("[SPEC] models目录存在但没有模型文件，请先运行: python copy_models.py")
else:
    print("[SPEC] ⚠️ models目录不存在！请先运行: python copy_models.py")
    print("[SPEC]    打包将继续，但运行时可能需要下载模型")

binaries = []

# ==================== 关键修复：手动添加 ONNX Runtime GPU DLL 文件 ====================
print("[SPEC] 检查并收集 ONNX Runtime GPU 依赖...")
try:
    import onnxruntime as ort
    ort_path = Path(ort.__file__).parent
    ort_capi_path = ort_path / 'capi'
    
    # 检查是否是 GPU 版本
    providers = ort.get_available_providers()
    is_gpu_version = 'CUDAExecutionProvider' in providers or 'TensorrtExecutionProvider' in providers
    
    if is_gpu_version:
        print(f"[SPEC] ✓ 检测到 ONNX Runtime GPU 版本")
        print(f"[SPEC]   支持的 Providers: {providers}")
        print(f"[SPEC]   ONNX Runtime 路径: {ort_path}")
        
        # 收集所有 DLL 文件
        if ort_capi_path.exists():
            dll_files = list(ort_capi_path.glob('*.dll'))
            if dll_files:
                print(f"[SPEC]   找到 {len(dll_files)} 个 DLL 文件:")
                for dll in dll_files:
                    # 添加到 binaries，目标路径为 onnxruntime/capi/
                    binaries.append((str(dll), 'onnxruntime/capi'))
                    print(f"[SPEC]     - {dll.name}")
                print(f"[SPEC] ✓ 已添加 ONNX Runtime GPU DLL 到打包列表")
            else:
                print(f"[SPEC] ⚠️ 警告: capi 目录下没有找到 DLL 文件")
        else:
            print(f"[SPEC] ⚠️ 警告: capi 目录不存在: {ort_capi_path}")
        
        # 同时检查是否需要添加 CUDA 运行库 DLL
        # 注意：这些 DLL 通常在系统 PATH 中，但为了保险起见，我们也尝试收集
        cuda_dll_names = [
            'cudart64_*.dll',
            'cublas64_*.dll', 
            'cublasLt64_*.dll',
            'cudnn64_*.dll',
            'cudnn_*.dll',
        ]
        
        # 搜索 CUDA DLL（在 onnxruntime 或系统路径中）
        found_cuda_dlls = []
        for pattern in cuda_dll_names:
            # 先在 onnxruntime 目录搜索
            cuda_dlls = list(ort_path.rglob(pattern))
            if cuda_dlls:
                for dll in cuda_dlls:
                    binaries.append((str(dll), '.'))
                    found_cuda_dlls.append(dll.name)
        
        if found_cuda_dlls:
            print(f"[SPEC] ✓ 找到并添加 CUDA 运行库 DLL:")
            for dll_name in found_cuda_dlls:
                print(f"[SPEC]     - {dll_name}")
        else:
            print(f"[SPEC] ⚠️ 注意: 未在 onnxruntime 目录找到 CUDA 运行库 DLL")
            print(f"[SPEC]         GPU 功能依赖系统已安装的 CUDA 运行库")
            print(f"[SPEC]         如果目标机器没有 CUDA，程序会自动降级到 CPU 模式")
    else:
        print(f"[SPEC] 检测到 ONNX Runtime CPU 版本")
        print(f"[SPEC]   支持的 Providers: {providers}")
        print(f"[SPEC]   打包的程序将只支持 CPU 模式")
        
except ImportError:
    print("[SPEC] ⚠️ onnxruntime 未安装，跳过 GPU DLL 收集")
except Exception as e:
    print(f"[SPEC] ⚠️ 收集 ONNX Runtime GPU DLL 时出错: {e}")
    print(f"[SPEC]    将继续打包，但 GPU 功能可能不可用")

print("[SPEC] " + "=" * 60)

hiddenimports = [
    'unittest', 'unittest.mock', 'doctest',
    # OCR相关模块 - RapidOCR
    'rapidocr_onnxruntime',
    'onnxruntime',
    # 情绪分析模块
    'snownlp',
    # 其他依赖
    'cv2', 'PIL', 'numpy', 'pandas', 'tkinter', 'sqlite3', 'flask', 'flask_cors'
]

# 收集 RapidOCR 的所有子模块和数据
print("[SPEC] 开始收集 RapidOCR 模块...")
try:
    tmp_ret = collect_all('rapidocr_onnxruntime')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] rapidocr_onnxruntime: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: rapidocr_onnxruntime collect_all失败: {e}")

try:
    hiddenimports += collect_submodules('rapidocr_onnxruntime')
    print("[SPEC] rapidocr_onnxruntime子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: rapidocr_onnxruntime子模块收集失败: {e}")

# 收集 ONNX Runtime
print("[SPEC] 开始收集 ONNX Runtime...")
try:
    tmp_ret = collect_all('onnxruntime')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] onnxruntime: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: onnxruntime collect_all失败: {e}")

# 收集snownlp的数据文件
try:
    tmp_ret = collect_all('snownlp')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] snownlp: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: snownlp collect_all失败: {e}")

try:
    hiddenimports += collect_submodules('snownlp')
    print("[SPEC] snownlp子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: snownlp子模块收集失败: {e}")

# 收集 OpenCV
try:
    tmp_ret = collect_all('cv2')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] cv2: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: cv2 collect_all失败: {e}")

print("[SPEC] 模块收集完成")


a = Analysis(
    ['main.py'],
    pathex=[],  # 添加当前目录到路径，以便找到hook文件
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],  # 使用当前目录的hook文件
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'IPython'],
    noarchive=False,
    optimize=0,
    # 确保收集所有paddle相关的二进制文件和数据文件
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)
pyz = PYZ(a.pure)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MEMEFinder',
)
