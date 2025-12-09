#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图标管理模块
"""

import os
import tkinter as tk
from PIL import Image, ImageTk
from ...utils.logger import get_logger

logger = get_logger()

class IconManager:
    """图标管理器"""
    
    def __init__(self):
        self.icons = {}
        self._load_icons()
    
    def _load_icons(self):
        """加载图标（优先从项目 assets/ 目录）"""
        self.icons = {}
        try:
            assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..', 'assets'))
            # 图标文件名到功能映射
            icon_map = {
                'favorite': '收藏.ico',
                'unfavorite': '取消收藏.ico',
                'tag': '标签.ico',
                'emotion': '情感.ico',
                'search': '查找.png',
                'delete': '删除.png',
                'image': '图片.ico',
                'folder': '文件夹.png',
                'refresh': '刷新.ico'
            }
            
            # 选择合适的重采样常量
            try:
                resample = Image.Resampling.LANCZOS
            except Exception:
                resample = Image.ANTIALIAS
            
            for key, filename in icon_map.items():
                fpath = os.path.join(assets_dir, filename)
                if os.path.exists(fpath):
                    try:
                        img = Image.open(fpath)
                        img = img.convert('RGBA')
                        img = img.resize((16, 16), resample)
                        self.icons[key] = ImageTk.PhotoImage(img)
                    except Exception as e:
                        logger.debug(f"加载图标失败 {filename}: {e}")
                        self.icons[key] = None
                else:
                    self.icons[key] = None
        except Exception as e:
            logger.warning(f"加载图标时出错: {e}")
            self.icons = {k: None for k in ('favorite', 'unfavorite', 'tag', 'emotion', 'search', 'delete', 'image', 'folder', 'refresh')}

    def get(self, key):
        """获取图标"""
        return self.icons.get(key)
