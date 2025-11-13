# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

# 检查哪些补丁文件存在
patch_files = [
    'paddlex_runtime_patch.py',  # 最重要的补丁！
    'paddlex_patch.py',
    'paddle_runtime_patch.py',
    'cv2_patch.py',
    'snownlp_patch.py',
    'ocr_model_patch.py',
    'pyclipper_patch.py',
    'stdout_stderr_patch.py'
]

datas = [
    ('src', 'src'), 
    ('README.md', '.'), 
    ('LICENSE', '.'),
]

# 只添加存在的补丁文件
for patch in patch_files:
    if Path(patch).exists():
        datas.append((patch, '.'))
        print(f"[SPEC] 添加补丁文件: {patch}")

binaries = []

# 手动添加pyclipper的二进制文件（collect_all可能无法正确收集）
try:
    import pyclipper
    import site
    from pathlib import Path
    
    # 获取pyclipper的安装路径
    pyclipper_path = Path(pyclipper.__file__).parent
    
    # 查找所有.pyd和.dll文件
    for ext in ['*.pyd', '*.dll', '*.so']:
        for binary_file in pyclipper_path.glob(ext):
            binaries.append((str(binary_file), 'pyclipper'))
            print(f"[SPEC] 手动添加pyclipper二进制文件: {binary_file.name}")
    
    if not any('pyclipper' in str(b[1]) for b in binaries):
        print("[SPEC] 警告: 未找到pyclipper二进制文件，可能需要手动指定路径")
except Exception as e:
    print(f"[SPEC] 警告: 查找pyclipper二进制文件失败: {e}")
hiddenimports = [
    'unittest', 'unittest.mock', 'doctest',
    # OCR相关模块
    'pyclipper',  # PaddleOCR需要
    # 情绪分析模块
    'snownlp',
    # Paddle核心模块
    'paddle',
    'paddle.framework',
    'paddle.framework.core',
    'paddle.framework.io',
    'paddle.fluid',
    'paddle.fluid.core',
    'paddle.fluid.framework',
    'paddle.fluid.io',
    'paddle.fluid.layers',
    'paddle.fluid.dygraph',
    'paddle.fluid.executor',
    'paddle.fluid.program_guard',
    # PaddleOCR和PaddleNLP
    'paddleocr',
    'paddlenlp',
    # PaddleX - 添加更多具体的模块
    'paddlex',
    'paddlex.inference',
    'paddlex.inference.pipelines',
    'paddlex.inference.pipelines.ocr',
    'paddlex.inference.models',
    'paddlex.modules',
    'paddlex.utils',
    'paddlex.utils.deps',  # 依赖检查模块
    'paddlex.utils.env',
    'paddlex.utils.logging',
    # 其他依赖
    'cv2', 'PIL', 'numpy', 'pandas', 'tkinter', 'sqlite3', 'sklearn', 'scipy', 'pypdfium2'
]

# 收集所有子模块 - 必须确保paddle被收集
print("[SPEC] 开始收集paddle模块...")
try:
    hiddenimports += collect_submodules('paddlex')
    print("[SPEC] paddlex子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: paddlex子模块收集失败: {e}")

try:
    paddle_submodules = collect_submodules('paddle')
    hiddenimports += paddle_submodules
    print(f"[SPEC] paddle子模块收集完成: {len(paddle_submodules)} 个模块")
except Exception as e:
    print(f"[SPEC] 警告: paddle子模块收集失败: {e}")

try:
    hiddenimports += collect_submodules('paddleocr')
    print("[SPEC] paddleocr子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: paddleocr子模块收集失败: {e}")

try:
    hiddenimports += collect_submodules('paddlenlp')
    print("[SPEC] paddlenlp子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: paddlenlp子模块收集失败: {e}")

try:
    hiddenimports += collect_submodules('pypdfium2')
    print("[SPEC] pypdfium2子模块收集完成")
except Exception as e:
    print(f"[SPEC] 警告: pypdfium2子模块收集失败: {e}")

# 使用collect_all收集所有数据文件和二进制文件
print("[SPEC] 开始收集所有数据文件和二进制文件...")
try:
    tmp_ret = collect_all('paddlex')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] paddlex: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: paddlex collect_all失败: {e}")

try:
    tmp_ret = collect_all('paddle')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] paddle: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: paddle collect_all失败: {e}")

try:
    tmp_ret = collect_all('paddleocr')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] paddleocr: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: paddleocr collect_all失败: {e}")

try:
    tmp_ret = collect_all('paddlenlp')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] paddlenlp: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: paddlenlp collect_all失败: {e}")

try:
    tmp_ret = collect_all('pypdfium2')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] pypdfium2: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: pypdfium2 collect_all失败: {e}")

# 收集pyclipper（PaddleOCR必需，包含C扩展）
print("[SPEC] 开始收集pyclipper模块...")
try:
    tmp_ret = collect_all('pyclipper')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    print(f"[SPEC] pyclipper: {len(tmp_ret[0])} 数据文件, {len(tmp_ret[1])} 二进制文件")
except Exception as e:
    print(f"[SPEC] 警告: pyclipper collect_all失败: {e}")

try:
    pyclipper_submodules = collect_submodules('pyclipper')
    hiddenimports += pyclipper_submodules
    print(f"[SPEC] pyclipper子模块收集完成: {len(pyclipper_submodules)} 个模块")
except Exception as e:
    print(f"[SPEC] 警告: pyclipper子模块收集失败: {e}")

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
