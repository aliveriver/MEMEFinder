#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详情面板UI组件模块
"""

import os
import tkinter as tk
from tkinter import ttk
import colorsys
from PIL import Image, ImageTk

def bind_mousewheel(widget, callback):
    """为控件绑定鼠标滚轮事件"""
    widget.bind('<MouseWheel>', callback)
    widget.bind('<Button-4>', callback)
    widget.bind('<Button-5>', callback)

def create_info_row(parent, label_text, value_text, scroll_callback, selectable=False):
    """创建信息行"""
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X, pady=5, padx=10)
    bind_mousewheel(frame, scroll_callback)
    
    label = ttk.Label(frame, text=label_text, font=('TkDefaultFont', 9, 'bold'))
    label.pack(anchor='w')
    bind_mousewheel(label, scroll_callback)
    
    if selectable:
        text_widget = tk.Text(frame, height=1, wrap=tk.NONE, font=('TkDefaultFont', 9))
        text_widget.insert('1.0', value_text)
        text_widget.config(state=tk.DISABLED, bg='#f0f0f0')
        text_widget.pack(fill=tk.X, pady=2)
        bind_mousewheel(text_widget, scroll_callback)
    else:
        value = ttk.Label(frame, text=value_text, font=('TkDefaultFont', 9))
        value.pack(anchor='w', pady=2)
        bind_mousewheel(value, scroll_callback)
    return frame

def get_contrast_color(hex_color):
    """根据背景色返回对比色（黑色或白色）"""
    try:
        # 移除#号
        hex_color = hex_color.lstrip('#')
        # 转换为RGB
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        # 计算亮度
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return 'black' if brightness > 128 else 'white'
    except:
        return 'black'

def create_tag_label(parent, name, color, scroll_callback):
    """创建一个彩色标签显示"""
    tag_label = tk.Label(
        parent,
        text=f" {name} ",
        bg=color,
        fg=get_contrast_color(color),
        font=('TkDefaultFont', 8, 'bold'),
        relief=tk.RAISED,
        padx=5,
        pady=2
    )
    tag_label.pack(side=tk.LEFT, padx=2, pady=2)
    bind_mousewheel(tag_label, scroll_callback)
    return tag_label

def create_color_section(parent, detail, scroll_callback, padding=10):
    """创建主题色显示区域"""
    color_hue_idx = detail.get('color_hue_idx')
    color_lightness = detail.get('color_lightness')
    hsv_h = detail.get('hsv_h')
    hsv_s = detail.get('hsv_s')
    hsv_v = detail.get('hsv_v')
    
    if color_hue_idx is None or color_lightness is None:
        return None

    color_frame = ttk.Frame(parent)
    color_frame.pack(fill=tk.X, pady=5, padx=padding)
    bind_mousewheel(color_frame, scroll_callback)
    
    color_title = ttk.Label(color_frame, text="主题色:", font=('TkDefaultFont', 9, 'bold'))
    color_title.pack(anchor='w')
    bind_mousewheel(color_title, scroll_callback)
    
    # 显示色块和信息
    color_display_frame = ttk.Frame(color_frame)
    color_display_frame.pack(fill=tk.X, pady=5)
    bind_mousewheel(color_display_frame, scroll_callback)
    
    # 从HSV转换为RGB显示色块
    if hsv_h is not None and hsv_h >= 0:
        rgb = colorsys.hsv_to_rgb(hsv_h/179, hsv_s/255, hsv_v/255)
        rgb_hex = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        
        color_block = tk.Frame(color_display_frame, width=40, height=40, bg=rgb_hex, relief=tk.SOLID, borderwidth=1)
        color_block.pack(side=tk.LEFT, padx=(0, 10))
        color_block.pack_propagate(False)
        bind_mousewheel(color_block, scroll_callback)
        
        # 颜色信息
        color_info_frame = ttk.Frame(color_display_frame)
        color_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bind_mousewheel(color_info_frame, scroll_callback)
        
        # 色相分类
        color_names = [
            "灰色", "红色", "橙黄", "黄绿", "绿色", "青色", "蓝色",
            "深蓝", "紫色", "品红", "洋红", "玫红", "红色"
        ]
        color_name = color_names[color_hue_idx] if 0 <= color_hue_idx < len(color_names) else "未知"
        
        name_label = ttk.Label(color_info_frame, text=f"色系: {color_name}", font=('TkDefaultFont', 9))
        name_label.pack(anchor='w')
        bind_mousewheel(name_label, scroll_callback)
        
        lightness_label = ttk.Label(color_info_frame, text=f"明度: {color_lightness}/100", font=('TkDefaultFont', 9))
        lightness_label.pack(anchor='w')
        bind_mousewheel(lightness_label, scroll_callback)
        
        hsv_label = ttk.Label(color_info_frame, text=f"HSV: ({hsv_h}, {hsv_s}, {hsv_v})", font=('TkDefaultFont', 8), foreground='gray')
        hsv_label.pack(anchor='w')
        bind_mousewheel(hsv_label, scroll_callback)
        
    return color_frame

def create_thumbnail(parent, file_path, scroll_callback, padding=10):
    """创建缩略图"""
    thumb_label = ttk.Label(parent, text="缩略图:")
    thumb_label.pack(pady=(10, 5), anchor='w', padx=padding)
    bind_mousewheel(thumb_label, scroll_callback)
    
    try:
        if os.path.exists(file_path):
            img = Image.open(file_path)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img.close()
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            photo = ImageTk.PhotoImage(img)
            img_label = ttk.Label(parent, image=photo)
            img_label.image = photo
            img_label.pack(pady=5, padx=padding)
            bind_mousewheel(img_label, scroll_callback)
            return img_label
        else:
            no_img_label = ttk.Label(parent, text="(图片文件不存在)", foreground='red')
            no_img_label.pack(pady=5, padx=padding)
            bind_mousewheel(no_img_label, scroll_callback)
    except Exception as e:
        error_img_label = ttk.Label(parent, text=f"(无法加载图片: {e})", foreground='red')
        error_img_label.pack(pady=5, padx=padding)
        bind_mousewheel(error_img_label, scroll_callback)
    return None
