#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理标签页 - 重构版本
使用模块化设计,将功能拆分为多个独立模块
"""

import tkinter as tk
import threading
from datetime import datetime
from typing import Optional

from ..core.database import ImageDatabase
from ..utils.logger import get_logger

# 导入重构后的模块
from .process_tab_ui import ProcessTabUI
from .process_tab_models import ModelManager
from .process_tab_gpu import GPUManager
from .process_tab_processor import ImageProcessor

logger = get_logger()


class ProcessTab:
    """图片处理标签页 - 协调器"""
    
    def __init__(self, parent, db: ImageDatabase, stats_callback=None):
        self.parent = parent
        self.db = db
        self.stats_callback = stats_callback
        
        # 处理状态
        self.processing = False
        self.processing_thread = None
        
        # 创建主框架
        self.frame = tk.Frame(parent)
        
        # 初始化UI模块
        self.ui = ProcessTabUI(self.frame)
        
        # 准备回调函数
        callbacks = {
            'start_processing': self.start_processing,
            'pause_processing': self.pause_processing,
            'stop_processing': self.stop_processing,
            'check_model_status': self._check_model_status,
            'on_ocr_toggle': self._on_ocr_toggle,
            'on_sentiment_toggle': self._on_sentiment_toggle,
            'on_gpu_toggle': self._on_gpu_toggle,
            'configure_cuda_path': self._configure_cuda_path,
            'download_ocr_models': self._download_ocr_models,
            'download_sentiment_model': self._download_sentiment_model
        }
        
        initial_values = {
            'max_workers': 2,  # 降低默认线程数，减少CPU和内存压力
            'use_multithread': True
        }
        
        # 创建所有UI组件
        self.ui.create_all_widgets(callbacks, initial_values)
        
        # 初始化模型管理器
        ui_vars = {
            'enable_ocr_var': self.ui.enable_ocr_var,
            'enable_sentiment_var': self.ui.enable_sentiment_var
        }
        self.model_manager = ModelManager(self.log_message, ui_vars)
        
        # 初始化GPU管理器
        gpu_ui_components = {
            'gpu_checkbox': self.ui.gpu_checkbox,
            'gpu_status_label': self.ui.gpu_status_label,
            'cuda_path_btn': self.ui.cuda_path_btn,
            'gpu_enabled_var': self.ui.gpu_enabled_var,
            'parent': self.parent
        }
        
        ocr_state = {
            '_ocr_initialized': False,
            'ocr_processor': None,
            'set_ocr_state': self._set_ocr_state
        }
        
        self.gpu_manager = GPUManager(self.log_message, gpu_ui_components, ocr_state)
        
        # 初始化图片处理器
        ui_updaters = {
            'progress': lambda v: self.frame.after(0, lambda: self.ui.progress_var.set(v)),
            'progress_label': lambda t: self.frame.after(0, lambda: self.ui.progress_label.config(text=t)),
            'stats': self._update_stats
        }
        
        processor_ui_vars = {
            'enable_ocr_var': self.ui.enable_ocr_var,
            'enable_sentiment_var': self.ui.enable_sentiment_var,
            'gpu_enabled_var': self.ui.gpu_enabled_var
        }
        
        self.processor = ImageProcessor(self.db, self.log_message, ui_updaters, processor_ui_vars)
        
        # 检查GPU状态
        self.gpu_manager.check_gpu_status()
        
        # 同步OCR状态
        self._sync_ocr_state()
    
    def _set_ocr_state(self, initialized, processor):
        """设置OCR状态(供GPU管理器调用)"""
        self.processor._ocr_initialized = initialized
        self.processor.ocr_processor = processor
        self.model_manager._ocr_initialized = initialized
        self.model_manager.ocr_processor = processor
    
    def _sync_ocr_state(self):
        """同步OCR状态到GPU管理器"""
        self.gpu_manager.ocr_state['_ocr_initialized'] = self.processor._ocr_initialized
        self.gpu_manager.ocr_state['ocr_processor'] = self.processor.ocr_processor
    
    def _update_stats(self):
        """更新统计信息"""
        if self.stats_callback:
            try:
                self.frame.after(0, self.stats_callback)
            except Exception:
                pass
    
    # 委托给模型管理器的方法
    def _check_model_status(self):
        self.model_manager.check_model_status()
    
    def _on_ocr_toggle(self):
        self.model_manager.on_ocr_toggle()
    
    def _on_sentiment_toggle(self):
        self.model_manager.on_sentiment_toggle()
    
    def _download_ocr_models(self):
        self.model_manager.download_ocr_models()
    
    def _download_sentiment_model(self):
        self.model_manager.download_sentiment_model()
    
    # 委托给GPU管理器的方法
    def _on_gpu_toggle(self):
        self.gpu_manager.on_gpu_toggle()
        self._sync_ocr_state()
    
    def _configure_cuda_path(self):
        self.gpu_manager.configure_cuda_path()
    
    # 处理控制方法
    def start_processing(self):
        """开始处理图片"""
        if self.processing:
            from tkinter import messagebox
            messagebox.showinfo("提示", "正在处理中...")
            return
        
        unprocessed = self.db.get_unprocessed_images(limit=1)
        if not unprocessed:
            from tkinter import messagebox
            messagebox.showinfo("提示", "没有待处理的图片")
            return
        
        # 检查模型状态并让用户确认
        if not self._check_and_confirm_models():
            return
        
        # 标记应用状态
        try:
            self.db.set_app_state('processing_state', 'running')
        except Exception:
            pass
         
        self.processing = True
        self.processor.processing = True
        self.log_message("=" * 50)
        self.log_message("开始处理图片...")
        
        # 如果OCR未初始化，提示用户后台加载中
        if not self.processor._ocr_initialized:
            self.log_message("[提示] 正在后台加载OCR模型，请稍候...")
            self.log_message("[提示] 首次加载需要5-10秒，请耐心等待")
        
        self.log_message("=" * 50)
        
        # 在单独线程中处理（OCR初始化也在线程中）
        self.processing_thread = threading.Thread(target=self._process_images_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _check_and_confirm_models(self):
        """
        检查模型状态并让用户确认
        
        Returns:
            bool: 用户是否确认开始处理
        """
        from tkinter import messagebox
        from ..utils.model_manager import get_model_manager
        
        try:
            model_manager = get_model_manager()
            
            # 检查OCR模型
            ocr_exists, ocr_missing = model_manager.check_ocr_models()
            
            # 检查情感分析模型
            sentiment_installed, sentiment_name = model_manager.check_sentiment_model()
            
            # 获取当前设置
            enable_ocr = self.ui.enable_ocr_var.get()
            enable_sentiment = self.ui.enable_sentiment_var.get()
            
            # 构建状态信息
            issues = []
            warnings = []
            
            # 检查OCR状态
            if enable_ocr and not ocr_exists:
                issues.append(f"❌ OCR模型未安装\n   缺失: {', '.join(ocr_missing)}")
            elif enable_ocr:
                warnings.append("✅ OCR模型已安装")
            else:
                warnings.append("⚠ OCR功能已禁用")
            
            # 检查情感分析状态  
            if enable_sentiment and not sentiment_installed:
                warnings.append("⚠ 情感分析模型未安装，将使用关键词匹配")
            elif enable_sentiment:
                warnings.append(f"✅ 情感分析已启用 ({sentiment_name})")
            else:
                warnings.append("⚠ 情感分析已禁用")
            
            # 如果有严重问题，拒绝开始
            if issues:
                message = "无法开始处理，存在以下问题:\n\n" + "\n\n".join(issues)
                message += "\n\n请先下载缺失的模型。"
                messagebox.showerror("模型检查失败", message)
                return False
            
            # 显示确认对话框
            total_images = len(self.db.get_unprocessed_images(limit=10000))
            message = f"准备处理 {total_images} 张图片\n\n当前模型状态:\n\n"
            message += "\n".join(warnings)
            message += "\n\n是否开始处理？"
            
            result = messagebox.askyesno("确认开始处理", message, icon='question')
            
            if result:
                self.log_message("=" * 50)
                self.log_message("[确认] 用户已确认开始处理")
                for msg in warnings:
                    self.log_message(f"  {msg}")
                self.log_message("=" * 50)
            else:
                self.log_message("[取消] 用户取消了处理操作")
            
            return result
            
        except Exception as e:
            logger.error(f"模型状态检查失败: {e}")
            # 如果检查失败，询问用户是否继续
            result = messagebox.askyesno(
                "模型检查异常",
                f"模型状态检查时出现异常:\n{str(e)}\n\n是否继续处理？",
                icon='warning'
            )
            return result
    
    def pause_processing(self):
        """暂停处理"""
        if self.processing:
            self.processing = False
            self.processor.processing = False
            self.log_message("[暂停] 处理已暂停")
            try:
                self.db.set_app_state('processing_state', 'paused')
            except Exception:
                pass
     
    def stop_processing(self):
        """停止处理"""
        if self.processing:
            self.processing = False
            self.processor.processing = False
            self.log_message("[停止] 处理已停止")
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
    
    def _process_images_thread(self):
        """处理图片的线程"""
        try:
            # 在后台线程中初始化OCR（如果需要）
            if not self.processor._ocr_initialized:
                # 更新UI显示"正在加载模型"
                self.frame.after(0, lambda: self.ui.progress_label.config(text="正在加载OCR模型，请稍候..."))
                self.frame.after(0, lambda: self.ui.progress_var.set(5))
                
                self.log_message("[INFO] 后台初始化OCR处理器...")
                if not self.processor.initialize_ocr():
                    self.log_message("[错误] OCR初始化失败，无法继续处理")
                    self.processing = False
                    self.processor.processing = False
                    self.frame.after(0, lambda: self.ui.progress_label.config(text="OCR初始化失败"))
                    self.frame.after(0, lambda: self.ui.progress_var.set(0))
                    try:
                        self.db.set_app_state('processing_state', 'idle')
                    except Exception:
                        pass
                    return
                
                # 初始化完成，更新UI
                self.frame.after(0, lambda: self.ui.progress_label.config(text="OCR模型加载完成"))
                self.frame.after(0, lambda: self.ui.progress_var.set(10))
            
            unprocessed = self.db.get_unprocessed_images(limit=10000)
            
            if not unprocessed:
                self.log_message("[INFO] 没有待处理的图片")
                self.processing = False
                self.processor.processing = False
                return
            
            total = len(unprocessed)
            
            # 读取用户设置
            max_workers = self.ui.get_thread_count()
            max_workers = max(1, min(16, max_workers))
            use_multithread = self.ui.get_multithread_enabled()
            
            if use_multithread and max_workers > 1:
                self.log_message(f"[INFO] 使用多线程模式，{max_workers} 个并行工作线程")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self.processor.process_images_multithread(unprocessed, max_workers, self._finish_processing)
            else:
                self.log_message(f"[INFO] 使用单线程模式")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self.processor.process_images_singlethread(unprocessed, self._finish_processing)
            
        except Exception as e:
            self.processing = False
            self.processor.processing = False
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
            error_msg = f"处理线程异常: {e}"
            self.log_message(f"[错误] {error_msg}")
            logger.error(error_msg)
            import traceback
            traceback_str = traceback.format_exc()
            self.log_message(traceback_str)
            logger.debug(traceback_str)
    
    def _finish_processing(self, processed_count, error_count):
        """完成处理的收尾工作"""
        self.processing = False
        self.processor.processing = False
        try:
            self.db.set_app_state('processing_state', 'idle')
        except Exception:
            pass
        
        # 清理数据库缓存
        try:
            # ImageDatabase使用conn而不是connection
            if hasattr(self.db, 'conn'):
                self.db.conn.commit()  # 确保所有更改已写入
                logger.info("数据库缓存已清理")
        except Exception as e:
            logger.warning(f"清理数据库缓存失败: {e}")
        
        # 最后一次更新统计信息
        self._update_stats()
        
        # 更新UI
        self.frame.after(0, lambda: self.ui.progress_var.set(100))
        self.frame.after(0, lambda: self.ui.progress_label.config(
            text=f"处理完成: 成功 {processed_count}, 失败 {error_count}"))
        self.log_message("=" * 50)
        self.log_message(f"[完成] 处理结束")
        self.log_message(f"  成功: {processed_count} 张")
        self.log_message(f"  失败: {error_count} 张")
        self.log_message("=" * 50)
    
    def log_message(self, message: str):
        """添加日志消息(线程安全)"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            
            # 插入日志
            self.ui.log_text.insert(tk.END, log_line)
            
            # 限制日志大小：保留最近500行
            try:
                line_count = int(self.ui.log_text.index('end-1c').split('.')[0])
                if line_count > 500:
                    # 删除前100行
                    self.ui.log_text.delete('1.0', '101.0')
            except Exception as e:
                logger.debug(f"清理日志时出错: {e}")
            
            self.ui.log_text.see(tk.END)
        
        try:
            self.frame.after(0, _log)
        except:
            try:
                _log()
            except:
                pass
