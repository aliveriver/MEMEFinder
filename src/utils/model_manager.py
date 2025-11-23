#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型管理器 - 负责模型的检查和下载
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import threading


class ModelManager:
    """模型管理器 - 处理模型下载和路径管理"""
    
    # OCR模型下载URLs
    OCR_MODEL_URLS = {
        'ch_PP-OCRv4_det_infer.onnx': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_infer.tar',
        'ch_PP-OCRv4_rec_infer.onnx': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar',
        'ch_ppocr_mobile_v2.0_cls_infer.onnx': 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar',
    }
    
    def __init__(self):
        """初始化模型管理器"""
        self.model_dir = self._get_model_directory()
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_model_directory(self) -> Path:
        """
        获取模型存储目录
        
        优先级:
        1. 打包后: 运行目录/_internal/models
        2. 开发环境: 项目根目录/models
        """
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            app_path = Path(sys.executable).parent
            internal_path = app_path / '_internal' / 'models'
            return internal_path
        else:
            # 开发环境
            project_root = Path(__file__).parent.parent.parent
            return project_root / 'models'
    
    def check_ocr_models(self) -> Tuple[bool, list]:
        """
        检查OCR模型是否已下载
        
        Returns:
            (是否全部存在, 缺失的模型列表)
        """
        required_models = [
            'ch_PP-OCRv4_det_infer.onnx',
            'ch_PP-OCRv4_rec_infer.onnx',
            'ch_ppocr_mobile_v2.0_cls_infer.onnx',
        ]
        
        missing = []
        for model_file in required_models:
            if not (self.model_dir / model_file).exists():
                missing.append(model_file)
        
        return len(missing) == 0, missing
    
    def check_sentiment_model(self) -> Tuple[bool, str]:
        """
        检查情感分析模型是否已安装
        
        Returns:
            (是否已安装, 模型名称)
        """
        try:
            import snownlp
            # 检查SnowNLP的情感分析模型
            snownlp_data = Path(snownlp.__file__).parent / 'sentiment'
            if snownlp_data.exists() and (snownlp_data / 'sentiment.marshal.3').exists():
                return True, 'SnowNLP'
        except ImportError:
            pass
        
        return False, ''
    
    def download_ocr_models(self, progress_callback=None) -> bool:
        """
        下载OCR模型（从rapidocr_onnxruntime包自动复制）
        
        Args:
            progress_callback: 进度回调函数 callback(current, total, message)
        
        Returns:
            是否下载成功
        """
        all_exists, missing = self.check_ocr_models()
        
        if all_exists:
            if progress_callback:
                progress_callback(1, 1, "OCR模型已存在")
            return True
        
        if progress_callback:
            progress_callback(0, len(missing), f"开始下载OCR模型，缺失{len(missing)}个文件...")
        
        try:
            # 尝试从rapidocr_onnxruntime包中复制模型
            import rapidocr_onnxruntime
            import shutil
            
            # 获取rapidocr_onnxruntime的安装路径
            rapidocr_path = Path(rapidocr_onnxruntime.__file__).parent
            source_model_dir = rapidocr_path / 'models'
            
            if not source_model_dir.exists():
                error_msg = f"未找到rapidocr_onnxruntime的models目录: {source_model_dir}"
                if progress_callback:
                    progress_callback(0, len(missing), error_msg)
                return False
            
            # 确保目标目录存在
            self.model_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制缺失的模型文件
            success_count = 0
            for i, model_name in enumerate(missing, 1):
                source_file = source_model_dir / model_name
                target_file = self.model_dir / model_name
                
                if source_file.exists():
                    if progress_callback:
                        progress_callback(i, len(missing), f"正在复制: {model_name}")
                    
                    shutil.copy2(source_file, target_file)
                    success_count += 1
                    
                    if progress_callback:
                        progress_callback(i, len(missing), f"✓ 已复制: {model_name}")
                else:
                    if progress_callback:
                        progress_callback(i, len(missing), f"✗ 源文件不存在: {model_name}")
            
            if success_count == len(missing):
                if progress_callback:
                    progress_callback(len(missing), len(missing), 
                                    f"OCR模型下载完成！成功复制{success_count}个文件")
                return True
            else:
                if progress_callback:
                    progress_callback(success_count, len(missing), 
                                    f"部分模型下载失败，成功{success_count}/{len(missing)}")
                return False
                
        except ImportError:
            error_msg = "未安装rapidocr_onnxruntime包，请先运行: pip install rapidocr_onnxruntime"
            if progress_callback:
                progress_callback(0, len(missing), error_msg)
            return False
        except Exception as e:
            error_msg = f"复制模型文件失败: {str(e)}"
            if progress_callback:
                progress_callback(0, len(missing), error_msg)
            return False
    
    def install_sentiment_model(self, progress_callback=None) -> bool:
        """
        安装情感分析模型
        
        Args:
            progress_callback: 进度回调函数 callback(current, total, message)
        
        Returns:
            是否安装成功
        """
        try:
            import subprocess
            
            if progress_callback:
                progress_callback(0, 1, "正在安装 SnowNLP...")
            
            # 尝试安装snownlp
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'snownlp'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(1, 1, "SnowNLP 安装成功")
                return True
            else:
                if progress_callback:
                    progress_callback(0, 1, f"安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(0, 1, f"安装失败: {str(e)}")
            return False
    
    def get_model_dir(self) -> Path:
        """获取模型目录路径"""
        return self.model_dir


# 全局单例
_model_manager_instance: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """获取模型管理器单例"""
    global _model_manager_instance
    if _model_manager_instance is None:
        _model_manager_instance = ModelManager()
    return _model_manager_instance
