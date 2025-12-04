#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量标签编辑对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List
from ..tag_manager_dialog import TagManagerDialog


class BatchTagEditor(tk.Toplevel):
    """批量标签编辑对话框"""
    
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
        
        # 获取所有图片ID
        self.image_ids = []
        for path in file_paths:
            img_info = self.db.get_image_info(path)
            if img_info:
                self.image_ids.append(img_info[0])
        
        if not self.image_ids:
            messagebox.showerror("错误", "无法获取图片信息")
            self.destroy()
            return
        
        # 标签复选框变量
        self.tag_vars = {}
        
        self.title(f"批量编辑标签 - {len(file_paths)} 张图片")
        self.geometry("550x550")  # 增加高度以确保按钮可见
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
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 提示
        hint_label = ttk.Label(
            main_frame,
            text=f"为 {len(self.file_paths)} 张图片添加或移除标签：",
            font=('TkDefaultFont', 9)
        )
        hint_label.pack(anchor='w', pady=(0, 10))
        
        # 操作模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="操作模式", padding=5)
        mode_frame.pack(fill=tk.X, pady=(0, 8))  # 减小间距
        
        self.mode_var = tk.StringVar(value="add")
        ttk.Radiobutton(
            mode_frame,
            text="添加标签（保留原有标签）",
            variable=self.mode_var,
            value="add"
        ).pack(anchor='w', pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="移除标签（仅移除选中的标签）",
            variable=self.mode_var,
            value="remove"
        ).pack(anchor='w', pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="替换标签（清空原有标签，设置为选中的）",
            variable=self.mode_var,
            value="replace"
        ).pack(anchor='w', pady=2)
        
        # 标签列表
        list_frame = ttk.LabelFrame(main_frame, text="可用标签", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))  # 减小间距
        
        # Canvas + Scrollbar
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        self.tags_container = ttk.Frame(canvas)
        
        canvas_window = canvas.create_window((0, 0), window=self.tags_container, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        self.tags_container.bind("<Configure>", _on_frame_configure)
        
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # 鼠标滚轮
        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind('<MouseWheel>', _on_mousewheel)
        canvas.bind('<Button-4>', _on_mousewheel)
        canvas.bind('<Button-5>', _on_mousewheel)
        
        # 没有标签时的提示
        self.no_tags_label = ttk.Label(
            self.tags_container,
            text="暂无可用标签。请先在标签管理中创建标签。",
            foreground='gray'
        )
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 左侧按钮组
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="💾 应用",
            command=self._apply_tags,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            left_buttons,
            text="取消",
            command=self.destroy,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            left_buttons,
            text="🔖 管理标签",
            command=self._open_tag_manager,
            width=12
        ).pack(side=tk.LEFT)
        
        # 右侧按钮组
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_buttons,
            text="全不选",
            command=self._deselect_all,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            right_buttons,
            text="全选",
            command=self._select_all,
            width=8
        ).pack(side=tk.LEFT)
    
    def _load_tags(self):
        """加载所有可用标签"""
        try:
            all_tags = self.db.get_all_tags()
            
            if not all_tags:
                self.no_tags_label.pack(pady=20)
                return
            
            # 创建复选框
            for tag in all_tags:
                tag_id = tag['id']
                tag_name = tag['name']
                tag_color = tag['color']
                
                var = tk.BooleanVar(value=False)
                self.tag_vars[tag_id] = var
                
                tag_frame = ttk.Frame(self.tags_container)
                tag_frame.pack(fill=tk.X, pady=2)
                
                cb = ttk.Checkbutton(tag_frame, variable=var)
                cb.pack(side=tk.LEFT, padx=(5, 5))
                
                color_label = tk.Label(
                    tag_frame,
                    text=f" {tag_name} ",
                    bg=tag_color,
                    fg=self._get_contrast_color(tag_color),
                    font=('TkDefaultFont', 9, 'bold'),
                    relief=tk.RAISED,
                    padx=5,
                    pady=2
                )
                color_label.pack(side=tk.LEFT)
                color_label.bind('<Button-1>', lambda e, v=var: v.set(not v.get()))
        
        except Exception as e:
            messagebox.showerror("错误", f"加载标签失败: {e}")
    
    def _get_contrast_color(self, hex_color: str):
        """根据背景色返回对比色"""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return 'black' if brightness > 128 else 'white'
        except:
            return 'black'
    
    def _select_all(self):
        """全选"""
        for var in self.tag_vars.values():
            var.set(True)
    
    def _deselect_all(self):
        """全不选"""
        for var in self.tag_vars.values():
            var.set(False)
    
    def _apply_tags(self):
        """应用标签更改"""
        selected_tag_ids = [tag_id for tag_id, var in self.tag_vars.items() if var.get()]
        mode = self.mode_var.get()
        
        if not selected_tag_ids and mode != "replace":
            messagebox.showwarning("警告", "请至少选择一个标签")
            return
        
        try:
            success_count = 0
            
            for image_id in self.image_ids:
                if mode == "add":
                    # 添加模式：添加选中的标签（不影响已有标签）
                    for tag_id in selected_tag_ids:
                        self.db.add_tag_to_image(image_id, tag_id)
                    success_count += 1
                
                elif mode == "remove":
                    # 移除模式：只移除选中的标签
                    for tag_id in selected_tag_ids:
                        self.db.remove_tag_from_image(image_id, tag_id)
                    success_count += 1
                
                elif mode == "replace":
                    # 替换模式：用选中的标签替换所有标签
                    self.db.set_image_tags(image_id, selected_tag_ids)
                    success_count += 1
            
            mode_text = {"add": "添加", "remove": "移除", "replace": "替换"}[mode]
            messagebox.showinfo("成功", f"已为 {success_count} 张图片{mode_text}标签")
            
            if self.callback:
                self.callback()
            
            self.destroy()
        
        except Exception as e:
            messagebox.showerror("错误", f"应用标签失败: {e}")
    
    def _open_tag_manager(self):
        """打开标签管理对话框"""
        from ..tag_manager_dialog import TagManagerDialog
        
        dialog = TagManagerDialog(
            self.winfo_toplevel(),
            self.db,
            callback=self._reload_tags
        )
        dialog.wait_window()
    
    def _reload_tags(self):
        """重新加载标签列表"""
        # 清空现有标签
        for widget in self.tags_container.winfo_children():
            widget.destroy()
        
        # 重新加载
        self._load_tags()
