#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片扫描模块
"""

import os
from pathlib import Path
from typing import List, Set, Tuple, Dict
from .image_hash import calculate_image_hashes


class ImageScanner:
    """图片扫描器"""
    
    # 支持的图片扩展名
    IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif', '.tiff'}
    
    def __init__(self):
        pass
    
    @staticmethod
    def is_image_file(file_path: Path) -> bool:
        """判断是否为图片文件"""
        return file_path.is_file() and file_path.suffix.lower() in ImageScanner.IMG_EXTENSIONS
    
    @staticmethod
    def scan_folder(folder_path: str) -> List[Path]:
        """扫描文件夹中的所有图片"""
        folder = Path(folder_path)
        if not folder.exists():
            return []
        
        images = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = Path(root) / file
                if ImageScanner.is_image_file(file_path):
                    images.append(file_path)
        
        return sorted(images)
    
    @staticmethod
    def find_new_images(folder_path: str, existing_paths: Set[str]) -> List[Path]:
        """查找新图片（返回图片路径列表）
        
        注意：不再在扫描时计算哈希值，哈希值将在OCR处理时计算
        """
        all_images = ImageScanner.scan_folder(folder_path)
        new_images = []
        
        for img_path in all_images:
            # 使用os.path.abspath规范化路径，确保与数据库中的格式一致
            img_path_str = os.path.abspath(str(img_path))
            if img_path_str not in existing_paths:
                new_images.append(img_path)
                existing_paths.add(img_path_str)
        
        return new_images
