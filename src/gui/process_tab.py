#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理标签页
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from pathlib import Path
import threading
import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

from ..core.database import ImageDatabase
from ..core.ocr_processor import OCRProcessor
from ..utils.logger import get_logger

logger = get_logger()


class ProcessTab:
    """图片处理标签页"""
    
    def __init__(self, parent, db: ImageDatabase, stats_callback=None):
        self.parent = parent
        self.db = db
        self.stats_callback = stats_callback  # 用于更新统计信息的回调函数
        
        # OCR处理器（延迟初始化）
        self.ocr_processor: Optional[OCRProcessor] = None
        self._ocr_initialized = False
        
        # 处理状态
        self.processing = False
        self.processing_thread = None
        
        # 多线程配置
        self.max_workers = 4  # 默认4个工作线程
        self.use_multithread = True  # 是否启用多线程
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def _should_use_gpu(self) -> bool:
        """
        检查是否应该使用GPU
        
        优先级：
        1. 环境变量 MEMEFINDER_USE_GPU (1/true/yes 启用，0/false/no 禁用)
        2. 自动检测GPU是否可用
        
        Returns:
            bool: 是否使用GPU
        """
        from ..utils.gpu_detector import should_use_gpu
        return should_use_gpu()
    
    def create_widgets(self):
        """创建界面组件"""
        # 顶部按钮区
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 第一行：基本控制按钮
        control_row1 = ttk.Frame(btn_frame)
        control_row1.pack(fill=tk.X, pady=2)
        
        ttk.Button(control_row1, text="▶️ 开始处理", 
                  command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row1, text="⏸️ 暂停", 
                  command=self.pause_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row1, text="⏹️ 停止", 
                  command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        
        # 多线程设置
        thread_frame = ttk.Frame(control_row1)
        thread_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(thread_frame, text="并行线程数:").pack(side=tk.LEFT, padx=5)
        self.thread_spinbox = ttk.Spinbox(thread_frame, from_=1, to=16, width=5)
        self.thread_spinbox.set(self.max_workers)
        self.thread_spinbox.pack(side=tk.LEFT, padx=5)
        
        self.multithread_var = tk.BooleanVar(value=self.use_multithread)
        ttk.Checkbutton(thread_frame, text="启用多线程", 
                       variable=self.multithread_var).pack(side=tk.LEFT, padx=5)
        
        # 第二行：模型管理按钮
        control_row2 = ttk.Frame(btn_frame)
        control_row2.pack(fill=tk.X, pady=2)
        
        # 模型状态检查按钮
        ttk.Button(control_row2, text="🔍 检查模型状态", 
                  command=self.check_model_status).pack(side=tk.LEFT, padx=5)
        
        # OCR开关
        self.enable_ocr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_row2, text="启用OCR", 
                       variable=self.enable_ocr_var,
                       command=self.on_ocr_toggle).pack(side=tk.LEFT, padx=5)
        
        # 情感分析开关
        self.enable_sentiment_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_row2, text="启用情感分析", 
                       variable=self.enable_sentiment_var,
                       command=self.on_sentiment_toggle).pack(side=tk.LEFT, padx=5)
        
        # 下载模型按钮
        ttk.Button(control_row2, text="📥 下载OCR模型", 
                  command=self.download_ocr_models).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row2, text="📥 下载情感分析模型", 
                  command=self.download_sentiment_model).pack(side=tk.LEFT, padx=5)
        
        # 进度信息
        progress_frame = ttk.LabelFrame(self.frame, text="处理进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack()
        
        # 日志输出
        log_frame = ttk.LabelFrame(self.frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def on_ocr_toggle(self):
        """OCR开关切换事件"""
        enabled = self.enable_ocr_var.get()
        if enabled:
            # 检查OCR模型是否存在
            from ..utils.model_manager import get_model_manager
            model_manager = get_model_manager()
            all_exists, missing = model_manager.check_ocr_models()
            
            if not all_exists:
                self.log_message("[警告] OCR模型未下载，请先下载模型")
                self.log_message(f"[警告] 缺失模型: {', '.join(missing)}")
                messagebox.showwarning("警告", 
                    f"OCR模型未下载！\n\n缺失的模型:\n" + "\n".join(f"  - {m}" for m in missing) + 
                    f"\n\n模型目录: {model_manager.get_model_dir()}\n\n" +
                    "请点击\"下载OCR模型\"按钮获取下载说明。")
                self.enable_ocr_var.set(False)
                return
            
            self.log_message("[信息] OCR功能已启用")
        else:
            self.log_message("[信息] OCR功能已禁用")
    
    def on_sentiment_toggle(self):
        """情感分析开关切换事件"""
        enabled = self.enable_sentiment_var.get()
        if enabled:
            # 检查情感分析模型是否安装
            from ..utils.model_manager import get_model_manager
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
                    self.enable_sentiment_var.set(False)
                return
            
            self.log_message(f"[信息] 情感分析功能已启用 (使用 {model_name})")
        else:
            self.log_message("[信息] 情感分析功能已禁用")
    
    def download_ocr_models(self):
        """下载OCR模型"""
        from ..utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        # 检查是否已安装
        all_exists, missing = model_manager.check_ocr_models()
        if all_exists:
            messagebox.showinfo("提示", "OCR模型已存在，无需下载！")
            return
        
        # 询问用户是否开始下载
        model_dir = model_manager.get_model_dir()
        result = messagebox.askyesno("确认下载", 
            f"将从rapidocr_onnxruntime包自动复制OCR模型到:\n{model_dir}\n\n"
            f"缺失的模型:\n" + "\n".join(f"  - {m}" for m in missing) + "\n\n"
            "是否开始下载？")
        
        if not result:
            return
        
        self.log_message("=" * 50)
        self.log_message("[下载] 开始下载OCR模型...")
        
        def download_progress(current, total, message):
            self.log_message(f"[下载] {message}")
        
        # 在后台线程中下载
        def download_thread():
            success = model_manager.download_ocr_models(download_progress)
            if success:
                self.log_message("[成功] OCR模型下载完成！")
                self.log_message("=" * 50)
                messagebox.showinfo("成功", "OCR模型下载成功！\n可以启用OCR功能了。")
                # 如果下载成功，自动启用OCR
                self.enable_ocr_var.set(True)
            else:
                self.log_message("[失败] OCR模型下载失败")
                self.log_message("=" * 50)
                messagebox.showerror("失败", 
                    "OCR模型下载失败！\n\n"
                    "可能的原因:\n"
                    "1. 未安装rapidocr_onnxruntime包\n"
                    "2. rapidocr_onnxruntime包中缺少模型文件\n\n"
                    "请查看处理日志获取详细信息。")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_sentiment_model(self):
        """下载/安装情感分析模型"""
        from ..utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        # 检查是否已安装
        installed, model_name = model_manager.check_sentiment_model()
        if installed:
            messagebox.showinfo("提示", f"情感分析模型已安装 ({model_name})！")
            return
        
        self.log_message("[信息] 开始安装 SnowNLP...")
        
        def install_progress(current, total, message):
            self.log_message(f"[安装] {message}")
        
        # 在后台线程中安装
        def install_thread():
            success = model_manager.install_sentiment_model(install_progress)
            if success:
                self.log_message("[成功] SnowNLP 安装成功！")
                messagebox.showinfo("成功", "SnowNLP 安装成功！")
            else:
                self.log_message("[失败] SnowNLP 安装失败")
                messagebox.showerror("失败", "SnowNLP 安装失败，请查看日志")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def check_model_status(self):
        """检查模型状态"""
        from ..utils.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        self.log_message("=" * 50)
        self.log_message("[状态检查] 正在检查模型状态...")
        
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
        
        # 显示状态报告
        self.log_message(status_report)
        self.log_message("=" * 50)
        
        # 弹窗显示简洁版本
        summary = f"""模型状态:\n
OCR模型: {'✅ 已安装' if ocr_exists else '❌ 未安装'}
情感分析: {'✅ 已安装 (' + sentiment_name + ')' if sentiment_installed else '❌ 未安装'}

模型目录: {model_dir}

详细信息请查看处理日志。"""
        
        messagebox.showinfo("模型状态", summary)
    
    def _initialize_ocr(self):
        """初始化OCR处理器（如果尚未初始化）"""
        if self._ocr_initialized and self.ocr_processor:
            return True
        
        # 如果没有预加载的实例，则现在加载
        if self.ocr_processor is None:
            try:
                self.log_message("[INFO] 正在初始化 OCR 处理器（延迟加载模式）...")
                from pathlib import Path
                from ..utils.model_manager import get_model_manager
                
                # 使用模型管理器获取模型目录
                model_manager = get_model_manager()
                model_dir = model_manager.get_model_dir()
                
                # 使用延迟加载模式初始化OCR处理器
                self.ocr_processor = OCRProcessor(
                    use_gpu=None, 
                    model_dir=model_dir, 
                    lazy_load=True,  # 启用延迟加载
                    use_senta=self.enable_sentiment_var.get()  # 根据用户设置启用情感分析
                )
                self._ocr_initialized = True
                self.log_message("[INFO] OCR 处理器初始化完成（延迟加载模式）")
                self.log_message("[INFO] OCR模型将在首次使用时加载")
                return True
            except Exception as e:
                error_msg = f"OCR 初始化失败: {e}"
                self.log_message(f"[错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                logger.debug(traceback.format_exc())
                messagebox.showerror("错误", error_msg)
                return False
        else:
            # 已经有预加载的实例
            self._ocr_initialized = True
            self.log_message("[INFO] 使用预加载的 OCR 处理器")
            return True
    
    def start_processing(self):
        """开始处理图片"""
        if self.processing:
            messagebox.showinfo("提示", "正在处理中...")
            return
        
        unprocessed = self.db.get_unprocessed_images(limit=1)
        if not unprocessed:
            messagebox.showinfo("提示", "没有待处理的图片")
            return
        
        # 首次运行时初始化OCR
        if not self._ocr_initialized:
            if not self._initialize_ocr():
                return  # 初始化失败，不继续处理
        
        # 标记应用状态为正在运行（用于断点恢复）
        try:
            self.db.set_app_state('processing_state', 'running')
        except Exception:
            pass
         
        self.processing = True
        self.log_message("=" * 50)
        self.log_message("开始处理图片...")
        self.log_message("=" * 50)
        
        # 在单独线程中处理
        self.processing_thread = threading.Thread(target=self.process_images_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def pause_processing(self):
        """暂停处理"""
        if self.processing:
            self.processing = False
            self.log_message("[暂停] 处理已暂停")
            try:
                self.db.set_app_state('processing_state', 'paused')
            except Exception:
                pass
     
    def stop_processing(self):
        """停止处理"""
        if self.processing:
            self.processing = False
            self.log_message("[停止] 处理已停止")
            try:
                self.db.set_app_state('processing_state', 'idle')
            except Exception:
                pass
    
    def process_images_thread(self):
        """处理图片的线程"""
        try:
            # 获取未处理的图片
            unprocessed = self.db.get_unprocessed_images(limit=10000)
            
            if not unprocessed:
                self.log_message("[INFO] 没有待处理的图片")
                self.processing = False
                return
            
            total = len(unprocessed)
            
            # 读取用户设置的线程数
            try:
                max_workers = int(self.thread_spinbox.get())
                max_workers = max(1, min(16, max_workers))  # 限制在1-16之间
            except:
                max_workers = self.max_workers
            
            use_multithread = self.multithread_var.get()
            
            if use_multithread and max_workers > 1:
                self.log_message(f"[INFO] 使用多线程模式，{max_workers} 个并行工作线程")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self._process_images_multithread(unprocessed, max_workers)
            else:
                self.log_message(f"[INFO] 使用单线程模式")
                self.log_message(f"[INFO] 开始处理 {total} 张图片...")
                self._process_images_singlethread(unprocessed)
            
        except Exception as e:
            self.processing = False
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
    
    def _process_single_image(self, img_info):
        """处理单张图片的工作函数"""
        img_id = img_info['id']
        img_path = img_info['file_path']
        
        try:
            # 检查文件是否存在
            if not Path(img_path).exists():
                return {
                    'success': False,
                    'id': img_id,
                    'path': img_path,
                    'error': '文件不存在'
                }
            
            # 检查是否启用OCR
            enable_ocr = self.enable_ocr_var.get()
            enable_sentiment = self.enable_sentiment_var.get()
            
            if not enable_ocr:
                # 如果OCR未启用，直接返回空结果
                self.db.update_image_data(
                    image_id=img_id,
                    ocr_text='',
                    filtered_text='',
                    emotion='未处理',
                    pos_score=0.0,
                    neg_score=0.0
                )
                return {
                    'success': True,
                    'id': img_id,
                    'path': img_path,
                    'result': {
                        'ocr_text': '',
                        'filtered_text': '',
                        'emotion': '未处理',
                        'emotion_positive': 0.0,
                        'emotion_negative': 0.0
                    }
                }
            
            # OCR识别和情绪分析
            assert self.ocr_processor is not None, "OCR处理器未初始化"
            
            # 如果禁用情感分析，临时修改ocr_processor的设置
            if not enable_sentiment:
                # 保存原始设置
                original_use_senta = self.ocr_processor._use_senta
                # 临时禁用情感分析
                self.ocr_processor._use_senta = False
                
                try:
                    result = self.ocr_processor.process_image(Path(img_path))
                finally:
                    # 恢复原始设置
                    self.ocr_processor._use_senta = original_use_senta
            else:
                result = self.ocr_processor.process_image(Path(img_path))
            
            # 更新数据库
            self.db.update_image_data(
                image_id=img_id,
                ocr_text=result['ocr_text'],
                filtered_text=result['filtered_text'],
                emotion=result['emotion'],
                pos_score=result['emotion_positive'],
                neg_score=result['emotion_negative']
            )
            
            return {
                'success': True,
                'id': img_id,
                'path': img_path,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': str(e)
            }
    
    def _process_images_multithread(self, unprocessed, max_workers):
        """多线程处理图片"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        # 用于跟踪任务提交和完成的计数器
        import threading
        progress_lock = threading.Lock()
        
        self.log_message("=" * 50)
        self.log_message(f"多线程处理模式: {max_workers} 个工作线程")
        self.log_message(f"待处理图片总数: {total}")
        self.log_message("=" * 50)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_img = {
                executor.submit(self._process_single_image, img_info): (idx, img_info)
                for idx, img_info in enumerate(unprocessed, 1)
            }
            
            self.log_message(f"已提交 {len(future_to_img)} 个处理任务到线程池")
            
            # 处理完成的任务
            for future in as_completed(future_to_img):
                if not self.processing:
                    self.log_message("[暂停] 处理已暂停，取消剩余任务...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                idx, img_info = future_to_img[future]
                img_path = img_info['file_path']
                
                try:
                    task_result = future.result()
                    
                    # 线程安全地更新计数器
                    with progress_lock:
                        if task_result['success']:
                            processed_count += 1
                        else:
                            error_count += 1
                        completed = processed_count + error_count
                    
                    # 更新进度
                    progress = (completed / total) * 100
                    self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                    self.frame.after(0, lambda t=f"正在处理: {completed}/{total} (成功:{processed_count}, 失败:{error_count})": 
                                    self.progress_label.config(text=t))
                    
                    if task_result['success']:
                        result = task_result['result']
                        
                        # 日志输出
                        filename = Path(img_path).name
                        self.log_message(f"[{completed}/{total}] ✓ {filename}")
                        if result['filtered_text']:
                            preview = result['filtered_text'][:50]
                            if len(result['filtered_text']) > 50:
                                preview += "..."
                            self.log_message(f"  文本: {preview}")
                            self.log_message(f"  情绪: {result['emotion']} (正:{result['emotion_positive']:.2f}, 负:{result['emotion_negative']:.2f})")
                        else:
                            self.log_message(f"  未识别到文本")
                    else:
                        error = task_result.get('error', '未知错误')
                        filename = Path(img_path).name
                        self.log_message(f"[{completed}/{total}] ✗ {filename}")
                        self.log_message(f"  错误: {error}")
                    
                    # 定期更新统计信息
                    if completed % 5 == 0 and self.stats_callback:
                        try:
                            self.frame.after(0, self.stats_callback)
                        except Exception:
                            pass
                    
                    # 每处理10张图片输出一次进度摘要
                    if completed % 10 == 0:
                        self.log_message(f"--- 进度: {completed}/{total} ({progress:.1f}%) | 成功: {processed_count} | 失败: {error_count} ---")
                    
                except Exception as e:
                    with progress_lock:
                        error_count += 1
                        completed = processed_count + error_count
                    
                    filename = Path(img_path).name
                    self.log_message(f"[{completed}/{total}] ✗ {filename}")
                    self.log_message(f"  异常: {str(e)}")
                    logger.error(f"处理图片失败 [{filename}]: {e}")
        
        # 完成处理
        self._finish_processing(processed_count, error_count)
    
    def _process_images_singlethread(self, unprocessed):
        """单线程处理图片（原有逻辑）"""
        total = len(unprocessed)
        processed_count = 0
        error_count = 0
        
        for idx, img_info in enumerate(unprocessed, 1):
            if not self.processing:
                self.log_message("[暂停] 处理已暂停")
                break
            
            img_id = img_info['id']
            img_path = img_info['file_path']
            
            try:
                # 更新进度
                progress = (idx / total) * 100
                self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                self.frame.after(0, lambda t=f"正在处理: {idx}/{total} - {Path(img_path).name}": 
                                self.progress_label.config(text=t))
                
                self.log_message(f"[{idx}/{total}] 处理: {Path(img_path).name}")
                
                # 检查文件是否存在
                if not Path(img_path).exists():
                    self.log_message(f"  [跳过] 文件不存在: {img_path}")
                    error_count += 1
                    continue
                
                # OCR识别和情绪分析
                assert self.ocr_processor is not None, "OCR处理器未初始化"
                result = self.ocr_processor.process_image(Path(img_path))
                
                # 更新数据库
                self.db.update_image_data(
                    image_id=img_id,
                    ocr_text=result['ocr_text'],
                    filtered_text=result['filtered_text'],
                    emotion=result['emotion'],
                    pos_score=result['emotion_positive'],
                    neg_score=result['emotion_negative']
                )
                
                # 更新统计信息
                if self.stats_callback:
                    try:
                        self.frame.after(0, self.stats_callback)
                    except Exception:
                        pass
                
                # 日志输出
                if result['filtered_text']:
                    self.log_message(f"  ✓ 识别文本: {result['filtered_text'][:50]}")
                    self.log_message(f"  ✓ 情绪分类: {result['emotion']} (正:{result['emotion_positive']:.2f}, 负:{result['emotion_negative']:.2f})")
                else:
                    self.log_message(f"  - 未识别到文本")
                
                processed_count += 1
                
            except Exception as e:
                error_msg = f"处理图片失败 [{Path(img_path).name}]: {e}"
                self.log_message(f"  [错误] {error_msg}")
                logger.error(error_msg)
                import traceback
                logger.debug(traceback.format_exc())
                error_count += 1
                continue
        
        # 完成处理
        self._finish_processing(processed_count, error_count)
    
    def _finish_processing(self, processed_count, error_count):
        """完成处理的收尾工作"""
        self.processing = False
        try:
            self.db.set_app_state('processing_state', 'idle')
        except Exception:
            pass
        
        # 最后一次更新统计信息
        if self.stats_callback:
            try:
                self.frame.after(0, self.stats_callback)
            except Exception:
                pass
        
        # 更新UI
        self.frame.after(0, lambda: self.progress_var.set(100))
        self.frame.after(0, lambda: self.progress_label.config(
            text=f"处理完成: 成功 {processed_count}, 失败 {error_count}"))
        self.log_message("=" * 50)
        self.log_message(f"[完成] 处理结束")
        self.log_message(f"  成功: {processed_count} 张")
        self.log_message(f"  失败: {error_count} 张")
        self.log_message("=" * 50)
    
    def log_message(self, message: str):
        """添加日志消息（线程安全）"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
        
        # 如果在主线程中，直接执行；否则使用 after 调度到主线程
        try:
            self.frame.after(0, _log)
        except:
            # 如果 after 失败，尝试直接执行（可能是在主线程中）
            try:
                _log()
            except:
                pass  # 静默失败，避免崩溃
