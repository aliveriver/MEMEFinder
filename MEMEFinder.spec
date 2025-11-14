# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

datas = [
    ('src', 'src'), 
    ('README.md', '.'), 
    ('LICENSE', '.'),
]

binaries = []

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
