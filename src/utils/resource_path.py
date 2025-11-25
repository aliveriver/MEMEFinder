#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源路径工具模块
用于处理开发环境和打包环境下的资源文件路径
"""

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    
    在开发环境中，从项目根目录获取资源
    在打包环境中，从 PyInstaller 的临时目录获取资源
    
    Args:
        relative_path: 相对于项目根目录的路径，例如 'assets/icon.ico'
    
    Returns:
        Path: 资源文件的绝对路径
    
    Examples:
        >>> icon_path = get_resource_path('assets/icon.ico')
        >>> config_path = get_resource_path('config/settings.json')
    """
    try:
        # PyInstaller 打包后会设置 sys._MEIPASS
        # 这是 PyInstaller 解压文件的临时目录
        if hasattr(sys, '_MEIPASS'):
            # 打包环境：从 _MEIPASS 目录获取
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境：从项目根目录获取
            # __file__ 是当前文件的路径，向上三级到达项目根目录
            base_path = Path(__file__).parent.parent.parent
        
        # 组合基础路径和相对路径
        resource_path = base_path / relative_path
        
        return resource_path
        
    except Exception:
        # 如果出错，返回相对路径（作为后备方案）
        return Path(relative_path)


def get_icon_path() -> Path:
    """
    获取应用程序图标路径
    
    Returns:
        Path: 图标文件路径，如果不存在则返回 None
    """
    icon_path = get_resource_path('assets/icon.ico')
    
    if icon_path.exists():
        return icon_path
    
    # 尝试其他可能的位置
    alternative_paths = [
        get_resource_path('assets/icon.png'),
        get_resource_path('img/icon.ico'),
        get_resource_path('img/icon.png'),
    ]
    
    for path in alternative_paths:
        if path.exists():
            return path
    
    return None


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    try:
        if hasattr(sys, '_MEIPASS'):
            # 打包环境：使用可执行文件所在目录
            return Path(sys.executable).parent
        else:
            # 开发环境：使用项目根目录
            return Path(__file__).parent.parent.parent
    except Exception:
        return Path.cwd()
