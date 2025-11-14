#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复打包环境中 stdout/stderr 为 None 的问题
必须在所有其他导入之前执行
"""

import sys
import os

# 在打包环境中，sys.stdout 和 sys.stderr 可能为 None
# 这会导致任何 print 语句崩溃
# 必须在最早期修复这个问题

class DummyFile:
    """虚拟文件对象，安全地忽略所有输出"""
    def write(self, x):
        pass
    
    def flush(self):
        pass
    
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = DummyFile()

if sys.stderr is None:
    sys.stderr = DummyFile()

# 确保 print 函数可以安全使用
def safe_print(*args, **kwargs):
    """安全的 print 函数"""
    try:
        print(*args, **kwargs)
    except:
        pass  # 忽略任何错误

# 替换内置的 print（可选）
# import builtins
# builtins.print = safe_print
