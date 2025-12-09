#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索工具栏模块
"""

import tkinter as tk
from tkinter import ttk
from .checkbox_dropdown import CheckboxDropdown
from .search_filters import SearchFilters

class SearchToolbar:
    """搜索工具栏"""
    
    def __init__(self, parent_frame, db, icon_manager, callbacks):
        """
        Args:
            parent_frame: 父框架
            db: 数据库实例
            icon_manager: 图标管理器
            callbacks: 回调函数字典 {
                'search': func,
                'refresh': func,
                'image_search': func,
                'tag_manage': func,
                'sort_mode_change': func
            }
        """
        self.parent = parent_frame
        self.db = db
        self.icons = icon_manager
        self.callbacks = callbacks
        
        self.frame = ttk.LabelFrame(parent_frame, text="搜索条件", padding=10)
        self.frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.search_keyword = tk.StringVar()
        self.favorite_filter_var = tk.BooleanVar(value=False)
        self.sort_mode_var = tk.StringVar(value="time")
        
        self._create_widgets()
        
        # 初始化筛选器
        self.filters = SearchFilters(
            db=self.db,
            dropdowns={
                'emotion': self.emotion_dropdown,
                'source': self.source_dropdown,
                'tag': self.tag_dropdown
            },
            on_filter_change_callback=self.callbacks['search']
        )
        self.filters.load_sources()
        self.filters.load_tags()
        
    def _create_widgets(self):
        """创建组件"""
        # 第一行：关键词搜索
        ttk.Label(self.frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        keyword_entry = ttk.Entry(self.frame, textvariable=self.search_keyword, width=40)
        keyword_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        keyword_entry.bind('<Return>', lambda e: self.callbacks['search']())
        
        # 按钮组
        self._create_buttons()
        
        # 第二行：筛选器
        self._create_filters()
        
        # 第三行：排序
        self._create_sort_controls()
        
    def _create_buttons(self):
        """创建按钮"""
        # 搜索按钮
        search_btn = ttk.Button(
            self.frame, text=" 搜索", 
            image=self.icons.get('search'), 
            compound=tk.LEFT, 
            command=self.callbacks['search']
        )
        search_btn.grid(row=0, column=4, padx=5)
        if self.icons.get('search'):
            search_btn.image = self.icons.get('search')
            
        # 刷新按钮
        refresh_btn = ttk.Button(
            self.frame, text=" 刷新", 
            image=self.icons.get('refresh'), 
            compound=tk.LEFT, 
            command=self.callbacks['refresh']
        )
        refresh_btn.grid(row=0, column=5, padx=5)
        if self.icons.get('refresh'):
            refresh_btn.image = self.icons.get('refresh')
            
        # 以图搜图按钮
        img_search_btn = ttk.Button(
            self.frame, text=" 以图搜图", 
            image=self.icons.get('image'), 
            compound=tk.LEFT, 
            command=self.callbacks['image_search']
        )
        img_search_btn.grid(row=0, column=6, padx=5)
        if self.icons.get('image'):
            img_search_btn.image = self.icons.get('image')
            
        # 标签管理按钮
        tag_btn = ttk.Button(
            self.frame, text=" 管理标签", 
            image=self.icons.get('tag'), 
            compound=tk.LEFT, 
            command=self.callbacks['tag_manage']
        )
        tag_btn.grid(row=0, column=7, padx=5)
        if self.icons.get('tag'):
            tag_btn.image = self.icons.get('tag')
            
    def _create_filters(self):
        """创建筛选器"""
        # 情感筛选
        ttk.Label(self.frame, text="情绪:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        emotions = [('正向', '正向'), ('负向', '负向'), ('中性', '中性')]
        self.emotion_dropdown = CheckboxDropdown(
            self.frame, emotions, default_text="全部情绪",
            callback=lambda: self.filters.on_emotion_change() if hasattr(self, 'filters') else None, 
            width=15
        )
        self.emotion_dropdown.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 图源筛选
        ttk.Label(self.frame, text="图源:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.source_dropdown = CheckboxDropdown(
            self.frame, [], default_text="全部图源",
            callback=lambda: self.filters.on_source_change() if hasattr(self, 'filters') else None, 
            width=15
        )
        self.source_dropdown.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 标签筛选
        tag_frame = ttk.Frame(self.frame)
        tag_frame.grid(row=1, column=4, columnspan=2, sticky=tk.W, padx=(5,0), pady=5)
        ttk.Label(tag_frame, text="标签:").pack(side=tk.LEFT)
        self.tag_dropdown = CheckboxDropdown(
            tag_frame, [], default_text="全部标签",
            callback=lambda: self.filters.on_tag_change() if hasattr(self, 'filters') else None, 
            width=15
        )
        self.tag_dropdown.pack(side=tk.LEFT, padx=(5,0))
        
        # 收藏筛选
        ttk.Checkbutton(
            self.frame, text=" 只看收藏",
            image=self.icons.get('favorite'), compound='left',
            variable=self.favorite_filter_var,
            command=lambda: self.filters.on_favorite_change() if hasattr(self, 'filters') else None
        ).grid(row=1, column=6, sticky=tk.W, padx=5, pady=5)
        
    def _create_sort_controls(self):
        """创建排序控件"""
        ttk.Label(self.frame, text="排序:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        sort_modes = [("按时间", "time"), ("颜色聚类", "color")]
        sort_frame = ttk.Frame(self.frame)
        sort_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        for text, value in sort_modes:
            ttk.Radiobutton(
                sort_frame, text=text, value=value,
                variable=self.sort_mode_var,
                command=self.callbacks['sort_mode_change']
            ).pack(side=tk.LEFT, padx=5)
            
        # 将排序信息移到新的一行，避免影响上方按钮布局
        self.sort_info_label = ttk.Label(self.frame, text="(右键图片可选择'以此为参考排序')", foreground="gray")
        self.sort_info_label.grid(row=3, column=0, columnspan=8, sticky=tk.W, padx=5, pady=(0, 5))
        
    def update_sort_info(self, text, color="gray"):
        """更新排序信息"""
        self.sort_info_label.config(text=text, foreground=color)
        
    def get_keyword(self):
        return self.search_keyword.get().strip()
