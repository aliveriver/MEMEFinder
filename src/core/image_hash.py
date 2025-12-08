#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片哈希和颜色特征计算模块 - PHash、RGB直方图主色调
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from skimage import color


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
        将RGB转换为LCh色彩空间
        
        Args:
            rgb: RGB值数组 [R, G, B]，范围0-255
            
        Returns:
            (L, C, h) 三元组：
            - L: 亮度 (0-100)
            - C: 色度/饱和度 (0-100+)
            - h: 色相角 (0-360度)
        """
        # 归一化到0-1
        rgb_normalized = rgb / 255.0
        
        # RGB -> Lab
        lab = color.rgb2lab([[rgb_normalized]])[0][0]
        L, a, b = lab
        
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
        2. 直方图：16x16x16的RGB直方图(4096 bins)，归一化后序列化
        
        Args:
            image_path: 图片路径
            
        Returns:
            (hue_idx, lightness, histogram_bytes) 三元组：
            - hue_idx: 色相索引 (0=灰色, 1-12=色系)
            - lightness: 亮度值 (0-100)
            - histogram_bytes: 归一化RGB直方图的二进制数据
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
            
            # ========== 5. 生成完整RGB直方图（用于相似度） ==========
            hist_full = cv2.calcHist(
                [img_rgb],
                channels=[0, 1, 2],
                mask=None,
                histSize=[16, 16, 16],
                ranges=[0, 256, 0, 256, 0, 256]
            )
            
            hist_full = hist_full.flatten()
            hist_full = hist_full / (hist_full.sum() + 1e-7)
            histogram_bytes = hist_full.astype(np.float32).tobytes()
            
            return (hue_idx, lightness, histogram_bytes)
            
        except Exception as e:
            print(f"计算颜色特征失败 {image_path}: {e}")
            import traceback
            traceback.print_exc()
            return (0, 0, b'')
    
    @staticmethod
    def calculate_histogram_similarity(hist1_bytes: bytes, hist2_bytes: bytes) -> float:
        """
        计算两个直方图的相似度（余弦相似度）
        
        Args:
            hist1_bytes: 第一个直方图的字节数据
            hist2_bytes: 第二个直方图的字节数据
            
        Returns:
            相似度分数 (0-1)，1表示完全相同
        """
        if not hist1_bytes or not hist2_bytes:
            return 0.0
        
        try:
            # 反序列化
            hist1 = np.frombuffer(hist1_bytes, dtype=np.float32)
            hist2 = np.frombuffer(hist2_bytes, dtype=np.float32)
            
            # 余弦相似度
            dot_product = np.dot(hist1, hist2)
            norm1 = np.linalg.norm(hist1)
            norm2 = np.linalg.norm(hist2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(max(0.0, min(1.0, similarity)))
            
        except Exception as e:
            print(f"计算直方图相似度失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_hsv_dominant(image_path: Path, bins: int = 180) -> Tuple[int, int, int]:
        """
        【已废弃】计算HSV主色调（保留用于向后兼容）
        
        新代码应使用 calculate_dominant_color_kmeans()（实际已改为直方图众数法）
        """
        # 调用新方法并转换格式
        hue_idx, lightness, _ = ImageHashCalculator.calculate_dominant_color_kmeans(image_path)
        
        # 简单映射：将LCh转换回近似的HSV
        # 这只是为了兼容性，实际应该使用新的存储字段
        h = (hue_idx - 1) * 30 if hue_idx > 0 else -1
        s = 128 if hue_idx > 0 else 30  # 粗略估计
        v = int(lightness * 2.55)  # 0-100 -> 0-255
        
        return (h, s, v)
    
    @staticmethod
    def calculate_both(image_path: Path) -> Tuple[str, int, int, int, int, bytes]:
        """
        同时计算PHash和颜色特征（直方图众数主色调 + RGB直方图）
        
        Args:
            image_path: 图片路径
            
        Returns:
            (phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v, histogram_bytes)
            - phash: 感知哈希字符串
            - hue_idx: 色相索引 (0-12)
            - lightness: 亮度 (0-100)
            - histogram_bytes: RGB直方图字节数据
        """
        phash = ImageHashCalculator.calculate_phash(image_path)
        hue_idx, lightness, histogram_bytes = ImageHashCalculator.calculate_dominant_color_kmeans(image_path)
        
        # 为了向后兼容，也计算HSV（但不推荐使用）
        hsv_h, hsv_s, hsv_v = ImageHashCalculator.calculate_hsv_dominant(image_path)
        
        return phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v, histogram_bytes


def calculate_image_hashes(image_path: Path) -> Tuple[str, int, int, int, int, int, bytes]:
    """
    便捷函数：计算图片的完整特征
    
    Args:
        image_path: 图片路径
        
    Returns:
        (phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v, histogram_bytes)
    """
    return ImageHashCalculator.calculate_both(image_path)
