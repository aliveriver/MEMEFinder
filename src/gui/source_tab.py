#!/usr:bin/env python
# -*- coding: utf-8 -*-
"""
图源管理标签页
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from ..core.database import ImageDatabase
from ..core.scanner import ImageScanner


class SourceTab:
    """图源管理标签页"""
    
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        self.scanner = ImageScanner()
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 顶部按钮区
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="➕ 添加图源文件夹", 
                  command=self.add_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除选中", 
                  command=self.remove_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新列表", 
                  command=self.refresh_sources).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 扫描新图片", 
                  command=self.scan_sources).pack(side=tk.LEFT, padx=5)
        
        # 图源列表
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ('路径', '添加时间', '最后扫描', '状态')
        self.source_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        # 设置列
        self.source_tree.heading('#0', text='ID')
        self.source_tree.column('#0', width=50)
        for col in columns:
            self.source_tree.heading(col, text=col)
        
        self.source_tree.column('路径', width=400)
        self.source_tree.column('添加时间', width=150)
        self.source_tree.column('最后扫描', width=150)
        self.source_tree.column('状态', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.source_tree.yview)
        self.source_tree.configure(yscrollcommand=scrollbar.set)
        
        self.source_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self.source_menu = tk.Menu(self.frame, tearoff=0)
        self.source_menu.add_command(label="打开文件夹", command=self.open_source_folder)
        self.source_menu.add_command(label="启用/禁用", command=self.toggle_source)
        self.source_menu.add_separator()
        self.source_menu.add_command(label="删除", command=self.remove_source)
        
        self.source_tree.bind("<Button-3>", self.show_source_menu)
        
        # 统计信息区
        stats_frame = ttk.LabelFrame(self.frame, text="统计信息", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.StringVar(value="总图片: 0 | 已处理: 0 | 未处理: 0")
        ttk.Label(stats_frame, textvariable=self.stats_text, font=('Arial', 10)).pack()
    
    def add_source(self):
        """添加图源文件夹"""
        folder = filedialog.askdirectory(title="选择图源文件夹")
        if folder:
            # 标准化为绝对路径
            folder = os.path.abspath(folder)

            # 检查是否已有已添加的目录包含当前选择的目录（即父目录已被添加）
            try:
                sources = self.db.get_sources()
            except Exception:
                sources = []

            for s in sources:
                try:
                    src_path = os.path.abspath(s.get('folder_path') or '')
                    # 相同路径或 src_path 是 folder 的父目录
                    if src_path and (src_path == folder or os.path.commonpath([src_path, folder]) == src_path):
                        messagebox.showwarning("警告", f"该文件夹已被包含于已添加的图源：{src_path}")
                        return
                except Exception:
                    # os.path.commonpath 在不同磁盘可能抛异常，忽略并继续检查下一项
                    continue

            if self.db.add_source(folder):
                messagebox.showinfo("成功", f"已添加图源：{folder}")
                self.refresh_sources()
                self.update_statistics()
            else:
                messagebox.showwarning("警告", "该文件夹已存在")
    
    def remove_source(self):
        """删除选中的图源"""
        selected = self.source_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的图源")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的图源吗？\n这将同时删除该图源的所有图片记录。"):
            for item in selected:
                source_id = int(self.source_tree.item(item)['text'])
                self.db.remove_source(source_id)
            self.refresh_sources()
            self.update_statistics()
            messagebox.showinfo("成功", "已删除选中的图源")
    
    def refresh_sources(self):
        """刷新图源列表"""
        # 清空列表
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        
        # 重新加载
        sources = self.db.get_sources()
        for source in sources:
            status = "✓ 启用" if source['enabled'] else "✗ 禁用"
            last_scan = source['last_scan_time'] or "未扫描"
            self.source_tree.insert('', tk.END, text=source['id'],
                                   values=(source['folder_path'], 
                                          source['added_time'][:19],
                                          last_scan[:19] if last_scan != "未扫描" else last_scan,
                                          status))
    
    def show_source_menu(self, event):
        """显示右键菜单"""
        item = self.source_tree.identify_row(event.y)
        if item:
            self.source_tree.selection_set(item)
            self.source_menu.post(event.x_root, event.y_root)
    
    def open_source_folder(self):
        """打开图源文件夹"""
        selected = self.source_tree.selection()
        if selected:
            item = selected[0]
            folder_path = self.source_tree.item(item)['values'][0]
            if os.path.exists(folder_path):
                os.startfile(folder_path)
            else:
                messagebox.showerror("错误", "文件夹不存在")
    
    def toggle_source(self):
        """启用/禁用图源"""
        selected = self.source_tree.selection()
        if selected:
            item = selected[0]
            source_id = int(self.source_tree.item(item)['text'])
            status = self.source_tree.item(item)['values'][3]
            enabled = "✗" in status
            self.db.toggle_source(source_id, enabled)
            self.refresh_sources()
    
    def scan_sources(self):
        """扫描图源中的新图片"""
        sources = self.db.get_sources()
        enabled_sources = [s for s in sources if s['enabled']]
        
        if not enabled_sources:
            messagebox.showwarning("警告", "没有启用的图源")
            return
        
        total_new = 0
        for source in enabled_sources:
            folder_path = source['folder_path']
            if not os.path.exists(folder_path):
                continue
            
            # 获取全局已存在的图片哈希（不限定图源）
            # 这样可以避免重复添加相同的图片，即使它们在不同图源
            existing_hashes = self.db.get_image_hashes()
            
            # 查找新图片
            new_images = self.scanner.find_new_images(folder_path, existing_hashes)
            
            # 批量添加到数据库（优化性能）
            if new_images:
                batch_data = [(str(img_path), img_hash, source['id']) for img_path, img_hash in new_images]
                added = self.db.add_images_batch(batch_data)
                total_new += added
            
            self.db.update_scan_time(source['id'])
        
        self.refresh_sources()
        self.update_statistics()
        messagebox.showinfo("完成", f"扫描完成！\n发现新图片: {total_new} 张")

        # 仅在发现新图片时自动切换到图片处理标签页
        if total_new > 0:
            try:
                # 先按标签文本查找（更稳健）
                for tab_id in self.parent.tabs():
                    try:
                        if self.parent.tab(tab_id, 'text') == '图片处理':
                            self.parent.select(tab_id)
                            break
                    except Exception:
                        continue
            except Exception:
                # 忽略切换错误，不影响扫描结果
                pass
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.db.get_statistics()
        emotions = stats['emotions']
        emotion_str = " | ".join([f"{k}: {v}" for k, v in emotions.items()])
        
        text = f"总图片: {stats['total']} | 已处理: {stats['processed']} | 未处理: {stats['unprocessed']}"
        if emotion_str:
            text += f" | {emotion_str}"
        
        self.stats_text.set(text)
