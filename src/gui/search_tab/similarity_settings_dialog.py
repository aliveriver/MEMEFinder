#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
以图搜图权重设置对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox


class SimilaritySettingsDialog:
    """以图搜图权重设置对话框"""
    
    def __init__(self, parent, current_dl_weight=0.8, current_phash_weight=0.2):
        """
        Args:
            parent: 父窗口
            current_dl_weight: 当前深度学习权重
            current_phash_weight: 当前PHash权重
        """
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("以图搜图权重设置")
        self.dialog.geometry("700x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # 创建界面
        self._create_widgets(current_dl_weight, current_phash_weight)
        
    def _create_widgets(self, dl_weight, phash_weight):
        """创建界面组件"""
        # 标题
        title_frame = ttk.Frame(self.dialog, padding=10)
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="⚙️ 以图搜图相似度计算权重配置",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack()
        
        desc_label = ttk.Label(
            title_frame,
            text="调整不同特征在相似度计算中的权重比例",
            foreground="gray"
        )
        desc_label.pack(pady=(5, 0))
        
        # 分隔线
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # 权重设置区域
        settings_frame = ttk.LabelFrame(self.dialog, text="权重配置", padding=15)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 深度学习特征权重
        ttk.Label(settings_frame, text="🧠 深度学习特征权重:", font=('TkDefaultFont', 10)).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        dl_frame = ttk.Frame(settings_frame)
        dl_frame.grid(row=1, column=0, sticky=tk.EW, pady=(0, 15))
        
        # 先创建滑块但不绑定command
        self.dl_scale = ttk.Scale(
            dl_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL
        )
        self.dl_scale.set(dl_weight)
        self.dl_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 手动输入框
        input_frame1 = ttk.Frame(dl_frame)
        input_frame1.pack(side=tk.LEFT, padx=(10, 0))
        
        self.dl_entry = ttk.Entry(input_frame1, width=6)
        self.dl_entry.pack(side=tk.LEFT)
        self.dl_entry.insert(0, str(int(dl_weight*100)))
        self.dl_entry.bind('<Return>', self._on_dl_entry_change)
        self.dl_entry.bind('<FocusOut>', self._on_dl_entry_change)
        
        # 现在绑定command
        self.dl_scale.config(command=self._on_dl_scale_change)
        
        ttk.Label(input_frame1, text="%").pack(side=tk.LEFT, padx=(2, 0))
        
        ttk.Label(
            settings_frame,
            text="捕捉语义信息（物体、场景、构图等）",
            foreground="gray",
            font=('TkDefaultFont', 9)
        ).grid(row=2, column=0, sticky=tk.W, pady=(0, 20))
        
        # PHash权重
        ttk.Label(settings_frame, text="🔷 PHash特征权重:", font=('TkDefaultFont', 10)).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        phash_frame = ttk.Frame(settings_frame)
        phash_frame.grid(row=4, column=0, sticky=tk.EW, pady=(0, 15))
        
        # 先创建滑块但不绑定command
        self.phash_scale = ttk.Scale(
            phash_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL
        )
        self.phash_scale.set(phash_weight)
        self.phash_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 手动输入框
        input_frame2 = ttk.Frame(phash_frame)
        input_frame2.pack(side=tk.LEFT, padx=(10, 0))
        
        self.phash_entry = ttk.Entry(input_frame2, width=6)
        self.phash_entry.pack(side=tk.LEFT)
        self.phash_entry.insert(0, str(int(phash_weight*100)))
        self.phash_entry.bind('<Return>', self._on_phash_entry_change)
        self.phash_entry.bind('<FocusOut>', self._on_phash_entry_change)
        
        # 现在绑定command
        self.phash_scale.config(command=self._on_phash_scale_change)
        
        ttk.Label(input_frame2, text="%").pack(side=tk.LEFT, padx=(2, 0))
        
        ttk.Label(
            settings_frame,
            text="捕捉视觉结构相似度（布局、形状等）",
            foreground="gray",
            font=('TkDefaultFont', 9)
        ).grid(row=5, column=0, sticky=tk.W, pady=(0, 20))
        
        # 权重和提示
        self.sum_label = ttk.Label(
            settings_frame,
            text="",
            font=('TkDefaultFont', 9)
        )
        self.sum_label.grid(row=6, column=0, sticky=tk.W)
        self._update_sum_label()
        
        # 预设按钮
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.grid(row=7, column=0, sticky=tk.W, pady=(15, 0))
        
        ttk.Label(preset_frame, text="快速预设:", font=('TkDefaultFont', 9)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preset_frame, text="推荐 (80:20)", command=lambda: self._apply_preset(0.8, 0.2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="平衡 (70:30)", command=lambda: self._apply_preset(0.7, 0.3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="结构优先 (50:50)", command=lambda: self._apply_preset(0.5, 0.5)).pack(side=tk.LEFT, padx=2)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="✓ 确定", command=self._on_ok, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✗ 取消", command=self._on_cancel, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="🔄 重置为默认", command=lambda: self._apply_preset(0.8, 0.2)).pack(side=tk.LEFT, padx=5)
    
    def _on_dl_scale_change(self, value):
        """DL权重滑块变化时更新"""
        dl_weight = self.dl_scale.get()
        self.dl_entry.delete(0, tk.END)
        self.dl_entry.insert(0, str(int(dl_weight*100)))
        self._update_sum_label()
    
    def _on_phash_scale_change(self, value):
        """PHash权重滑块变化时更新"""
        phash_weight = self.phash_scale.get()
        self.phash_entry.delete(0, tk.END)
        self.phash_entry.insert(0, str(int(phash_weight*100)))
        self._update_sum_label()
    
    def _on_dl_entry_change(self, event):
        """DL输入框变化时更新滑块并自动调整PHash"""
        try:
            value = int(self.dl_entry.get())
            value = max(0, min(100, value))  # 限制在0-100
            
            self.dl_scale.set(value / 100.0)
            
            # 自动调整PHash使总和为100
            phash_value = 100 - value
            self.phash_scale.set(phash_value / 100.0)
            self.phash_entry.delete(0, tk.END)
            self.phash_entry.insert(0, str(phash_value))
            
            self._update_sum_label()
        except ValueError:
            pass
    
    def _on_phash_entry_change(self, event):
        """PHash输入框变化时更新滑块并自动调整DL"""
        try:
            value = int(self.phash_entry.get())
            value = max(0, min(100, value))  # 限制在0-100
            
            self.phash_scale.set(value / 100.0)
            
            # 自动调整DL使总和为100
            dl_value = 100 - value
            self.dl_scale.set(dl_value / 100.0)
            self.dl_entry.delete(0, tk.END)
            self.dl_entry.insert(0, str(dl_value))
            
            self._update_sum_label()
        except ValueError:
            pass
    
    def _on_weight_change(self, value):
        """权重滑块变化时更新显示（已废弃，保留以兼容）"""
        pass
    
    def _update_sum_label(self):
        """更新权重和显示"""
        dl_weight = self.dl_scale.get()
        phash_weight = self.phash_scale.get()
        weight_sum = dl_weight + phash_weight
        
        if abs(weight_sum - 1.0) < 0.01:
            self.sum_label.config(
                text=f"✓ 权重总和: {weight_sum:.2f} (正常)",
                foreground="green"
            )
        else:
            self.sum_label.config(
                text=f"⚠ 权重总和: {weight_sum:.2f} (建议调整为1.0)",
                foreground="orange"
            )
    
    def _apply_preset(self, dl_weight, phash_weight):
        """应用预设权重"""
        self.dl_scale.set(dl_weight)
        self.phash_scale.set(phash_weight)
        
        self.dl_entry.delete(0, tk.END)
        self.dl_entry.insert(0, str(int(dl_weight*100)))
        
        self.phash_entry.delete(0, tk.END)
        self.phash_entry.insert(0, str(int(phash_weight*100)))
        
        self._update_sum_label()
    
    def _on_ok(self):
        """确定按钮"""
        dl_weight = self.dl_scale.get()
        phash_weight = self.phash_scale.get()
        weight_sum = dl_weight + phash_weight
        
        # 验证权重和
        if abs(weight_sum - 1.0) > 0.1:
            response = messagebox.askyesno(
                "权重提示",
                f"当前权重总和为 {weight_sum:.2f}，不等于1.0\n是否继续？"
            )
            if not response:
                return
        
        self.result = (dl_weight, phash_weight)
        self.dialog.destroy()
    
    def _on_cancel(self):
        """取消按钮"""
        self.result = None
        self.dialog.destroy()
    
    def wait_window(self):
        """等待对话框关闭"""
        self.dialog.wait_window()
        return self.result
