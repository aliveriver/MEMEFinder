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
from .detail_panel import DetailPanel
from .canvas_renderer import CanvasRenderer
from .event_handlers import EventHandlers
from .context_menu import ContextMenu
from .similarity_search import SimilaritySearch
from .icon_manager import IconManager
from .pagination_control import PaginationControl
from .search_toolbar import SearchToolbar

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
        
        # 延迟调度ID
        self._reload_after_id = None
        self._scroll_after_id = None
        self._configure_after_id = None
        
        # 加载图标
        self.icon_manager = IconManager()
        self.icons = self.icon_manager.icons # 兼容旧代码访问
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 1. 初始化分页控件（但不显示，为了让ResultFrame能访问thumb_size_var）
        self.pager = PaginationControl(
            self.frame,
            load_page_callback=self.load_page,
            thumb_size_callback=self._on_thumb_change
        )

        # 2. 搜索工具栏
        self.toolbar = SearchToolbar(
            self.frame, 
            self.db, 
            self.icon_manager,
            callbacks={
                'search': self.search_images,
                'refresh': self.refresh_page,
                'image_search': self._on_search_by_image,
                'tag_manage': self._open_tag_manager,
                'sort_mode_change': self._on_sort_mode_change
            }
        )
        
        # 3. 结果显示区
        self._create_result_frame()
        
        # 4. 显示分页控件（放在底部）
        self.pager.pack()
        
        # 5. 初始化相似度搜索模块
        self.similarity_search = SimilaritySearch(
            parent_frame=self.frame,
            renderer=self.renderer,
            sort_info_label=self.toolbar.sort_info_label,
            db=self.db
        )
        
        # 初始加载
        self.load_page()
    
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
        self.renderer = CanvasRenderer(self.canvas, self.pager.thumb_size_var, thumb_padding=20)
        
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
            sort_by_similarity_callback=self._sort_by_similarity_reference,
            icons=self.icons
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
    
    # ==================== 筛选和加载 ====================
    
    def set_source_filter(self, source_ids):
        """从外部设置图源筛选（适配器方法）"""
        self.toolbar.filters.set_source_filter(source_ids)
    
    def search_images(self):
        """搜索图片"""
        self.pager.set_current_page(1)
        self.load_page()
    
    def refresh_page(self):
        """刷新页面"""
        # 退出相似度搜索模式（如果处于该模式）
        if hasattr(self, 'similarity_search') and self.similarity_search.is_similarity_mode:
            self.similarity_search.exit_similarity_mode()
            logger.info("刷新页面：退出相似度搜索模式，回到正常分页模式")
        
        # 使用filters模块重新加载
        self.toolbar.filters.reload_all()
        
        # 清除相似度排序参考
        self.similarity_reference = None
        if hasattr(self, 'similarity_search'):
            self.similarity_search.similarity_reference = None
        
        # 根据当前排序模式设置正确的排序说明文本
        self._update_sort_info_label()
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
        
        # 检查是否处于相似度搜索模式
        is_similarity = hasattr(self, 'similarity_search') and self.similarity_search.is_similarity_mode
        
        if not is_similarity:
            # 清除相似度排序参考（仅在非相似度模式下清除）
            self.similarity_reference = None
            # 根据当前排序模式设置正确的排序说明文本
            self._update_sort_info_label()
        
        page = self.pager.get_current_page()
        page_size = self.pager.get_page_size()
        keyword = self.toolbar.get_keyword()
        
        # 使用筛选器模块获取筛选参数
        filter_params = self.toolbar.filters.get_filter_params(self.toolbar.favorite_filter_var)
        emotions = filter_params['emotions']
        source_ids = filter_params['source_ids']
        tag_ids = filter_params['tag_ids']
        is_favorite = filter_params['is_favorite']
        
        # 清空渲染器
        self.renderer.clear_all()
        
        # 延迟GC
        self.frame.after(100, gc.collect)
        
        if is_similarity:
            # 相似度搜索模式：带过滤条件的相似度搜索
            filters = {
                'keyword': keyword,
                'emotions': emotions,
                'source_ids': source_ids,
                'tag_ids': tag_ids,
                'is_favorite': is_favorite
            }
            # 执行带过滤的相似度搜索
            self.all_results = self.similarity_search.search_with_filters(filters)
            
            # 在相似度模式下，我们不使用标准分页，而是显示所有结果
            # 更新分页控件显示为第1页/共1页
            self.pager.update_display(1, 1)
            
        else:
            # 正常模式：分页查询
            # 计算总页数
            total = self.db.get_images_count(
                processed=1, keyword=keyword, emotions=emotions,
                source_ids=source_ids, tag_ids=tag_ids, is_favorite=is_favorite
            )
            total_pages = max(1, (total + page_size - 1) // page_size)
            
            if page > total_pages:
                page = total_pages
                self.pager.set_current_page(page)
            
            # 更新分页控件
            self.pager.update_display(total_pages, page)
            
            # 获取数据
            self.all_results = self.db.get_images_page(
                page=page, page_size=page_size, processed=1,
                keyword=keyword, emotions=emotions, source_ids=source_ids,
                tag_ids=tag_ids, is_favorite=is_favorite
            )
            
            # 应用排序（仅在非相似度模式下应用常规排序）
            self._apply_sort()
        
        # 保存原始结果
        self.original_results = self.all_results.copy()
        
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
        
        self._render_visible_items()
        self.canvas.update_idletasks()
    
    def _render_visible_items(self):
        """渲染可见项"""
        self.renderer.render_visible_items(
            self.all_results, self.selected_items, self.favorite_cache
        )
    
    def _on_thumb_change(self, value):
        """缩略图大小改变"""
        try:
            v = int(float(value))
            self.pager.set_thumb_size(v)
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
        # 更新排序说明文本
        self._update_sort_info_label()
        
        # 应用排序
        self._apply_sort()
    
    def _update_sort_info_label(self):
        """根据当前排序模式更新排序说明文本"""
        mode = self.toolbar.sort_mode_var.get()
        
        if mode == "time":
            self.toolbar.update_sort_info("(右键图片可选择'以此为参考排序')", "gray")
        elif mode == "color":
            self.toolbar.update_sort_info("(将颜色相近的图片聚集在一起)", "blue")
    
    def _apply_sort(self):
        """应用当前排序模式"""
        if not self.all_results:
            return
        
        mode = self.toolbar.sort_mode_var.get()
        
        if mode == "color":
            # 按颜色聚类排序
            self.all_results = ImageSorter.sort_by_color(self.all_results)
        elif mode == "time":
            # 恢复原始的时间排序（从数据库获取的顺序）
            if hasattr(self, 'original_results') and self.original_results:
                self.all_results = self.original_results.copy()
        # similarity模式通过右键菜单触发
        
        # 重新渲染
        self.renderer.clear_all()
        self._render_visible_items()
    
    def _sort_by_similarity_reference(self, reference_path: str):
        """以指定图片为参考进行相似度排序（适配器方法）"""
        sorted_results = self.similarity_search.sort_by_similarity(
            self.all_results,
            reference_path
        )
        if sorted_results:
            self.all_results = sorted_results
            self.renderer.clear_all()
            self._render_visible_items()
    
    # ==================== 适配器方法（保持向后兼容）====================
    
    def _on_search_by_image(self):
        """以图搜图（适配器方法）"""
        def render_callback():
            self.renderer.clear_all()
            self._render_visible_items()
            
        self.similarity_search.search_by_image(
            all_results_getter=lambda: self.all_results,
            all_results_setter=lambda r: setattr(self, 'all_results', r),
            render_callback=render_callback
        )
