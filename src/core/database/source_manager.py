#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图源管理模块
"""

import sqlite3
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class SourceManager:
    """图源管理器"""
    
    def __init__(self, get_cursor_func):
        """
        Args:
            get_cursor_func: 获取数据库游标的函数
        """
        self.get_cursor = get_cursor_func
    
    def add_source(self, folder_path: str) -> bool:
        """添加图源文件夹"""
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO image_sources (folder_path, added_time)
                    VALUES (?, ?)
                """, (folder_path, datetime.now().isoformat()))
            logger.info(f"添加图源: {folder_path}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"图源已存在: {folder_path}")
            return False
    
    def get_sources(self) -> List[Dict]:
        """获取所有图源"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, folder_path, added_time, last_scan_time, enabled
                FROM image_sources
                ORDER BY added_time DESC
            """)
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    'id': row[0],
                    'folder_path': row[1],
                    'added_time': row[2],
                    'last_scan_time': row[3],
                    'enabled': bool(row[4])
                })
        logger.debug(f"获取到 {len(sources)} 个图源")
        return sources
    
    def remove_source(self, source_id: int):
        """删除图源"""
        with self.get_cursor(commit=True) as cursor:
            # 先获取图源信息
            cursor.execute("SELECT folder_path FROM image_sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            if row:
                folder_path = row[0]
                # 删除相关图片
                cursor.execute("DELETE FROM images WHERE source_id = ?", (source_id,))
                deleted_images = cursor.rowcount
                # 删除图源
                cursor.execute("DELETE FROM image_sources WHERE id = ?", (source_id,))
                logger.info(f"删除图源: {folder_path} (删除 {deleted_images} 张图片)")
            else:
                logger.warning(f"图源不存在: ID={source_id}")
    
    def toggle_source(self, source_id: int, enabled: bool):
        """启用/禁用图源"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE image_sources 
                SET enabled = ?
                WHERE id = ?
            """, (1 if enabled else 0, source_id))
        logger.info(f"{'启用' if enabled else '禁用'}图源: ID={source_id}")
    
    def update_scan_time(self, source_id: int):
        """更新扫描时间"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE image_sources 
                SET last_scan_time = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), source_id))
        logger.debug(f"更新扫描时间: ID={source_id}")
