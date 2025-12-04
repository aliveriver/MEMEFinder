#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
右键菜单模块
处理多选图片的批量操作
"""

import os
import shutil
from pathlib import Path
from tkinter import Menu, messagebox, simpledialog
from typing import Set, Callable


class ContextMenu:
    """右键菜单处理器"""
    
    def __init__(self, parent, db, get_selected_items_func, 
                 get_favorite_cache_func, refresh_callback):
        """
        Args:
            parent: 父窗口
            db: 数据库实例
            get_selected_items_func: 获取选中项的函数
            get_favorite_cache_func: 获取收藏缓存的函数
            refresh_callback: 刷新页面的回调
        """
        self.parent = parent
        self.db = db
        self.get_selected_items = get_selected_items_func
        self.get_favorite_cache = get_favorite_cache_func
        self.refresh_callback = refresh_callback
        
        # 创建菜单
        self.menu = Menu(parent, tearoff=0)
    
    def show(self, event, clicked_item_path=None):
        """显示右键菜单
        
        Args:
            event: 事件对象
            clicked_item_path: 点击位置的图片路径（如果有）
        """
        selected_items = self.get_selected_items()
        
        # 如果点击的位置有图片但未选中，则选中它
        if clicked_item_path and clicked_item_path not in selected_items:
            selected_items = {clicked_item_path}
        
        # 如果没有选中项，不显示菜单
        if not selected_items:
            return
        
        # 重建菜单
        self.menu.delete(0, 'end')
        
        count = len(selected_items)
        self.menu.add_command(
            label=f"已选中 {count} 张图片",
            state='disabled'
        )
        self.menu.add_separator()
        
        # 收藏/取消收藏
        favorite_cache = self.get_favorite_cache() or {}
        need_favorite = any(not favorite_cache.get(path, False) for path in selected_items)
        need_unfavorite = any(favorite_cache.get(path, False) for path in selected_items)
        
        if need_favorite:
            self.menu.add_command(
                label="❤ 收藏",
                command=lambda: self._batch_favorite(selected_items)
            )
        
        if need_unfavorite:
            self.menu.add_command(
                label="💔 取消收藏",
                command=lambda: self._batch_unfavorite(selected_items)
            )
        
        # 编辑标签
        self.menu.add_command(
            label="🏷️ 编辑标签",
            command=lambda: self._batch_edit_tags(selected_items)
        )
        
        # 编辑情感
        self.menu.add_command(
            label="😊 编辑情感",
            command=lambda: self._batch_edit_emotion(selected_items)
        )
        
        # 转移到图源
        self.menu.add_command(
            label="📁 转移到图源",
            command=lambda: self._batch_move_to_source(selected_items)
        )
        
        self.menu.add_separator()
        
        # 删除
        self.menu.add_command(
            label="🗑️ 删除",
            command=lambda: self._batch_delete(selected_items)
        )
        
        # 显示菜单
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
    
    def _batch_favorite(self, items: Set[str]):
        """批量收藏"""
        favorite_cache = self.get_favorite_cache() or {}
        success_count = 0
        
        for file_path in items:
            # 只收藏未收藏的
            if not favorite_cache.get(file_path, False):
                if self.db.update_favorite(file_path, True):
                    favorite_cache[file_path] = True
                    success_count += 1
        
        if success_count > 0:
            messagebox.showinfo("成功", f"已收藏 {success_count} 张图片")
            self.refresh_callback()
        else:
            messagebox.showinfo("提示", "所选图片已全部收藏")
    
    def _batch_unfavorite(self, items: Set[str]):
        """批量取消收藏"""
        favorite_cache = self.get_favorite_cache() or {}
        success_count = 0
        
        for file_path in items:
            # 只取消收藏已收藏的
            if favorite_cache.get(file_path, False):
                if self.db.update_favorite(file_path, False):
                    favorite_cache[file_path] = False
                    success_count += 1
        
        if success_count > 0:
            messagebox.showinfo("成功", f"已取消收藏 {success_count} 张图片")
            self.refresh_callback()
        else:
            messagebox.showinfo("提示", "所选图片均未收藏")
    
    def _batch_edit_tags(self, items: Set[str]):
        """批量编辑标签"""
        from .batch_tag_editor import BatchTagEditor
        
        dialog = BatchTagEditor(
            self.parent.winfo_toplevel(),
            self.db,
            list(items),
            callback=self.refresh_callback
        )
        dialog.wait_window()
    
    def _batch_edit_emotion(self, items: Set[str]):
        """批量编辑情感"""
        from .batch_emotion_editor import BatchEmotionEditor
        
        dialog = BatchEmotionEditor(
            self.parent.winfo_toplevel(),
            self.db,
            list(items),
            callback=self.refresh_callback
        )
        dialog.wait_window()
    
    def _batch_move_to_source(self, items: Set[str]):
        """批量转移到图源"""
        from .batch_move_dialog import BatchMoveDialog
        
        dialog = BatchMoveDialog(
            self.parent.winfo_toplevel(),
            self.db,
            list(items),
            callback=self.refresh_callback
        )
        dialog.wait_window()
    
    def _batch_delete(self, items: Set[str]):
        """批量删除"""
        count = len(items)
        
        # 二次确认
        message = '确定要从磁盘删除这 {} 张图片吗？\n\n⚠️ 此操作不可恢复！图片将被永久删除。\n\n点击"确定"继续删除，点击"取消"放弃操作。'.format(count)
        
        result = messagebox.askokcancel(
            "确认删除",
            message,
            icon='warning'
        )
        
        if not result:
            return
        
        # 执行删除
        success_count = 0
        failed_count = 0
        failed_files = []
        
        for file_path in items:
            try:
                # 从磁盘删除
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 从数据库删除
                with self.db.get_cursor(commit=True) as cursor:
                    cursor.execute("DELETE FROM images WHERE file_path = ?", (file_path,))
                
                success_count += 1
            except Exception as e:
                failed_count += 1
                failed_files.append(f"{Path(file_path).name}: {str(e)}")
        
        # 显示结果
        if failed_count == 0:
            messagebox.showinfo("成功", f"已成功删除 {success_count} 张图片")
        else:
            msg = f"删除完成：\n成功: {success_count} 张\n失败: {failed_count} 张"
            if failed_files:
                msg += "\n\n失败的文件：\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    msg += f"\n... 还有 {len(failed_files) - 5} 个"
            messagebox.showwarning("部分失败", msg)
        
        # 刷新页面
        if success_count > 0:
            self.refresh_callback()
