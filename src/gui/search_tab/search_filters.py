#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索筛选器模块
负责管理搜索标签页的所有筛选逻辑
"""

import tkinter as tk


class SearchFilters:
    """搜索筛选器 - 管理情感、图源、标签和收藏筛选"""
    
    def __init__(self, db, dropdowns, on_filter_change_callback):
        """
        初始化筛选器
        
        Args:
            db: 数据库实例
            dropdowns: 下拉框字典 {'emotion': widget, 'source': widget, 'tag': widget}
            on_filter_change_callback: 筛选条件变化时的回调函数
        """
        self.db = db
        self.emotion_dropdown = dropdowns['emotion']
        self.source_dropdown = dropdowns['source']
        self.tag_dropdown = dropdowns['tag']
        self.on_filter_change = on_filter_change_callback
        
        # 当前选中的筛选条件
        self.selected_emotions = []
        self.selected_sources = []
        self.selected_tags = []
    
    def load_sources(self):
        """加载图源列表到下拉框"""
        sources = self.db.get_sources()
        options = []
        for source in sources:
            folder_path = source['folder_path']
            folder_name = folder_path.split('\\')[-1] or folder_path.split('/')[-1] or folder_path
            display_text = f"[{source['id']}] {folder_name}"
            options.append((display_text, source['id']))
        
        self.source_dropdown.options = options
        self.source_dropdown.vars = {}
        for label, value in options:
            self.source_dropdown.vars[value] = tk.BooleanVar(value=False)
        self.source_dropdown._update_button_text()
    
    def load_tags(self):
        """加载标签列表到下拉框"""
        tags = self.db.get_all_tags()
        options = []
        for tag in tags:
            display_text = f"{tag['name']}"
            options.append((display_text, tag['id']))
        
        self.tag_dropdown.options = options
        self.tag_dropdown.vars = {}
        for label, value in options:
            self.tag_dropdown.vars[value] = tk.BooleanVar(value=False)
        self.tag_dropdown._update_button_text()
    
    def on_emotion_change(self):
        """情感筛选变化"""
        self.selected_emotions = self.emotion_dropdown.get_selected_values()
        self.on_filter_change()
    
    def on_source_change(self):
        """图源筛选变化"""
        self.selected_sources = self.source_dropdown.get_selected_values()
        self.on_filter_change()
    
    def on_tag_change(self):
        """标签筛选变化"""
        self.selected_tags = self.tag_dropdown.get_selected_values()
        self.on_filter_change()
    
    def on_favorite_change(self):
        """收藏筛选变化"""
        self.on_filter_change()
    
    def set_source_filter(self, source_ids):
        """
        从外部设置图源筛选
        
        Args:
            source_ids: 图源ID列表或单个ID
        """
        if not isinstance(source_ids, list):
            source_ids = [source_ids]
        
        self.selected_sources = source_ids
        self.source_dropdown.set_selected_values(source_ids)
        self.on_filter_change()
    
    def get_filter_params(self, favorite_filter_var):
        """
        获取当前的筛选参数
        
        Args:
            favorite_filter_var: 收藏筛选的变量
            
        Returns:
            dict: 筛选参数字典
        """
        return {
            'emotions': self.selected_emotions if self.selected_emotions else None,
            'source_ids': self.selected_sources if self.selected_sources else None,
            'tag_ids': self.selected_tags if self.selected_tags else None,
            'is_favorite': True if favorite_filter_var.get() else None
        }
    
    def reload_all(self):
        """重新加载所有筛选选项"""
        self.load_sources()
        self.load_tags()
