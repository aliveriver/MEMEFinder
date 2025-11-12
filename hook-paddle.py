"""
PyInstaller hook for paddle module
确保paddle模块及其所有依赖被正确收集
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# 收集paddle的所有子模块
hiddenimports = collect_submodules('paddle')

# 收集paddle的所有数据文件和二进制文件
datas, binaries, hiddenimports_extra = collect_all('paddle')
hiddenimports += hiddenimports_extra

# 添加paddle的核心模块
hiddenimports += [
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
]

