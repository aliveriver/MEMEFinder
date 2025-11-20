"""
PyInstaller hook for tkinter
修复 Tcl/Tk 版本冲突问题
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.compat import is_win
import os
import sys

# 收集 tkinter 相关的数据文件和库
datas = []
binaries = []

if is_win:
    # Windows 环境下，确保从正确的位置收集 Tcl/Tk
    try:
        # 获取 conda 环境路径
        conda_prefix = sys.prefix
        tcl_lib = os.path.join(conda_prefix, 'Library', 'lib')
        tcl_bin = os.path.join(conda_prefix, 'Library', 'bin')
        
        # 收集 tcl86t.dll 和 tk86t.dll
        for dll_name in ['tcl86t.dll', 'tk86t.dll']:
            dll_path = os.path.join(tcl_bin, dll_name)
            if os.path.exists(dll_path):
                binaries.append((dll_path, '.'))
                print(f"[HOOK-tkinter] 添加 DLL: {dll_name}")
        
        # 收集 tcl 和 tk 库文件
        # 查找实际的 tcl 版本目录
        for item in os.listdir(tcl_lib):
            if item.startswith('tcl8'):
                tcl_dir = os.path.join(tcl_lib, item)
                if os.path.isdir(tcl_dir):
                    datas.append((tcl_dir, os.path.join('_tcl_data', item)))
                    print(f"[HOOK-tkinter] 添加 Tcl 库: {item}")
            elif item.startswith('tk8'):
                tk_dir = os.path.join(tcl_lib, item)
                if os.path.isdir(tk_dir):
                    datas.append((tk_dir, os.path.join('_tk_data', item)))
                    print(f"[HOOK-tkinter] 添加 Tk 库: {item}")
        
        print(f"[HOOK-tkinter] 收集了 {len(binaries)} 个二进制文件")
        print(f"[HOOK-tkinter] 收集了 {len(datas)} 个数据目录")
        
    except Exception as e:
        print(f"[HOOK-tkinter] 警告: {e}")

# 隐藏导入
hiddenimports = ['tkinter', 'tkinter.ttk', '_tkinter']
