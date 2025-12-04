#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标签管理对话框
用于创建、编辑、删除标签
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class TagManagerDialog(tk.Toplevel):
    """标签管理对话框"""
    
    # 预设颜色
    PRESET_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
        "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B88B", "#AAB7B8",
        "#FF9FF3", "#54A0FF", "#48DBFB", "#00D2D3", "#1DD1A1",
        "#FFC312", "#EE5A6F", "#C4E538", "#FDA7DF", "#F79F1F"
    ]
    
    def __init__(self, parent, db, callback=None):
        """
        初始化标签管理对话框
        
        Args:
            parent: 父窗口
            db: 数据库实例
            callback: 标签更新后的回调函数
        """
        super().__init__(parent)
        self.db = db
        self.callback = callback
        self.selected_color = self.PRESET_COLORS[0]
        
        self.title("标签管理")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_tags()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标签列表区域
        list_frame = ttk.LabelFrame(main_frame, text="现有标签", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview显示标签
        columns = ("name", "color", "count")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.tree.heading("name", text="标签名称")
        self.tree.heading("color", text="颜色")
        self.tree.heading("count", text="使用次数")
        
        self.tree.column("name", width=200)
        self.tree.column("color", width=100)
        self.tree.column("count", width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # 新建/编辑标签区域
        edit_frame = ttk.LabelFrame(main_frame, text="标签编辑", padding=5)
        edit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 标签名称
        name_frame = ttk.Frame(edit_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="标签名称:").pack(side=tk.LEFT, padx=(0, 5))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 颜色选择
        color_frame = ttk.Frame(edit_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="标签颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 颜色预览
        self.color_preview = tk.Canvas(color_frame, width=60, height=25, 
                                       bg=self.selected_color, relief=tk.SUNKEN)
        self.color_preview.pack(side=tk.LEFT, padx=(0, 5))
        
        # 自定义颜色按钮
        ttk.Button(color_frame, text="自定义颜色", 
                  command=self._choose_custom_color).pack(side=tk.LEFT, padx=(0, 10))
        
        # 预设颜色
        preset_frame = ttk.Frame(edit_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(preset_frame, text="快速选择:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建预设颜色按钮
        colors_container = ttk.Frame(preset_frame)
        colors_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        for i, color in enumerate(self.PRESET_COLORS[:10]):  # 显示前10个预设颜色
            btn = tk.Button(colors_container, bg=color, width=3, height=1,
                          command=lambda c=color: self._select_color(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 操作按钮区域
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="新建标签", 
                  command=self._create_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="更新标签", 
                  command=self._update_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除标签", 
                  command=self._delete_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清除选择", 
                  command=self._clear_selection).pack(side=tk.LEFT, padx=2)
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="关闭", 
                  command=self._on_close).pack(side=tk.RIGHT)
    
    def _select_color(self, color):
        """选择预设颜色"""
        self.selected_color = color
        self.color_preview.configure(bg=color)
    
    def _choose_custom_color(self):
        """选择自定义颜色"""
        color = colorchooser.askcolor(initialcolor=self.selected_color, title="选择标签颜色")
        if color[1]:  # 用户选择了颜色
            self.selected_color = color[1]
            self.color_preview.configure(bg=color[1])
    
    def _load_tags(self):
        """加载所有标签"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # 获取标签统计
            stats = self.db.get_tag_statistics()
            
            for stat in stats:
                tag_id = stat['id']
                name = stat['name']
                color = stat['color']
                count = stat['count']
                
                # 在Treeview中插入
                item_id = self.tree.insert("", tk.END, values=(name, color, count))
                # 存储tag_id在item的tags中
                self.tree.item(item_id, tags=(str(tag_id),))
                
                # 设置颜色预览
                self.tree.tag_configure(str(tag_id), background=color)
            
            logger.info(f"加载了 {len(stats)} 个标签")
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
            messagebox.showerror("错误", f"加载标签失败: {e}")
    
    def _on_select(self, event):
        """选中标签时填充编辑区域"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, "values")
        tag_id = self.tree.item(item, "tags")[0]
        
        # 填充名称和颜色
        self.name_var.set(values[0])
        self._select_color(values[1])
    
    def _clear_selection(self):
        """清除选择和编辑区域"""
        self.tree.selection_remove(self.tree.selection())
        self.name_var.set("")
        self._select_color(self.PRESET_COLORS[0])
    
    def _create_tag(self):
        """创建新标签"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入标签名称")
            return
        
        try:
            # 检查标签名是否已存在
            existing = self.db.get_tag_by_name(name)
            if existing:
                messagebox.showwarning("警告", f"标签 '{name}' 已存在")
                return
            
            # 创建标签
            tag_id = self.db.create_tag(name, self.selected_color)
            logger.info(f"创建标签: {name} (ID: {tag_id})")
            
            # 刷新列表
            self._load_tags()
            self._clear_selection()
            
            # 触发回调
            if self.callback:
                self.callback()
            
            messagebox.showinfo("成功", f"标签 '{name}' 创建成功")
        except Exception as e:
            logger.error(f"创建标签失败: {e}")
            messagebox.showerror("错误", f"创建标签失败: {e}")
    
    def _update_tag(self):
        """更新选中的标签"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要更新的标签")
            return
        
        item = selection[0]
        tag_id = int(self.tree.item(item, "tags")[0])
        name = self.name_var.get().strip()
        
        if not name:
            messagebox.showwarning("警告", "请输入标签名称")
            return
        
        try:
            # 检查新名称是否与其他标签冲突
            existing = self.db.get_tag_by_name(name)
            if existing and existing['id'] != tag_id:
                messagebox.showwarning("警告", f"标签名称 '{name}' 已被使用")
                return
            
            # 更新标签
            self.db.update_tag(tag_id, name, self.selected_color)
            logger.info(f"更新标签 ID {tag_id}: {name}")
            
            # 刷新列表
            self._load_tags()
            self._clear_selection()
            
            # 触发回调
            if self.callback:
                self.callback()
            
            messagebox.showinfo("成功", f"标签 '{name}' 更新成功")
        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            messagebox.showerror("错误", f"更新标签失败: {e}")
    
    def _delete_tag(self):
        """删除选中的标签"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的标签")
            return
        
        item = selection[0]
        tag_id = int(self.tree.item(item, "tags")[0])
        name = self.tree.item(item, "values")[0]
        count = self.tree.item(item, "values")[2]
        
        # 确认删除
        msg = f"确定要删除标签 '{name}' 吗？"
        if int(count) > 0:
            msg += f"\n\n该标签已被 {count} 张图片使用，删除后将从这些图片中移除。"
        
        if not messagebox.askyesno("确认删除", msg):
            return
        
        try:
            self.db.delete_tag(tag_id)
            logger.info(f"删除标签 ID {tag_id}: {name}")
            
            # 刷新列表
            self._load_tags()
            self._clear_selection()
            
            # 触发回调
            if self.callback:
                self.callback()
            
            messagebox.showinfo("成功", f"标签 '{name}' 已删除")
        except Exception as e:
            logger.error(f"删除标签失败: {e}")
            messagebox.showerror("错误", f"删除标签失败: {e}")
    
    def _on_close(self):
        """关闭对话框"""
        self.destroy()
