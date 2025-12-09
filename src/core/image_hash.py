#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片哈希和颜色特征计算模块 - PHash、RGB直方图主色调、深度学习特征
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional


class ImageHashCalculator:
    """图片哈希和颜色特征计算器"""
    
    @staticmethod
    def calculate_phash(image_path: Path, hash_size: int = 8) -> str:
        """
        计算感知哈希（PHash）
        
        Args:
            image_path: 图片路径
            hash_size: 哈希大小，默认8（生成64位哈希）
            
        Returns:
            十六进制格式的哈希字符串
        """
        try:
            # 读取图片
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return "0" * 16  # 返回空哈希
            
            # 调整大小
            img = cv2.resize(img, (hash_size * 4, hash_size * 4), interpolation=cv2.INTER_AREA)
            
            # 转换为float32进行DCT
            img_float = np.float32(img)
            
            # 执行DCT变换
            dct = cv2.dct(img_float)
            
            # 取左上角的低频部分
            dct_low = dct[:hash_size, :hash_size]
            
            # 计算平均值（不包括DC系数）
            avg = np.mean(dct_low[1:, 1:])
            
            # 生成哈希
            hash_bits = (dct_low > avg).flatten()
            
            # 转换为十六进制字符串
            hash_str = ""
            for i in range(0, len(hash_bits), 4):
                nibble = 0
                for j in range(4):
                    if i + j < len(hash_bits) and hash_bits[i + j]:
                        nibble |= (1 << (3 - j))
                hash_str += format(nibble, 'x')
            
            return hash_str
        except Exception as e:
            print(f"计算PHash失败 {image_path}: {e}")
            return "0" * 16
    
    @staticmethod
    def rgb_to_lch(rgb: np.ndarray) -> Tuple[float, float, float]:
        """
        将RGB转换为LCh色彩空间（使用OpenCV实现，无需scikit-image）
        
        Args:
            rgb: RGB值数组 [R, G, B]，范围0-255
            
        Returns:
            (L, C, h) 三元组：
            - L: 亮度 (0-100)
            - C: 色度/饱和度 (0-100+)
            - h: 色相角 (0-360度)
        """
        # RGB -> Lab (使用OpenCV)
        # OpenCV需要BGR格式，并且范围0-255
        bgr = np.array([[[rgb[2], rgb[1], rgb[0]]]], dtype=np.uint8)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)
        L, a, b = lab[0][0]
        
        # Lab值需要转换：
        # L: 0-255 -> 0-100
        # a, b: 0-255 -> -128-127
        L = L * 100.0 / 255.0
        a = a - 128
        b = b - 128
        
        # Lab -> LCh
        C = np.sqrt(a**2 + b**2)
        h = np.arctan2(b, a) * 180 / np.pi
        if h < 0:
            h += 360
        
        return (L, C, h)
    
    @staticmethod
    def calculate_dominant_color_kmeans(image_path: Path) -> Tuple[int, int, bytes]:
        """
        使用多策略RGB直方图提取主色调，并生成RGB直方图
        
        策略：
        1. 主色调：排除低饱和度颜色（背景），从彩色像素中取众数
        2. 转换到LCh色彩空间进行分类
        
        Args:
            image_path: 图片路径
            
        Returns:
            (hue_idx, lightness) 二元组：
            - hue_idx: 色相索引 (0=灰色, 1-12=色系)
            - lightness: 亮度值 (0-100)
        """
        try:
            # 读取图片
            img = cv2.imread(str(image_path))
            if img is None:
                return (0, 0, b'')
            
            # 转换BGR到RGB和HSV
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # ========== 1. 创建彩色像素mask（排除背景） ==========
            # HSV: H(0-179), S(0-255), V(0-255)
            # 低饱和度(S<30)或极暗(V<30)或极亮(V>240)视为背景
            s_channel = img_hsv[:, :, 1]
            v_channel = img_hsv[:, :, 2]
            
            # 彩色像素条件：饱和度足够 AND 亮度适中
            color_mask = (s_channel > 30) & (v_channel > 30) & (v_channel < 240)
            color_mask = color_mask.astype(np.uint8) * 255
            
            # ========== 2. 加权策略：彩色优先 + 中心加权 ==========
            height, width = img_rgb.shape[:2]
            
            # 创建中心权重（高斯型）
            y, x = np.ogrid[:height, :width]
            center_y, center_x = height / 2, width / 2
            
            # 高斯衰减
            sigma_x, sigma_y = width * 0.3, height * 0.3
            center_weight = np.exp(-((x - center_x)**2 / (2 * sigma_x**2) + 
                                     (y - center_y)**2 / (2 * sigma_y**2)))
            
            # 组合mask：彩色像素权重高，中心权重高
            combined_mask = color_mask.astype(np.float32) / 255.0
            combined_mask = combined_mask * (0.7 + 0.3 * center_weight)  # 彩色=0.7-1.0, 灰色=0-0.3
            combined_mask = (combined_mask * 255).astype(np.uint8)
            
            # ========== 3. 计算加权直方图 ==========
            hist_weighted = cv2.calcHist(
                [img_rgb],
                channels=[0, 1, 2],
                mask=combined_mask,
                histSize=[16, 16, 16],
                ranges=[0, 256, 0, 256, 0, 256]
            )
            
            # ========== 4. 主色调提取 ==========
            hist_3d = hist_weighted.reshape(16, 16, 16)
            
            # 排除灰色bins (R≈G≈B)
            for i in range(16):
                for j in range(16):
                    for k in range(16):
                        # 如果RGB差异小于2个bin，视为灰色
                        if abs(i - j) <= 2 and abs(j - k) <= 2 and abs(i - k) <= 2:
                            hist_3d[i, j, k] *= 0.1  # 降低灰色权重
            
            max_idx = np.unravel_index(np.argmax(hist_3d), (16, 16, 16))
            
            # 将索引转换回RGB值
            r_bin, g_bin, b_bin = max_idx
            dominant_r = (r_bin * 16) + 8
            dominant_g = (g_bin * 16) + 8
            dominant_b = (b_bin * 16) + 8
            dominant_rgb = np.array([dominant_r, dominant_g, dominant_b])
            
            # 转换到LCh空间
            L, C, h = ImageHashCalculator.rgb_to_lch(dominant_rgb)
            
            # 判断是否为灰色系
            C_THRESHOLD = 8.0
            if C < C_THRESHOLD:
                hue_idx = 0
            else:
                hue_idx = int(h / 30) + 1
                if hue_idx > 12:
                    hue_idx = 1
            
            lightness = int(round(L))
            
            return (hue_idx, lightness)
            
        except Exception as e:
            print(f"计算颜色特征失败 {image_path}: {e}")
            import traceback
            traceback.print_exc()
            return (0, 0)
    
    # 已删除: calculate_histogram_similarity
    # 原因: 改用深度学习特征后不再需要RGB直方图相似度计算
    
    @staticmethod
    def calculate_hsv_dominant(image_path: Path, bins: int = 180) -> Tuple[int, int, int]:
        """
        【已废弃】计算HSV主色调（保留用于向后兼容）
        
        新代码应使用 calculate_dominant_color_kmeans()
        """
        # 调用新方法并转换格式
        hue_idx, lightness = ImageHashCalculator.calculate_dominant_color_kmeans(image_path)
        
        # 简单映射：将LCh转换回近似的HSV
        # 这只是为了兼容性，实际应该使用新的存储字段
        h = (hue_idx - 1) * 30 if hue_idx > 0 else -1
        s = 128 if hue_idx > 0 else 30  # 粗略估计
        v = int(lightness * 2.55)  # 0-100 -> 0-255
        
        return (h, s, v)
    
    @staticmethod
    def calculate_both(image_path: Path) -> Tuple[str, int, int, int, int, int]:
        """
        同时计算PHash和颜色特征
        
        Args:
            image_path: 图片路径
            
        Returns:
            (phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v)
            - phash: 感知哈希字符串
            - hue_idx: 色相索引 (0-12)
            - lightness: 亮度 (0-100)
            - hsv_h, hsv_s, hsv_v: 为向后兼容保留
        """
        phash = ImageHashCalculator.calculate_phash(image_path)
        hue_idx, lightness = ImageHashCalculator.calculate_dominant_color_kmeans(image_path)
        
        # 为了向后兼容，也计算HSV（但不推荐使用）
        hsv_h, hsv_s, hsv_v = ImageHashCalculator.calculate_hsv_dominant(image_path)
        
        return phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v


def calculate_image_hashes(image_path: Path) -> Tuple[str, int, int, int, int, int]:
    """
    便捷函数：计算图片的完整特征
    
    Args:
        image_path: 图片路径
        
    Returns:
        (phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v)
    """
    return ImageHashCalculator.calculate_both(image_path)


def calculate_dl_features(image_path: Path) -> Optional[bytes]:
    """
    计算深度学习特征（MobileNetV3）
    
    Args:
        image_path: 图片路径
        
    Returns:
        特征向量bytes，失败返回None
    """
    try:
        from .dl_feature_extractor import get_feature_extractor
        from .dl_model_manager import DLModelManager
        
        # 获取模型路径
        models_dir = Path(__file__).parent.parent.parent / "models"
        manager = DLModelManager(models_dir)
        model_path = manager.get_model_path()
        
        if not model_path:
            # 模型不可用，返回None
            return None
        
        # 获取特征提取器
        extractor = get_feature_extractor(model_path)
        if not extractor or not extractor.session:
            return None
        
        # 提取特征
        features = extractor.extract_features(image_path)
        if features is None:
            return None
        
        # 转换为bytes
        return extractor.features_to_bytes(features)
        
    except Exception as e:
        # 如果DL模块不可用或出错，静默失败
        return None
