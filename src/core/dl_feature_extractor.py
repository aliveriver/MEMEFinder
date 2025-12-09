#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
深度学习特征提取模块 - 基于MobileNetV3-Small的图像特征提取

使用轻量级MobileNetV3-Small模型（~2MB）提取图像的语义特征向量，
相比传统的pHash和直方图方法，能够更好地捕捉图像的语义信息。
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import onnxruntime as ort
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class DLFeatureExtractor:
    """深度学习特征提取器（基于MobileNetV3-Small）"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化特征提取器
        
        Args:
            model_path: ONNX模型路径，如果为None则使用默认路径
        """
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_name = None
        self.feature_dim = None  # 自动检测特征维度
        self.model_type = "unknown"  # 模型类型：mobilenet/squeezenet/resnet等
        
    def load_model(self, model_path: Path) -> bool:
        """
        加载ONNX模型
        
        Args:
            model_path: ONNX模型文件路径
            
        Returns:
            是否加载成功
        """
        try:
            if not model_path.exists():
                logger.error(f"模型文件不存在: {model_path}")
                return False
            
            # 创建ONNX Runtime会话
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # 尝试使用GPU，失败则使用CPU
            providers = ['CPUExecutionProvider']
            try:
                if 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.insert(0, 'CUDAExecutionProvider')
            except:
                pass
            
            self.session = ort.InferenceSession(
                str(model_path),
                sess_options=sess_options,
                providers=providers
            )
            
            # 获取输入输出名称
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            
            # 自动检测特征维度和模型类型
            output_shape = self.session.get_outputs()[0].shape
            logger.info(f"  输出形状: {output_shape}")
            
            # 检测模型类型
            if 'mobilenet' in str(model_path).lower():
                self.model_type = 'mobilenet'
            elif 'squeezenet' in str(model_path).lower():
                self.model_type = 'squeezenet'
            elif 'resnet' in str(model_path).lower():
                self.model_type = 'resnet'
            else:
                self.model_type = 'unknown'
            
            logger.info(f"  模型类型: {self.model_type}")
            
            logger.info(f"✓ 成功加载模型: {model_path.name}")
            logger.info(f"  使用设备: {providers[0]}")
            
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def preprocess_image(self, image_path: Path) -> Optional[np.ndarray]:
        """
        预处理图像
        
        MobileNetV3预处理步骤：
        1. 读取图像
        2. 调整大小到224x224
        3. 归一化到[0,1]
        4. 标准化：mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        5. 转换为NCHW格式
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            预处理后的图像数组，失败返回None
        """
        try:
            # 读取图像
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"无法读取图像: {image_path}")
                return None
            
            # BGR转RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 调整大小到224x224
            img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_LINEAR)
            
            # 归一化到[0, 1]
            img = img.astype(np.float32) / 255.0
            
            # ImageNet标准化
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img = (img - mean) / std
            
            # HWC -> CHW
            img = np.transpose(img, (2, 0, 1))
            
            # 添加batch维度: CHW -> NCHW
            img = np.expand_dims(img, axis=0)
            
            return img
            
        except Exception as e:
            logger.error(f"图像预处理失败 {image_path}: {e}")
            return None
    
    def extract_features(self, image_path: Path) -> Optional[np.ndarray]:
        """
        提取图像特征向量（自动适配不同模型）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            特征向量，失败返回None
        """
        if self.session is None:
            logger.error("模型未加载，请先调用load_model()")
            return None
        
        try:
            # 预处理图像
            img_array = self.preprocess_image(image_path)
            if img_array is None:
                return None
            
            # 推理
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: img_array}
            )
            
            # 获取特征向量并展平
            features = outputs[0]
            
            # 处理不同的输出形状
            # 可能是 [1, C, H, W] 或 [1, C] 或 [1, C, 1, 1]
            if len(features.shape) == 4:
                # [1, C, H, W] -> 全局平均池化 -> [1, C]
                features = features.mean(axis=(2, 3))
            
            features = features.flatten()
            
            # 记录特征维度（首次）
            if self.feature_dim is None:
                self.feature_dim = len(features)
                logger.info(f"检测到特征维度: {self.feature_dim}")
            
            # L2归一化
            features = features / (np.linalg.norm(features) + 1e-6)
            
            return features
            
        except Exception as e:
            logger.error(f"特征提取失败 {image_path}: {e}")
            return None
            
            
        except Exception as e:
            logger.error(f"特征提取失败 {image_path}: {e}")
            return None
    
    def extract_features_batch(self, image_paths: list[Path]) -> list[Optional[np.ndarray]]:
        """
        批量提取特征向量
        
        Args:
            image_paths: 图像文件路径列表
            
        Returns:
            特征向量列表
        """
        results = []
        for img_path in image_paths:
            features = self.extract_features(img_path)
            results.append(features)
        return results
    
    @staticmethod
    def calculate_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算两个特征向量的余弦相似度
        
        Args:
            features1: 第一个特征向量
            features2: 第二个特征向量
            
        Returns:
            余弦相似度（0-1之间，1表示完全相同）
        """
        try:
            # 确保是1维向量
            f1 = features1.flatten()
            f2 = features2.flatten()
            
            # 余弦相似度
            similarity = np.dot(f1, f2)
            
            # 转换为Python标量
            if isinstance(similarity, np.ndarray):
                similarity = similarity.item()
            
            # 由于已经L2归一化，直接点积即为余弦相似度
            # 归一化到[0, 1]范围（从[-1, 1]映射）
            similarity = float((similarity + 1.0) / 2.0)
            
            # 确保在有效范围内
            similarity = max(0.0, min(1.0, similarity))
            
            return similarity
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    @staticmethod
    def features_to_bytes(features: np.ndarray) -> bytes:
        """
        将特征向量转换为bytes以便存储到数据库
        
        Args:
            features: 特征向量（numpy数组）
            
        Returns:
            序列化后的bytes
        """
        return features.astype(np.float32).tobytes()
    
    @staticmethod
    def bytes_to_features(data: bytes, feature_dim: int = None) -> np.ndarray:
        """
        从bytes恢复特征向量（自动检测维度）
        
        Args:
            data: 序列化的bytes数据
            feature_dim: 特征维度（可选，自动从数据长度推断）
            
        Returns:
            特征向量（numpy数组）
        """
        if feature_dim is None:
            # 自动计算维度
            feature_dim = len(data) // 4  # float32每个元素4字节
        return np.frombuffer(data, dtype=np.float32).reshape(feature_dim)


# 全局单例
_extractor_instance: Optional[DLFeatureExtractor] = None


def get_feature_extractor(model_path: Optional[Path] = None) -> DLFeatureExtractor:
    """
    获取全局特征提取器实例（单例模式）
    
    Args:
        model_path: 模型路径，首次调用时必须提供
        
    Returns:
        特征提取器实例
    """
    global _extractor_instance
    
    if _extractor_instance is None:
        _extractor_instance = DLFeatureExtractor(model_path)
        if model_path and model_path.exists():
            _extractor_instance.load_model(model_path)
    
    return _extractor_instance
