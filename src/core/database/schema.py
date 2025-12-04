#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库表结构和初始化模块
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class DatabaseSchema:
    """数据库表结构管理"""
    
    @staticmethod
    def init_tables(cursor):
        """初始化所有数据库表"""
        logger.info("初始化数据库表结构...")
        
        # 图源文件夹表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                added_time TEXT NOT NULL,
                last_scan_time TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        # 图片信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                source_id INTEGER,
                ocr_text TEXT,
                filtered_text TEXT,
                emotion TEXT,
                emotion_positive REAL,
                emotion_negative REAL,
                added_time TEXT NOT NULL,
                processed INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                emotion_manual INTEGER DEFAULT 0,
                FOREIGN KEY (source_id) REFERENCES image_sources(id)
            )
        """)
        
        # 应用状态表（用于持久化断点/恢复状态）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        logger.info("数据库表结构初始化完成")
    
    @staticmethod
    def create_indexes(cursor):
        """创建数据库索引"""
        logger.info("创建数据库索引...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON images(file_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emotion ON images(emotion)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed ON images(processed)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_id ON images(source_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filtered_text ON images(filtered_text)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_favorite ON images(is_favorite)
        """)
        
        logger.info("数据库索引创建完成")
