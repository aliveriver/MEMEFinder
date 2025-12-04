#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量转移到图源对话框
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
        self.geometry("600x500")
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
        
        # 创建新图源按钮
        new_source_btn_frame = ttk.Frame(main_frame)
        new_source_btn_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Button(
            new_source_btn_frame,
            text="➕ 创建新图源",
            command=self._create_new_source,
            width=15
        ).pack(side=tk.LEFT)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            button_frame,
            text="📁 转移",
            command=self._move_images,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy,
            width=12
        ).pack(side=tk.LEFT)
    
    def _load_sources(self):
        """加载所有图源"""
        try:
            # 清空现有列表
            self.source_listbox.delete(0, tk.END)
            self.sources = []
            
            # 加载新数据
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
    
    def _create_new_source(self):
        """创建新图源"""
        dialog = CreateSourceDialog(self, self.db)
        self.wait_window(dialog)
        
        # 如果创建成功，刷新图源列表
        if dialog.created_source_id:
            self._load_sources()
            # 自动选中新创建的图源
            for i, source in enumerate(self.sources):
                if source['id'] == dialog.created_source_id:
                    self.source_listbox.selection_clear(0, tk.END)
                    self.source_listbox.selection_set(i)
                    self.source_listbox.see(i)
                    break


class CreateSourceDialog(tk.Toplevel):
    """创建新图源对话框"""
    
    def __init__(self, parent, db):
        """
        Args:
            parent: 父窗口
            db: 数据库实例
        """
        super().__init__(parent)
        self.db = db
        self.created_source_id = None
        
        self.title("创建新图源")
        self.geometry("600x320")
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="创建新图源文件夹",
            font=('TkDefaultFont', 10, 'bold')
        )
        title_label.pack(pady=(0, 15))
        
        # 说明
        info_text = (
            "在指定的父目录下创建一个新的文件夹作为图源，\n"
            "并自动添加到数据库中。"
        )
        info_label = ttk.Label(
            main_frame,
            text=info_text,
            font=('TkDefaultFont', 8),
            foreground='#666'
        )
        info_label.pack(pady=(0, 20))
        
        # 父目录选择
        parent_dir_frame = ttk.Frame(main_frame)
        parent_dir_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            parent_dir_frame,
            text="父目录："
        ).pack(side=tk.LEFT)
        
        self.parent_dir_var = tk.StringVar()
        parent_dir_entry = ttk.Entry(
            parent_dir_frame,
            textvariable=self.parent_dir_var,
            width=40
        )
        parent_dir_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        ttk.Button(
            parent_dir_frame,
            text="📁 浏览",
            command=self._select_parent_dir,
            width=8
        ).pack(side=tk.LEFT)
        
        # 文件夹名称
        folder_name_frame = ttk.Frame(main_frame)
        folder_name_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            folder_name_frame,
            text="文件夹名："
        ).pack(side=tk.LEFT)
        
        self.folder_name_var = tk.StringVar()
        folder_name_entry = ttk.Entry(
            folder_name_frame,
            textvariable=self.folder_name_var,
            width=40
        )
        folder_name_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # 预览完整路径
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            preview_frame,
            text="完整路径："
        ).pack(side=tk.LEFT)
        
        self.preview_label = ttk.Label(
            preview_frame,
            text="请先选择父目录和输入文件夹名称",
            foreground='#666',
            font=('TkDefaultFont', 8)
        )
        self.preview_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 绑定输入变化事件
        self.parent_dir_var.trace_add('write', self._update_preview)
        self.folder_name_var.trace_add('write', self._update_preview)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="✅ 创建",
            command=self._create_source,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy,
            width=12
        ).pack(side=tk.LEFT)
    
    def _select_parent_dir(self):
        """选择父目录"""
        directory = filedialog.askdirectory(
            title="选择父目录",
            parent=self
        )
        if directory:
            self.parent_dir_var.set(directory)
    
    def _update_preview(self, *args):
        """更新完整路径预览"""
        parent_dir = self.parent_dir_var.get().strip()
        folder_name = self.folder_name_var.get().strip()
        
        if parent_dir and folder_name:
            full_path = os.path.join(parent_dir, folder_name)
            self.preview_label.config(
                text=full_path,
                foreground='#000'
            )
        else:
            self.preview_label.config(
                text="请先选择父目录和输入文件夹名称",
                foreground='#666'
            )
    
    def _create_source(self):
        """创建新图源"""
        parent_dir = self.parent_dir_var.get().strip()
        folder_name = self.folder_name_var.get().strip()
        
        # 验证输入
        if not parent_dir:
            messagebox.showwarning("警告", "请选择父目录")
            return
        
        if not folder_name:
            messagebox.showwarning("警告", "请输入文件夹名称")
            return
        
        if not os.path.exists(parent_dir):
            messagebox.showerror("错误", f"父目录不存在：{parent_dir}")
            return
        
        # 检查文件夹名称是否合法
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        if any(char in folder_name for char in invalid_chars):
            messagebox.showerror(
                "错误",
                f"文件夹名称包含非法字符：{', '.join(invalid_chars)}"
            )
            return
        
        # 生成完整路径
        full_path = os.path.join(parent_dir, folder_name)
        
        # 检查是否已存在
        if os.path.exists(full_path):
            messagebox.showerror("错误", f"文件夹已存在：{full_path}")
            return
        
        try:
            # 创建文件夹
            os.makedirs(full_path, exist_ok=True)
            
            # 添加到数据库
            success = self.db.add_source(full_path)
            
            if not success:
                messagebox.showerror("错误", "图源已在数据库中存在")
                # 如果数据库添加失败但文件夹已创建，询问是否删除
                if messagebox.askyesno("清理", "是否删除刚创建的文件夹？"):
                    os.rmdir(full_path)
                return
            
            # 获取新创建的图源ID
            sources = self.db.get_all_sources()
            for source in sources:
                if source['folder_path'] == full_path:
                    self.created_source_id = source['id']
                    break
            
            messagebox.showinfo("成功", f"已创建新图源：\n{full_path}")
            self.destroy()
        
        except PermissionError:
            messagebox.showerror("错误", f"没有权限创建文件夹：{full_path}")
        except Exception as e:
            messagebox.showerror("错误", f"创建图源失败：{e}")
