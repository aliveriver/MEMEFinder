#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProcessTab 模型管理模块
负责OCR和情感分析模型的下载、检查和管理
"""

import threading
from tkinter import messagebox
from ...utils.logger import get_logger

logger = get_logger()


class ModelManager:
    """模型管理器"""
    
    def __init__(self, log_callback, ui_vars):
        """
        初始化模型管理器
        
        Args:
            log_callback: 日志记录回调函数
            ui_vars: UI变量字典 {'enable_ocr_var': var, ...}
        """
        self.log_message = log_callback
        self.ui_vars = ui_vars
        self._ocr_initialized = False
        self.ocr_processor = None
        
    def download_ocr_models(self):
        """下载OCR模型"""
        from ...utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        # 检查是否已安装
        all_exists, missing = model_manager.check_ocr_models()
        logger.info(f"OCR models check: all_exists={all_exists}, missing={missing}")
        if all_exists:
            self.log_message("[INFO] OCR模型已存在，无需下载")
            messagebox.showinfo("提示", "OCR模型已存在，无需下载！")
            return
        
        # 询问用户是否开始下载
        model_dir = model_manager.get_model_dir()
        result = messagebox.askyesno("确认下载", 
            f"将从rapidocr_onnxruntime包自动复制OCR模型到:\n{model_dir}\n\n"
            f"缺失的模型:\n" + "\n".join(f"  - {m}" for m in missing) + "\n\n"
            "是否开始下载？")
        
        if not result:
            self.log_message("[INFO] 用户取消了OCR模型下载")
            logger.info("User cancelled OCR model download")
            return
        
        self.log_message("=" * 50)
        self.log_message("[下载] 开始下载OCR模型...")
        self.log_message(f"[下载] 目标目录: {model_dir}")
        logger.info(f"Starting OCR model download to {model_dir}")
        
        def download_progress(current, total, message):
            self.log_message(f"[下载] {message}")
        
        # 在后台线程中下载
        def download_thread():
            success = model_manager.download_ocr_models(download_progress)
            if success:
                self.log_message("[成功] ✓ OCR模型下载完成！")
                self.log_message("=" * 50)
                logger.info("OCR models downloaded successfully")
                messagebox.showinfo("成功", "OCR模型下载成功！\n可以启用OCR功能了。")
                # 如果下载成功，自动启用OCR
                self.ui_vars['enable_ocr_var'].set(True)
            else:
                self.log_message("[失败] ✗ OCR模型下载失败")
                self.log_message("=" * 50)
                logger.error("OCR model download failed")
                messagebox.showerror("失败", 
                    "OCR模型下载失败！\n\n"
                    "可能的原因:\n"
                    "1. 未安装rapidocr_onnxruntime包\n"
                    "2. rapidocr_onnxruntime包中缺少模型文件\n\n"
                    "请查看处理日志获取详细信息。")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_sentiment_model(self):
        """下载/安装情感分析模型"""
        from ...utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        # 检查是否已安装
        installed, model_name = model_manager.check_sentiment_model()
        logger.info(f"Sentiment model check: installed={installed}, model={model_name}")
        if installed:
            self.log_message(f"[INFO] 情感分析模型已安装 ({model_name})")
            messagebox.showinfo("提示", f"情感分析模型已安装 ({model_name})！")
            return
        
        self.log_message("=" * 50)
        self.log_message("[信息] 开始安装 SnowNLP...")
        logger.info("Starting SnowNLP installation")
        
        def install_progress(current, total, message):
            self.log_message(f"[安装] {message}")
        
        # 在后台线程中安装
        def install_thread():
            success = model_manager.install_sentiment_model(install_progress)
            if success:
                self.log_message("[成功] ✓ SnowNLP 安装成功！")
                self.log_message("=" * 50)
                logger.info("SnowNLP installed successfully")
                messagebox.showinfo("成功", "SnowNLP 安装成功！")
            else:
                self.log_message("[失败] ✗ SnowNLP 安装失败")
                self.log_message("=" * 50)
                logger.error("SnowNLP installation failed")
                messagebox.showerror("失败", "SnowNLP 安装失败，请查看日志")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def check_model_status(self):
        """检查模型状态（异步执行，不阻塞UI）"""
        self.log_message("=" * 50)
        self.log_message("[状态检查] 正在后台检查模型状态...")
        logger.info("Starting async model status check")
        
        # 在后台线程中执行检查
        def check_thread():
            try:
                from ...utils.model_manager import get_model_manager
                model_manager = get_model_manager()
                
                # 检查OCR模型
                ocr_exists, ocr_missing = model_manager.check_ocr_models()
                
                # 检查情感分析模型
                sentiment_installed, sentiment_name = model_manager.check_sentiment_model()
                
                # 获取模型目录
                model_dir = model_manager.get_model_dir()
                
                # 构建状态报告
                status_report = f"""模型状态检查报告
    
