#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查找pyclipper的二进制文件位置
"""

import pyclipper
import os
from pathlib import Path

# 获取pyclipper的安装路径
pyclipper_path = Path(pyclipper.__file__).parent
print(f"pyclipper安装路径: {pyclipper_path}")

# 查找所有.pyd和.dll文件
pyd_files = list(pyclipper_path.glob("*.pyd"))
dll_files = list(pyclipper_path.glob("*.dll"))

print(f"\n找到的.pyd文件:")
for f in pyd_files:
    print(f"  {f.name} -> {f}")

print(f"\n找到的.dll文件:")
for f in dll_files:
    print(f"  {f.name} -> {f}")

# 生成spec文件需要的格式
print(f"\n=== 用于spec文件的格式 ===")
if pyd_files or dll_files:
    print("binaries = [")
    for f in pyd_files + dll_files:
        # 获取相对于site-packages的路径
        rel_path = f.relative_to(pyclipper_path)
        print(f"    (r'{f}', 'pyclipper'),")
    print("]")
else:
    print("未找到二进制文件！")

