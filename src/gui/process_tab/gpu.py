#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProcessTab GPU管理模块
负责GPU状态检测、安装和配置
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class GPUManager:
    """GPU管理器"""
    
    def __init__(self, log_callback, ui_components, ocr_state):
        """
        初始化GPU管理器
        
        Args:
            log_callback: 日志记录回调函数
            ui_components: UI组件字典 {
                'gpu_checkbox': widget,
                'gpu_status_label': widget,
                'cuda_path_btn': widget,
                'gpu_enabled_var': var,
                'parent': parent_widget
            }
            ocr_state: OCR状态字典 {
                '_ocr_initialized': bool,
                'ocr_processor': processor,
                'set_ocr_state': callback(initialized, processor)
            }
        """
        self.log_message = log_callback
        self.ui = ui_components
        self.ocr_state = ocr_state
        
        self.gpu_info = None
        self.gpu_install_btn = None
        
    def check_gpu_status(self):
        """检查GPU状态并更新UI"""
        from ...utils.gpu_detector import get_gpu_recommendation
        
        # 获取详细的GPU状态
        self.gpu_info = get_gpu_recommendation()
        
        has_hw = self.gpu_info['has_hardware']
        has_ort_gpu = self.gpu_info['has_onnxruntime_gpu']
        device_info = self.gpu_info.get('device_info', '')
        
        # 更新UI状态
        if not has_hw:
            # 无GPU硬件
            self.ui['gpu_status_label'].config(text="GPU: 不可用", foreground="gray")
            self.ui['gpu_checkbox'].config(state="disabled")
            self.ui['gpu_enabled_var'].set(False)
            if self.gpu_install_btn:
                self.gpu_install_btn.pack_forget()
                
        elif has_hw and not has_ort_gpu:
            # 有硬件但未配置CUDA DLL
            self.ui['gpu_status_label'].config(text="GPU: 可用 (需配置)", foreground="#E6A23C")  # 橙色
            self.ui['gpu_checkbox'].config(state="normal")
            self.ui['gpu_enabled_var'].set(False)
            
            # 显示配置按钮
            if not self.gpu_install_btn:
                self.gpu_install_btn = ttk.Button(
                    self.ui['gpu_checkbox'].master,
                    text="⚙️ 配置CUDA",
                    command=self.prompt_configure_gpu,
                    style="Accent.TButton"  # 如果有自定义样式
                )
            self.gpu_install_btn.pack(side=tk.LEFT, padx=5)
        
            # 显示 CUDA 路径设置按钮（仅在有GPU硬件时）
            self.ui['cuda_path_btn'].pack(side=tk.LEFT, padx=5)
        
        else:
            # GPU可用且已配置CUDA DLL
            gpu_name = device_info.replace("CUDA GPU:", "").strip()
                
            self.ui['gpu_status_label'].config(text=f"GPU: {gpu_name} ✨", foreground="#67C23A")  # 绿色
            self.ui['gpu_checkbox'].config(state="normal")
            
            # 默认启用（如果之前没有保存过设置）
            self.ui['gpu_enabled_var'].set(True)
            
            if self.gpu_install_btn:
                self.gpu_install_btn.pack_forget()
            
            # GPU已配置，不显示CUDA路径设置按钮（已经默认不pack）

    def on_gpu_toggle(self):
        """GPU开关切换事件"""
        enabled = self.ui['gpu_enabled_var'].get()
        
        if enabled:
            # 检查是否真的可用
            if not self.gpu_info['has_onnxruntime_gpu']:
                # 提示配置
                self.prompt_configure_gpu()
                # 如果配置未完成，保持关闭状态
                if not self.gpu_info['has_onnxruntime_gpu']:
                    self.ui['gpu_enabled_var'].set(False)
                return
            
            self.log_message("[信息] GPU加速已启用")
        else:
            self.log_message("[信息] GPU加速已禁用")
            
        # 如果OCR处理器已初始化，需要重新初始化以应用更改
        if self.ocr_state['_ocr_initialized'] and self.ocr_state['ocr_processor']:
            self.log_message("[信息] OCR处理器设置已更改，将在下次处理时重新初始化")
            self.ocr_state['set_ocr_state'](False, None)

    def prompt_configure_gpu(self):
        """提示GPU加速（复制CUDA DLL）"""
        from ...utils.gpu_installer import show_install_dialog, show_install_progress_dialog
        
        # 显示配置确认对话框
        if show_install_dialog(self.ui['parent']):
            # 用户确认配置，显示进度对话框并执行配置
            success = show_install_progress_dialog(self.ui['parent'])
            
            if success:
                # 重新检查状态
                self.check_gpu_status()
                # 自动启用
                if self.gpu_info['has_onnxruntime_gpu']:
                    self.ui['gpu_enabled_var'].set(True)
                    self.log_message("[成功] GPU加速已配置并启用！")
    
    def configure_cuda_path(self):
        """配置 CUDA 路径"""
        from ...utils.cuda_validator import validate_cuda_path
        from ...utils.cuda_finder import find_cuda_installation
        
        # 获取默认CUDA路径（从环境变量）
        default_cuda_path = os.environ.get('CUDA_PATH', '')
        if not default_cuda_path:
            # 尝试自动查找
            auto_found = find_cuda_installation()
            if auto_found:
                default_cuda_path = auto_found
            else:
                default_cuda_path = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA"
        
        # 让用户选择CUDA路径
        cuda_path = filedialog.askdirectory(
            title="选择 CUDA Toolkit 安装目录",
            initialdir=default_cuda_path
        )
        
        if not cuda_path:
            return

        # 规范化路径分隔符
        cuda_path = os.path.normpath(cuda_path)

        self.log_message(f"[信息] 正在验证 CUDA 路径: {cuda_path}")
        
        # 使用完整的验证器进行验证
        validation_result = validate_cuda_path(cuda_path)
        
        if not validation_result['valid']:
            # 验证失败，显示详细错误信息
            messagebox.showerror(
                "CUDA 路径验证失败",
                validation_result['message']
            )
            self.log_message(f"[错误] CUDA 路径验证失败: {validation_result['message']}")
            return
        
        # 验证成功
        dll_count = len(validation_result['dlls'])
        dll_list = '\n  - '.join([name for name, _ in validation_result['dlls']])
        
        self.log_message(f"[成功] {validation_result['message']}")
        self.log_message(f"[信息] 找到 {dll_count} 个必需的 DLL 文件:")
        self.log_message(f"  - {dll_list}")
        
        # 设置环境变量，供安装函数读取
        os.environ['CUDA_PATH'] = cuda_path
        self.log_message(f"[信息] 已设置 CUDA_PATH 环境变量")
        
        # 询问用户是否继续配置
        if messagebox.askyesno(
            "CUDA 验证成功",
            f"CUDA 路径验证成功！\n\n"
            f"版本: {validation_result['cuda_version']}\n"
            f"找到 {dll_count} 个 DLL 文件\n\n"
            f"是否继续配置 GPU 加速支持？"
        ):
            # 立即调用配置
            self.prompt_configure_gpu()
