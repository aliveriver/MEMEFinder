#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片搜索标签页
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from ..core.database import ImageDatabase


class SearchTab:
    """图片搜索标签页"""
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 搜索条件区
        search_frame = ttk.LabelFrame(self.frame, text="搜索条件", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 关键词搜索
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_keyword = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_keyword, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 情绪筛选
        ttk.Label(search_frame, text="情绪:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.search_emotion = tk.StringVar()
        emotion_combo = ttk.Combobox(search_frame, textvariable=self.search_emotion, 
                                     values=['', '正向', '负向', '中性'], width=10, state='readonly')
        emotion_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        emotion_combo.set('')
        
        # 搜索按钮
        ttk.Button(search_frame, text="🔍 搜索", 
                  command=self.search_images).grid(row=0, column=4, padx=10)
        
        # 结果列表
        result_frame = ttk.LabelFrame(self.frame, text="搜索结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ('文本内容', '情绪', '正向分数', '负向分数', '图片路径')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        for col in columns:
            self.result_tree.heading(col, text=col)
        
        self.result_tree.column('文本内容', width=300)
        self.result_tree.column('情绪', width=80)
        self.result_tree.column('正向分数', width=100)
        self.result_tree.column('负向分数', width=100)
        self.result_tree.column('图片路径', width=300)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击打开图片
        self.result_tree.bind("<Double-1>", self.open_image)
    
    def search_images(self):
        """搜索图片"""
        keyword = self.search_keyword.get().strip()
        emotion = self.search_emotion.get()
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 搜索
        results = self.db.search_images(keyword, emotion)
        
        # 显示结果
        for result in results:
            text = result['text'][:50] + '...' if result['text'] and len(result['text']) > 50 else result['text']
            self.result_tree.insert('', tk.END, values=(
                text or '(无文本)',
                result['emotion'] or '未分类',
                f"{result['pos_score']:.2f}" if result['pos_score'] else 'N/A',
                f"{result['neg_score']:.2f}" if result['neg_score'] else 'N/A',
                result['file_path']
            ))
    
    def open_image(self, event):
        """打开选中的图片"""
        selected = self.result_tree.selection()
        if selected:
            item = selected[0]
            file_path = self.result_tree.item(item)['values'][4]
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                messagebox.showerror("错误", "图片文件不存在")
