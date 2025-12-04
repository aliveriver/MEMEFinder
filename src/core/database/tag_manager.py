#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标签管理模块
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class TagManager:
    """标签管理器"""
    
    def __init__(self, get_cursor_func):
        """
        Args:
            get_cursor_func: 获取数据库游标的函数
        """
        self.get_cursor = get_cursor_func
    
    # ==================== 标签管理 ====================
    
    def create_tag(self, name: str, color: str) -> Optional[int]:
        """创建新标签
        
        Args:
            name: 标签名称
            color: 背景颜色（十六进制，如 #FF5733）
            
        Returns:
            标签ID，如果已存在则返回None
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO tags (name, color, created_time)
                    VALUES (?, ?, ?)
                """, (name, color, datetime.now().isoformat()))
                tag_id = cursor.lastrowid
            logger.info(f"创建标签: {name} (颜色: {color})")
            return tag_id
        except sqlite3.IntegrityError:
            logger.warning(f"标签已存在: {name}")
            return None
    
    def get_all_tags(self) -> List[Dict]:
        """获取所有标签"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, color, created_time
                FROM tags
                ORDER BY name
            """)
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'created_time': row[3]
                })
        logger.debug(f"获取到 {len(tags)} 个标签")
        return tags
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Dict]:
        """根据ID获取标签"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, color, created_time
                FROM tags
                WHERE id = ?
            """, (tag_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'created_time': row[3]
                }
        return None
    
    def get_tag_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取标签"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, color, created_time
                FROM tags
                WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'created_time': row[3]
                }
        return None
    
    def update_tag(self, tag_id: int, name: str = None, color: str = None) -> bool:
        """更新标签信息
        
        Args:
            tag_id: 标签ID
            name: 新名称（可选）
            color: 新颜色（可选）
            
        Returns:
            是否成功
        """
        if name is None and color is None:
            return False
        
        try:
            with self.get_cursor(commit=True) as cursor:
                if name and color:
                    cursor.execute("""
                        UPDATE tags SET name = ?, color = ? WHERE id = ?
                    """, (name, color, tag_id))
                elif name:
                    cursor.execute("""
                        UPDATE tags SET name = ? WHERE id = ?
                    """, (name, tag_id))
                elif color:
                    cursor.execute("""
                        UPDATE tags SET color = ? WHERE id = ?
                    """, (color, tag_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"更新标签: ID={tag_id}")
                    return True
        except sqlite3.IntegrityError:
            logger.warning(f"标签名称冲突: {name}")
        
        return False
    
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签（会同时删除所有关联）
        
        Args:
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        with self.get_cursor(commit=True) as cursor:
            # 先删除关联
            cursor.execute("DELETE FROM image_tags WHERE tag_id = ?", (tag_id,))
            deleted_relations = cursor.rowcount
            
            # 删除标签
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"删除标签: ID={tag_id} (删除 {deleted_relations} 个关联)")
                return True
        
        return False
    
    # ==================== 图片-标签关联 ====================
    
    def add_tag_to_image(self, image_id: int, tag_id: int) -> bool:
        """为图片添加标签
        
        Args:
            image_id: 图片ID
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO image_tags (image_id, tag_id, added_time)
                    VALUES (?, ?, ?)
                """, (image_id, tag_id, datetime.now().isoformat()))
            logger.info(f"添加标签关联: 图片ID={image_id}, 标签ID={tag_id}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"标签关联已存在: 图片ID={image_id}, 标签ID={tag_id}")
            return False
    
    def remove_tag_from_image(self, image_id: int, tag_id: int) -> bool:
        """从图片移除标签
        
        Args:
            image_id: 图片ID
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM image_tags
                WHERE image_id = ? AND tag_id = ?
            """, (image_id, tag_id))
            
            if cursor.rowcount > 0:
                logger.info(f"移除标签关联: 图片ID={image_id}, 标签ID={tag_id}")
                return True
        
        return False
    
    def get_image_tags(self, image_id: int) -> List[Dict]:
        """获取图片的所有标签
        
        Args:
            image_id: 图片ID
            
        Returns:
            标签列表
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.name, t.color, it.added_time
                FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                WHERE it.image_id = ?
                ORDER BY it.added_time DESC
            """, (image_id,))
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'added_time': row[3]
                })
        
        return tags
    
    def get_image_tags_by_path(self, file_path: str) -> List[Dict]:
        """根据文件路径获取图片的所有标签
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            标签列表
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.name, t.color, it.added_time
                FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                JOIN images i ON it.image_id = i.id
                WHERE i.file_path = ?
                ORDER BY it.added_time DESC
            """, (file_path,))
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'added_time': row[3]
                })
        
        return tags
    
    def set_image_tags(self, image_id: int, tag_ids: List[int]) -> bool:
        """设置图片的标签（会清空原有标签）
        
        Args:
            image_id: 图片ID
            tag_ids: 标签ID列表
            
        Returns:
            是否成功
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                # 删除原有标签
                cursor.execute("DELETE FROM image_tags WHERE image_id = ?", (image_id,))
                
                # 添加新标签
                if tag_ids:
                    current_time = datetime.now().isoformat()
                    data = [(image_id, tag_id, current_time) for tag_id in tag_ids]
                    cursor.executemany("""
                        INSERT INTO image_tags (image_id, tag_id, added_time)
                        VALUES (?, ?, ?)
                    """, data)
            
            logger.info(f"设置图片标签: 图片ID={image_id}, 标签数={len(tag_ids)}")
            return True
        except Exception as e:
            logger.error(f"设置图片标签失败: {e}")
            return False
    
    def set_image_tags_by_path(self, file_path: str, tag_ids: List[int]) -> bool:
        """根据文件路径设置图片的标签
        
        Args:
            file_path: 图片文件路径
            tag_ids: 标签ID列表
            
        Returns:
            是否成功
        """
        with self.get_cursor() as cursor:
            cursor.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"图片不存在: {file_path}")
                return False
            
            image_id = row[0]
        
        return self.set_image_tags(image_id, tag_ids)
    
    def get_images_by_tag(self, tag_id: int, limit: int = 100) -> List[str]:
        """获取包含指定标签的所有图片路径
        
        Args:
            tag_id: 标签ID
            limit: 限制数量
            
        Returns:
            图片路径列表
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.file_path
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id = ?
                ORDER BY it.added_time DESC
                LIMIT ?
            """, (tag_id, limit))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_tag_statistics(self) -> List[Dict]:
        """获取每个标签的使用统计
        
        Returns:
            [{'id': ..., 'name': ..., 'color': ..., 'count': ...}, ...]
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.name, t.color, COUNT(it.image_id) as count
                FROM tags t
                LEFT JOIN image_tags it ON t.id = it.tag_id
                GROUP BY t.id
                ORDER BY count DESC, t.name
            """)
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'count': row[3]
                })
            return stats
