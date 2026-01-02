#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪切板辅助模块
提供将图片复制到系统剪切板的功能
"""

import os
import io
import tkinter as tk
from tkinter import messagebox
from PIL import Image


def copy_image_to_clipboard(file_path: str, parent=None) -> bool:
    """
    将图片复制到系统剪切板
    
    Args:
        file_path: 图片文件路径
        parent: 父窗口（用于显示消息框）
    
    Returns:
        bool: 是否成功复制
    """
    if not os.path.exists(file_path):
        if parent:
            messagebox.showerror("错误", f"文件不存在：\n{file_path}")
        return False
    
    try:
        # 打开图片
        img = Image.open(file_path)
        
        # 如果是RGBA模式，转换为RGB（Windows剪切板不支持透明度）
        if img.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 使用alpha通道作为蒙版
            img = background
        elif img.mode != 'RGB':
            # 其他格式转换为RGB
            img = img.convert('RGB')
        
        # 将图片转换为BMP格式（Windows剪切板标准格式）
        output = io.BytesIO()
        img.save(output, 'BMP')
        data = output.getvalue()[14:]  # BMP文件头14字节需要去掉
        output.close()
        
        # 复制到剪切板（Windows平台）
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        
        if parent:
            messagebox.showinfo("成功", "图片已复制到剪切板")
        return True
        
    except ImportError:
        # 如果没有win32clipboard，尝试使用tkinter方法
        try:
            # 创建临时Tk窗口
            temp_root = tk.Tk()
            temp_root.withdraw()
            
            # 打开图片
            img = Image.open(file_path)
            
            # 转换为PhotoImage
            photo = tk.PhotoImage(file=file_path)
            
            # 复制到剪切板
            temp_root.clipboard_clear()
            temp_root.clipboard_append(file_path)
            temp_root.update()
            temp_root.destroy()
            
            if parent:
                messagebox.showinfo("提示", "图片路径已复制到剪切板\n（需要安装pywin32以支持图片内容复制）")
            return True
            
        except Exception as e:
            if parent:
                messagebox.showerror("错误", f"复制失败：\n{str(e)}\n\n建议安装pywin32库以获得更好的支持")
            return False
            
    except Exception as e:
        if parent:
            messagebox.showerror("错误", f"复制失败：\n{str(e)}")
        return False


def copy_images_to_clipboard_batch(file_paths: list, parent=None) -> tuple:
    """
    批量复制图片到剪切板（仅复制第一张）
    
    Args:
        file_paths: 图片文件路径列表
        parent: 父窗口（用于显示消息框）
    
    Returns:
        tuple: (成功数, 失败数)
    """
    if not file_paths:
        if parent:
            messagebox.showwarning("提示", "没有选中任何图片")
        return (0, 0)
    
    # 确保顺序一致：按路径排序
    sorted_paths = sorted(file_paths)
    
    # 批量操作时只复制第一张图片
    if len(sorted_paths) > 1:
        if parent:
            # 获取将要复制的文件名
            first_file = os.path.basename(sorted_paths[0])
            result = messagebox.askyesno(
                "提示", 
                f"已选中 {len(sorted_paths)} 张图片\n剪切板只能保存一张图片\n\n将复制：{first_file}\n\n是否继续？"
            )
            if not result:
                return (0, 0)
    
    # 复制第一张图片
    success = copy_image_to_clipboard(sorted_paths[0], parent)
    return (1, 0) if success else (0, 1)
