#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys

from .source_tab import SourceTab
from .process_tab import ProcessTab
from .search_tab import SearchTab
from ..core.database import ImageDatabase


class MemeFinderGUI:
    """表情包查找器GUI主窗口"""
    
    def __init__(self, root):
        self.root = root
        
        self.root.title("MEMEFinder")
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
        
        # 在窗口完全创建后设置图标
        self.root.after(50, self._set_window_icon)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建笔记本（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建三个标签页
        self.source_tab = SourceTab(self.notebook, self.db)
        # 传递统计更新回调给process_tab
        self.process_tab = ProcessTab(self.notebook, self.db, stats_callback=self.source_tab.update_statistics)
        self.search_tab = SearchTab(self.notebook, self.db)
        
        # 设置图源页的跳转回调
        self.source_tab.jump_to_search_callback = self.jump_to_search_with_sources
        
        # 添加到笔记本
        self.notebook.add(self.source_tab.frame, text="图源管理")
        self.notebook.add(self.process_tab.frame, text="图片处理")
        self.notebook.add(self.search_tab.frame, text="图片搜索")
        
        # 绑定标签页切换事件，自动刷新搜索页
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)
    
    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            from ..utils.resource_path import get_icon_path
            
            icon_path = get_icon_path()
            
            if icon_path and icon_path.exists():
                icon_str = str(icon_path.resolve())
                
                # 设置Tkinter图标
                self.root.iconbitmap(default=icon_str)
                self.root.iconbitmap(icon_str)
                
                # Windows任务栏图标需要通过API设置
                if sys.platform == 'win32':
                    self.root.after(200, lambda: self._set_taskbar_icon(icon_str))
                return
            
        except Exception:
            pass
    
    def _set_taskbar_icon(self, icon_path):
        """设置Windows任务栏图标"""
        try:
            import ctypes
            
            # 确保窗口已经完全显示
            self.root.update_idletasks()
            
            # 加载图标文件
            hicon = ctypes.windll.user32.LoadImageW(
                0,          # hinst (NULL表示从文件加载)
                icon_path,  # 图标文件路径
                1,          # IMAGE_ICON
                0, 0,       # 使用默认大小
                0x00000010 | 0x00008000  # LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
            
            if hicon:
                # 获取窗口句柄
                hwnd = self.root.winfo_id()
                
                # WM_SETICON = 0x0080
                # ICON_SMALL = 0, ICON_BIG = 1
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)  # 任务栏大图标
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)  # 标题栏小图标
                
                # 强制刷新窗口
                self.root.update()
        except Exception:
            pass
    
    def _on_tab_changed(self, event):
        """标签页切换事件处理"""
        try:
            # 获取当前选中的标签页索引
            current_tab =  self.notebook.index(self.notebook.select())
            # 2 是搜索页的索引（0:图源管理， 1:图片处理，2:图片搜索）
            if current_tab == 2:
                # 切换到搜索页时自动刷新
                self.search_tab.refresh_page()
        except Exception:
            pass
    
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
    
    def jump_to_search_with_sources(self, source_ids):
        """跳转到搜索页并设置图源筛选"""
        # 切换到搜索页
        try:
            self.notebook.select(self.search_tab.frame)
        except Exception:
            try:
                tabs = self.notebook.tabs()
                if len(tabs) >= 3:
                    self.notebook.select(tabs[2])  # 搜索页是第3个标签页
            except Exception:
                pass
        
        # 设置图源筛选并触发搜索
        try:
            self.search_tab.set_source_filter(source_ids)
        except Exception as e:
            messagebox.showerror("错误", f"无法设置图源筛选: {e}")
