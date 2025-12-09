#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分页控制模块
"""

import tkinter as tk
from tkinter import ttk

class PaginationControl:
    """分页控制器"""
    
    def __init__(self, parent_frame, load_page_callback, thumb_size_callback):
        """
        Args:
            parent_frame: 父框架
            load_page_callback: 加载页面的回调函数
            thumb_size_callback: 缩略图大小改变的回调函数
        """
        self.parent = parent_frame
        self.load_page_callback = load_page_callback
        self.thumb_size_callback = thumb_size_callback
        
        self.page_size_var = tk.IntVar(value=20)
        self.page_var = tk.IntVar(value=1)
        self.thumb_size_var = tk.IntVar(value=120)
        self.goto_var = tk.IntVar(value=1)
        self.total_pages = 1
        
        self.frame = ttk.Frame(parent_frame)
        # 不在初始化时自动pack，由外部控制布局顺序
        
        self._create_widgets()
        
    def pack(self, **kwargs):
        """显示组件"""
        default_args = {'fill': tk.X, 'padx': 10, 'pady': 5}
        default_args.update(kwargs)
        self.frame.pack(**default_args)
        
    def _create_widgets(self):
        """创建组件"""
        # 每页条数
        ttk.Label(self.frame, text="每页:").pack(side=tk.LEFT)
        page_size_cb = ttk.Combobox(
            self.frame, textvariable=self.page_size_var,
            values=[10, 20, 50, 100], width=5, state='readonly'
        )
        page_size_cb.pack(side=tk.LEFT, padx=5)
        page_size_cb.bind('<<ComboboxSelected>>', lambda e: self.load_page_callback())
        
        # 缩略图大小
        ttk.Label(self.frame, text=" 缩略图:").pack(side=tk.LEFT)
        thumb_scale = ttk.Scale(
            self.frame, from_=60, to=240, orient=tk.HORIZONTAL,
            command=lambda v: self.thumb_size_callback(v)
        )
        thumb_scale.set(self.thumb_size_var.get())
        thumb_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.frame, textvariable=self.thumb_size_var).pack(side=tk.LEFT)
        
        # 分页按钮
        ttk.Button(self.frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.frame, text="下一页", command=self.next_page).pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(self.frame, text="第 1 / 1 页")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 跳转
        ttk.Label(self.frame, text=" 跳转到页:").pack(side=tk.LEFT)
        self.goto_entry = ttk.Entry(self.frame, width=6, textvariable=self.goto_var)
        self.goto_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.frame, text="跳转", command=self.goto_page).pack(side=tk.LEFT)
        
    def prev_page(self):
        """上一页"""
        p = max(1, self.page_var.get() - 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page_callback()
            
    def next_page(self):
        """下一页"""
        p = min(self.total_pages, self.page_var.get() + 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page_callback()
            
    def goto_page(self):
        """跳转到指定页"""
        try:
            p = int(self.goto_var.get())
        except:
            p = 1
        p = max(1, min(self.total_pages, p))
        self.page_var.set(p)
        self.load_page_callback()
        
    def update_display(self, total_pages, current_page):
        """更新显示"""
        self.total_pages = total_pages
        self.page_var.set(current_page)
        self.page_label.config(text=f"第 {current_page} / {total_pages} 页")
        
    def get_page_size(self):
        return int(self.page_size_var.get())
        
    def get_current_page(self):
        return int(self.page_var.get())
        
    def set_current_page(self, page):
        self.page_var.set(page)
        
    def set_thumb_size(self, size):
        self.thumb_size_var.set(size)
