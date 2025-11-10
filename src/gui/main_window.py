#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import tkinter as tk
from tkinter import ttk, messagebox

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
        
        # 启动时检查是否有未完成的处理，需要用户确认是否继续
        try:
            self.check_resume()
        except Exception:
            pass
    
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
    
    def check_resume(self):
        """检查上次的处理状态并询问用户是否继续"""
        state = self.db.get_app_state('processing_state')
        if not state:
            return

        # 仅在上次为 running 或 paused 时提示
        if state not in ('running', 'paused'):
            return

        # 如果没有未处理的图片则无需提示，清理状态
        remaining = self.db.get_unprocessed_images(limit=1)
        if not remaining:
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
            return

        # 弹窗询问
        msg = f"检测到上次图片处理在 '{state}' 状态下未完成。是否继续处理未完成的图片？"
        cont = messagebox.askyesno("恢复处理", msg)
        if cont:
            # 跳转到图片处理页并开始
            try:
                self.notebook.select(self.process_tab.frame)
            except Exception:
                try:
                    tabs = self.notebook.tabs()
                    if len(tabs) >= 2:
                        self.notebook.select(tabs[1])
                except Exception:
                    pass
            try:
                self.process_tab.start_processing()
            except Exception:
                pass
        else:
            # 标记为暂停
            try:
                self.db.set_app_state('processing_state', 'paused')
            except Exception:
                pass
