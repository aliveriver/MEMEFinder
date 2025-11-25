#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU CUDA DLL 复制工具
用于复制用户系统上的 CUDA DLL 到 onnxruntime 目录

由于已在打包时包含 onnxruntime-gpu，此工具仅负责复制 CUDA DLL
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import logging


def check_onnxruntime_gpu_installed() -> bool:
    """
    检查 onnxruntime-gpu 是否已安装
    
    Returns:
        bool: 是否已安装
    """
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        return 'CUDAExecutionProvider' in providers
    except ImportError:
        return False


def show_install_dialog(parent) -> bool:
    """
    显示GPU加速配置对话框
    
    Args:
        parent: 父窗口
        
    Returns:
        bool: 用户是否确认配置
    """
    # 检查是否已配置
    if check_onnxruntime_gpu_installed():
        messagebox.showinfo(
            "GPU加速",
            "GPU加速支持已配置完成！\n\n您可以在处理选项中启用GPU加速。",
            parent=parent
        )
        return False
    
    # 获取GPU信息
    try:
        from .gpu_detector import get_gpu_recommendation
        gpu_status = get_gpu_recommendation()
        has_hw = gpu_status['has_hardware']
        gpu_info = gpu_status.get('device_info', 'NVIDIA GPU')
        
        if not has_hw:
            messagebox.showwarning(
                "警告", 
                "未检测到NVIDIA GPU硬件。\n\nGPU加速需要NVIDIA显卡支持。",
                parent=parent
            )
            return False
    except Exception as e:
        print(f"GPU检测出错: {e}")
        gpu_info = "NVIDIA GPU"
    
    # 创建配置确认对话框
    dialog = tk.Toplevel(parent)
    dialog.title("配置GPU加速")
    dialog.geometry("450x280")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # 居中显示
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (280 // 2)
    dialog.geometry(f"450x280+{x}+{y}")
    
    result = {'confirmed': False}
    
    # 标题
    title_label = ttk.Label(
        dialog,
        text="检测到NVIDIA GPU！",
        font=("Arial", 14, "bold")
    )
    title_label.pack(pady=20)
    
    # 分隔线
    separator = ttk.Separator(dialog, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=5)
    
    # GPU信息
    info_frame = ttk.Frame(dialog)
    info_frame.pack(pady=10)
    
    if gpu_info and isinstance(gpu_info, str) and "CUDA GPU:" in gpu_info:
        gpu_name = gpu_info.replace("CUDA GPU:", "").strip()
        ttk.Label(
            info_frame,
            text=f"设备: {gpu_name}",
            font=("Arial", 10)
        ).pack(anchor='w')
    
    # 说明文字
    desc_frame = ttk.Frame(dialog)
    desc_frame.pack(pady=10, padx=30)
    
    desc_text = """是否配置GPU加速支持？

配置后可大幅提升OCR处理速度（3-5倍）

• 需要复制 CUDA DLL 文件
• 需要有效的 CUDA 安装路径"""
    
    ttk.Label(
        desc_frame,
        text=desc_text,
        justify='left',
        font=("Arial", 9)
    ).pack(anchor='w')
    
    # 按钮
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=20)
    
    def on_confirm():
        result['confirmed'] = True
        dialog.destroy()
    
    def on_cancel():
        result['confirmed'] = False
        dialog.destroy()
    
    ttk.Button(
        btn_frame,
        text="✓ 配置GPU加速",
        command=on_confirm,
        width=15
    ).pack(side=tk.LEFT, padx=10)
    
    ttk.Button(
        btn_frame,
        text="暂不配置",
        command=on_cancel,
        width=15
    ).pack(side=tk.LEFT, padx=10)
    
    # 等待对话框关闭
    dialog.wait_window()
    
    return result['confirmed']


