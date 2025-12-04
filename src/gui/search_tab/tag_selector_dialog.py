#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标签选择对话框
用于为图片选择和管理标签
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class TagSelectorDialog(tk.Toplevel):
    """标签选择对话框"""
    
    def __init__(self, parent, db, file_path, callback=None):
        """
        初始化标签选择对话框
        
        Args:
            parent: 父窗口
            db: 数据库实例
            file_path: 图片文件路径
            callback: 标签更新后的回调函数
        """
        super().__init__(parent)
        self.db = db
        self.file_path = file_path
        self.callback = callback
        
        # 获取图片ID
        img_info = self.db.get_image_info(file_path)
        if not img_info:
            messagebox.showerror("错误", "无法获取图片信息")
            self.destroy()
            return
        
        self.image_id = img_info[0]
        
        # 标签复选框变量
        self.tag_vars = {}
        
        self.title(f"编辑标签 - {Path(file_path).name}")
        self.geometry("500x400")
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
        
        # 提示文本
        hint_label = ttk.Label(
            main_frame,
            text="请选择要为图片添加的标签：",
            font=('TkDefaultFont', 9)
        )
        hint_label.pack(anchor='w', pady=(0, 10))
        
        # 标签列表区域（可滚动）
        list_frame = ttk.LabelFrame(main_frame, text="可用标签", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Canvas+Scrollbar实现滚动
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        self.tags_container = ttk.Frame(canvas)
        
        canvas_window = canvas.create_window((0, 0), window=self.tags_container, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 更新滚动区域
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 更新canvas window宽度以填充canvas
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        self.tags_container.bind("<Configure>", _on_frame_configure)
        
        def _on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            if event.num == 4:  # Linux向上滚动
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux向下滚动
                canvas.yview_scroll(1, "units")
            else:  # Windows/Mac
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind('<MouseWheel>', _on_mousewheel)
        canvas.bind('<Button-4>', _on_mousewheel)
        canvas.bind('<Button-5>', _on_mousewheel)
        self.tags_container.bind('<MouseWheel>', _on_mousewheel)
        self.tags_container.bind('<Button-4>', _on_mousewheel)
        self.tags_container.bind('<Button-5>', _on_mousewheel)
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="💾 保存",
            command=self._save_tags
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 右侧按钮
        ttk.Button(
            button_frame,
            text="全选",
            command=self._select_all
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="全不选",
            command=self._deselect_all
        ).pack(side=tk.RIGHT)
        
        # 没有标签时的提示
        self.no_tags_label = ttk.Label(
            self.tags_container,
            text="暂无可用标签。请先在标签管理中创建标签。",
            foreground='gray'
        )
    
    def _load_tags(self):
        """加载所有标签和当前图片的标签"""
        try:
            # 获取所有标签
            all_tags = self.db.get_all_tags()
            
            if not all_tags:
                self.no_tags_label.pack(pady=20)
                return
            
            # 获取图片当前的标签
            current_tags = self.db.get_image_tags(self.image_id)
            current_tag_ids = {tag['id'] for tag in current_tags}
            
            # 创建复选框
            for tag in all_tags:
                tag_id = tag['id']
                tag_name = tag['name']
                tag_color = tag['color']
                
                var = tk.BooleanVar(value=tag_id in current_tag_ids)
                self.tag_vars[tag_id] = var
                
                # 创建带颜色的复选框
                tag_frame = ttk.Frame(self.tags_container)
                tag_frame.pack(fill=tk.X, pady=2)
                
                # 复选框
                cb = ttk.Checkbutton(
                    tag_frame,
                    variable=var
                )
                cb.pack(side=tk.LEFT, padx=(5, 5))
                
                # 彩色标签预览
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
                
                # 点击标签也能切换复选框
                color_label.bind('<Button-1>', lambda e, v=var: v.set(not v.get()))
            
            logger.info(f"加载了 {len(all_tags)} 个标签，图片当前有 {len(current_tag_ids)} 个标签")
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
            messagebox.showerror("错误", f"加载标签失败: {e}")
    
    def _get_contrast_color(self, hex_color: str):
        """根据背景色返回对比色（黑色或白色）"""
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
    
    def _save_tags(self):
        """保存标签选择"""
        try:
            # 获取选中的标签ID
            selected_tag_ids = [tag_id for tag_id, var in self.tag_vars.items() if var.get()]
            
            # 更新数据库
            self.db.set_image_tags(self.image_id, selected_tag_ids)
            logger.info(f"为图片 {self.file_path} 设置了 {len(selected_tag_ids)} 个标签")
            
            # 触发回调
            if self.callback:
                self.callback()
            
            messagebox.showinfo("成功", "标签已更新")
            self.destroy()
        except Exception as e:
            logger.error(f"保存标签失败: {e}")
            messagebox.showerror("错误", f"保存标签失败: {e}")
