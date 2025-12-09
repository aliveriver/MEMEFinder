#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片搜索标签页 - 主类（重构版）
"""

import gc
import tkinter as tk
from tkinter import ttk, messagebox

from ...core.database import ImageDatabase
from ...core.database.image_sorter import ImageSorter
from ...utils.logger import get_logger
from .checkbox_dropdown import CheckboxDropdown
from .detail_panel import DetailPanel
from .canvas_renderer import CanvasRenderer
from .event_handlers import EventHandlers
from .context_menu import ContextMenu

logger = get_logger()


class SearchTab:
    """图片搜索标签页"""
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        
        # 数据相关
        self.all_results = []
        self.selected_items = set()  # 存储选中的file_path
        self.last_clicked_index = None
        self.favorite_cache = {}
        
        # 筛选条件
        self.selected_emotions = []
        self.selected_sources = []
        self.selected_tags = []
        
        # 延迟调度ID
        self._reload_after_id = None
        self._scroll_after_id = None
        self._configure_after_id = None
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 1. 搜索条件区
        self._create_search_frame()
        
        # 2. 结果显示区
        self._create_result_frame()
        
        # 3. 分页控件
        self._create_pager_frame()
        
        # 初始加载
        self.load_page()
    
    def _create_search_frame(self):
        """创建搜索条件框架"""
        search_frame = ttk.LabelFrame(self.frame, text="搜索条件", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 关键词
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_keyword = tk.StringVar()
        keyword_entry = ttk.Entry(search_frame, textvariable=self.search_keyword, width=40)
        keyword_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        keyword_entry.bind('<Return>', lambda e: self.search_images())
        
        ttk.Button(search_frame, text="🔍 搜索", command=self.search_images).grid(row=0, column=4, padx=5)
        ttk.Button(search_frame, text="🔄 刷新", command=self.refresh_page).grid(row=0, column=5, padx=5)
        ttk.Button(search_frame, text="🖼️ 以图搜图", command=self._search_by_image).grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="🔖 管理标签", command=self._open_tag_manager).grid(row=0, column=7, padx=5)
        
        # 情感筛选
        ttk.Label(search_frame, text="情绪:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        emotions = [('正向', '正向'), ('负向', '负向'), ('中性', '中性')]
        self.emotion_dropdown = CheckboxDropdown(
            search_frame, emotions, default_text="全部情绪",
            callback=self._on_emotion_filter_change, width=15
        )
        self.emotion_dropdown.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 图源筛选
        ttk.Label(search_frame, text="图源:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.source_dropdown = CheckboxDropdown(
            search_frame, [], default_text="全部图源",
            callback=self._on_source_filter_change, width=15
        )
        self.source_dropdown.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 标签筛选（使用小 Frame 控制间距，避免 grid 列被拉宽）
        tag_frame = ttk.Frame(search_frame)
        tag_frame.grid(row=1, column=4, columnspan=2, sticky=tk.W, padx=(5,0), pady=5)
        ttk.Label(tag_frame, text="标签:").pack(side=tk.LEFT)
        self.tag_dropdown = CheckboxDropdown(
            tag_frame, [], default_text="全部标签",
            callback=self._on_tag_filter_change, width=15
        )
        self.tag_dropdown.pack(side=tk.LEFT, padx=(5,0))
        
        # 收藏筛选
        self.favorite_filter_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            search_frame, text="❤ 只看收藏",
            variable=self.favorite_filter_var,
            command=self._on_favorite_filter_change
        ).grid(row=1, column=6, sticky=tk.W, padx=5, pady=5)
        
        # 第三行：排序选项
        ttk.Label(search_frame, text="排序:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 排序模式选择
        self.sort_mode_var = tk.StringVar(value="time")
        sort_modes = [
            ("按时间", "time"),
            ("颜色聚类", "color")
        ]
        sort_frame = ttk.Frame(search_frame)
        sort_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        for text, value in sort_modes:
            ttk.Radiobutton(
                sort_frame, text=text, value=value,
                variable=self.sort_mode_var,
                command=self._on_sort_mode_change
            ).pack(side=tk.LEFT, padx=5)
        
        # 排序说明
        self.sort_info_label = ttk.Label(search_frame, text="(右键图片可选择'以此为参考排序')", foreground="gray")
        self.sort_info_label.grid(row=2, column=4, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # 相似度排序的参考图片
        self.similarity_reference = None
        
        # 以图搜图权重配置（默认值）
        self.dl_weight = 0.8  # 深度学习特征权重
        self.phash_weight = 0.2  # PHash权重
        self._load_similarity_weights()  # 从配置文件加载
        
        self._load_sources()
        self._load_tags()
    
    def _create_result_frame(self):
        """创建结果显示框架"""
        result_frame = ttk.LabelFrame(self.frame, text="搜索结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # PanedWindow分割左右
        self.paned_window = ttk.PanedWindow(result_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图片列表
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)
        
        vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(left_frame, yscrollcommand=vsb.set, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动
        def on_yview_scroll(*args):
            self.canvas.yview(*args)
            if self._scroll_after_id:
                try:
                    self.frame.after_cancel(self._scroll_after_id)
                except:
                    pass
            self._scroll_after_id = self.frame.after(30, self._render_visible_items)
        vsb.configure(command=on_yview_scroll)
        
        # 右侧：详情面板
        detail_frame = ttk.Frame(self.paned_window, width=350)
        self.paned_window.add(detail_frame, weight=1)
        
        # 初始化渲染器
        self.thumb_size_var = tk.IntVar(value=120)
        self.renderer = CanvasRenderer(self.canvas, self.thumb_size_var, thumb_padding=20)
        
        # 初始化详情面板
        self.detail_panel = DetailPanel(
            detail_frame, self.db, self.favorite_cache,
            on_favorite_toggle=self._on_detail_favorite_toggle,
            on_ocr_save=self._on_ocr_save,
            on_emotion_save=self._on_emotion_save,
            open_folder_callback=self._open_folder
        )
        
        # 初始化事件处理器
        self.event_handler = EventHandlers(
            self.frame, self.canvas, self.renderer,
            get_all_results_func=lambda: self.all_results,
            get_selected_items_func=lambda: self.selected_items,
            set_last_clicked_func=lambda idx: setattr(self, 'last_clicked_index', idx),
            toggle_selection_func=self._toggle_selection,
            toggle_favorite_func=self._toggle_favorite,
            show_detail_func=self._show_image_detail
        )
        
        # 初始化上下文菜单
        self.context_menu = ContextMenu(
            self.frame,
            self.db,
            get_selected_items_func=lambda: self.selected_items,
            get_favorite_cache_func=lambda: self.favorite_cache,
            refresh_callback=self.refresh_page,
            sort_by_similarity_callback=self._sort_by_similarity_reference
        )
        
        # 将上下文菜单附加到事件处理器
        self.event_handler.context_menu = self.context_menu
        
        # 绑定事件
        self.canvas.bind('<MouseWheel>', self.event_handler.on_mousewheel)
        self.canvas.bind('<Button-4>', self.event_handler.on_mousewheel)
        self.canvas.bind('<Button-5>', self.event_handler.on_mousewheel)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<Button-3>', self.event_handler.on_right_click)
        self.canvas.bind('<Double-Button-1>', self.event_handler.on_double_click)
        self.canvas.bind('<Button-1>', self.event_handler.on_single_click)
        self.canvas.bind('<Motion>', self.event_handler.on_mouse_motion)
        self.canvas.bind('<Leave>', self.event_handler.on_mouse_leave)
        
        # 让事件处理器能够访问last_clicked_index
        self.event_handler.get_last_clicked_index = lambda: self.last_clicked_index
        # 让事件处理器能够触发渲染
        self.event_handler._render_visible = self._render_visible_items
    
    def _create_pager_frame(self):
        """创建分页控件"""
        pager_frame = ttk.Frame(self.frame)
        pager_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 每页条数
        self.page_size_var = tk.IntVar(value=20)
        ttk.Label(pager_frame, text="每页:").pack(side=tk.LEFT)
        page_size_cb = ttk.Combobox(
            pager_frame, textvariable=self.page_size_var,
            values=[10, 20, 50, 100], width=5, state='readonly'
        )
        page_size_cb.pack(side=tk.LEFT, padx=5)
        page_size_cb.bind('<<ComboboxSelected>>', lambda e: self.load_page())
        
        # 缩略图大小
        ttk.Label(pager_frame, text=" 缩略图:").pack(side=tk.LEFT)
        thumb_scale = ttk.Scale(
            pager_frame, from_=60, to=240, orient=tk.HORIZONTAL,
            command=lambda v: self._on_thumb_change(v)
        )
        thumb_scale.set(self.thumb_size_var.get())
        thumb_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(pager_frame, textvariable=self.thumb_size_var).pack(side=tk.LEFT)
        
        # 分页按钮
        self.page_var = tk.IntVar(value=1)
        self.total_pages = 1
        
        ttk.Button(pager_frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="下一页", command=self.next_page).pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(pager_frame, text="第 1 / 1 页")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 跳转
        ttk.Label(pager_frame, text=" 跳转到页:").pack(side=tk.LEFT)
        self.goto_var = tk.IntVar(value=1)
        self.goto_entry = ttk.Entry(pager_frame, width=6, textvariable=self.goto_var)
        self.goto_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(pager_frame, text="跳转", command=self.goto_page).pack(side=tk.LEFT)
    
    # ==================== 筛选和加载 ====================
    
    def _load_sources(self):
        """加载图源列表"""
        sources = self.db.get_sources()
        options = []
        for source in sources:
            folder_path = source['folder_path']
            folder_name = folder_path.split('\\')[-1] or folder_path.split('/')[-1] or folder_path
            display_text = f"[{source['id']}] {folder_name}"
            options.append((display_text, source['id']))
        
        self.source_dropdown.options = options
        self.source_dropdown.vars = {}
        for label, value in options:
            self.source_dropdown.vars[value] = tk.BooleanVar(value=False)
        self.source_dropdown._update_button_text()
    
    def _load_tags(self):
        """加载标签列表"""
        tags = self.db.get_all_tags()
        options = []
        for tag in tags:
            display_text = f"{tag['name']}"
            options.append((display_text, tag['id']))
        
        self.tag_dropdown.options = options
        self.tag_dropdown.vars = {}
        for label, value in options:
            self.tag_dropdown.vars[value] = tk.BooleanVar(value=False)
        self.tag_dropdown._update_button_text()
    
    def _on_emotion_filter_change(self):
        """情感筛选变化"""
        self.selected_emotions = self.emotion_dropdown.get_selected_values()
        self.search_images()
    
    def _on_source_filter_change(self):
        """图源筛选变化"""
        self.selected_sources = self.source_dropdown.get_selected_values()
        self.search_images()
    
    def _on_tag_filter_change(self):
        """标签筛选变化"""
        self.selected_tags = self.tag_dropdown.get_selected_values()
        self.search_images()
    
    def _on_favorite_filter_change(self):
        """收藏筛选变化"""
        self.search_images()
    
    def set_source_filter(self, source_ids):
        """从外部设置图源筛选"""
        if not isinstance(source_ids, list):
            source_ids = [source_ids]
        
        self.selected_sources = source_ids
        self.source_dropdown.set_selected_values(source_ids)
        self.search_images()
    
    def search_images(self):
        """搜索图片"""
        self.page_var.set(1)
        self.load_page()
    
    def refresh_page(self):
        """刷新页面"""
        self._load_sources()
        self._load_tags()
        # 清除排序提示，重置为默认状态
        self.similarity_reference = None
        self.sort_info_label.config(
            text="(右键图片可选择'以此为参考排序')",
            foreground="gray"
        )
        self.load_page()
        # 刷新详情面板（如果正在显示某张图片）
        self.detail_panel.refresh()
    
    def load_page(self):
        """加载当前页"""
        if self._reload_after_id is not None:
            try:
                self.frame.after_cancel(self._reload_after_id)
            except:
                pass
            self._reload_after_id = None
        
        # 清除排序参考和提示
        self.similarity_reference = None
        self.sort_info_label.config(text="", foreground="black")
        
        page = max(1, int(self.page_var.get()))
        page_size = int(self.page_size_var.get())
        keyword = self.search_keyword.get().strip()
        
        emotions = self.selected_emotions if self.selected_emotions else None
        source_ids = self.selected_sources if self.selected_sources else None
        tag_ids = self.selected_tags if self.selected_tags else None
        is_favorite = True if self.favorite_filter_var.get() else None
        
        # 清空渲染器
        self.renderer.clear_all()
        
        # 延迟GC
        self.frame.after(100, gc.collect)
        
        # 计算总页数
        total = self.db.get_images_count(
            processed=1, keyword=keyword, emotions=emotions,
            source_ids=source_ids, tag_ids=tag_ids, is_favorite=is_favorite
        )
        self.total_pages = max(1, (total + page_size - 1) // page_size)
        if page > self.total_pages:
            page = self.total_pages
            self.page_var.set(page)
        
        # 获取数据
        self.all_results = self.db.get_images_page(
            page=page, page_size=page_size, processed=1,
            keyword=keyword, emotions=emotions, source_ids=source_ids,
            tag_ids=tag_ids, is_favorite=is_favorite
        )
        
        # 保存原始结果
        self.original_results = self.all_results.copy()
        
        # 应用排序
        self._apply_sort()
        
        # 重新加载favorite_cache，确保收藏状态是最新的
        self.favorite_cache = {}
        for result in self.all_results:
            file_path = result['file_path']
            is_fav = result.get('is_favorite', False)
            self.favorite_cache[file_path] = bool(is_fav)
        
        # 计算布局
        try:
            canvas_width = max(400, self.canvas.winfo_width())
            self.renderer.calculate_layout(canvas_width)
        except:
            pass
        
        # 设置滚动区域
        if self.all_results:
            total_rows = (len(self.all_results) + self.renderer.cols - 1) // self.renderer.cols
            self.renderer.set_scrollregion(total_rows)
        
        self.update_pager()
        self._render_visible_items()
        self.canvas.update_idletasks()
    
    def _render_visible_items(self):
        """渲染可见项"""
        self.renderer.render_visible_items(
            self.all_results, self.selected_items, self.favorite_cache
        )
    
    # ==================== 分页控制 ====================
    
    def prev_page(self):
        """上一页"""
        p = max(1, self.page_var.get() - 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page()
    
    def next_page(self):
        """下一页"""
        p = min(self.total_pages, self.page_var.get() + 1)
        if p != self.page_var.get():
            self.page_var.set(p)
            self.load_page()
    
    def goto_page(self):
        """跳转到指定页"""
        try:
            p = int(self.goto_var.get())
        except:
            p = 1
        p = max(1, min(self.total_pages, p))
        self.page_var.set(p)
        self.load_page()
    
    def update_pager(self):
        """更新分页显示"""
        self.page_label.config(text=f"第 {self.page_var.get()} / {self.total_pages} 页")
    
    def _on_thumb_change(self, value):
        """缩略图大小改变"""
        try:
            v = int(float(value))
            self.thumb_size_var.set(v)
        except:
            pass
        self._schedule_reload(250)
    
    def _schedule_reload(self, delay: int = 200):
        """延迟重新加载"""
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
        """执行重新加载"""
        self._reload_after_id = None
        try:
            self.load_page()
        except:
            pass
    
    def _on_canvas_configure(self, event=None):
        """Canvas大小变化"""
        if self._configure_after_id:
            try:
                self.frame.after_cancel(self._configure_after_id)
            except:
                pass
        self._configure_after_id = self.frame.after(100, self._handle_canvas_resize)
    
    def _handle_canvas_resize(self):
        """处理Canvas大小变化"""
        self._configure_after_id = None
        
        if not self.all_results:
            return
        
        try:
            canvas_width = max(400, self.canvas.winfo_width())
            old_cols = self.renderer.cols
            self.renderer.calculate_layout(canvas_width)
            
            if self.renderer.cols != old_cols:
                total_rows = (len(self.all_results) + self.renderer.cols - 1) // self.renderer.cols
                self.renderer.set_scrollregion(total_rows)
                self.renderer.clear_all()
                self._render_visible_items()
            else:
                self._render_visible_items()
        except:
            pass
    
    # ==================== 选中和收藏 ====================
    
    def _toggle_selection(self, key):
        """切换选中状态"""
        if key not in self.renderer.item_paths:
            return
        
        file_path = self.renderer.item_paths[key]
        if file_path in self.selected_items:
            self.selected_items.remove(file_path)
        else:
            self.selected_items.add(file_path)
        
        self.renderer.update_checkbox_display(key, file_path in self.selected_items)
    
    def _toggle_favorite(self, key):
        """切换收藏状态"""
        if key not in self.renderer.item_paths:
            return
        
        file_path = self.renderer.item_paths[key]
        current_state = self.favorite_cache.get(file_path, False)
        new_state = not current_state
        
        if self.db.update_favorite(file_path, new_state):
            self.favorite_cache[file_path] = new_state
            self.renderer.update_favorite_display(key, new_state)
    
    def _on_detail_favorite_toggle(self, file_path, new_state):
        """详情面板收藏状态变化"""
        # 更新列表中的显示
        for key, path in self.renderer.item_paths.items():
            if path == file_path:
                self.renderer.update_favorite_display(key, new_state)
                break
    
    # ==================== 详情面板 ====================
    
    def _show_image_detail(self, file_path):
        """显示图片详情"""
        self.detail_panel.show_image_detail(file_path)
    
    def _on_ocr_save(self, file_path, new_text):
        """保存OCR修改"""
        success = self.db.update_image_ocr(file_path, new_text)
        if success:
            messagebox.showinfo("成功", "OCR文本已保存")
            self.load_page()
        else:
            messagebox.showerror("错误", "保存OCR文本失败")
    
    def _on_emotion_save(self, file_path, new_emotion):
        """保存情绪修改"""
        success = self.db.update_emotion(file_path, new_emotion, manual=True)
        if success:
            messagebox.showinfo("成功", "情绪标签已保存")
            self.detail_panel.show_image_detail(file_path)
            self.load_page()
        else:
            messagebox.showerror("错误", "保存情绪标签失败")
    
    def _open_folder(self, file_path):
        """打开文件夹"""
        self.event_handler.open_folder(file_path)
    
    def _open_tag_manager(self):
        """打开标签管理对话框"""
        from ..tag_manager_dialog import TagManagerDialog
        
        TagManagerDialog(
            self.parent.winfo_toplevel(),
            self.db,
            callback=None
        )
    
    # ==================== 排序相关 ====================
    
    def _on_sort_mode_change(self):
        """排序模式变化"""
        mode = self.sort_mode_var.get()
        
        if mode == "time":
            self.sort_info_label.config(text="(右键图片可选择'以此为参考排序')", foreground="gray")
        elif mode == "color":
            self.sort_info_label.config(text="(将颜色相近的图片聚集在一起)", foreground="blue")
        
        # 应用排序
        self._apply_sort()
    
    def _apply_sort(self):
        """应用当前排序模式"""
        if not self.all_results:
            return
        
        mode = self.sort_mode_var.get()
        
        if mode == "color":
            # 按颜色聚类排序
            self.all_results = ImageSorter.sort_by_color(self.all_results)
        # time模式不需要重新排序，数据库已经按时间排序
        # similarity模式通过右键菜单触发
        
        # 重新渲染
        self.renderer.clear_all()
        self._render_visible_items()
    
    def _sort_by_similarity_reference(self, reference_path: str):
        """以指定图片为参考进行相似度排序（支持DL特征 + PHash）
        
        优先使用数据库中已有的特征，如果不存在则重新计算
        
        Args:
            reference_path: 参考图片的文件路径
        """
        if not self.all_results:
            return
        
        try:
            from pathlib import Path
            from ...core.image_hash import calculate_image_hashes, calculate_dl_features
            
            image_path = Path(reference_path)
            if not image_path.exists():
                messagebox.showerror("错误", "参考图片不存在")
                return
            
            # 先尝试从all_results中找到该图片的数据（优先使用数据库特征）
            reference_image = None
            for img in self.all_results:
                if img.get('file_path') == reference_path:
                    reference_image = img.copy()  # 复制一份
                    break
            
            # 如果数据库中有特征，直接使用
            if reference_image and reference_image.get('phash'):
                logger.info("使用数据库中的特征进行相似度排序")
                dl_features = reference_image.get('dl_features')
            else:
                # 否则重新计算特征
                logger.info("数据库中无特征，重新计算...")
                phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v = calculate_image_hashes(image_path)
                
                # 尝试计算深度学习特征
                dl_features = None
                try:
                    dl_features = calculate_dl_features(image_path)
                    if dl_features:
                        logger.info("✓ 成功提取深度学习特征用于相似度排序")
                except Exception as e:
                    logger.debug(f"深度学习特征提取失败（使用PHash备用方案）: {e}")
                
                # 构建参考图片对象
                reference_image = {
                    'file_path': str(image_path),
                    'phash': phash,
                    'color_hue_idx': hue_idx,
                    'color_lightness': lightness,
                    'hsv_h': hsv_h,
                    'hsv_s': hsv_s,
                    'hsv_v': hsv_v,
                    'dl_features': dl_features
                }
            
            # 保存参考图片
            self.similarity_reference = reference_image
            
            # 选择排序方法
            dl_features = reference_image.get('dl_features')
            phash = reference_image.get('phash')
            
            # 优先使用混合方法，只要有DL特征且权重不为0，或有PHash且权重不为0
            if dl_features and (self.dl_weight > 0 or (phash and self.phash_weight > 0)):
                # 使用混合相似度排序（使用配置的权重）
                self.all_results = ImageSorter.sort_by_hybrid_similarity(
                    self.all_results, reference_image,
                    dl_weight=self.dl_weight, phash_weight=self.phash_weight
                )
                sort_method = f"混合相似度 [深度学习:{int(self.dl_weight*100)}% + PHash:{int(self.phash_weight*100)}%]"
            elif dl_features:
                # 只有深度学习特征
                self.all_results = ImageSorter.sort_by_dl_similarity(
                    self.all_results, reference_image
                )
                sort_method = "深度学习特征相似度"
            elif phash:
                # 只有PHash特征
                self.all_results = ImageSorter.sort_by_similarity(
                    self.all_results, reference_image
                )
                sort_method = "PHash相似度"
            else:
                # 无特征可用
                messagebox.showwarning("警告", "参考图片缺少特征数据，无法排序")
                return
            
            # 更新排序说明
            ref_name = image_path.name
            self.sort_info_label.config(
                text=f"（已按与 {ref_name} 的相似度排序）",
                foreground="green"
            )
            
            # 重新渲染
            self.renderer.clear_all()
            self._render_visible_items()
            
            messagebox.showinfo("成功", f"已按与 {ref_name} 的相似度排序\n使用：{sort_method}")
            
        except Exception as e:
            logger.error(f"相似度排序失败: {e}")
            messagebox.showerror("错误", f"相似度排序失败：{e}")
    
    def _search_by_image(self):
        """以图搜图（支持文件选择和剪贴板）"""
        from tkinter import filedialog
        from PIL import ImageGrab
        import tempfile
        
        # 创建选择对话框（加入设置按钮）
        choice_dialog = tk.Toplevel(self.frame)
        choice_dialog.title("以图搜图")
        choice_dialog.geometry("350x220")
        choice_dialog.transient(self.frame)
        choice_dialog.grab_set()
        
        # 居中显示
        choice_dialog.update_idletasks()
        x = (choice_dialog.winfo_screenwidth() // 2) - (choice_dialog.winfo_width() // 2)
        y = (choice_dialog.winfo_screenheight() // 2) - (choice_dialog.winfo_height() // 2)
        choice_dialog.geometry(f"+{x}+{y}")
        
        selected_path = [None]  # 使用列表以便在内部函数中修改
        
        def select_from_file():
            """从文件选择"""
            file_path = filedialog.askopenfilename(
                title="选择图片",
                filetypes=[
                    ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                    ("所有文件", "*.*")
                ]
            )
            if file_path:
                selected_path[0] = file_path
                choice_dialog.destroy()
        
        def select_from_clipboard():
            """从剪贴板获取"""
            try:
                img = ImageGrab.grabclipboard()
                if img is None:
                    messagebox.showwarning("提示", "剪贴板中没有图片")
                    return
                
                # 保存到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                img.save(temp_file.name)
                temp_file.close()
                
                selected_path[0] = temp_file.name
                choice_dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"从剪贴板获取图片失败：{e}")
        
        def open_settings():
            """打开设置"""
            from .similarity_settings_dialog import SimilaritySettingsDialog
            
            dialog = SimilaritySettingsDialog(
                choice_dialog,
                current_dl_weight=self.dl_weight,
                current_phash_weight=self.phash_weight
            )
            
            result = dialog.wait_window()
            
            if result:
                self.dl_weight, self.phash_weight = result
                # 保存权重设置
                self._save_similarity_weights()
                # 更新按钮文本显示当前权重
                settings_text = f"⚙️ 权重设置 (DL:{int(self.dl_weight*100)}% PHash:{int(self.phash_weight*100)}%)"
                settings_btn.config(text=settings_text)
        
        # 标题
        ttk.Label(choice_dialog, text="请选择图片来源：", font=('TkDefaultFont', 11, 'bold')).pack(pady=15)
        
        # 按钮框架
        btn_frame = ttk.Frame(choice_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📁 从文件选择", command=select_from_file, width=18).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📋 从剪贴板", command=select_from_clipboard, width=18).pack(side=tk.LEFT, padx=10)
        
        # 设置按钮
        settings_text = f"⚙️ 权重设置 (DL:{int(self.dl_weight*100)}% PHash:{int(self.phash_weight*100)}%)"
        settings_btn = ttk.Button(choice_dialog, text=settings_text, command=open_settings, width=40)
        settings_btn.pack(pady=15)
        
        # 取消按钮
        ttk.Button(choice_dialog, text="取消", command=choice_dialog.destroy, width=15).pack(pady=10)
        
        # 等待对话框关闭
        self.frame.wait_window(choice_dialog)
        
        if not selected_path[0]:
            return
        
        # 计算选中图片的特征
        try:
            from pathlib import Path
            from ...core.image_hash import calculate_image_hashes
            from ...core.database.image_sorter import ImageSorter
            
            image_path = Path(selected_path[0])
            if not image_path.exists():
                messagebox.showerror("错误", "图片文件不存在")
                return
            
            # 计算特征
            messagebox.showinfo("提示", "正在计算图片特征，请稍候...")
            phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v = calculate_image_hashes(image_path)
            
            # 尝试计算深度学习特征
            dl_features = None
            try:
                from ...core.image_hash import calculate_dl_features
                dl_features = calculate_dl_features(image_path)
                if dl_features:
                    logger.info("✓ 成功提取深度学习特征用于以图搜图")
            except:
                pass
            
            # 构建参考图片对象
            reference_image = {
                'file_path': str(image_path),
                'phash': phash,
                'color_hue_idx': hue_idx,
                'color_lightness': lightness,
                'hsv_h': hsv_h,
                'hsv_s': hsv_s,
                'hsv_v': hsv_v,
                'dl_features': dl_features
            }
            
            if not self.all_results:
                messagebox.showwarning("提示", "当前没有搜索结果")
                return
            
            # 选择排序方法
            # 优先使用混合方法，只要有DL特征且权重不为0，或有PHash且权重不为0
            if dl_features and (self.dl_weight > 0 or (phash and self.phash_weight > 0)):
                # 使用混合相似度排序（使用配置的权重）
                print(f"[DEBUG] 排序前总数: {len(self.all_results)}")
                print(f"[DEBUG] 权重: DL={self.dl_weight}, PHash={self.phash_weight}")
                print(f"[DEBUG] 参考图片特征: dl_features={dl_features is not None}, phash={phash}")
                
                self.all_results = ImageSorter.sort_by_hybrid_similarity(
                    self.all_results, reference_image,
                    dl_weight=self.dl_weight, phash_weight=self.phash_weight
                )
                
                print(f"[DEBUG] 排序后总数: {len(self.all_results)}")
                sort_method = f"混合相似度 [深度学习:{int(self.dl_weight*100)}% + PHash:{int(self.phash_weight*100)}%]"
            elif dl_features:
                # 只有深度学习特征
                self.all_results = ImageSorter.sort_by_dl_similarity(
                    self.all_results, reference_image
                )
                sort_method = "深度学习特征相似度"
            elif phash:
                # 只有PHash特征
                self.all_results = ImageSorter.sort_by_similarity(
                    self.all_results, reference_image
                )
                sort_method = "PHash相似度"
            else:
                messagebox.showwarning("警告", "参考图片缺少特征数据，无法排序")
                return
            
            # 调试：打印排序后的前5个结果
            print("\n[DEBUG] 排序后的前5个结果:")
            from pathlib import Path
            for i, item in enumerate(self.all_results[:5]):
                score = item.get('similarity_score', 0)
                name = Path(item.get('file_path', 'unknown')).name
                print(f"  {i+1}. {name} -> 相似度: {score:.4f}")
            
            # 保存参考图片
            self.similarity_reference = reference_image
            
            # 更新排序说明
            img_name = image_path.name
            self.sort_info_label.config(
                text=f"(已按与 {img_name} 的相似度排序)",
                foreground="blue"
            )
            
            # 重新渲染（修复排序不生效的bug）
            self.renderer.clear_all()
            self._render_visible_items()
            
            # 强制更新画布
            self.renderer.canvas.update_idletasks()
            
            messagebox.showinfo("成功", f"已按与 {img_name} 的相似度排序\n使用：{sort_method}")
            
        except Exception as e:
            logger.error(f"以图搜图失败: {e}")
            messagebox.showerror("错误", f"以图搜图失败：{e}")
    
    def _open_similarity_settings(self):
        """打开以图搜图权重设置对话框"""
        from .similarity_settings_dialog import SimilaritySettingsDialog
        
        dialog = SimilaritySettingsDialog(
            self.frame.winfo_toplevel(),
            current_dl_weight=self.dl_weight,
            current_phash_weight=self.phash_weight
        )
        
        result = dialog.wait_window()
        
        if result:
            self.dl_weight, self.phash_weight = result
            messagebox.showinfo(
                "设置已保存",
                f"以图搜图权重已更新：\n"
                f"深度学习: {int(self.dl_weight*100)}%\n"
                f"PHash: {int(self.phash_weight*100)}%"
            )
            # 保存权重设置
            self._save_similarity_weights()
    
    def _load_similarity_weights(self):
        """从配置文件加载以图搜图权重"""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent.parent / 'version_config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.dl_weight = config.get('dl_weight', 0.8)
                    self.phash_weight = config.get('phash_weight', 0.2)
                    logger.debug(f"已加载权重设置: DL={self.dl_weight}, PHash={self.phash_weight}")
        except Exception as e:
            logger.warning(f"加载权重设置失败，使用默认值: {e}")
    
    def _save_similarity_weights(self):
        """保存以图搜图权重到配置文件"""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent.parent / 'version_config.json'
            
            # 读取现有配置
            config = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新权重
            config['dl_weight'] = self.dl_weight
            config['phash_weight'] = self.phash_weight
            
            # 保存
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"权重设置已保存: DL={self.dl_weight}, PHash={self.phash_weight}")
        except Exception as e:
            logger.error(f"保存权重设置失败: {e}")




