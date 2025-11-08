#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片搜索标签页
"""

import os
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from ..core.database import ImageDatabase


class SearchTab:
    """图片搜索标签页"""
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        
        # 保存缩略图引用，防止被GC
        self.image_refs = {}
        # item id -> 文件路径
        self.item_paths = {}

        # 延迟重绘调度ID（用于防抖）
        self._reload_after_id = None
        
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

        # 使用可滚动的 Canvas + 内部 Frame 来实现缩略图网格展示
        self.canvas = tk.Canvas(result_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=vsb.set)

        # 内部容器，用于放置缩略图网格
        self.grid_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')

        # 绑定滚动更新
        def _on_frame_config(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.grid_frame.bind('<Configure>', _on_frame_config)

        # 缩略图大小与布局参数（支持动态调整）
        self.thumb_size_var = tk.IntVar(value=120)  # 单边像素
        self.thumb_padding = 20
        self.cols = 4  # 初始每行列数，会在加载时根据画布宽度调整

        # 鼠标进入/离开画布时绑定滚轮事件，实现页面内滚动
        self.canvas.bind('<Enter>', lambda e: self._bind_mousewheel(True))
        self.canvas.bind('<Leave>', lambda e: self._bind_mousewheel(False))

        # 画布大小变化时重新布局（延迟刷新避免频繁重绘）
        self.canvas.bind('<Configure>', lambda e: self._schedule_reload(250))

        # 双击/单击不再依赖 Treeview，使用按钮直接打开图片

        # 分页控件
        pager_frame = ttk.Frame(self.frame)
        pager_frame.pack(fill=tk.X, padx=10, pady=5)

        self.page_size_var = tk.IntVar(value=20)
        ttk.Label(pager_frame, text="每页:").pack(side=tk.LEFT)
        page_size_cb = ttk.Combobox(pager_frame, textvariable=self.page_size_var, values=[10, 20, 50, 100], width=5, state='readonly')
        page_size_cb.pack(side=tk.LEFT, padx=5)
        page_size_cb.bind('<<ComboboxSelected>>', lambda e: self.load_page())

        # 缩略图大小控制
        ttk.Label(pager_frame, text=" 缩略图:").pack(side=tk.LEFT)
        thumb_scale = ttk.Scale(pager_frame, from_=60, to=240, orient=tk.HORIZONTAL, command=lambda v: self._on_thumb_change(v))
        thumb_scale.set(self.thumb_size_var.get())
        thumb_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(pager_frame, textvariable=self.thumb_size_var).pack(side=tk.LEFT)

        self.page_var = tk.IntVar(value=1)
        self.total_pages = 1

        ttk.Button(pager_frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="下一页", command=self.next_page).pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(pager_frame, text="第 1 / 1 页")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # 跳转到指定页
        ttk.Label(pager_frame, text=" 跳转到页:").pack(side=tk.LEFT)
        self.goto_var = tk.IntVar(value=1)
        self.goto_entry = ttk.Entry(pager_frame, width=6, textvariable=self.goto_var)
        self.goto_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="跳转", command=self.goto_page).pack(side=tk.LEFT)

        # 初始加载
        self.load_page()
    
    def search_images(self):
        """搜索图片（重置为第一页并加载）"""
        self.page_var.set(1)
        self.load_page()

    def load_page(self):
        """加载当前页的数据并显示（网格缩略图）"""
        # 进入实际重绘前，取消任何已排队的调度（避免重复）
        if self._reload_after_id is not None:
            try:
                self.frame.after_cancel(self._reload_after_id)
            except Exception:
                pass
            self._reload_after_id = None

        page = max(1, int(self.page_var.get()))
        page_size = int(self.page_size_var.get())
        keyword = self.search_keyword.get().strip()
        emotion = self.search_emotion.get()
 
        # 清空网格
        for child in self.grid_frame.winfo_children():
            child.destroy()

        # 清空引用映射
        self.image_refs.clear()
        self.item_paths.clear()

        # 计算总页数
        total = self.db.get_images_count(processed=1, keyword=keyword, emotion=emotion)
        self.total_pages = max(1, (total + page_size - 1) // page_size)
        if page > self.total_pages:
            page = self.total_pages
            self.page_var.set(page)

        # 获取这一页的数据
        results = self.db.get_images_page(page=page, page_size=page_size, processed=1, keyword=keyword, emotion=emotion)

        # 根据画布宽度和缩略图尺寸动态计算每行列数
        try:
            canvas_width = max(200, self.canvas.winfo_width())
            thumb_side = int(self.thumb_size_var.get())
            cell_width = thumb_side + self.thumb_padding
            cols = max(1, canvas_width // cell_width)
            self.cols = cols
        except Exception:
            self.cols = 4

        # 显示缩略图网格
        r = c = 0
        for idx, result in enumerate(results):
            file_path = result.get('file_path') or ''
            imgtk = None
            try:
                if file_path and os.path.exists(file_path):
                    img = Image.open(file_path)
                    img.thumbnail((thumb_side, thumb_side))
                    imgtk = ImageTk.PhotoImage(img)
            except Exception:
                imgtk = None

            cell = ttk.Frame(self.grid_frame, relief=tk.FLAT, padding=5)
            cell.grid(row=r, column=c, padx=5, pady=5, sticky='n')

            if imgtk is not None:
                btn = ttk.Button(cell, image=imgtk, command=lambda p=file_path: self.open_file(p))
                btn.image = imgtk
                btn.pack()
                # 保留引用，避免被GC
                self.image_refs[f"{r}_{c}"] = imgtk
            else:
                lbl = ttk.Label(cell, text='(无法加载)', width=16, anchor='center')
                lbl.pack()

            # 文本摘要
            text = result['text'][:40] + '...' if result['text'] and len(result['text']) > 40 else (result['text'] or '(无文本)')
            ttk.Label(cell, text=text, wraplength=thumb_side).pack()
            ttk.Label(cell, text=result['emotion'] or '未分类').pack()

            self.item_paths[f"{r}_{c}"] = file_path

            c += 1
            if c >= self.cols:
                c = 0
                r += 1

        # 更新滚动区域并页码显示
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.update_pager()

    def prev_page(self):
        p = max(1, self.page_var.get() - 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page()

    def next_page(self):
        p = min(self.total_pages, self.page_var.get() + 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page()

    def update_pager(self):
        self.page_label.config(text=f"第 {self.page_var.get()} / {self.total_pages} 页")
    
    def goto_page(self):
        try:
            p = int(self.goto_var.get())
        except Exception:
            p = 1
        p = max(1, min(self.total_pages, p))
        self.page_var.set(p)
        self.load_page()

    def _on_thumb_change(self, value):
        try:
            v = int(float(value))
            self.thumb_size_var.set(v)
        except Exception:
            pass
        # 防抖：延迟重绘，避免滑块拖动时频繁重绘
        self._schedule_reload(250)

    def _schedule_reload(self, delay: int = 200):
        """安排在 delay 毫秒后重绘页面，若已有计划则重置计时器."""
        try:
            if self._reload_after_id is not None:
                self.frame.after_cancel(self._reload_after_id)
        except Exception:
            pass
        try:
            self._reload_after_id = self.frame.after(delay, self._do_reload)
        except Exception:
            # 后备直接调用
            self._do_reload()

    def _do_reload(self):
        """真正执行的重绘回调（由 after 调用）."""
        self._reload_after_id = None
        try:
            self.load_page()
        except Exception:
            # 忽略重绘错误以保证响应性
            pass
    
    def _bind_mousewheel(self, bind: bool):
        if bind:
            # Windows
            self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
            # Linux
            self.canvas.bind_all('<Button-4>', self._on_mousewheel)
            self.canvas.bind_all('<Button-5>', self._on_mousewheel)
        else:
            try:
                self.canvas.unbind_all('<MouseWheel>')
                self.canvas.unbind_all('<Button-4>')
                self.canvas.unbind_all('<Button-5>')
            except Exception:
                pass

    def _on_mousewheel(self, event):
        # 支持 Windows 和 Linux/Mac 事件差异
        try:
            if event.num == 4:
                delta = -120
            elif event.num == 5:
                delta = 120
            else:
                delta = -1 * int(event.delta)
        except Exception:
            delta = -1 * int(getattr(event, 'delta', 0))

        # 将滚动量应用到 canvas
        self.canvas.yview_scroll(int(delta / 120), 'units')

    def open_file(self, file_path: str):
        """跨平台使用系统默认程序打开图片文件"""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "图片文件不存在")
            return

        try:
            if sys.platform.startswith('win'):
                # Windows
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                # macOS
                subprocess.run(['open', file_path], check=False)
            else:
                # 其他类 Unix（Linux）
                if shutil.which('xdg-open'):
                    subprocess.run(['xdg-open', file_path], check=False)
                elif shutil.which('gio'):
                    subprocess.run(['gio', 'open', file_path], check=False)
                else:
                    messagebox.showerror("错误", "无法找到系统打开命令，请手动打开图片")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")
