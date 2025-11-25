"""
PyInstaller hook for rapidocr_onnxruntime

这个 hook 确保 rapidocr_onnxruntime 的模型文件被正确打包到应用程序中。
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path
import os

# 收集所有数据文件
datas = collect_data_files('rapidocr_onnxruntime')

# 收集所有子模块
hiddenimports = collect_submodules('rapidocr_onnxruntime')

# 手动添加 models 目录下的 .onnx 文件
try:
    import rapidocr_onnxruntime
    rapidocr_path = Path(rapidocr_onnxruntime.__file__).parent
    models_dir = rapidocr_path / 'models'
    
    if models_dir.exists():
        model_files = list(models_dir.glob('*.onnx'))
        
        if model_files:
            print(f"[HOOK-rapidocr] 找到 {len(model_files)} 个模型文件")
            
            # 添加每个模型文件到 datas
            for model_file in model_files:
                # 目标路径：rapidocr_onnxruntime/models/
                datas.append((str(model_file), 'rapidocr_onnxruntime/models'))
                print(f"[HOOK-rapidocr] 添加模型: {model_file.name}")
        else:
            print("[HOOK-rapidocr] 警告: models 目录存在但未找到 .onnx 文件")
    else:
        print(f"[HOOK-rapidocr] 警告: 未找到 models 目录: {models_dir}")
        
except Exception as e:
    print(f"[HOOK-rapidocr] 错误: {e}")

print(f"[HOOK-rapidocr] 收集了 {len(datas)} 个数据文件")
print(f"[HOOK-rapidocr] 收集了 {len(hiddenimports)} 个隐藏导入")