模型存储目录:
{model_dir}

【OCR模型状态】
"""
                
                if ocr_exists:
                    status_report += "✅ OCR模型已安装\n"
                    status_report += "  - ch_PP-OCRv4_det_infer.onnx (检测模型)\n"
                    status_report += "  - ch_PP-OCRv4_rec_infer.onnx (识别模型)\n"
                    status_report += "  - ch_ppocr_mobile_v2.0_cls_infer.onnx (方向分类)\n"
                else:
                    status_report += "❌ OCR模型未完整安装\n"
                    status_report += f"  缺失的模型:\n"
                    for model in ocr_missing:
                        status_report += f"  - {model}\n"
                    status_report += "\n  建议：点击'下载OCR模型'按钮进行安装\n"
                
                status_report += "\n【情感分析模型状态】\n"
                
                if sentiment_installed:
                    status_report += f"✅ 情感分析模型已安装 ({sentiment_name})\n"
                else:
                    status_report += "❌ 情感分析模型未安装\n"
                    status_report += "  建议：点击'下载情感分析模型'按钮进行安装\n"
                
                status_report += "\n【OCR处理器状态】\n"
                if self._ocr_initialized and self.ocr_processor:
                    if hasattr(self.ocr_processor, '_ocr_loaded') and self.ocr_processor._ocr_loaded:
                        status_report += "✅ OCR处理器已加载并就绪\n"
                    else:
                        status_report += "⏳ OCR处理器已初始化（延迟加载模式，将在首次使用时加载）\n"
                else:
                    status_report += "❌ OCR处理器未初始化\n"
                
                # 在主线程中显示结果
                self.log_message(status_report)
                self.log_message("=" * 50)
                logger.info("Model status check completed")
                
                # 弹窗显示简洁版本
                summary = f"""模型状态:\n
OCR模型: {'✅ 已安装' if ocr_exists else '❌ 未安装'}
情感分析: {'✅ 已安装 (' + sentiment_name + ')' if sentiment_installed else '❌ 未安装'}

模型目录: {model_dir}

详细信息请查看处理日志。"""
                
                messagebox.showinfo("模型状态", summary)
                
            except Exception as e:
                error_msg = f"模型状态检查失败: {e}"
                self.log_message(f"[错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                logger.debug(traceback.format_exc())
                messagebox.showerror("错误", f"模型状态检查失败:\n{str(e)}")
        
        # 启动后台线程（daemon线程，不阻塞程序退出）
        threading.Thread(target=check_thread, daemon=True).start()
    
    def on_ocr_toggle(self):
        """OCR开关切换事件"""
        enabled = self.ui_vars['enable_ocr_var'].get()
        if enabled:
            # 检查OCR模型是否存在
            from ...utils.model_manager import get_model_manager
            model_manager = get_model_manager()
            all_exists, missing = model_manager.check_ocr_models()
            
            if not all_exists:
                self.log_message("[警告] OCR模型未下载，请先下载模型")
                self.log_message(f"[警告] 缺失模型: {', '.join(missing)}")
                messagebox.showwarning(
                    "警告",
                    f"OCR模型未下载！\n\n"
                    f"缺失的模型:\n" + "\n".join(f"  - {m}" for m in missing) + "\n\n"
                    f"模型目录: {model_manager.get_model_dir()}\n\n"
                    "请点击“下载OCR模型”按钮获取下载说明。"
                )
                self.ui_vars['enable_ocr_var'].set(False)
                return
            
            self.log_message("[信息] ✓ OCR功能已启用")
            logger.info("OCR enabled")
        else:
            self.log_message("[信息] OCR功能已禁用")
            logger.info("OCR disabled")
    
    def on_sentiment_toggle(self):
        """情感分析开关切换事件"""
        enabled = self.ui_vars['enable_sentiment_var'].get()
        if enabled:
            # 检查情感分析模型是否安装
            from ...utils.model_manager import get_model_manager
            model_manager = get_model_manager()
            installed, model_name = model_manager.check_sentiment_model()
            
            if not installed:
                self.log_message("[警告] 情感分析模型未安装")
                result = messagebox.askyesno("提示", 
                    "情感分析模型（SnowNLP）未安装！\n\n" +
                    "是否现在安装？")
                if result:
                    self.download_sentiment_model()
                else:
                    self.ui_vars['enable_sentiment_var'].set(False)
                return
            
            self.log_message(f"[信息] ✓ 情感分析功能已启用 (使用 {model_name})")
            logger.info(f"Sentiment analysis enabled using {model_name}")
        else:
            self.log_message("[信息] 情感分析功能已禁用")
            logger.info("Sentiment analysis disabled")
