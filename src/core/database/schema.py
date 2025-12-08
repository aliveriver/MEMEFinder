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
                file_hash TEXT,
                phash TEXT,
                hsv_h INTEGER,
                hsv_s INTEGER,
                hsv_v INTEGER,
                color_hue_idx TINYINT,
                color_lightness TINYINT,
                color_histogram BLOB,
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
        
        # 标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT NOT NULL,
                created_time TEXT NOT NULL
            )
        """)
        
        # 图片-标签关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_tags (
                image_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                added_time TEXT NOT NULL,
                PRIMARY KEY (image_id, tag_id),
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        logger.info("数据库表结构初始化完成")
    
    @staticmethod
    def create_indexes(cursor):
        """创建数据库索引"""
        logger.info("创建数据库索引...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phash ON images(phash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hsv_h ON images(hsv_h)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_color_hue_idx ON images(color_hue_idx)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_color_sort ON images(color_hue_idx, color_lightness)
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
        
        # 标签相关索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag_name ON tags(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_tags_image ON image_tags(image_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_tags_tag ON image_tags(tag_id)
        """)
        
        logger.info("数据库索引创建完成")
