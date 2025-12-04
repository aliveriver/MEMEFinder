#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
复选框下拉菜单组件
"""

import tkinter as tk
from tkinter import ttk


class CheckboxDropdown:
    """带复选框的下拉菜单控件"""
    
    def __init__(self, parent, options, default_text="请选择", callback=None, width=20):
        """
        Args:
            parent: 父控件
            options: 选项列表 [(显示文本, 值), ...]
            default_text: 默认显示文本
            callback: 选择变化时的回调函数
            width: 按钮宽度
        """
        self.parent = parent
        self.options = options
        self.default_text = default_text
        self.callback = callback
        self.width = width
        
        # 存储选中状态
        self.vars = {}  # {value: BooleanVar}
        for label, value in options:
            self.vars[value] = tk.BooleanVar(value=False)
        
        # 创建主按钮
        self.button = ttk.Button(parent, text=default_text, command=self._toggle_menu, width=width)
        
        # 下拉菜单窗口（初始为None）
        self.menu_window = None
        self.is_open = False
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.button.grid(**kwargs)
    
    def _toggle_menu(self):
        """切换下拉菜单显示/隐藏"""
        if self.is_open:
            self._close_menu()
        else:
            self._open_menu()
    
    def _open_menu(self):
        """打开下拉菜单"""
        if self.is_open:
            return
        
        # 创建Toplevel窗口作为下拉菜单
        self.menu_window = tk.Toplevel(self.parent)
        self.menu_window.withdraw()  # 先隐藏
        self.menu_window.overrideredirect(True)  # 去掉窗口边框
        
        # 创建框架
        frame = ttk.Frame(self.menu_window, relief=tk.RAISED, borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加复选框
        for label, value in self.options:
            cb = ttk.Checkbutton(
                frame, 
                text=label, 
                variable=self.vars[value],
                command=self._on_selection_change
            )
            cb.pack(anchor=tk.W, padx=5, pady=2)
        
        # 添加"全选"和"清空"按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="全选", command=self._select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空", command=self._clear_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="确定", command=self._close_menu, width=8).pack(side=tk.LEFT, padx=2)
        
        # 计算位置（在按钮下方）
        self.menu_window.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        self.menu_window.geometry(f"+{x}+{y}")
        
        # 显示窗口
        self.menu_window.deiconify()
        self.is_open = True
        
        # 绑定点击外部关闭菜单（延迟绑定，避免立即触发）
        def bind_outside_click():
            # 绑定到根窗口，检测点击事件
            def on_click(event):
                # 检查点击是否在菜单窗口外部
                if self.menu_window and self.menu_window.winfo_exists():
                    x, y = event.x_root, event.y_root
                    mx, my = self.menu_window.winfo_rootx(), self.menu_window.winfo_rooty()
                    mw, mh = self.menu_window.winfo_width(), self.menu_window.winfo_height()
                    
                    # 如果点击在菜单外部，关闭菜单
                    if not (mx <= x <= mx + mw and my <= y <= my + mh):
                        self._close_menu()
            
            # 获取根窗口
            root = self.parent.winfo_toplevel()
            root.bind("<Button-1>", on_click, add=True)
            
            # 保存绑定ID以便后续解除
            self._outside_click_handler = on_click
        
        # 延迟100ms后绑定，避免打开菜单的点击事件被捕获
        self.parent.after(100, bind_outside_click)
    
    def _close_menu(self):
        """关闭下拉菜单"""
        if self.menu_window:
            self.menu_window.destroy()
            self.menu_window = None
        self.is_open = False
        self._update_button_text()
        
        # 解除外部点击绑定
        if hasattr(self, '_outside_click_handler'):
            try:
                root = self.parent.winfo_toplevel()
                root.unbind("<Button-1>", self._outside_click_handler)
            except:
                pass
            delattr(self, '_outside_click_handler')
    
    def _on_selection_change(self):
        """选择变化时的处理"""
        self._update_button_text()
        if self.callback:
            self.callback()
    
    def _update_button_text(self):
        """更新按钮显示文本"""
        selected = self.get_selected_values()
        if not selected:
            text = self.default_text
        elif len(selected) == 1:
            # 找到对应的显示文本
            for label, value in self.options:
                if value == selected[0]:
                    text = label
                    break
            else:
                text = selected[0]
        else:
            text = f"已选 {len(selected)} 项"
        
        self.button.config(text=text)
    
    def _select_all(self):
        """全选"""
        for var in self.vars.values():
            var.set(True)
        self._on_selection_change()
    
    def _clear_all(self):
        """清空选择"""
        for var in self.vars.values():
            var.set(False)
        self._on_selection_change()
    
    def get_selected_values(self):
        """获取选中的值列表"""
        return [value for value, var in self.vars.items() if var.get()]
    
    def set_selected_values(self, values):
        """设置选中的值"""
        for value, var in self.vars.items():
            var.set(value in values)
        self._update_button_text()
