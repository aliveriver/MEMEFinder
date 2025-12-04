#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索和查询管理模块
"""

from typing import List, Dict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class SearchManager:
    """搜索和查询管理器"""
    
    def __init__(self, get_cursor_func):
        """
        Args:
            get_cursor_func: 获取数据库游标的函数
        """
        self.get_cursor = get_cursor_func
    
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

    def get_images_count(self, processed: int = None, keyword: str = "", emotion: str = "", 
                        emotions: List[str] = None, source_ids: List[int] = None, 
                        is_favorite: bool = None) -> int:
        """获取符合条件的图片总数（用于分页）

        Args:
            processed: 1 for 已处理，0 为未处理，None 表示全部
            emotions: 情感列表，支持多选
            source_ids: 图源ID列表，支持多图源筛选
            is_favorite: True只显示收藏，False不显示收藏，None全部显示
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
            # 支持多选情感
            if emotions:
                placeholders = ','.join(['?' for _ in emotions])
                query += f" AND emotion IN ({placeholders})"
                params.extend(emotions)
            elif emotion:  # 向后兼容单选
                query += " AND emotion = ?"
                params.append(emotion)
            # 支持多图源筛选
            if source_ids:
                placeholders = ','.join(['?' for _ in source_ids])
                query += f" AND source_id IN ({placeholders})"
                params.extend(source_ids)
            # 支持收藏筛选
            if is_favorite is not None:
                query += " AND is_favorite = ?"
                params.append(1 if is_favorite else 0)

            cursor.execute(query, params)
            total = cursor.fetchone()[0]
        
        logger.debug(f"统计图片数量: {total} 张 (processed={processed}, keyword='{keyword}', emotion='{emotion}', emotions={emotions}, source_ids={source_ids}, is_favorite={is_favorite})")
        return total

    def get_images_page(self, page: int = 1, page_size: int = 20, processed: int = None,
                        keyword: str = "", emotion: str = "", emotions: List[str] = None,
                        source_ids: List[int] = None, is_favorite: bool = None) -> List[Dict]:
        """分页获取图片数据，返回指定页的记录列表

        Args:
            page: 页码，从1开始
            page_size: 每页条数
            processed: 1/0/None 同 get_images_count
            emotions: 情感列表，支持多选
            source_ids: 图源ID列表，支持多图源筛选
            is_favorite: True只显示收藏，False不显示收藏，None全部显示
        """
        offset = max(0, (page - 1) * page_size)
        
        with self.get_cursor() as cursor:
            query = "SELECT id, file_path, filtered_text, emotion, emotion_positive, emotion_negative, processed, is_favorite, source_id, emotion_manual FROM images WHERE 1=1"
            params = []
            if processed is not None:
                query += " AND processed = ?"
                params.append(processed)
            if keyword:
                query += " AND (filtered_text LIKE ? OR ocr_text LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            # 支持多选情感
            if emotions:
                placeholders = ','.join(['?' for _ in emotions])
                query += f" AND emotion IN ({placeholders})"
                params.extend(emotions)
            elif emotion:  # 向后兼容单选
                query += " AND emotion = ?"
                params.append(emotion)
            # 支持多图源筛选
            if source_ids:
                placeholders = ','.join(['?' for _ in source_ids])
                query += f" AND source_id IN ({placeholders})"
                params.extend(source_ids)
            # 支持收藏筛选
            if is_favorite is not None:
                query += " AND is_favorite = ?"
                params.append(1 if is_favorite else 0)

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
                    'processed': bool(row[6]),
                    'is_favorite': bool(row[7]),
                    'source_id': row[8],
                    'emotion_manual': bool(row[9])
                })
        
        logger.debug(f"分页查询: 第{page}页, 每页{page_size}条, 返回{len(results)}条")
        return results
    
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
