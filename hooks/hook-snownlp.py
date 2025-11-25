# -*- coding: utf-8 -*-
"""
PyInstaller hook for snownlp
排除snownlp的数据文件以减小打包体积
"""

from PyInstaller.utils.hooks import get_package_paths

# 获取snownlp的路径
pkg_base, pkg_dir = get_package_paths('snownlp')

# 排除snownlp的数据文件
# 只保留必要的模块代码，数据文件将在运行时由用户安装
excludedimports = []
datas = []

# 注意：完全排除数据文件会导致snownlp无法工作
# 用户需要在打包后的环境中重新安装snownlp
hiddenimports = ['snownlp.sentiment']
