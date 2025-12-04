#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详情面板模块
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


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
        self.detail_canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.detail_canvas.bind('<Button-4>', self._on_mousewheel)
        self.detail_canvas.bind('<Button-5>', self._on_mousewheel)
        self.detail_content_frame.bind('<MouseWheel>', self._on_mousewheel)
        self.detail_content_frame.bind('<Button-4>', self._on_mousewheel)
        self.detail_content_frame.bind('<Button-5>', self._on_mousewheel)
        
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
    
    def _bind_mousewheel_to_widget(self, widget):
        """为控件绑定鼠标滚轮事件"""
        widget.bind('<MouseWheel>', self._on_mousewheel)
        widget.bind('<Button-4>', self._on_mousewheel)
        widget.bind('<Button-5>', self._on_mousewheel)
    
    def show_no_selection(self):
        """显示未选择图片的提示"""
        # 清除当前显示的图片
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
        self._bind_mousewheel_to_widget(hint_label)
    
    def refresh(self):
        """刷新当前显示的图片详情"""
        if self.current_file_path:
            # 重新加载当前图片的详情
            self.show_image_detail(self.current_file_path)
    
    def show_image_detail(self, file_path: str):
        """显示图片详细信息"""
        # 保存当前显示的图片路径
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
            self._bind_mousewheel_to_widget(error_label)
            return
        
        padding = 10
        
        # 1. 标题行（包含收藏状态）
        title_frame = ttk.Frame(self.detail_content_frame)
        title_frame.pack(fill=tk.X, pady=(padding, 5), padx=padding)
        self._bind_mousewheel_to_widget(title_frame)
        
        title_label = ttk.Label(
            title_frame,
            text="图片详情",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        self._bind_mousewheel_to_widget(title_label)
        
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
        self._bind_mousewheel_to_widget(favorite_btn)
        
        sep1 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep1.pack(fill=tk.X, pady=5, padx=padding)
        self._bind_mousewheel_to_widget(sep1)
        
        # 2. 缩略图
        thumb_label = ttk.Label(self.detail_content_frame, text="缩略图:")
        thumb_label.pack(pady=(10, 5), anchor='w', padx=padding)
        self._bind_mousewheel_to_widget(thumb_label)
        
        try:
            if os.path.exists(file_path):
                img = Image.open(file_path)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img.close()
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                photo = ImageTk.PhotoImage(img)
                img_label = ttk.Label(self.detail_content_frame, image=photo)
                img_label.image = photo
                img_label.pack(pady=5, padx=padding)
                self._bind_mousewheel_to_widget(img_label)
            else:
                no_img_label = ttk.Label(self.detail_content_frame, text="(图片文件不存在)", foreground='red')
                no_img_label.pack(pady=5, padx=padding)
                self._bind_mousewheel_to_widget(no_img_label)
        except Exception as e:
            error_img_label = ttk.Label(self.detail_content_frame, text=f"(无法加载图片: {e})", foreground='red')
            error_img_label.pack(pady=5, padx=padding)
            self._bind_mousewheel_to_widget(error_img_label)
        
        sep2 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep2.pack(fill=tk.X, pady=10, padx=padding)
        self._bind_mousewheel_to_widget(sep2)
        
        # 3. 文件信息
        filename = os.path.basename(file_path)
        self._create_info_row("文件名称:", filename, selectable=True)
        
        # 所属图源
        source_id = detail.get('source_id')
        if source_id:
            sources = self.db.get_sources()
            source_info = next((s for s in sources if s['id'] == source_id), None)
            if source_info:
                source_path = source_info['folder_path']
                source_name = source_path.split('\\')[-1] or source_path.split('/')[-1] or source_path
                self._create_info_row("所属图源:", f"[{source_id}] {source_name}")
            else:
                self._create_info_row("所属图源:", f"图源ID: {source_id}")
        else:
            self._create_info_row("所属图源:", "未知")
        
        # 文件路径
        path_frame = ttk.Frame(self.detail_content_frame)
        path_frame.pack(fill=tk.X, pady=5, padx=padding)
        self._bind_mousewheel_to_widget(path_frame)
        
        path_label = ttk.Label(path_frame, text="文件路径:", font=('TkDefaultFont', 9, 'bold'))
        path_label.pack(anchor='w')
        self._bind_mousewheel_to_widget(path_label)
        
        path_text = tk.Text(path_frame, height=2, wrap=tk.WORD, font=('TkDefaultFont', 8))
        path_text.insert('1.0', file_path)
        path_text.config(state=tk.DISABLED, bg='#f0f0f0')
        path_text.pack(fill=tk.X, pady=2)
        self._bind_mousewheel_to_widget(path_text)
        
        open_folder_btn = ttk.Button(
            path_frame,
            text="📁 在资源管理器中打开",
            command=lambda: self.open_folder_callback(file_path)
        )
        open_folder_btn.pack(pady=2)
        self._bind_mousewheel_to_widget(open_folder_btn)
        
        # 时间信息
        try:
            file_time = os.path.getctime(file_path)
            file_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))
        except:
            file_time_str = "未知"
        self._create_info_row("添加时间:", file_time_str)
        
        scan_time = detail.get('added_time', '未知')
        if scan_time and scan_time != '未知':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(scan_time)
                scan_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        self._create_info_row("扫描时间:", scan_time)
        
        sep3 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep3.pack(fill=tk.X, pady=10, padx=padding)
        self._bind_mousewheel_to_widget(sep3)
        
        # OCR结果
        ocr_frame = ttk.Frame(self.detail_content_frame)
        ocr_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=padding)
        self._bind_mousewheel_to_widget(ocr_frame)
        
        ocr_label = ttk.Label(ocr_frame, text="OCR识别结果:", font=('TkDefaultFont', 9, 'bold'))
        ocr_label.pack(anchor='w')
        self._bind_mousewheel_to_widget(ocr_label)
        
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
        
        self.ocr_text_widget.bind('<MouseWheel>', _on_ocr_mousewheel)
        self.ocr_text_widget.bind('<Button-4>', _on_ocr_mousewheel)
        self.ocr_text_widget.bind('<Button-5>', _on_ocr_mousewheel)
        
        save_btn = ttk.Button(
            ocr_frame,
            text="💾 保存OCR修改",
            command=lambda: self._save_ocr(file_path)
        )
        save_btn.pack(pady=5)
        self._bind_mousewheel_to_widget(save_btn)
        
        # 情绪标签
        emotion = detail.get('emotion', '未分类')
        emotion_manual = detail.get('emotion_manual', False)
        
        emotion_frame = ttk.Frame(self.detail_content_frame)
        emotion_frame.pack(fill=tk.X, pady=5, padx=padding)
        self._bind_mousewheel_to_widget(emotion_frame)
        
        emotion_label1 = ttk.Label(emotion_frame, text="情绪标签:", font=('TkDefaultFont', 9, 'bold'))
        emotion_label1.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self._bind_mousewheel_to_widget(emotion_label1)
        
        self.emotion_var = tk.StringVar(value=emotion)
        emotion_combo = ttk.Combobox(
            emotion_frame,
            textvariable=self.emotion_var,
            values=['正向', '负向', '中性', '未分类'],
            state='readonly',
            width=10
        )
        emotion_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self._bind_mousewheel_to_widget(emotion_combo)
        
        save_emotion_btn = ttk.Button(
            emotion_frame,
            text="💾 保存",
            command=lambda: self._save_emotion(file_path)
        )
        save_emotion_btn.grid(row=0, column=2, padx=(0, 10))
        self._bind_mousewheel_to_widget(save_emotion_btn)
        
        if emotion_manual:
            manual_label = ttk.Label(
                emotion_frame,
                text="(手动)",
                foreground='orange',
                font=('TkDefaultFont', 8)
            )
            manual_label.grid(row=0, column=3)
            self._bind_mousewheel_to_widget(manual_label)
        
        if not emotion_manual and detail.get('emotion_positive') is not None and detail.get('emotion_negative') is not None:
            score_text = f"正向: {detail['emotion_positive']:.2f}, 负向: {detail['emotion_negative']:.2f}"
            score_label = ttk.Label(
                emotion_frame,
                text=score_text,
                font=('TkDefaultFont', 8),
                foreground='gray'
            )
            score_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
            self._bind_mousewheel_to_widget(score_label)
        
        # 自定义标签区域
        sep4 = ttk.Separator(self.detail_content_frame, orient=tk.HORIZONTAL)
        sep4.pack(fill=tk.X, pady=10, padx=10)
        self._bind_mousewheel_to_widget(sep4)
        
        tags_frame = ttk.Frame(self.detail_content_frame)
        tags_frame.pack(fill=tk.X, pady=5, padx=10)
        self._bind_mousewheel_to_widget(tags_frame)
        
        tags_label = ttk.Label(tags_frame, text="自定义标签:", font=('TkDefaultFont', 9, 'bold'))
        tags_label.pack(anchor='w', pady=(0, 5))
        self._bind_mousewheel_to_widget(tags_label)
        
        # 标签显示区域
        self.tags_display_frame = ttk.Frame(tags_frame)
        self.tags_display_frame.pack(fill=tk.X, pady=(0, 5))
        self._bind_mousewheel_to_widget(self.tags_display_frame)
        
        # 加载并显示当前图片的标签
        self._load_and_display_tags(file_path)
        
        # 标签编辑按钮
        tags_btn_frame = ttk.Frame(tags_frame)
        tags_btn_frame.pack(fill=tk.X)
        self._bind_mousewheel_to_widget(tags_btn_frame)
        
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
                self._bind_mousewheel_to_widget(no_tags_label)
            else:
                # 显示标签为彩色标签
                tags_container = ttk.Frame(self.tags_display_frame)
                tags_container.pack(fill=tk.X)
                self._bind_mousewheel_to_widget(tags_container)
                
                for tag in tags:
                    self._create_tag_label(tags_container, tag['name'], tag['color'])
        except Exception as e:
            error_label = ttk.Label(
                self.tags_display_frame,
                text=f"加载标签失败: {e}",
                foreground='red',
                font=('TkDefaultFont', 8)
            )
            error_label.pack(anchor='w')
            self._bind_mousewheel_to_widget(error_label)
    
    def _create_tag_label(self, parent, name: str, color: str):
        """创建一个彩色标签显示"""
        tag_label = tk.Label(
            parent,
            text=f" {name} ",
            bg=color,
            fg=self._get_contrast_color(color),
            font=('TkDefaultFont', 8, 'bold'),
            relief=tk.RAISED,
            padx=5,
            pady=2
        )
        tag_label.pack(side=tk.LEFT, padx=2, pady=2)
        self._bind_mousewheel_to_widget(tag_label)
    
    def _get_contrast_color(self, hex_color: str):
        """根据背景色返回对比色（黑色或白色）"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            # 计算亮度
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return 'black' if brightness > 128 else 'white'
        except:
            return 'black'
    
    def _edit_image_tags(self, file_path: str):
        """编辑图片标签"""
        from .tag_selector_dialog import TagSelectorDialog
        
        dialog = TagSelectorDialog(
            self.parent_frame.winfo_toplevel(),
            self.db,
            file_path,
            callback=lambda: self._on_tags_updated(file_path)
        )
    
    def _on_tags_updated(self, file_path: str):
        """标签更新后的回调"""
        self._load_and_display_tags(file_path)
    
    def _open_tag_manager(self):
        """打开标签管理对话框"""
        from ..tag_manager_dialog import TagManagerDialog
        
        TagManagerDialog(
            self.parent_frame.winfo_toplevel(),
            self.db,
            callback=None
        )
    
    def _create_info_row(self, label_text: str, value_text: str, selectable: bool = False):
        """创建信息行"""
        frame = ttk.Frame(self.detail_content_frame)
        frame.pack(fill=tk.X, pady=5, padx=10)
        self._bind_mousewheel_to_widget(frame)
        
        label = ttk.Label(frame, text=label_text, font=('TkDefaultFont', 9, 'bold'))
        label.pack(anchor='w')
        self._bind_mousewheel_to_widget(label)
        
        if selectable:
            text_widget = tk.Text(frame, height=1, wrap=tk.NONE, font=('TkDefaultFont', 9))
            text_widget.insert('1.0', value_text)
            text_widget.config(state=tk.DISABLED, bg='#f0f0f0')
            text_widget.pack(fill=tk.X, pady=2)
            self._bind_mousewheel_to_widget(text_widget)
        else:
            value = ttk.Label(frame, text=value_text, font=('TkDefaultFont', 9))
            value.pack(anchor='w', pady=2)
            self._bind_mousewheel_to_widget(value)
    
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
