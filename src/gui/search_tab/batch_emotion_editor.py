#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量情感编辑对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List


class BatchEmotionEditor(tk.Toplevel):
    """批量情感编辑对话框"""
    
    def __init__(self, parent, db, file_paths: List[str], callback=None):
        """
        Args:
            parent: 父窗口
            db: 数据库实例
            file_paths: 图片路径列表
            callback: 完成后的回调函数
        """
        super().__init__(parent)
        self.db = db
        self.file_paths = file_paths
        self.callback = callback
        
        self.title(f"批量编辑情感 - {len(file_paths)} 张图片")
        self.geometry("450x350")  # 增加高度以确保按钮可见
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding=15)  # 减小padding
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 提示
        hint_label = ttk.Label(
            main_frame,
            text=f"将 {len(self.file_paths)} 张图片的情感标签设置为：",
            font=('TkDefaultFont', 10)
        )
        hint_label.pack(pady=(0, 15))  # 减小间距
        
        # 情感选择
        emotion_frame = ttk.LabelFrame(main_frame, text="选择情感", padding=10)  # 减小padding
        emotion_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))  # 减小间距
        
        self.emotion_var = tk.StringVar(value="正向")
        
        emotions = [
            ("😊 正向", "正向"),
            ("😢 负向", "负向"),
            ("😐 中性", "中性"),
            ("❓ 未分类", "未分类")
        ]
        
        for text, value in emotions:
            ttk.Radiobutton(
                emotion_frame,
                text=text,
                variable=self.emotion_var,
                value=value
            ).pack(anchor='w', pady=3)  # 减小间距
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="💾 应用",
            command=self._apply_emotion,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy,
            width=8
        ).pack(side=tk.LEFT)
    
    def _apply_emotion(self):
        """应用情感更改"""
        emotion = self.emotion_var.get()
        
        try:
            success_count = 0
            
            for file_path in self.file_paths:
                if self.db.update_emotion(file_path, emotion, manual=True):
                    success_count += 1
            
            messagebox.showinfo("成功", f"已为 {success_count} 张图片设置情感为：{emotion}")
            
            if self.callback:
                self.callback()
            
            self.destroy()
        
        except Exception as e:
            messagebox.showerror("错误", f"应用情感失败: {e}")
