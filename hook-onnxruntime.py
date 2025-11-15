"""
PyInstaller hook for onnxruntime-gpu

这个 hook 确保 onnxruntime-gpu 的所有必要文件（特别是 CUDA 相关的 DLL）
都被正确打包到最终的可执行文件中。
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
from pathlib import Path
import os

# 收集所有 onnxruntime 的动态库（包括 CUDA DLL）
binaries = collect_dynamic_libs('onnxruntime')
datas = collect_data_files('onnxruntime')

# 额外确保 capi 目录下的所有 DLL 都被包含
try:
    import onnxruntime
    ort_path = Path(onnxruntime.__file__).parent
    
    # 收集 capi 目录下的所有 DLL
    capi_path = ort_path / 'capi'
    if capi_path.exists():
        for dll_file in capi_path.glob('*.dll'):
            # 添加到 binaries，保持原有的目录结构
            binaries.append((str(dll_file), 'onnxruntime/capi'))
        
        # 同时收集 .so 文件（Linux）和 .dylib 文件（macOS）
        for lib_file in capi_path.glob('*.so*'):
            binaries.append((str(lib_file), 'onnxruntime/capi'))
        for lib_file in capi_path.glob('*.dylib'):
            binaries.append((str(lib_file), 'onnxruntime/capi'))
    
    # 收集可能的 CUDA 相关 DLL（如果存在于 onnxruntime 目录中）
    for cuda_dll in ort_path.rglob('cudart*.dll'):
        binaries.append((str(cuda_dll), '.'))
    for cuda_dll in ort_path.rglob('cublas*.dll'):
        binaries.append((str(cuda_dll), '.'))
    for cuda_dll in ort_path.rglob('cudnn*.dll'):
        binaries.append((str(cuda_dll), '.'))
    
    print(f"[HOOK-onnxruntime] 收集了 {len(binaries)} 个二进制文件")
    print(f"[HOOK-onnxruntime] 收集了 {len(datas)} 个数据文件")
    
except Exception as e:
    print(f"[HOOK-onnxruntime] 警告: {e}")

# 隐藏导入
hiddenimports = [
    'onnxruntime.capi',
    'onnxruntime.capi.onnxruntime_pybind11_state',
]
