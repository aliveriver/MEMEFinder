"""
PyInstaller hook for onnxruntime

这个 hook 确保 onnxruntime 的所有必要文件被正确打包，
但排除 CUDA DLLs 以使用系统的 CUDA 安装。
"""

from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path
import os

# 收集数据文件
datas = collect_data_files('onnxruntime')

# CUDA DLL 模式列表 - 这些将使用系统CUDA
cuda_dll_patterns = [
    'cublas', 'cublaslt', 'cudnn', 'cudart', 'cufft',
    'curand', 'cusolver', 'cusparse', 'nvrtc', 'nvcuda',
    'nvjitlink'  # CUDA 12+
]

# 手动收集 onnxruntime 的 DLL（排除CUDA DLLs）
binaries = []

try:
    import onnxruntime
    ort_path = Path(onnxruntime.__file__).parent
    
    # 收集 capi 目录下的所有 DLL（但排除CUDA DLLs）
    capi_path = ort_path / 'capi'
    if capi_path.exists():
        excluded_count = 0
        included_count = 0
        
        for dll_file in capi_path.glob('*.dll'):
            dll_name = dll_file.name.lower()
            # 检查是否是CUDA DLL
            is_cuda_dll = any(pattern in dll_name for pattern in cuda_dll_patterns)
            
            if not is_cuda_dll:
                # 添加到 binaries，保持原有的目录结构
                binaries.append((str(dll_file), 'onnxruntime/capi'))
                included_count += 1
            else:
                print(f"[HOOK-onnxruntime] 排除CUDA DLL: {dll_file.name}（将使用系统CUDA）")
                excluded_count += 1
        
        # 同时收集 .so 文件（Linux）和 .dylib 文件（macOS）
        for lib_file in capi_path.glob('*.so*'):
            binaries.append((str(lib_file), 'onnxruntime/capi'))
        for lib_file in capi_path.glob('*.dylib'):
            binaries.append((str(lib_file), 'onnxruntime/capi'))
    
    print(f"[HOOK-onnxruntime] 添加了 {included_count} 个DLL，排除了 {excluded_count} 个CUDA DLL")
    print(f"[HOOK-onnxruntime] 收集了 {len(datas)} 个数据文件")
    print(f"[HOOK-onnxruntime] GPU版本将使用系统CUDA库")
    
except Exception as e:
    print(f"[HOOK-onnxruntime] 警告: {e}")

# 隐藏导入 - 确保 onnxruntime 的所有关键模块都被包含
hiddenimports = [
    'onnxruntime.capi',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'onnxruntime.capi._pybind_state',
    'onnxruntime.transformers',
    # 以下是关键的枚举和类，需要明确导入
    'onnxruntime.GraphOptimizationLevel',
    'onnxruntime.ExecutionMode',
    'onnxruntime.SessionOptions',
    'onnxruntime.RunOptions',
    'onnxruntime.InferenceSession',
]
