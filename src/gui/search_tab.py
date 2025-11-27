#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片搜索标签页
"""

import gc  # 添加垃圾回收模块

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
        self._scroll_after_id = None  # 滚动延迟调度ID
        
        # 虚拟化列表相关变量
        self.all_results = []  # 当前页的所有数据
        self.rendered_cells = {}  # {row_col_key: cell_widget} 已渲染的单元格
        self.cell_height = 200  # 单个单元格的估计高度
        self.placeholder_item = None  # 占位符，用于设置滚动区域
        
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
                  command=self.search_images).grid(row=0, column=4, padx=5)
        
        # 刷新按钮
        ttk.Button(search_frame, text="🔄 刷新", 
                  command=self.refresh_page).grid(row=0, column=5, padx=5)
        
        # 结果列表
        result_frame = ttk.LabelFrame(self.frame, text="搜索结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 使用可滚动的 Canvas + 内部 Frame 来实现缩略图网格展示
        # 先添加滚动条，再添加画布，确保滚动条不被覆盖
        vsb = ttk.Scrollbar(result_frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(result_frame, yscrollcommand=vsb.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vsb.configure(command=self.canvas.yview)

        # 内部容器，用于放置缩略图网格
        self.grid_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
        
        # 初始化占位符（用于虚拟化列表的滚动区域设置）
        self.placeholder_item = None

        # 绑定滚动更新
        def _on_frame_config(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.grid_frame.bind('<Configure>', _on_frame_config)

        # 缩略图大小与布局参数（支持动态调整）
        self.thumb_size_var = tk.IntVar(value=120)  # 单边像素
        self.thumb_padding = 20
        self.cols = 4  # 初始每行列数，会在加载时根据画布宽度调整

        # 滚轮事件绑定到整个result_frame，而不仅是Canvas
        # 这样整个图片浏览区域都可以使用滚轮
        result_frame.bind('<Enter>', lambda e: self._bind_mousewheel(True))
        result_frame.bind('<Leave>', lambda e: self._bind_mousewheel(False))
        
        # 绑定滚动事件，用于虚拟化渲染
        self.canvas.bind('<Configure>', self._on_canvas_scroll)
        self.canvas.bind_all('<MouseWheel>', self._on_canvas_scroll, add='+')

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
    
    def refresh_page(self):
        """刷新当前页面（保持当前页码和搜索条件）"""
        self.load_page()

    def load_page(self):
        """加载当前页的数据并显示（网格缩略图 - 使用虚拟化渲染）"""
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
 
        # 清空网格和已渲染的单元格
        for child in self.grid_frame.winfo_children():
            child.destroy()

        # 清空引用映射
        self.image_refs.clear()
        self.item_paths.clear()
        self.rendered_cells.clear()
        
        # 强制垃圾回收，释放旧页面的图片内存
        gc.collect()
        
        # 重置GC累积计数器
        self._removed_count = 0

        # 计算总页数
        total = self.db.get_images_count(processed=1, keyword=keyword, emotion=emotion)
        self.total_pages = max(1, (total + page_size - 1) // page_size)
        if page > self.total_pages:
            page = self.total_pages
            self.page_var.set(page)

        # 获取这一页的数据，保存到all_results
        self.all_results = self.db.get_images_page(page=page, page_size=page_size, processed=1, keyword=keyword, emotion=emotion)

        # 根据画布宽度和缩略图尺寸动态计算每行列数
        try:
            canvas_width = max(200, self.canvas.winfo_width())
            thumb_side = int(self.thumb_size_var.get())
            cell_width = thumb_side + self.thumb_padding
            cols = max(1, canvas_width // cell_width)
            self.cols = cols
        except Exception:
            self.cols = 4

        # 不要设置grid_frame的固定高度，会导致窗口无法拖动和拉伸
        # 使用占位符方法设置滚动区域
        if self.all_results:
            total_rows = (len(self.all_results) + self.cols - 1) // self.cols
            thumb_side = int(self.thumb_size_var.get())
            estimated_cell_height = thumb_side + 120
            total_height = total_rows * estimated_cell_height
            
            # 删除旧的占位符
            if self.placeholder_item:
                try:
                    self.canvas.delete(self.placeholder_item)
                except Exception:
                    pass
            
            # 创建一个不可见的占位符，定位在底部，用于设置滚动区域
            self.placeholder_item = self.canvas.create_line(0, total_height, 1, total_height, fill='')

        # 更新滚动区域
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.update_pager()
        
        # 触发虚拟化渲染，只渲染可见项
        self._render_visible_items()


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

    # ========== 虚拟化列表相关方法 ==========
    
    def _get_visible_range(self):
        """计算当前可见的行范围"""
        try:
            # 获取画布的可视区域
            canvas_top = self.canvas.canvasy(0)  # 可视区域顶部的Y坐标
            canvas_bottom = self.canvas.canvasy(self.canvas.winfo_height())  # 可视区域底部的Y坐标
            
            # 计算单元格高度（缩略图 + 文本 + padding）
            thumb_side = int(self.thumb_size_var.get())
            estimated_cell_height = thumb_side + 120  # 缩略图 + 文本 + padding（增加一些余量）
            
            # 计算可见行范围（缓冲区恢复到2行，平衡内存和流畅度）
            cell_width = thumb_side + self.thumb_padding
            first_visible_row = max(0, int(canvas_top / estimated_cell_height) - 2)
            last_visible_row = int(canvas_bottom / estimated_cell_height) + 2
            
            return first_visible_row, last_visible_row, estimated_cell_height
        except Exception:
            # 出错时返回默认值
            return 0, 10, 200
    
    def _on_canvas_scroll(self, event=None):
        """画布滚动时的回调，触发虚拟化渲染"""
        # 延迟渲染，避免滚动时频繁调用
        if hasattr(self, '_scroll_after_id') and self._scroll_after_id:
            try:
                self.frame.after_cancel(self._scroll_after_id)
            except Exception:
                pass
        
        self._scroll_after_id = self.frame.after(200, self._render_visible_items)  # 增加延迟至200ms，进一步降低触发频率，减少残影
    
    def _render_visible_items(self):
        """根据可见区域渲染缩略图"""
        if not self.all_results:
            return
        
        first_row, last_row, cell_height = self._get_visible_range()
        
        # 计算需要渲染的项目
        items_to_render = set()
        for idx in range(len(self.all_results)):
            r = idx // self.cols
            if first_row <= r <= last_row:
                items_to_render.add(idx)
        
        # 移除不在可见范围内的项目（释放内存）
        to_remove = []
        for key in self.rendered_cells.keys():
            try:
                idx = int(key.split('_')[-1])  # 从key中提取索引
                if idx not in items_to_render:
                    to_remove.append(key)
            except Exception:
                pass
        
        for key in to_remove:
            if key in self.rendered_cells:
                try:
                    self.rendered_cells[key].destroy()
                    del self.rendered_cells[key]
                except Exception:
                    pass
            # 主动释放图片引用
            if key in self.image_refs:
                try:
                    # 删除ImageTk对象
                    del self.image_refs[key]
                except Exception:
                    pass
            if key in self.item_paths:
                try:
                    del self.item_paths[key]
                except Exception:
                    pass
        
        # 优化GC策略：使用累积计数而非每次都检查
        # 只有累积删除超过10个项目时才触发GC，避免频繁GC造成卡顿
        if len(to_remove) > 0:
            # 累积删除计数
            if not hasattr(self, '_removed_count'):
                self._removed_count = 0
            self._removed_count += len(to_remove)
            
            # 当累积删除超过10个项目时才GC
            if self._removed_count >= 10:
                gc.collect()
                self._removed_count = 0
        
        # 渲染新的可见项目
        thumb_side = int(self.thumb_size_var.get())
        for idx in items_to_render:
            r = idx // self.cols
            c = idx % self.cols
            key = f"{r}_{c}_{idx}"
            
            # 如果已经渲染过，跳过
            if key in self.rendered_cells:
                continue
            
            result = self.all_results[idx]
            file_path = result.get('file_path') or ''
            
            # 创建单元格
            cell = ttk.Frame(self.grid_frame, relief=tk.FLAT, padding=5)
            cell.grid(row=r, column=c, padx=5, pady=5, sticky='n')
            self.rendered_cells[key] = cell
            
            # 加载缩略图
            imgtk = None
            try:
                if file_path and os.path.exists(file_path):
                    img = Image.open(file_path)
                    img.thumbnail((thumb_side, thumb_side))
                    imgtk = ImageTk.PhotoImage(img)
            except Exception:
                imgtk = None
            
            if imgtk is not None:
                btn = ttk.Button(cell, image=imgtk)
                # 修复lambda闭包问题，确保file_path绑定正确
                btn.bind('<Double-Button-1>', lambda e, path=file_path: self.open_file(path))
                btn.image = imgtk
                btn.pack()
                self.image_refs[key] = imgtk
            else:
                lbl = ttk.Label(cell, text='(无法加载)', width=16, anchor='center')
                lbl.pack()
            
            # 文本摘要
            text = result['text'][:40] + '...' if result['text'] and len(result['text']) > 40 else (result['text'] or '(无文本)')
            ttk.Label(cell, text=text, wraplength=thumb_side).pack()
            ttk.Label(cell, text=result['emotion'] or '未分类').pack()
            
            self.item_paths[key] = file_path
