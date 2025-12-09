#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详情面板模块
"""

import os
import time
import tkinter as tk
from tkinter import ttk
from . import detail_widgets

class DetailPanel:
    """图片详情面板"""
    
    def __init__(self, parent_frame, db, favorite_cache, on_favorite_toggle, on_ocr_save, on_emotion_save, open_folder_callback):
        """
        Args:
            parent_frame: 父框架
            db: 数据库实例
            favorite_cache: 收藏状态缓存字典
            on_favorite_toggle: 切换收藏回调 (file_path, new_state)
            on_ocr_save: 保存OCR回调 (file_path, new_text)
            on_emotion_save: 保存情绪回调 (file_path, new_emotion)
            open_folder_callback: 打开文件夹回调 (file_path)
        """
        self.parent_frame = parent_frame
        self.db = db
        self.favorite_cache = favorite_cache
        self.on_favorite_toggle = on_favorite_toggle
        self.on_ocr_save = on_ocr_save
        self.on_emotion_save = on_emotion_save
        self.open_folder_callback = open_folder_callback
        
        # 记录当前显示的图片
        self.current_file_path = None
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        # 使用Canvas+Scrollbar实现可滚动的详情面板
        self.detail_canvas = tk.Canvas(self.parent_frame, bg='white', highlightthickness=0)
        detail_scrollbar = ttk.Scrollbar(self.parent_frame, orient=tk.VERTICAL, command=self.detail_canvas.yview)
        
        self.detail_content_frame = ttk.Frame(self.detail_canvas)
        
        # 创建窗口
        self.detail_canvas_window = self.detail_canvas.create_window((0, 0), window=self.detail_content_frame, anchor='nw')
        self.detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        
        # 布局
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 更新滚动区域
        self.detail_content_frame.bind("<Configure>", self._configure_scroll_region)
        self.detail_canvas.bind("<Configure>", self._configure_canvas_width)
        
        # 绑定鼠标滚轮
        detail_widgets.bind_mousewheel(self.detail_canvas, self._on_mousewheel)
        detail_widgets.bind_mousewheel(self.detail_content_frame, self._on_mousewheel)
        
        # 默认显示提示
        self.show_no_selection()
    
    def _configure_scroll_region(self, event):
        """配置滚动区域"""
        self.detail_canvas.update_idletasks()
        bbox = self.detail_canvas.bbox("all")
        if bbox:
            canvas_height = self.detail_canvas.winfo_height()
            content_height = bbox[3] - bbox[1]
            
            if content_height > canvas_height:
                self.detail_canvas.configure(scrollregion=bbox)
            else:
                self.detail_canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                self.detail_canvas.yview_moveto(0)
    
    def _configure_canvas_width(self, event):
        """配置Canvas宽度"""
        canvas_width = event.width
        canvas_height = event.height
        if canvas_width > 1:
            self.detail_canvas.itemconfig(self.detail_canvas_window, width=canvas_width)
            self.detail_canvas.update_idletasks()
            
            bbox = self.detail_canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                if content_height > canvas_height:
                    self.detail_canvas.configure(scrollregion=bbox)
                else:
                    self.detail_canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                    self.detail_canvas.yview_moveto(0)
    
    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        try:
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = -1 * int(event.delta / 120)
            self.detail_canvas.yview_scroll(delta, 'units')
        except:
            pass
            
    def show_no_selection(self):
        """显示未选择图片的提示"""
        self.current_file_path = None
        
        for widget in self.detail_content_frame.winfo_children():
            widget.destroy()
        
        hint_label = ttk.Label(
            self.detail_content_frame, 
            text="请点击左侧图片查看详情", 
            font=('TkDefaultFont', 10),
            foreground='gray'
        )
        hint_label.pack(pady=50)
        detail_widgets.bind_mousewheel(hint_label, self._on_mousewheel)
    
    def refresh(self):
        """刷新当前显示的图片详情"""
        if self.current_file_path:
            self.show_image_detail(self.current_file_path)
    
    def show_image_detail(self, file_path: str):
        """显示图片详细信息"""
        self.current_file_path = file_path
        
        # 清空详情面板
        for widget in self.detail_content_frame.winfo_children():
            widget.destroy()
        
        # 从数据库获取详细信息
        detail = self.db.get_image_detail(file_path)
        if not detail:
            error_label = ttk.Label(
                self.detail_content_frame,
                text="无法获取图片信息",
                foreground='red'
            )
            error_label.pack(pady=20)
            detail_widgets.bind_mousewheel(error_label, self._on_mousewheel)
            return
        
        padding = 10
        
        # 1. 标题行（包含收藏状态）
        self._create_title_section(detail, file_path, padding)
        
        # 2. 缩略图
        detail_widgets.create_thumbnail(self.detail_content_frame, file_path, self._on_mousewheel, padding)
        
        sep2 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep2.pack(fill=tk.X, pady=10, padx=padding)
        detail_widgets.bind_mousewheel(sep2, self._on_mousewheel)
        
        # 3. 文件信息
        self._create_file_info_section(detail, file_path, padding)
        
        sep3 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep3.pack(fill=tk.X, pady=10, padx=padding)
        detail_widgets.bind_mousewheel(sep3, self._on_mousewheel)
        
        # 4. OCR结果
        self._create_ocr_section(detail, file_path, padding)
        
        # 5. 情绪标签
        self._create_emotion_section(detail, file_path, padding)
        
        # 6. 主题色显示
        detail_widgets.create_color_section(self.detail_content_frame, detail, self._on_mousewheel, padding)
        
        # 7. 自定义标签区域
        self._create_tags_section(file_path, padding)

    def _create_title_section(self, detail, file_path, padding):
        """创建标题区域"""
        title_frame = ttk.Frame(self.detail_content_frame)
        title_frame.pack(fill=tk.X, pady=(padding, 5), padx=padding)
        detail_widgets.bind_mousewheel(title_frame, self._on_mousewheel)
        
        title_label = ttk.Label(
            title_frame,
            text="图片详情",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        detail_widgets.bind_mousewheel(title_label, self._on_mousewheel)
        
        # 收藏按钮
        is_favorite = detail.get('is_favorite', False)
        try:
            style = ttk.Style()
            default_bg = style.lookup('TFrame', 'background')
        except:
            default_bg = 'SystemButtonFace'
        
        favorite_btn = tk.Button(
            title_frame,
            text='❤' if is_favorite else '♥',
            font=('Segoe UI Emoji', 16, 'normal'),
            fg='#ff4757' if is_favorite else '#dfe4ea',
            bd=0,
            bg=default_bg,
            cursor='hand2',
            command=lambda: self._toggle_favorite(file_path, favorite_btn)
        )
        favorite_btn.pack(side=tk.RIGHT, padx=5)
        detail_widgets.bind_mousewheel(favorite_btn, self._on_mousewheel)
        
        sep1 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep1.pack(fill=tk.X, pady=5, padx=padding)
        detail_widgets.bind_mousewheel(sep1, self._on_mousewheel)

    def _create_file_info_section(self, detail, file_path, padding):
        """创建文件信息区域"""
        filename = os.path.basename(file_path)
        detail_widgets.create_info_row(self.detail_content_frame, "文件名称:", filename, self._on_mousewheel, selectable=True)
        
        # 所属图源
        source_id = detail.get('source_id')
        if source_id:
            sources = self.db.get_sources()
            source_info = next((s for s in sources if s['id'] == source_id), None)
            if source_info:
                source_path = source_info['folder_path']
                source_name = source_path.split('\\')[-1] or source_path.split('/')[-1] or source_path
                source_text = f"[{source_id}] {source_name}"
            else:
                source_text = f"图源ID: {source_id}"
        else:
            source_text = "未知"
        detail_widgets.create_info_row(self.detail_content_frame, "所属图源:", source_text, self._on_mousewheel)
        
        # 文件路径
        path_frame = ttk.Frame(self.detail_content_frame)
        path_frame.pack(fill=tk.X, pady=5, padx=padding)
        detail_widgets.bind_mousewheel(path_frame, self._on_mousewheel)
        
        path_label = ttk.Label(path_frame, text="文件路径:", font=('TkDefaultFont', 9, 'bold'))
        path_label.pack(anchor='w')
        detail_widgets.bind_mousewheel(path_label, self._on_mousewheel)
        
        path_text = tk.Text(path_frame, height=2, wrap=tk.WORD, font=('TkDefaultFont', 8))
        path_text.insert('1.0', file_path)
        path_text.config(state=tk.DISABLED, bg='#f0f0f0')
        path_text.pack(fill=tk.X, pady=2)
        detail_widgets.bind_mousewheel(path_text, self._on_mousewheel)
        
        open_folder_btn = ttk.Button(
            path_frame,
            text="📁 在资源管理器中打开",
            command=lambda: self.open_folder_callback(file_path)
        )
        open_folder_btn.pack(pady=2)
        detail_widgets.bind_mousewheel(open_folder_btn, self._on_mousewheel)
        
        # 时间信息
        try:
            file_time = os.path.getctime(file_path)
            file_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))
        except:
            file_time_str = "未知"
        detail_widgets.create_info_row(self.detail_content_frame, "添加时间:", file_time_str, self._on_mousewheel)
        
        scan_time = detail.get('added_time', '未知')
        if scan_time and scan_time != '未知':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(scan_time)
                scan_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        detail_widgets.create_info_row(self.detail_content_frame, "扫描时间:", scan_time, self._on_mousewheel)

    def _create_ocr_section(self, detail, file_path, padding):
        """创建OCR区域"""
        ocr_frame = ttk.Frame(self.detail_content_frame)
        ocr_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=padding)
        detail_widgets.bind_mousewheel(ocr_frame, self._on_mousewheel)
        
        ocr_label = ttk.Label(ocr_frame, text="OCR识别结果:", font=('TkDefaultFont', 9, 'bold'))
        ocr_label.pack(anchor='w')
        detail_widgets.bind_mousewheel(ocr_label, self._on_mousewheel)
        
        self.ocr_text_widget = tk.Text(ocr_frame, height=8, wrap=tk.WORD, font=('TkDefaultFont', 9))
        self.ocr_text_widget.insert('1.0', detail.get('ocr_text', ''))
        self.ocr_text_widget.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # OCR文本框智能滚轮
        def _on_ocr_mousewheel(event):
            if self.ocr_text_widget.focus_get() == self.ocr_text_widget:
                try:
                    visible_lines = int(self.ocr_text_widget.cget('height'))
                    total_lines = int(self.ocr_text_widget.index('end-1c').split('.')[0])
                    
                    if total_lines <= visible_lines:
                        self._on_mousewheel(event)
                        return 'break'
                except:
                    self._on_mousewheel(event)
                    return 'break'
            else:
                self._on_mousewheel(event)
                return 'break'
        
        detail_widgets.bind_mousewheel(self.ocr_text_widget, _on_ocr_mousewheel)
        
        save_btn = ttk.Button(
            ocr_frame,
            text="💾 保存OCR修改",
            command=lambda: self._save_ocr(file_path)
        )
        save_btn.pack(pady=5)
        detail_widgets.bind_mousewheel(save_btn, self._on_mousewheel)

    def _create_emotion_section(self, detail, file_path, padding):
        """创建情绪标签区域"""
        emotion = detail.get('emotion', '未分类')
        emotion_manual = detail.get('emotion_manual', False)
        
        emotion_frame = ttk.Frame(self.detail_content_frame)
        emotion_frame.pack(fill=tk.X, pady=5, padx=padding)
        detail_widgets.bind_mousewheel(emotion_frame, self._on_mousewheel)
        
        emotion_label1 = ttk.Label(emotion_frame, text="情绪标签:", font=('TkDefaultFont', 9, 'bold'))
        emotion_label1.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        detail_widgets.bind_mousewheel(emotion_label1, self._on_mousewheel)
        
        self.emotion_var = tk.StringVar(value=emotion)
        emotion_combo = ttk.Combobox(
            emotion_frame,
            textvariable=self.emotion_var,
            values=['正向', '负向', '中性', '未分类'],
            state='readonly',
            width=10
        )
        emotion_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        detail_widgets.bind_mousewheel(emotion_combo, self._on_mousewheel)
        
        save_emotion_btn = ttk.Button(
            emotion_frame,
            text="💾 保存",
            command=lambda: self._save_emotion(file_path)
        )
        save_emotion_btn.grid(row=0, column=2, padx=(0, 10))
        detail_widgets.bind_mousewheel(save_emotion_btn, self._on_mousewheel)
        
        if emotion_manual:
            manual_label = ttk.Label(
                emotion_frame,
                text="(手动)",
                foreground='orange',
                font=('TkDefaultFont', 8)
            )
            manual_label.grid(row=0, column=3)
            detail_widgets.bind_mousewheel(manual_label, self._on_mousewheel)
        
        if not emotion_manual and detail.get('emotion_positive') is not None and detail.get('emotion_negative') is not None:
            score_text = f"正向: {detail['emotion_positive']:.2f}, 负向: {detail['emotion_negative']:.2f}"
            score_label = ttk.Label(
                emotion_frame,
                text=score_text,
                font=('TkDefaultFont', 8),
                foreground='gray'
            )
            score_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
            detail_widgets.bind_mousewheel(score_label, self._on_mousewheel)

    def _create_tags_section(self, file_path, padding):
        """创建标签区域"""
        sep4 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep4.pack(fill=tk.X, pady=10, padx=padding)
        detail_widgets.bind_mousewheel(sep4, self._on_mousewheel)
        
        tags_frame = ttk.Frame(self.detail_content_frame)
        tags_frame.pack(fill=tk.X, pady=5, padx=padding)
        detail_widgets.bind_mousewheel(tags_frame, self._on_mousewheel)
        
        tags_label = ttk.Label(tags_frame, text="自定义标签:", font=('TkDefaultFont', 9, 'bold'))
        tags_label.pack(anchor='w', pady=(0, 5))
        detail_widgets.bind_mousewheel(tags_label, self._on_mousewheel)
        
        # 标签显示区域
        self.tags_display_frame = ttk.Frame(tags_frame)
        self.tags_display_frame.pack(fill=tk.X, pady=(0, 5))
        detail_widgets.bind_mousewheel(self.tags_display_frame, self._on_mousewheel)
        
        # 加载并显示当前图片的标签
        self._load_and_display_tags(file_path)
        
        # 标签编辑按钮
        tags_btn_frame = ttk.Frame(tags_frame)
        tags_btn_frame.pack(fill=tk.X)
        detail_widgets.bind_mousewheel(tags_btn_frame, self._on_mousewheel)
        
        ttk.Button(
            tags_btn_frame,
            text="🏷️ 编辑标签",
            command=lambda: self._edit_image_tags(file_path)
        ).pack(side=tk.LEFT)

    def _load_and_display_tags(self, file_path: str):
        """加载并显示图片的标签"""
        # 清空现有标签显示
        for widget in self.tags_display_frame.winfo_children():
            widget.destroy()
        
        try:
            tags = self.db.get_image_tags_by_path(file_path)
            
            if not tags:
                no_tags_label = ttk.Label(
                    self.tags_display_frame,
                    text="暂无标签",
                    foreground='gray',
                    font=('TkDefaultFont', 8)
                )
                no_tags_label.pack(anchor='w')
                detail_widgets.bind_mousewheel(no_tags_label, self._on_mousewheel)
            else:
                # 显示标签为彩色标签
                tags_container = ttk.Frame(self.tags_display_frame)
                tags_container.pack(fill=tk.X)
                detail_widgets.bind_mousewheel(tags_container, self._on_mousewheel)
                
                for tag in tags:
                    detail_widgets.create_tag_label(tags_container, tag['name'], tag['color'], self._on_mousewheel)
        except Exception as e:
            error_label = ttk.Label(
                self.tags_display_frame,
                text=f"加载标签失败: {e}",
                foreground='red',
                font=('TkDefaultFont', 8)
            )
            error_label.pack(anchor='w')
            detail_widgets.bind_mousewheel(error_label, self._on_mousewheel)

    def _edit_image_tags(self, file_path: str):
        """编辑图片标签"""
        from .tag_selector_dialog import TagSelectorDialog
        
        TagSelectorDialog(
            self.parent_frame.winfo_toplevel(),
            self.db,
            file_path,
            callback=lambda: self._on_tags_updated(file_path)
        )
    
    def _on_tags_updated(self, file_path: str):
        """标签更新后的回调"""
        self._load_and_display_tags(file_path)
    
    def _toggle_favorite(self, file_path: str, btn):
        """切换收藏状态"""
        current_state = self.favorite_cache.get(file_path, False)
        new_state = not current_state
        
        if self.db.update_favorite(file_path, new_state):
            self.favorite_cache[file_path] = new_state
            btn.config(
                text='❤' if new_state else '♥',
                fg='#ff4757' if new_state else '#dfe4ea'
            )
            # 通知主窗口更新列表显示
            self.on_favorite_toggle(file_path, new_state)
    
    def _save_ocr(self, file_path: str):
        """保存OCR修改"""
        new_ocr_text = self.ocr_text_widget.get('1.0', tk.END).strip()
        self.on_ocr_save(file_path, new_ocr_text)
    
    def _save_emotion(self, file_path: str):
        """保存情绪修改"""
        new_emotion = self.emotion_var.get()
        self.on_emotion_save(file_path, new_emotion)
