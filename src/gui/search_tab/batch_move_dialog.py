#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量转移到图源对话框
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List


class BatchMoveDialog(tk.Toplevel):
    """批量转移到图源对话框"""
    
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
        
        self.title(f"批量转移图片 - {len(file_paths)} 张")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_sources()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 提示
        hint_label = ttk.Label(
            main_frame,
            text=f"将 {len(self.file_paths)} 张图片转移到：",
            font=('TkDefaultFont', 10, 'bold')
        )
        hint_label.pack(pady=(0, 10))
        
        # 说明
        info_text = (
            "⚠️ 转移操作将：\n"
            "1. 将图片文件移动到目标图源文件夹\n"
            "2. 更新数据库中的文件路径和图源信息\n"
            "3. 如果目标文件夹中已存在同名文件，将自动重命名\n\n"
            "此操作会修改磁盘上的文件位置，请谨慎操作。"
        )
        info_label = ttk.Label(
            main_frame,
            text=info_text,
            font=('TkDefaultFont', 8),
            foreground='#666',
            justify=tk.LEFT
        )
        info_label.pack(pady=(0, 15), fill=tk.X)
        
        # 图源列表
        list_frame = ttk.LabelFrame(main_frame, text="选择目标图源", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Listbox + Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.source_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('TkDefaultFont', 9),
            height=10
        )
        scrollbar.config(command=self.source_listbox.yview)
        
        self.source_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储图源信息
        self.sources = []
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="📁 转移",
            command=self._move_images
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.LEFT)
    
    def _load_sources(self):
        """加载所有图源"""
        try:
            self.sources = self.db.get_all_sources()
            
            if not self.sources:
                self.source_listbox.insert(tk.END, "暂无可用图源")
                return
            
            for source in self.sources:
                source_id = source['id']
                folder_path = source['folder_path']
                # 提取文件夹名称作为显示名称
                folder_name = Path(folder_path).name or folder_path
                self.source_listbox.insert(tk.END, f"{folder_name}  ({folder_path})")
        
        except Exception as e:
            messagebox.showerror("错误", f"加载图源失败: {e}")
    
    def _move_images(self):
        """转移图片"""
        # 获取选中的图源
        selection = self.source_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择目标图源")
            return
        
        target_source = self.sources[selection[0]]
        target_source_id = target_source['id']
        target_path = target_source['folder_path']
        
        # 检查目标路径是否存在
        if not os.path.exists(target_path):
            messagebox.showerror("错误", f"目标路径不存在：{target_path}")
            return
        
        # 提取文件夹名称
        folder_name = Path(target_path).name or target_path
        
        # 二次确认
        message = (
            f"确定要将 {len(self.file_paths)} 张图片转移到：\n\n"
            f"图源：{folder_name}\n"
            f"路径：{target_path}\n\n"
            "图片文件将被移动，原位置的文件将被删除。"
        )
        
        result = messagebox.askokcancel(
            "确认转移",
            message,
            icon='warning'
        )
        
        if not result:
            return
        
        # 执行转移
        success_count = 0
        failed_count = 0
        failed_files = []
        
        for old_path in self.file_paths:
            try:
                if not os.path.exists(old_path):
                    failed_count += 1
                    failed_files.append(f"{Path(old_path).name}: 文件不存在")
                    continue
                
                # 生成新路径
                filename = Path(old_path).name
                new_path = os.path.join(target_path, filename)
                
                # 如果目标已存在，添加序号
                if os.path.exists(new_path):
                    base_name = Path(filename).stem
                    ext = Path(filename).suffix
                    counter = 1
                    while os.path.exists(new_path):
                        new_filename = f"{base_name}_{counter}{ext}"
                        new_path = os.path.join(target_path, new_filename)
                        counter += 1
                
                # 移动文件
                shutil.move(old_path, new_path)
                
                # 更新数据库
                with self.db.get_cursor(commit=True) as cursor:
                    cursor.execute("""
                        UPDATE images 
                        SET file_path = ?, source_id = ?
                        WHERE file_path = ?
                    """, (new_path, target_source_id, old_path))
                
                success_count += 1
            
            except Exception as e:
                failed_count += 1
                failed_files.append(f"{Path(old_path).name}: {str(e)}")
        
        # 显示结果
        if failed_count == 0:
            messagebox.showinfo("成功", f"已成功转移 {success_count} 张图片")
        else:
            msg = f"转移完成：\n成功: {success_count} 张\n失败: {failed_count} 张"
            if failed_files:
                msg += "\n\n失败的文件：\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    msg += f"\n... 还有 {len(failed_files) - 5} 个"
            messagebox.showwarning("部分失败", msg)
        
        # 刷新页面
        if success_count > 0:
            if self.callback:
                self.callback()
            self.destroy()
