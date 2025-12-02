#!/usr:bin/env python
# -*- coding: utf-8 -*-
"""
图片搜索标签页 - Canvas+Widget混合架构（优化布局版本）
"""

import gc
import os
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, Menu
from tkinter import font as tkfont
from PIL import Image, ImageTk

from .. core. database import ImageDatabase


class CheckboxDropdown:
    """带复选框的下拉菜单控件"""
    
    def __init__(self, parent, options, default_text="请选择", callback=None, width=20):
        """
        Args:
            parent: 父控件
            options: 选项列表 [(显示文本, 值), ...]
            default_text: 默认显示文本
            callback: 选择变化时的回调函数
            width: 按钮宽度
        """
        self.parent = parent
        self.options = options
        self.default_text = default_text
        self.callback = callback
        self.width = width
        
        # 存储选中状态
        self.vars = {}  # {value: BooleanVar}
        for label, value in options:
            self.vars[value] = tk.BooleanVar(value=False)
        
        # 创建主按钮
        self.button = ttk.Button(parent, text=default_text, command=self._toggle_menu, width=width)
        
        # 下拉菜单窗口（初始为None）
        self.menu_window = None
        self.is_open = False
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.button.grid(**kwargs)
    
    def _toggle_menu(self):
        """切换下拉菜单显示/隐藏"""
        if self.is_open:
            self._close_menu()
        else:
            self._open_menu()
    
    def _open_menu(self):
        """打开下拉菜单"""
        if self.is_open:
            return
        
        # 创建Toplevel窗口作为下拉菜单
        self.menu_window = tk.Toplevel(self.parent)
        self.menu_window.withdraw()  # 先隐藏
        self.menu_window.overrideredirect(True)  # 去掉窗口边框
        
        # 创建框架
        frame = ttk.Frame(self.menu_window, relief=tk.RAISED, borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加复选框
        for label, value in self.options:
            cb = ttk.Checkbutton(
                frame, 
                text=label, 
                variable=self.vars[value],
                command=self._on_selection_change
            )
            cb.pack(anchor=tk.W, padx=5, pady=2)
        
        # 添加"全选"和"清空"按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="全选", command=self._select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空", command=self._clear_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="确定", command=self._close_menu, width=8).pack(side=tk.LEFT, padx=2)
        
        # 计算位置（在按钮下方）
        self.menu_window.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        self.menu_window.geometry(f"+{x}+{y}")
        
        # 显示窗口
        self.menu_window.deiconify()
        self.is_open = True
        
        # 绑定点击外部关闭菜单
        self.menu_window.bind("<FocusOut>", lambda e: self._close_menu())
        self.menu_window.focus_set()
    
    def _close_menu(self):
        """关闭下拉菜单"""
        if self.menu_window:
            self.menu_window.destroy()
            self.menu_window = None
        self.is_open = False
        self._update_button_text()
    
    def _on_selection_change(self):
        """选择变化时的处理"""
        self._update_button_text()
        if self.callback:
            self.callback()
    
    def _update_button_text(self):
        """更新按钮显示文本"""
        selected = self.get_selected_values()
        if not selected:
            text = self.default_text
        elif len(selected) == 1:
            # 找到对应的显示文本
            for label, value in self.options:
                if value == selected[0]:
                    text = label
                    break
            else:
                text = selected[0]
        else:
            text = f"已选 {len(selected)} 项"
        
        self.button.config(text=text)
    
    def _select_all(self):
        """全选"""
        for var in self.vars.values():
            var.set(True)
        self._on_selection_change()
    
    def _clear_all(self):
        """清空选择"""
        for var in self.vars.values():
            var.set(False)
        self._on_selection_change()
    
    def get_selected_values(self):
        """获取选中的值列表"""
        return [value for value, var in self.vars.items() if var.get()]
    
    def set_selected_values(self, values):
        """设置选中的值"""
        for value, var in self.vars.items():
            var.set(value in values)
        self._update_button_text()


class SearchTab:
    """图片搜索标签页"""
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        
        # Canvas Items 引用
        self.canvas_items = {}  # {key: [img_id, text_id, emotion_id, bg_rect_id]}
        self.image_refs = {}    # {key: PhotoImage}
        self.item_paths = {}    # {key: file_path}
        self.event_rects = {}   # {key: (x1, y1, x2, y2)} 事件区域
        
        # 延迟调度
        self._reload_after_id = None
        self._scroll_after_id = None
        
        # 虚拟化列表变量
        self. all_results = []
        self.cell_height = 200
        self.cell_width = 140
        
        # 🔥 创建字体对象用于精确测量文本
        self.text_font = tkfont.Font(family="TkDefaultFont", size=9)
        self.emotion_font = tkfont.Font(family="TkDefaultFont", size=8)
        
        # 多选筛选列表
        self.selected_emotions = []  # 选中的情感列表
        self.selected_sources = []   # 选中的图源ID列表
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 搜索条件区
        search_frame = ttk. LabelFrame(self.frame, text="搜索条件", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 第一行：关键词
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self. search_keyword = tk.StringVar()
        keyword_entry = ttk.Entry(search_frame, textvariable=self.search_keyword, width=40)
        keyword_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        keyword_entry.bind('<Return>', lambda e: self.search_images())
        
        ttk.Button(search_frame, text="🔍 搜索", command=self.search_images).grid(row=0, column=4, padx=5)
        ttk.Button(search_frame, text="🔄 刷新", command=self.refresh_page).grid(row=0, column=5, padx=5)
        
        # 第二行：情感多选下拉菜单
        ttk.Label(search_frame, text="情绪:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        emotions = [('正向', '正向'), ('负向', '负向'), ('中性', '中性')]
        self.emotion_dropdown = CheckboxDropdown(
            search_frame, 
            emotions, 
            default_text="全部情绪",
            callback=self._on_emotion_filter_change,
            width=15
        )
        self.emotion_dropdown.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 第三行：图源多选下拉菜单
        ttk.Label(search_frame, text="图源:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        # 先创建一个空的下拉菜单，稍后加载图源数据
        self.source_dropdown = CheckboxDropdown(
            search_frame,
            [],  # 初始为空
            default_text="全部图源",
            callback=self._on_source_filter_change,
            width=25
        )
        self.source_dropdown.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 加载图源列表
        self._load_sources()
        
        # 结果列表区
        result_frame = ttk.LabelFrame(self.frame, text="搜索结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 滚动条
        vsb = ttk.Scrollbar(result_frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas 用于渲染图片和文本
        self.canvas = tk.Canvas(result_frame, yscrollcommand=vsb. set, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.configure(command=self.canvas.yview)

        # 绑定Canvas事件
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)
        self.canvas.bind('<Button-5>', self._on_mousewheel)
        self.canvas.bind('<Configure>', self._on_canvas_scroll)
        
        # 绑定右键菜单和双击
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<Double-Button-1>', self._on_double_click)
        
        # 绑定悬停效果
        self.canvas.bind('<Motion>', self._on_mouse_motion)
        self.canvas.bind('<Leave>', self._on_mouse_leave)
        self._hover_item = None

        # 缩略图大小
        self.thumb_size_var = tk.IntVar(value=120)
        self.thumb_padding = 20
        self.cols = 4

        # 分页控件
        pager_frame = ttk.Frame(self.frame)
        pager_frame.pack(fill=tk.X, padx=10, pady=5)

        self.page_size_var = tk.IntVar(value=20)
        ttk.Label(pager_frame, text="每页:").pack(side=tk.LEFT)
        page_size_cb = ttk.Combobox(pager_frame, textvariable=self.page_size_var, 
                                     values=[10, 20, 50, 100], width=5, state='readonly')
        page_size_cb.pack(side=tk.LEFT, padx=5)
        page_size_cb.bind('<<ComboboxSelected>>', lambda e: self.load_page())

        ttk.Label(pager_frame, text=" 缩略图:").pack(side=tk.LEFT)
        thumb_scale = ttk.Scale(pager_frame, from_=60, to=240, orient=tk.HORIZONTAL, 
                                command=lambda v: self._on_thumb_change(v))
        thumb_scale.set(self.thumb_size_var.get())
        thumb_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(pager_frame, textvariable=self.thumb_size_var).pack(side=tk.LEFT)

        self.page_var = tk.IntVar(value=1)
        self.total_pages = 1

        ttk.Button(pager_frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="下一页", command=self.next_page).pack(side=tk. LEFT, padx=5)
        self.page_label = ttk.Label(pager_frame, text="第 1 / 1 页")
        self.page_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(pager_frame, text=" 跳转到页:").pack(side=tk. LEFT)
        self.goto_var = tk.IntVar(value=1)
        self.goto_entry = ttk.Entry(pager_frame, width=6, textvariable=self. goto_var)
        self. goto_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="跳转", command=self.goto_page).pack(side=tk.LEFT)

        # 初始加载
        self.load_page()
    
    def _load_sources(self):
        """加载图源列表到下拉菜单"""
        sources = self.db.get_sources()
        
        # 构建选项列表
        options = []
        for source in sources:
            folder_path = source['folder_path']
            # 显示文件夹名称（路径的最后部分）
            folder_name = folder_path.split('\\')[-1] or folder_path.split('/')[-1] or folder_path
            display_text = f"[{source['id']}] {folder_name}"
            options.append((display_text, source['id']))
        
        # 重新创建下拉菜单
        self.source_dropdown.options = options
        self.source_dropdown.vars = {}
        for label, value in options:
            self.source_dropdown.vars[value] = tk.BooleanVar(value=False)
        self.source_dropdown._update_button_text()
    
    def _on_emotion_filter_change(self):
        """情感筛选变化回调"""
        self.selected_emotions = self.emotion_dropdown.get_selected_values()
        # 自动触发搜索
        self.search_images()
    
    def _on_source_filter_change(self):
        """图源筛选变化回调"""
        self.selected_sources = self.source_dropdown.get_selected_values()
        # 自动触发搜索
        self.search_images()
    
    def set_source_filter(self, source_ids):
        """从外部设置图源筛选（用于从图源页面跳转）"""
        if not isinstance(source_ids, list):
            source_ids = [source_ids]
        
        self.selected_sources = source_ids
        
        # 在下拉菜单中选中对应的项
        self.source_dropdown.set_selected_values(source_ids)
        
        # 触发搜索
        self.search_images()
    
    def search_images(self):
        self.page_var.set(1)
        self.load_page()
    
    def refresh_page(self):
        self._load_sources()  # 刷新图源列表
        self.load_page()

    def load_page(self):
        """加载当前页数据"""
        if self._reload_after_id is not None:
            try:
                self.frame.after_cancel(self._reload_after_id)
            except:
                pass
            self._reload_after_id = None

        page = max(1, int(self.page_var.get()))
        page_size = int(self.page_size_var.get())
        keyword = self.search_keyword.get(). strip()
        
        # 使用多选情感列表
        emotions = self.selected_emotions if self.selected_emotions else None
        # 使用多选图源列表
        source_ids = self.selected_sources if self.selected_sources else None
 
        # 清空Canvas
        self.canvas.delete('all')
        
        # 清空引用
        self.canvas_items.clear()
        self.image_refs.clear()
        self.item_paths.clear()
        self.event_rects.clear()
        
        # 延迟GC
        def delayed_gc():
            gc. collect()
        self.frame.after(100, delayed_gc)

        # 计算总页数
        total = self.db.get_images_count(processed=1, keyword=keyword, emotions=emotions, source_ids=source_ids)
        self.total_pages = max(1, (total + page_size - 1) // page_size)
        if page > self.total_pages:
            page = self.total_pages
            self.page_var.set(page)

        # 获取数据
        self.all_results = self.db.get_images_page(page=page, page_size=page_size, 
                                                     processed=1, keyword=keyword, emotions=emotions, source_ids=source_ids)

        # 🔥 动态计算列数和单元格尺寸
        try:
            canvas_width = max(400, self.canvas.winfo_width())
            thumb_side = int(self.thumb_size_var.get())
            cell_width = thumb_side + self.thumb_padding
            self.cols = max(1, canvas_width // cell_width)
            self.cell_width = cell_width
            
            # 🔥 精确计算单元格高度
            self.cell_height = self._calculate_cell_height(thumb_side)
        except:
            self.cols = 4
            self.cell_width = 140
            self.cell_height = 240

        # 设置滚动区域
        if self.all_results:
            total_rows = (len(self.all_results) + self.cols - 1) // self.cols
            total_height = total_rows * self.cell_height + 50
            self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height))

        self.update_pager()
        self._render_visible_items()

    def _calculate_cell_height(self, thumb_side):
        """🔥 精确计算单元格高度"""
        # 组成部分：
        # 1. 上边距 padding
        top_padding = 10
        
        # 2. 缩略图高度
        image_height = thumb_side
        
        # 3. 图片与文本间距
        image_text_gap = 10
        
        # 4. 文本区域高度（2行）- 增加一些余量
        line_height = self.text_font.metrics('linespace')
        text_height = line_height * 2 + 5  # 最多2行 + 余量
        
        # 5. 文本与情绪标签间距
        text_emotion_gap = 8
        
        # 6. 情绪标签高度 + 余量
        emotion_height = self.emotion_font.metrics('linespace') + 4
        
        # 7. 下边距
        bottom_padding = 15
        
        total_height = (top_padding + image_height + image_text_gap + 
                       text_height + text_emotion_gap + emotion_height + bottom_padding)
        
        return total_height

    def prev_page(self):
        p = max(1, self.page_var.get() - 1)
        if p != self.page_var.get():
            self.page_var. set(p)
            self. load_page()

    def next_page(self):
        p = min(self.total_pages, self.page_var.get() + 1)
        if p != self.page_var. get():
            self.page_var.set(p)
            self.load_page()

    def update_pager(self):
        self.page_label.config(text=f"第 {self. page_var.get()} / {self.total_pages} 页")
    
    def goto_page(self):
        try:
            p = int(self.goto_var.get())
        except:
            p = 1
        p = max(1, min(self.total_pages, p))
        self.page_var.set(p)
        self.load_page()

    def _on_thumb_change(self, value):
        try:
            v = int(float(value))
            self.thumb_size_var.set(v)
        except:
            pass
        self._schedule_reload(250)

    def _schedule_reload(self, delay: int = 200):
        try:
            if self._reload_after_id is not None:
                self.frame.after_cancel(self._reload_after_id)
        except:
            pass
        try:
            self._reload_after_id = self.frame.after(delay, self._do_reload)
        except:
            self._do_reload()

    def _do_reload(self):
        self._reload_after_id = None
        try:
            self.load_page()
        except:
            pass

    def _on_mousewheel(self, event):
        try:
            if event.num == 4:
                delta = -120
            elif event.num == 5:
                delta = 120
            else:
                delta = -1 * int(event.delta)
        except:
            delta = -1 * int(getattr(event, 'delta', 0))
        self.canvas.yview_scroll(int(delta / 120), 'units')

    # ========== Canvas 虚拟化渲染 ==========
    
    def _get_visible_range(self):
        """计算可见行范围"""
        try:
            canvas_top = self.canvas.canvasy(0)
            canvas_bottom = self.canvas.canvasy(self.canvas.winfo_height())
            
            first_visible_row = max(0, int(canvas_top / self.cell_height) - 2)
            last_visible_row = int(canvas_bottom / self.cell_height) + 2
            
            return first_visible_row, last_visible_row
        except:
            return 0, 10
    
    def _on_canvas_scroll(self, event=None):
        """滚动回调"""
        if hasattr(self, '_scroll_after_id') and self._scroll_after_id:
            try:
                self.frame.after_cancel(self._scroll_after_id)
            except:
                pass
        
        # Canvas渲染可以更激进：30ms延迟
        self._scroll_after_id = self.frame. after(30, self._render_visible_items)
    
    def _truncate_text(self, text, max_width, max_lines=2):
        """🔥 截断文本确保不超过指定行数和宽度"""
        if not text:
            return "(无文本)"
        
        # 使用字体对象测量文本宽度
        words = text.replace('\n', ' ').split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # 测量宽度（单位：像素）
            width = self. text_font.measure(test_line)
            
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # 单个词太长，强制截断
                    current_line = word
                
                # 如果已经有了max_lines-1行，最后一行加省略号
                if len(lines) >= max_lines - 1:
                    # 为省略号留出空间
                    while self.text_font.measure(current_line + "...") > max_width and len(current_line) > 0:
                        current_line = current_line[:-1]
                    lines.append(current_line + "...")
                    break
        else:
            if current_line:
                lines. append(current_line)
        
        # 限制最多max_lines行
        return '\n'.join(lines[:max_lines])
    
    def _render_visible_items(self):
        """渲染可见项（Canvas版本 - 优化布局）"""
        if not self.all_results:
            return
        
        first_row, last_row = self._get_visible_range()
        
        # 计算需要渲染的项目
        items_to_render = set()
        for idx in range(len(self.all_results)):
            r = idx // self.cols
            if first_row <= r <= last_row:
                items_to_render.add(idx)
        
        # 删除不可见的Canvas Items
        to_remove = []
        for key in list(self.canvas_items.keys()):
            try:
                idx = int(key. split('_')[-1])
                if idx not in items_to_render:
                    to_remove.append(key)
            except:
                pass
        
        for key in to_remove:
            if key in self.canvas_items:
                for item_id in self.canvas_items[key]:
                    self.canvas.delete(item_id)
                del self.canvas_items[key]
            
            self.image_refs.pop(key, None)
            self.item_paths.pop(key, None)
            self.event_rects.pop(key, None)
        
        # 渲染新项目
        MAX_THUMB_SIZE = 150
        thumb_side = min(int(self.thumb_size_var.get()), MAX_THUMB_SIZE)
        
        for idx in items_to_render:
            r = idx // self.cols
            c = idx % self.cols
            key = f"{r}_{c}_{idx}"
            
            if key in self.canvas_items:
                continue
            
            result = self.all_results[idx]
            file_path = result. get('file_path') or ''
            
            # 🔥 精确计算布局位置
            cell_x = c * self.cell_width
            cell_y = r * self.cell_height
            
            # 内容居中的X坐标
            center_x = cell_x + self.cell_width // 2
            
            items = []
            
            # 🔥 1. 绘制背景矩形
            bg_rect = self.canvas.create_rectangle(
                cell_x + 5,
                cell_y + 5,
                cell_x + self.cell_width - 5,
                cell_y + self. cell_height - 5,
                fill='white',
                outline='#ddd',
                width=1,
                tags=key
            )
            items.append(bg_rect)
            
            # 🔥 2. 绘制缩略图（从顶部开始）
            image_y = cell_y + 10  # 顶部padding
            
            imgtk = self._load_thumbnail(file_path, thumb_side)
            if imgtk:
                img_id = self.canvas.create_image(
                    center_x, 
                    image_y + thumb_side // 2,  # 图片垂直居中
                    image=imgtk, 
                    tags=key
                )
                items.append(img_id)
                self.image_refs[key] = imgtk
            else:
                text_id = self.canvas.create_text(
                    center_x, 
                    image_y + thumb_side // 2, 
                    text='(无法加载)', 
                    fill='gray', 
                    font=self.text_font,
                    tags=key
                )
                items.append(text_id)
            
            # 🔥 3. 绘制文本（图片下方，不超过2行）
            text_y = image_y + thumb_side + 10  # 图片高度 + 间距
            
            raw_text = result['text'] or ''
            # 文本区域宽度（留出左右padding）
            text_max_width = self.cell_width - 20
            truncated_text = self._truncate_text(raw_text, text_max_width, max_lines=2)
            
            text_id = self. canvas.create_text(
                center_x, 
                text_y,
                text=truncated_text, 
                fill='black',
                font=self.text_font,
                width=text_max_width,  # 限制宽度，自动换行
                anchor='n',  # 从顶部锚定
                tags=key
            )
            items.append(text_id)
            
            # 🔥 4. 绘制情绪标签（固定在单元格底部）
            # 计算情绪标签位置（从单元格底部向上偏移）
            emotion_bottom_offset = 10  # 距离底部的距离
            emotion_height = self.emotion_font.metrics('linespace')
            emotion_y = cell_y + self.cell_height - emotion_bottom_offset - emotion_height
            
            emotion = result['emotion'] or '未分类'
            emotion_color = {'正向': 'green', '负向': 'red', '中性': 'blue'}.get(emotion, 'gray')
            emotion_id = self.canvas.create_text(
                center_x, 
                emotion_y,
                text=emotion, 
                fill=emotion_color,
                font=self.emotion_font,
                anchor='n',
                tags=key
            )
            items.append(emotion_id)
            
            # 保存
            self.canvas_items[key] = items
            self.item_paths[key] = file_path
            
            # 保存事件区域
            self.event_rects[key] = (
                cell_x + 5,
                cell_y + 5,
                cell_x + self.cell_width - 5,
                cell_y + self. cell_height - 5
            )
    
    def _load_thumbnail(self, file_path, thumb_side):
        """加载缩略图"""
        try:
            if not file_path or not os.path.exists(file_path):
                return None
            
            import io
            img = Image.open(file_path)
            img. thumbnail((thumb_side, thumb_side), Image.Resampling.LANCZOS)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img. close()
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=70, optimize=True)
            buffer. seek(0)
            img. close()
            del img
            
            compressed_img = Image.open(buffer)
            imgtk = ImageTk.PhotoImage(compressed_img)
            compressed_img.close()
            buffer.close()
            
            return imgtk
        except Exception as e:
            return None
    
    # ========== Canvas 事件处理 ==========
    
    def _get_item_at_pos(self, x, y):
        """获取鼠标位置的item key"""
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        for key, (x1, y1, x2, y2) in self.event_rects.items():
            if x1 <= canvas_x <= x2 and y1 <= canvas_y <= y2:
                return key
        return None
    
    def _on_mouse_motion(self, event):
        """鼠标移动 - 悬停高亮"""
        key = self._get_item_at_pos(event.x, event.y)
        
        if key != self._hover_item:
            # 恢复旧的
            if self._hover_item and self._hover_item in self. canvas_items:
                bg_rect = self.canvas_items[self._hover_item][0]
                self.canvas. itemconfig(bg_rect, fill='white', outline='#ddd', width=1)
            
            # 高亮新的
            if key and key in self.canvas_items:
                bg_rect = self. canvas_items[key][0]
                self.canvas.itemconfig(bg_rect, fill='#e3f2fd', outline='#1976d2', width=2)
            
            self._hover_item = key
    
    def _on_mouse_leave(self, event):
        """鼠标离开Canvas"""
        if self._hover_item and self._hover_item in self. canvas_items:
            bg_rect = self.canvas_items[self._hover_item][0]
            self.canvas.itemconfig(bg_rect, fill='white', outline='#ddd', width=1)
        self._hover_item = None
    
    def _on_double_click(self, event):
        """双击打开图片"""
        key = self._get_item_at_pos(event.x, event.y)
        if key and key in self.item_paths:
            self.open_file(self.item_paths[key])
    
    def _on_right_click(self, event):
        """右键菜单"""
        key = self._get_item_at_pos(event.x, event.y)
        if key and key in self.item_paths:
            file_path = self.item_paths[key]
            self.show_context_menu(event, file_path)
    
    def show_context_menu(self, event, file_path):
        """显示右键菜单"""
        menu = Menu(self.canvas, tearoff=0)
        menu.add_command(label="📂 打开图片", command=lambda: self. open_file(file_path))
        menu.add_command(label="📁 打开所在文件夹", command=lambda: self.open_folder(file_path))
        menu.add_separator()
        menu.add_command(label="📋 复制路径", command=lambda: self. copy_path(file_path))
        menu.add_command(label="🗑️ 删除图片", command=lambda: self. delete_image(file_path))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def open_file(self, file_path: str):
        """打开图片文件"""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "图片文件不存在")
            return

        try:
            if sys.platform. startswith('win'):
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess. run(['open', file_path], check=False)
            else:
                if shutil.which('xdg-open'):
                    subprocess.run(['xdg-open', file_path], check=False)
                elif shutil.which('gio'):
                    subprocess.run(['gio', 'open', file_path], check=False)
                else:
                    messagebox.showerror("错误", "无法找到系统打开命令")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")
    
    def open_folder(self, file_path):
        """打开文件所在文件夹"""
        folder = os.path.dirname(file_path)
        try:
            if sys.platform. startswith('win'):
                subprocess.run(['explorer', '/select,', file_path])
            elif sys.platform == 'darwin':
                subprocess.run(['open', '-R', file_path])
            else:
                subprocess.run(['xdg-open', folder])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    def copy_path(self, file_path):
        """复制路径到剪贴板"""
        self.frame.clipboard_clear()
        self.frame.clipboard_append(file_path)
        messagebox.showinfo("提示", "路径已复制到剪贴板")
    
    def delete_image(self, file_path):
        """删除图片"""
        if messagebox.askyesno("确认删除", f"确定要删除这张图片吗？\n{file_path}"):
            try:
                os.remove(file_path)
                # self.db.delete_image(file_path)  # 如果数据库有删除方法
                self.refresh_page()
                messagebox.showinfo("成功", "图片已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")