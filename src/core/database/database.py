#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理模块（重构版）
整合所有数据库功能
"""

from contextlib import contextmanager
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

from .connection_pool import DatabaseConnectionPool
from .schema import DatabaseSchema
from .source_manager import SourceManager
from .image_manager import ImageManager
from .search_manager import SearchManager
from .state_manager import StateManager

logger = get_logger()


class ImageDatabase:
    """图片数据库管理（整合版）"""
    
    def __init__(self, db_path: str = "meme_finder.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, pool_size)
        logger.info(f"初始化数据库: {db_path}")
        
        # 初始化数据库表结构
        self.init_database()
        
        # 初始化各功能管理器
        self._source_manager = SourceManager(self.get_cursor)
        self._image_manager = ImageManager(self.get_cursor)
        self._search_manager = SearchManager(self.get_cursor)
        self._state_manager = StateManager(self.get_cursor)
    
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
        with self.get_cursor(commit=True) as cursor:
            DatabaseSchema.init_tables(cursor)
            DatabaseSchema.create_indexes(cursor)
    
    # ==================== 图源管理（委托给 SourceManager） ====================
    
    def add_source(self, folder_path: str) -> bool:
        """添加图源文件夹"""
        return self._source_manager.add_source(folder_path)
    
    def get_sources(self):
        """获取所有图源"""
        return self._source_manager.get_sources()
    
    def remove_source(self, source_id: int):
        """删除图源"""
        self._source_manager.remove_source(source_id)
    
    def toggle_source(self, source_id: int, enabled: bool):
        """启用/禁用图源"""
        self._source_manager.toggle_source(source_id, enabled)
    
    def update_scan_time(self, source_id: int):
        """更新扫描时间"""
        self._source_manager.update_scan_time(source_id)
    
    # ==================== 图片管理（委托给 ImageManager） ====================
    
    def get_image_hashes(self, source_id: int = None):
        """获取已存在的图片哈希值"""
        return self._image_manager.get_image_hashes(source_id)
    
    def add_image(self, file_path: str, file_hash: str, source_id: int) -> bool:
        """添加新图片"""
        return self._image_manager.add_image(file_path, file_hash, source_id)
    
    def add_images_batch(self, images):
        """批量添加图片"""
        return self._image_manager.add_images_batch(images)
    
    def get_unprocessed_images(self, limit: int = 100):
        """获取未处理的图片"""
        return self._image_manager.get_unprocessed_images(limit)
    
    def update_image_data(self, image_id: int, ocr_text: str, filtered_text: str, 
                         emotion: str, pos_score: float, neg_score: float):
        """更新图片处理结果"""
        self._image_manager.update_image_data(image_id, ocr_text, filtered_text, 
                                             emotion, pos_score, neg_score)
    
    def update_images_batch(self, updates):
        """批量更新图片数据"""
        return self._image_manager.update_images_batch(updates)
    
    def get_image_detail(self, file_path: str):
        """获取单个图片的详细信息"""
        return self._image_manager.get_image_detail(file_path)
    
    def update_image_ocr(self, file_path: str, new_ocr_text: str, 
                        update_filtered: bool = True) -> bool:
        """更新图片的OCR文本"""
        return self._image_manager.update_image_ocr(file_path, new_ocr_text, update_filtered)
    
    def update_favorite(self, file_path: str, is_favorite: bool) -> bool:
        """更新图片的收藏状态"""
        return self._image_manager.update_favorite(file_path, is_favorite)
    
    def update_emotion(self, file_path: str, emotion: str, manual: bool = True) -> bool:
        """更新图片的情绪标签"""
        return self._image_manager.update_emotion(file_path, emotion, manual)
    
    def delete_processed_images(self, days: int = 30) -> int:
        """删除N天前处理过的图片记录"""
        return self._image_manager.delete_old_records(days)
    
    # ==================== 搜索功能（委托给 SearchManager） ====================
    
    def search_images(self, keyword: str = "", emotion: str = "", limit: int = 100):
        """搜索图片"""
        return self._search_manager.search_images(keyword, emotion, limit)
    
    def get_images_count(self, processed: int = None, keyword: str = "", emotion: str = "", 
                        emotions=None, source_ids=None, is_favorite: bool = None) -> int:
        """获取符合条件的图片总数（用于分页）"""
        return self._search_manager.get_images_count(processed, keyword, emotion, 
                                                     emotions, source_ids, is_favorite)
    
    def get_images_page(self, page: int = 1, page_size: int = 20, processed: int = None,
                        keyword: str = "", emotion: str = "", emotions=None,
                        source_ids=None, is_favorite: bool = None):
        """分页获取图片数据"""
        return self._search_manager.get_images_page(page, page_size, processed, 
                                                    keyword, emotion, emotions, 
                                                    source_ids, is_favorite)
    
    def get_statistics(self):
        """获取统计信息"""
        return self._search_manager.get_statistics()
    
    # ==================== 应用状态持久化（委托给 StateManager） ====================
    
    def set_app_state(self, key: str, value: str):
        """设置应用状态键值（持久化）"""
        self._state_manager.set_app_state(key, value)
    
    def get_app_state(self, key: str) -> str:
        """获取应用状态键对应的值"""
        return self._state_manager.get_app_state(key)
    
    # ==================== 数据库维护 ====================
    
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
    
    def close(self):
        """关闭数据库连接池"""
        self.pool.close_all()
        logger.info("数据库连接池已关闭")
