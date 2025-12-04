#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件处理器模块
"""

import os
import sys
import shutil
import subprocess
from tkinter import messagebox, Menu


class EventHandlers:
    """事件处理器 - 处理用户交互事件"""
    
    def __init__(self, parent, canvas, renderer, get_all_results_func, 
                 get_selected_items_func, set_last_clicked_func, 
                 toggle_selection_func, toggle_favorite_func, show_detail_func):
        """
        Args:
            parent: 父控件
            canvas: Canvas控件
            renderer: CanvasRenderer实例
            get_all_results_func: 获取所有结果的函数
            get_selected_items_func: 获取选中项的函数
            set_last_clicked_func: 设置最后点击索引的函数
            toggle_selection_func: 切换选中状态的函数
            toggle_favorite_func: 切换收藏状态的函数
            show_detail_func: 显示详情的函数
        """
        self.parent = parent
        self.canvas = canvas
        self.renderer = renderer
        self.get_all_results = get_all_results_func
        self.get_selected_items = get_selected_items_func
        self.set_last_clicked = set_last_clicked_func
        self.toggle_selection = toggle_selection_func
        self.toggle_favorite = toggle_favorite_func
        self.show_detail = show_detail_func
        
        self._hover_item = None
        self._scroll_after_id = None
    
    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
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
        
        # 延迟渲染
        if self._scroll_after_id:
            try:
                self.parent.after_cancel(self._scroll_after_id)
            except:
                pass
        self._scroll_after_id = self.parent.after(30, self._render_visible)
    
    def _render_visible(self):
        """延迟渲染可见项"""
        self._scroll_after_id = None
        # 这个方法需要主类提供
        pass
    
    def on_mouse_motion(self, event):
        """鼠标移动 - 悬停高亮"""
        key = self.renderer.get_item_at_pos(event.x, event.y)
        
        if key != self._hover_item:
            # 恢复旧的
            if self._hover_item:
                self.renderer.update_hover_highlight(self._hover_item, False)
            
            # 高亮新的
            if key:
                self.renderer.update_hover_highlight(key, True)
            
            self._hover_item = key
        
        # 更新鼠标指针
        if key:
            if self.renderer.is_click_on_checkbox(key, event.x, event.y):
                self.canvas.config(cursor='hand2')
            elif self.renderer.is_click_on_favorite(key, event.x, event.y):
                self.canvas.config(cursor='hand2')
            else:
                self.canvas.config(cursor='')
        else:
            self.canvas.config(cursor='')
    
    def on_mouse_leave(self, event):
        """鼠标离开Canvas"""
        if self._hover_item:
            self.renderer.update_hover_highlight(self._hover_item, False)
        self._hover_item = None
    
    def on_single_click(self, event):
        """单击处理 - 支持多选、收藏、详情显示"""
        key = self.renderer.get_item_at_pos(event.x, event.y)
        if not key or key not in self.renderer.item_paths:
            return
        
        # 获取索引
        try:
            idx = int(key.split('_')[-1])
        except:
            idx = None
        
        # 检查是否点击爱心（优先级最高）
        if self.renderer.is_click_on_favorite(key, event.x, event.y):
            self.toggle_favorite(key)
            return
        
        # 检查是否点击复选框
        is_on_checkbox = self.renderer.is_click_on_checkbox(key, event.x, event.y)
        
        # Shift+点击：范围选择
        if event.state & 0x0001:  # Shift键
            self._handle_shift_click(key, idx)
            return
        
        # Ctrl+点击：切换选中状态
        if event.state & 0x0004:  # Ctrl键
            self.toggle_selection(key)
            self.set_last_clicked(idx)
            return
        
        # 普通点击复选框
        if is_on_checkbox:
            self.toggle_selection(key)
            self.set_last_clicked(idx)
            return
        
        # 普通点击图片：显示详情
        file_path = self.renderer.item_paths[key]
        self.show_detail(file_path)
        self.set_last_clicked(idx)
    
    def _handle_shift_click(self, key, idx):
        """处理Shift+点击范围选择"""
        last_idx = self.get_last_clicked_index()
        if last_idx is not None and idx is not None:
            all_results = self.get_all_results()
            start = min(last_idx, idx)
            end = max(last_idx, idx)
            
            range_items = []
            for i in range(start, end + 1):
                if i < len(all_results):
                    r = i // self.renderer.cols
                    c = i % self.renderer.cols
                    item_key = f"{r}_{c}_{i}"
                    file_path = all_results[i].get('file_path')
                    if file_path:
                        range_items.append((item_key, file_path))
            
            # 检查是否全部已选中
            selected_items = self.get_selected_items()
            all_selected = all(fp in selected_items for _, fp in range_items)
            
            # 切换选中状态
            for item_key, file_path in range_items:
                if all_selected:
                    selected_items.discard(file_path)
                else:
                    selected_items.add(file_path)
                self.renderer.update_checkbox_display(item_key, file_path in selected_items)
        else:
            self.set_last_clicked(idx)
    
    def get_last_clicked_index(self):
        """获取最后点击的索引 - 需要主类实现"""
        return None
    
    def on_double_click(self, event):
        """双击打开图片"""
        key = self.renderer.get_item_at_pos(event.x, event.y)
        if key and key in self.renderer.item_paths:
            self.open_file(self.renderer.item_paths[key])
    
    def on_right_click(self, event):
        """右键菜单"""
        # 优先使用新的上下文菜单（支持多选）
        if hasattr(self, 'context_menu') and self.context_menu:
            key = self.renderer.get_item_at_pos(event.x, event.y)
            clicked_path = self.renderer.item_paths.get(key) if key else None
            self.context_menu.show(event, clicked_path)
            return
        
        # 旧的单个图片右键菜单（后备）
        key = self.renderer.get_item_at_pos(event.x, event.y)
        if key and key in self.renderer.item_paths:
            file_path = self.renderer.item_paths[key]
            self.show_context_menu(event, file_path)
    
    def show_context_menu(self, event, file_path):
        """显示右键菜单"""
        menu = Menu(self.canvas, tearoff=0)
        menu.add_command(label="📂 打开图片", command=lambda: self.open_file(file_path))
        menu.add_command(label="📁 打开所在文件夹", command=lambda: self.open_folder(file_path))
        menu.add_separator()
        menu.add_command(label="📋 复制路径", command=lambda: self.copy_path(file_path))
        menu.add_command(label="🗑️ 删除图片", command=lambda: self.delete_image(file_path))
        
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
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', file_path], check=False)
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
            if sys.platform.startswith('win'):
                subprocess.run(['explorer', '/select,', file_path])
            elif sys.platform == 'darwin':
                subprocess.run(['open', '-R', file_path])
            else:
                subprocess.run(['xdg-open', folder])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    def copy_path(self, file_path):
        """复制路径到剪贴板"""
        self.parent.clipboard_clear()
        self.parent.clipboard_append(file_path)
        messagebox.showinfo("提示", "路径已复制到剪贴板")
    
    def delete_image(self, file_path, refresh_callback):
        """删除图片"""
        if messagebox.askyesno("确认删除", f"确定要删除这张图片吗？\n{file_path}"):
            try:
                os.remove(file_path)
                refresh_callback()
                messagebox.showinfo("成功", "图片已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
