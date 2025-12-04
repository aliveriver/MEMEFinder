#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片管理模块
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class ImageManager:
    """图片管理器"""
    
    def __init__(self, get_cursor_func):
        """
        Args:
            get_cursor_func: 获取数据库游标的函数
        """
        self.get_cursor = get_cursor_func
    
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
    
    def get_image_detail(self, file_path: str) -> Optional[Dict]:
        """获取单个图片的详细信息
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            包含图片详细信息的字典，如果不存在返回None
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, file_path, file_hash, source_id, ocr_text, 
                       filtered_text, emotion, emotion_positive, emotion_negative, 
                       added_time, processed, is_favorite, emotion_manual
                FROM images
                WHERE file_path = ?
            """, (file_path,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"图片未找到: {file_path}")
                return None
            
            detail = {
                'id': row[0],
                'file_path': row[1],
                'file_hash': row[2],
                'source_id': row[3],
                'ocr_text': row[4] or '',
                'filtered_text': row[5] or '',
                'emotion': row[6] or '未分类',
                'emotion_positive': row[7],
                'emotion_negative': row[8],
                'added_time': row[9],
                'processed': bool(row[10]),
                'is_favorite': bool(row[11]),
                'emotion_manual': bool(row[12])
            }
        
        logger.debug(f"获取图片详情: {file_path}")
        return detail
    
    def update_image_ocr(self, file_path: str, new_ocr_text: str, 
                        update_filtered: bool = True) -> bool:
        """更新图片的OCR文本
        
        Args:
            file_path: 图片文件路径
            new_ocr_text: 新的OCR文本
            update_filtered: 是否同时更新filtered_text（默认True）
            
        Returns:
            更新是否成功
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                if update_filtered:
                    # 同时更新filtered_text（与ocr_text相同）
                    cursor.execute("""
                        UPDATE images 
                        SET ocr_text = ?, filtered_text = ?
                        WHERE file_path = ?
                    """, (new_ocr_text, new_ocr_text, file_path))
                else:
                    # 只更新ocr_text
                    cursor.execute("""
                        UPDATE images 
                        SET ocr_text = ?
                        WHERE file_path = ?
                    """, (new_ocr_text, file_path))
                
                if cursor.rowcount > 0:
                    logger.info(f"更新OCR文本成功: {file_path}")
                    return True
                else:
                    logger.warning(f"更新OCR文本失败，图片未找到: {file_path}")
                    return False
        except Exception as e:
            logger.error(f"更新OCR文本失败: {e}")
            return False
    
    def update_favorite(self, file_path: str, is_favorite: bool) -> bool:
        """更新图片的收藏状态
        
        Args:
            file_path: 图片文件路径
            is_favorite: 是否收藏
            
        Returns:
            更新是否成功
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE images 
                    SET is_favorite = ?
                    WHERE file_path = ?
                """, (1 if is_favorite else 0, file_path))
                
                if cursor.rowcount > 0:
                    logger.info(f"已{'收藏' if is_favorite else '取消收藏'}图片: {file_path}")
                    return True
                else:
                    logger.warning(f"图片未找到，无法更新收藏状态: {file_path}")
                    return False
        except Exception as e:
            logger.error(f"更新收藏状态失败: {e}")
            return False
    
    def update_emotion(self, file_path: str, emotion: str, manual: bool = True) -> bool:
        """更新图片的情绪标签
        
        Args:
            file_path: 图片文件路径
            emotion: 情绪标签（正向/负向/中性）
            manual: 是否手动修改（默认True，手动修改不保留得分）
            
        Returns:
            更新是否成功
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                if manual:
                    # 手动修改：清空得分，设置manual标记
                    cursor.execute("""
                        UPDATE images 
                        SET emotion = ?, emotion_positive = NULL, emotion_negative = NULL, emotion_manual = 1
                        WHERE file_path = ?
                    """, (emotion, file_path))
                else:
                    # 自动识别：保留得分，清除manual标记
                    cursor.execute("""
                        UPDATE images 
                        SET emotion = ?, emotion_manual = 0
                        WHERE file_path = ?
                    """, (emotion, file_path))
                
                if cursor.rowcount > 0:
                    logger.info(f"已更新图片情绪为: {emotion} ({'手动' if manual else '自动'}): {file_path}")
                    return True
                else:
                    logger.warning(f"图片未找到，无法更新情绪: {file_path}")
                    return False
        except Exception as e:
            logger.error(f"更新情绪失败: {e}")
            return False
    
    def delete_old_records(self, days: int = 30) -> int:
        """删除N天前处理过的图片记录
        
        Args:
            days: 保留最近N天的数据
            
        Returns:
            删除的记录数
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM images 
                WHERE processed = 1 AND added_time < ?
            """, (cutoff_date,))
            deleted = cursor.rowcount
        
        logger.info(f"清理旧数据: 删除了 {deleted} 条 {days} 天前的记录")
        return deleted
