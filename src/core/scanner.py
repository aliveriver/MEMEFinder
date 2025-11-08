#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片扫描模块
"""

import os
import hashlib
from pathlib import Path
from typing import List, Set, Tuple


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
    def calculate_file_hash(file_path: Path) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"error_{file_path.name}"
    
    @staticmethod
    def find_new_images(folder_path: str, existing_hashes: Set[str]) -> List[Tuple[Path, str]]:
        """查找新图片（返回图片路径和哈希值的列表）"""
        all_images = ImageScanner.scan_folder(folder_path)
        new_images = []
        
        for img_path in all_images:
            img_hash = ImageScanner.calculate_file_hash(img_path)
            if img_hash not in existing_hashes:
                new_images.append((img_path, img_hash))
                existing_hashes.add(img_hash)
        
        return new_images
