#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理模块（优化版）
- 连接池管理
- 批量操作优化
- 事务管理
- 详细日志记录
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Set, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager
import threading
import sys

# 添加日志支持
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class DatabaseConnectionPool:
    """SQLite连接池 - 线程安全"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = []
        self._lock = threading.Lock()
        self._local = threading.local()
        
        logger.debug(f"初始化数据库连接池: {db_path} (大小: {pool_size})")
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        # 使用线程本地存储，避免跨线程使用连接
        if hasattr(self._local, 'conn') and self._local.conn:
            return self._local.conn
        
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._local.conn = conn
                return conn
        
        # 创建新连接
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0  # 30秒超时
        )
        # 优化SQLite性能
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # 平衡安全和性能
        conn.execute("PRAGMA cache_size=-64000")  # 64MB缓存
        conn.execute("PRAGMA temp_store=MEMORY")  # 内存存储临时表
        
        self._local.conn = conn
        logger.debug("创建新数据库连接")
        return conn
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还连接到池"""
        if not conn:
            return
        
        with self._lock:
            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
            else:
                conn.close()
                logger.debug("连接池已满，关闭连接")
        
        if hasattr(self._local, 'conn'):
            self._local.conn = None
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()
            logger.info("已关闭所有数据库连接")


class ImageDatabase:
    """图片数据库管理（优化版）"""
    
    def __init__(self, db_path: str = "meme_finder.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, pool_size)
        logger.info(f"初始化数据库: {db_path}")
        self.init_database()
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """获取数据库游标的上下文管理器"""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()
    
    def init_database(self):
        """初始化数据库表"""
        logger.info("初始化数据库表结构...")
        
        with self.get_cursor(commit=True) as cursor:
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_id ON images(source_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_filtered_text ON images(filtered_text)
            """)

            # 应用状态表（用于持久化断点/恢复状态）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
        
        logger.info("数据库表结构初始化完成")
    
    # ==================== 图源管理 ====================
    
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
    
    # ==================== 图片管理 ====================
    
    def get_image_hashes(self, source_id: int = None) -> Set[str]:
        """获取已存在的图片哈希值"""
        with self.get_cursor() as cursor:
            if source_id:
                cursor.execute("SELECT file_hash FROM images WHERE source_id = ?", (source_id,))
            else:
                cursor.execute("SELECT file_hash FROM images")
            hashes = {row[0] for row in cursor.fetchall()}
        logger.debug(f"获取到 {len(hashes)} 个图片哈希值")
        return hashes
    
    def add_image(self, file_path: str, file_hash: str, source_id: int) -> bool:
        """添加新图片"""
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO images (file_path, file_hash, source_id, added_time)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_hash, source_id, datetime.now().isoformat()))
            logger.debug(f"添加图片: {Path(file_path).name}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"图片已存在: {Path(file_path).name}")
            return False
    
    def add_images_batch(self, images: List[Tuple[str, str, int]]) -> int:
        """批量添加图片
        
        Args:
            images: [(file_path, file_hash, source_id), ...]
            
        Returns:
            成功添加的数量
        """
        if not images:
            return 0
        
        added_count = 0
        current_time = datetime.now().isoformat()
        
        try:
            with self.get_cursor(commit=True) as cursor:
                # 使用executemany进行批量插入
                data = [(fp, fh, sid, current_time) for fp, fh, sid in images]
                cursor.executemany("""
                    INSERT OR IGNORE INTO images (file_path, file_hash, source_id, added_time)
                    VALUES (?, ?, ?, ?)
                """, data)
                added_count = cursor.rowcount
            
            logger.info(f"批量添加图片: {added_count}/{len(images)} 张")
            return added_count
        except Exception as e:
            logger.error(f"批量添加图片失败: {e}")
            return 0
    
    def get_unprocessed_images(self, limit: int = 100) -> List[Dict]:
        """获取未处理的图片"""
        with self.get_cursor() as cursor:
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
        logger.debug(f"获取到 {len(images)} 张未处理图片")
        return images
    
    def update_image_data(self, image_id: int, ocr_text: str, filtered_text: str, 
                         emotion: str, pos_score: float, neg_score: float):
        """更新图片处理结果"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE images 
                SET ocr_text = ?, filtered_text = ?, emotion = ?,
                    emotion_positive = ?, emotion_negative = ?, processed = 1
                WHERE id = ?
            """, (ocr_text, filtered_text, emotion, pos_score, neg_score, image_id))
        logger.debug(f"更新图片数据: ID={image_id}, 情绪={emotion}")
    
    def update_images_batch(self, updates: List[Tuple[int, str, str, str, float, float]]) -> int:
        """批量更新图片数据
        
        Args:
            updates: [(image_id, ocr_text, filtered_text, emotion, pos_score, neg_score), ...]
            
        Returns:
            更新的数量
        """
        if not updates:
            return 0
        
        try:
            with self.get_cursor(commit=True) as cursor:
                # 准备批量更新数据
                data = [(ocr, filt, emo, pos, neg, 1, img_id) 
                       for img_id, ocr, filt, emo, pos, neg in updates]
                cursor.executemany("""
                    UPDATE images 
                    SET ocr_text = ?, filtered_text = ?, emotion = ?,
                        emotion_positive = ?, emotion_negative = ?, processed = ?
                    WHERE id = ?
                """, data)
                updated_count = cursor.rowcount
            
            logger.info(f"批量更新图片数据: {updated_count} 张")
            return updated_count
        except Exception as e:
            logger.error(f"批量更新图片数据失败: {e}")
            return 0
    
    # ==================== 搜索功能 ====================
    
    def search_images(self, keyword: str = "", emotion: str = "", limit: int = 100) -> List[Dict]:
        """搜索图片"""
        with self.get_cursor() as cursor:
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
            
            query += " ORDER BY added_time DESC LIMIT ?"
            params.append(limit)
            
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
        
        logger.info(f"搜索图片: 关键词='{keyword}', 情绪='{emotion}', 结果={len(results)}张")
        return results

    def get_images_count(self, processed: int = None, keyword: str = "", emotion: str = "") -> int:
        """获取符合条件的图片总数（用于分页）

        Args:
            processed: 1 for 已处理，0 为未处理，None 表示全部
        """
        with self.get_cursor() as cursor:
            query = "SELECT COUNT(*) FROM images WHERE 1=1"
            params = []
            if processed is not None:
                query += " AND processed = ?"
                params.append(processed)
            if keyword:
                query += " AND (filtered_text LIKE ? OR ocr_text LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if emotion:
                query += " AND emotion = ?"
                params.append(emotion)

            cursor.execute(query, params)
            total = cursor.fetchone()[0]
        
        logger.debug(f"统计图片数量: {total} 张 (processed={processed}, keyword='{keyword}', emotion='{emotion}')")
        return total

    def get_images_page(self, page: int = 1, page_size: int = 20, processed: int = None,
                        keyword: str = "", emotion: str = "") -> List[Dict]:
        """分页获取图片数据，返回指定页的记录列表

        Args:
            page: 页码，从1开始
            page_size: 每页条数
            processed: 1/0/None 同 get_images_count
        """
        offset = max(0, (page - 1) * page_size)
        
        with self.get_cursor() as cursor:
            query = "SELECT id, file_path, filtered_text, emotion, emotion_positive, emotion_negative, processed FROM images WHERE 1=1"
            params = []
            if processed is not None:
                query += " AND processed = ?"
                params.append(processed)
            if keyword:
                query += " AND (filtered_text LIKE ? OR ocr_text LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if emotion:
                query += " AND emotion = ?"
                params.append(emotion)

            query += " ORDER BY added_time DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'file_path': row[1],
                    'text': row[2],
                    'emotion': row[3],
                    'pos_score': row[4],
                    'neg_score': row[5],
                    'processed': bool(row[6])
                })
        
        logger.debug(f"分页查询: 第{page}页, 每页{page_size}条, 返回{len(results)}条")
        return results
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_cursor() as cursor:
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
        
        stats = {
            'total': total,
            'processed': processed,
            'unprocessed': total - processed,
            'emotions': emotions
        }
        
        logger.debug(f"统计信息: 总数={total}, 已处理={processed}, 未处理={total-processed}")
        return stats
    
    # ==================== 应用状态持久化（断点/恢复） ====================

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
    
    # ==================== 数据清理和维护 ====================
    
    def vacuum(self):
        """优化数据库，回收空间"""
        logger.info("开始数据库VACUUM优化...")
        conn = self.pool.get_connection()
        try:
            conn.execute("VACUUM")
            conn.commit()
            logger.info("数据库VACUUM优化完成")
        except Exception as e:
            logger.error(f"数据库VACUUM失败: {e}")
        finally:
            self.pool.return_connection(conn)
    
    def delete_processed_images(self, days: int = 30) -> int:
        """删除N天前处理过的图片记录
        
        Args:
            days: 保留最近N天的数据
            
        Returns:
            删除的记录数
        """
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM images 
                WHERE processed = 1 AND added_time < ?
            """, (cutoff_date,))
            deleted = cursor.rowcount
        
        logger.info(f"清理旧数据: 删除了 {deleted} 条 {days} 天前的记录")
        return deleted
    
    def close(self):
        """关闭数据库连接池"""
        self.pool.close_all()
        logger.info("数据库连接池已关闭")
