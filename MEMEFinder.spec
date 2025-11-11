# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('src', 'src'), ('README.md', '.'), ('paddlex_patch.py', '.')]
binaries = []
hiddenimports = ['unittest', 'unittest.mock', 'doctest', 'paddleocr', 'paddlenlp', 'paddle', 'paddlex', 'paddlex.inference', 'paddlex.inference.pipelines', 'paddlex.inference.pipelines.ocr', 'paddlex.inference.models', 'paddlex.modules', 'cv2', 'PIL', 'numpy', 'pandas', 'tkinter', 'sqlite3', 'sklearn', 'scipy', 'pypdfium2']
hiddenimports += collect_submodules('paddlex')
hiddenimports += collect_submodules('paddle')
hiddenimports += collect_submodules('paddleocr')
hiddenimports += collect_submodules('paddlenlp')
hiddenimports += collect_submodules('pypdfium2')
tmp_ret = collect_all('paddlex')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddle')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddleocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddlenlp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pypdfium2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'IPython'],
    noarchive=False,
    optimize=0,
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
