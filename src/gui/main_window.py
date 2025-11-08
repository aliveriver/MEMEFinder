#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import tkinter as tk
from tkinter import ttk

from .source_tab import SourceTab
from .process_tab import ProcessTab
from .search_tab import SearchTab
from ..core.database import ImageDatabase


class MemeFinderGUI:
    """表情包查找器GUI主窗口"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("表情包查找器 - MEMEFinder")
        self.root.geometry("1000x700")
        
        # 数据库
        self.db = ImageDatabase()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化各标签页
        self.source_tab.refresh_sources()
        self.source_tab.update_statistics()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建笔记本（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建三个标签页
        self.source_tab = SourceTab(self.notebook, self.db)
        self.process_tab = ProcessTab(self.notebook, self.db)
        self.search_tab = SearchTab(self.notebook, self.db)
        
        # 添加到笔记本
        self.notebook.add(self.source_tab.frame, text="图源管理")
        self.notebook.add(self.process_tab.frame, text="图片处理")
        self.notebook.add(self.search_tab.frame, text="图片搜索")
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)
