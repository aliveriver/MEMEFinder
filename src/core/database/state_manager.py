#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用状态管理模块
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class StateManager:
    """应用状态管理器"""
    
    def __init__(self, get_cursor_func):
        """
        Args:
            get_cursor_func: 获取数据库游标的函数
        """
        self.get_cursor = get_cursor_func
    
    def set_app_state(self, key: str, value: str):
        """设置应用状态键值（持久化）"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, value))
        logger.debug(f"保存应用状态: {key} = {value}")

    def get_app_state(self, key: str) -> str:
        """获取应用状态键对应的值，找不到返回空字符串"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
            row = cursor.fetchone()
        
        value = row[0] if row and row[0] is not None else ''
        logger.debug(f"读取应用状态: {key} = {value}")
        return value
