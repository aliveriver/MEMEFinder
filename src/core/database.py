#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理模块
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Set, Any


class ImageDatabase:
    """图片数据库管理"""
    
    def __init__(self, db_path: str = "meme_finder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                FOREIGN KEY (source_id) REFERENCES image_sources(id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON images(file_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emotion ON images(emotion)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed ON images(processed)
        """)
        
        conn.commit()
        conn.close()
    
    # ==================== 图源管理 ====================
    
    def add_source(self, folder_path: str) -> bool:
        """添加图源文件夹"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO image_sources (folder_path, added_time)
                VALUES (?, ?)
            """, (folder_path, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_sources(self) -> List[Dict]:
        """获取所有图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.close()
        return sources
    
    def remove_source(self, source_id: int):
        """删除图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # 删除相关图片
        cursor.execute("DELETE FROM images WHERE source_id = ?", (source_id,))
        # 删除图源
        cursor.execute("DELETE FROM image_sources WHERE id = ?", (source_id,))
        conn.commit()
        conn.close()
    
    def toggle_source(self, source_id: int, enabled: bool):
        """启用/禁用图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE image_sources 
            SET enabled = ?
            WHERE id = ?
        """, (1 if enabled else 0, source_id))
        conn.commit()
        conn.close()
    
    def update_scan_time(self, source_id: int):
        """更新扫描时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE image_sources 
            SET last_scan_time = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), source_id))
        conn.commit()
        conn.close()
    
    # ==================== 图片管理 ====================
    
    def get_image_hashes(self, source_id: int = None) -> Set[str]:
        """获取已存在的图片哈希值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if source_id:
            cursor.execute("SELECT file_hash FROM images WHERE source_id = ?", (source_id,))
        else:
            cursor.execute("SELECT file_hash FROM images")
        hashes = {row[0] for row in cursor.fetchall()}
        conn.close()
        return hashes
    
    def add_image(self, file_path: str, file_hash: str, source_id: int):
        """添加新图片"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO images (file_path, file_hash, source_id, added_time)
                VALUES (?, ?, ?, ?)
            """, (file_path, file_hash, source_id, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_unprocessed_images(self, limit: int = 100) -> List[Dict]:
        """获取未处理的图片"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, source_id
            FROM images
            WHERE processed = 0
            LIMIT ?
        """, (limit,))
        images = []
        for row in cursor.fetchall():
            images.append({
                'id': row[0],
                'file_path': row[1],
                'source_id': row[2]
            })
        conn.close()
        return images
    
    def update_image_data(self, image_id: int, ocr_text: str, filtered_text: str, 
                         emotion: str, pos_score: float, neg_score: float):
        """更新图片处理结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE images 
            SET ocr_text = ?, filtered_text = ?, emotion = ?,
                emotion_positive = ?, emotion_negative = ?, processed = 1
            WHERE id = ?
        """, (ocr_text, filtered_text, emotion, pos_score, neg_score, image_id))
        conn.commit()
        conn.close()
    
    # ==================== 搜索功能 ====================
    
    def search_images(self, keyword: str = "", emotion: str = "") -> List[Dict]:
        """搜索图片"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, file_path, filtered_text, emotion, 
                   emotion_positive, emotion_negative
            FROM images
            WHERE processed = 1
        """
        params = []
        
        if keyword:
            query += " AND (filtered_text LIKE ? OR ocr_text LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if emotion:
            query += " AND emotion = ?"
            params.append(emotion)
        
        query += " ORDER BY added_time DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'file_path': row[1],
                'text': row[2],
                'emotion': row[3],
                'pos_score': row[4],
                'neg_score': row[5]
            })
        conn.close()
        return results
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总图片数
        cursor.execute("SELECT COUNT(*) FROM images")
        total = cursor.fetchone()[0]
        
        # 已处理数
        cursor.execute("SELECT COUNT(*) FROM images WHERE processed = 1")
        processed = cursor.fetchone()[0]
        
        # 情绪分布
        cursor.execute("""
            SELECT emotion, COUNT(*) 
            FROM images 
            WHERE processed = 1 
            GROUP BY emotion
        """)
        emotions = dict(cursor.fetchall())
        
        conn.close()
        return {
            'total': total,
            'processed': processed,
            'unprocessed': total - processed,
            'emotions': emotions
        }