def copy_cuda_dlls(cuda_path: str) -> bool:
    """
    复制 CUDA DLL 文件到 onnxruntime 目录
    
    Args:
        cuda_path: CUDA 安装路径
        
    Returns:
        bool: 是否成功
    """
    logger = logging.getLogger('MEMEFinder')
    
    try:
        from .cuda_finder import find_cuda_dlls
        
        # 获取当前可执行文件路径
        exe_path = sys.executable
        app_dir = os.path.dirname(exe_path)
        internal_dir = os.path.join(app_dir, "_internal")
        onnxruntime_path = os.path.join(internal_dir, 'onnxruntime')
        
        logger.info(f"[CUDA配置] 开始复制 CUDA DLL 文件")
        logger.info(f"[CUDA配置] CUDA 路径: {cuda_path}")
        logger.info(f"[CUDA配置] 目标路径: {onnxruntime_path}")
        
        # 查找 CUDA DLL
        dlls = find_cuda_dlls(cuda_path)
        if not dlls:
            logger.error(f"[CUDA配置] 未找到 CUDA DLL 文件")
            return False
        
        logger.info(f"[CUDA配置] 找到 {len(dlls)} 个 DLL 文件")
        
        # 目标目录
        capi_dir = os.path.join(onnxruntime_path, 'capi')
        if not os.path.exists(capi_dir):
            os.makedirs(capi_dir, exist_ok=True)
            logger.info(f"[CUDA配置] 创建目录: {capi_dir}")
        
        # 复制文件
        import shutil
        copied = 0
        failed = 0
        
        for dll_name, dll_path in dlls:
            target_path = os.path.join(capi_dir, dll_name)
            try:
                shutil.copy2(dll_path, target_path)
                if os.path.exists(target_path):
                    size = os.path.getsize(target_path)
                    logger.info(f"[CUDA配置] 复制成功: {dll_name} ({size:,} 字节)")
                    copied += 1
                else:
                    logger.error(f"[CUDA配置] 复制失败: {dll_name} - 文件未创建")
                    failed += 1
            except Exception as e:
                logger.error(f"[CUDA配置] 复制失败: {dll_name} - {e}")
                failed += 1
        
        logger.info(f"[CUDA配置] 复制完成: {copied} 成功, {failed} 失败")
        
        return copied > 0 and failed == 0
        
    except Exception as e:
        logger.error(f"[CUDA配置] 错误: {e}")
        return False


def show_install_progress_dialog(parent) -> bool:
    """
    显示配置进度对话框并执行 CUDA DLL 复制
    
    Args:
        parent: 父窗口
        
    Returns:
        bool: 是否配置成功
    """
    logger = logging.getLogger('MEMEFinder')
    
    # 获取 CUDA 路径
    cuda_path = os.environ.get('CUDA_PATH', '')
    
    if not cuda_path:
        messagebox.showerror(
            "错误",
            "未设置 CUDA 路径！\n\n请先使用 '设置 CUDA 路径' 按钮配置 CUDA 安装位置。",
            parent=parent
        )
        return False
    
    # 创建进度对话框
    dialog = tk.Toplevel(parent)
    dialog.title("配置GPU加速")
    dialog.geometry("400x150")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # 居中显示
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
    y = (dialog.winfo_screenheight() // 2) - (150 // 2)
    dialog.geometry(f"400x150+{x}+{y}")
    
    # 进度信息
    ttk.Label(
        dialog,
        text="正在复制 CUDA DLL 文件...",
        font=("Arial", 11)
    ).pack(pady=20)
    
    progress = ttk.Progressbar(
        dialog,
        mode='indeterminate',
        length=300
    )
    progress.pack(pady=10)
    progress.start(10)
    
    status_label = ttk.Label(dialog, text="请稍候...")
    status_label.pack(pady=10)
    
    result = {'success': False}
    
    def do_copy():
        try:
            success = copy_cuda_dlls(cuda_path)
            result['success'] = success
            
            # 在主线程中关闭对话框
            dialog.after(0, dialog.destroy)
            
            # 显示结果
            if success:
                dialog.after(100, lambda: messagebox.showinfo(
                    "成功",
                    "GPU加速已配置完成！\n\n现在可以启用GPU加速选项了。",
                    parent=parent
                ))
            else:
                dialog.after(100, lambda: messagebox.showerror(
                    "失败",
                    "CUDA DLL 复制失败。\n\n请检查 CUDA 路径是否正确。",
                    parent=parent
                ))
        except Exception as e:
            logger.error(f"[CUDA配置] 配置过程出错: {e}")
            result['success'] = False
            dialog.after(0, dialog.destroy)
            dialog.after(100, lambda: messagebox.showerror(
                "错误",
                f"配置过程出错:\n{e}",
                parent=parent
            ))
    
    # 在后台线程执行复制
    import threading
    thread = threading.Thread(target=do_copy, daemon=True)
    thread.start()
    
    # 等待对话框关闭
    dialog.wait_window()
    
    return result['success']


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()
    
    print(f"onnxruntime-gpu已安装: {check_onnxruntime_gpu_installed()}")
    
    if show_install_dialog(root):
        print("用户确认配置")
        show_install_progress_dialog(root)
    else:
        print("用户取消配置")
