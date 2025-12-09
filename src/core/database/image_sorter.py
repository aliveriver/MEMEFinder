#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片排序模块
"""

from typing import List, Dict, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class ImageSorter:
    """图片排序器"""
    
    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        计算两个哈希值的汉明距离
        
        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            
        Returns:
            汉明距离（不同位的数量）
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 999999  # 返回很大的值表示完全不相似
        
        distance = 0
        for c1, c2 in zip(hash1, hash2):
            try:
                # 转换为整数并进行异或
                xor = int(c1, 16) ^ int(c2, 16)
                # 统计异或结果中1的个数
                distance += bin(xor).count('1')
            except:
                return 999999
        
        return distance
    
    @staticmethod
    def sort_by_similarity(images: List[Dict], reference_image: Dict) -> List[Dict]:
        """
        按照与参考图片的相似度排序
        
        根据与参考图片的汉明距离排序，距离越小越相似。
        
        Args:
            images: 图片列表，每个图片应包含 'phash' 字段
            reference_image: 参考图片（必需），必须包含 'phash' 字段
            
        Returns:
            排序后的图片列表（按与参考图片的相似度从高到低）
        """
        if not images:
            return []
        
        if not reference_image or not reference_image.get('phash'):
            logger.warning("参考图片无效或缺少phash，返回原列表")
            return images
        
        reference_phash = reference_image.get('phash', '')
        
        # 过滤出有有效phash的图片
        valid_images = [img for img in images if img.get('phash') and img['phash'] != '0' * 16]
        invalid_images = [img for img in images if not img.get('phash') or img['phash'] == '0' * 16]
        
        if not valid_images:
            return images
        
        # 计算每张图片与参考图片的距离并排序
        image_distances = []
        for img in valid_images:
            img_phash = img.get('phash', '')
            distance = ImageSorter.hamming_distance(reference_phash, img_phash)
            
            # 计算相似度并添加到图片字典中
            phash_sim = max(0, 1 - distance / 256)  # 归一化到0-1
            img['similarity_score'] = phash_sim
            image_distances.append((distance, img))
        
        # 按距离排序（距离小的更相似）
        image_distances.sort(key=lambda x: x[0])
        sorted_images = [img for _, img in image_distances]
        
        logger.debug(f"相似度排序完成，共 {len(sorted_images)} 张有效图片，参考图片phash={reference_phash[:8]}...")
        return sorted_images + invalid_images
    
    @staticmethod
    def hsv_distance(h1: int, h2: int) -> int:
        """
        计算两个H值之间的环形距离
        
        由于色相是环形的（0-179），需要考虑环形距离
        例如：179和0之间的距离应该是1，而不是179
        
        Args:
            h1: 第一个H值（0-179）
            h2: 第二个H值（0-179）
            
        Returns:
            环形距离
        """
        if h1 < 0 or h2 < 0:
            return 999999  # 无效值
        
        # 计算环形距离
        diff = abs(h1 - h2)
        return min(diff, 180 - diff)
    
    @staticmethod
    def sort_by_color(images: List[Dict], reference_image: Dict = None) -> List[Dict]:
        """
        按照颜色排序（基于K-Means + LCh色彩空间）
        
        使用预先计算的color_hue_idx和color_lightness进行排序：
        1. 先按色相分组（hue_idx: 0=灰色, 1-12=30°色相分段）
        2. 在每个色相分组内，按明度排序（lightness: 0-100）
        
        优势：
        - 使用LCh色彩空间，感知均匀性好
        - K-Means提取主导色，鲁棒性强
        - 纯SQL排序，性能优异
        
        Args:
            images: 图片列表，每个图片应包含 'color_hue_idx', 'color_lightness' 字段
            reference_image: 参考图片（可选，为了向后兼容保留，但不使用）
            
        Returns:
            排序后的图片列表（颜色相近的图片聚集在一起）
        """
        if not images:
            return []
        
        def get_sort_key(img):
            """
            生成排序键：(色相索引, 明度)
            
            色相索引说明：
            - 0: 灰色/无彩色（色度C < 8.0）
            - 1-12: 彩色，每30°一个分段
              1=0-30° (红), 2=30-60° (橙黄), 3=60-90° (黄绿), 
              4=90-120° (绿), 5=120-150° (青), 6=150-180° (蓝),
              7=180-210° (深蓝), 8=210-240° (紫), 9=240-270° (品红),
              10=270-300° (洋红), 11=300-330° (玫红), 12=330-360° (红)
            """
            hue_idx = img.get('color_hue_idx', -1)
            lightness = img.get('color_lightness', 0)
            
            # 未处理的图片（没有颜色特征）排到最后
            if hue_idx < 0:
                return (999, 999)
            
            # 按(色相分组, 明度)排序
            return (hue_idx, lightness)
        
        # 排序所有图片
        sorted_images = sorted(images, key=get_sort_key)
        
        logger.debug(f"颜色排序完成，共 {len(sorted_images)} 张图片（基于K-Means主导色）")
        
        return sorted_images
    
    @staticmethod
    def get_color_name(hsv_h: int) -> str:
        """
        根据H值获取颜色名称（用于显示）
        
        Args:
            hsv_h: H值（0-179）
            
        Returns:
            颜色名称
        """
        if hsv_h < 0:
            return "未知"
        elif hsv_h < 11 or hsv_h >= 170:
            return "红色"
        elif hsv_h < 25:
            return "橙色"
        elif hsv_h < 35:
            return "黄色"
        elif hsv_h < 85:
            return "绿色"
        elif hsv_h < 100:
            return "青色"
        elif hsv_h < 130:
            return "蓝色"
        else:
            return "紫色"
    
    # 已删除: calculate_combined_similarity 和 sort_by_combined_similarity
    # 原因: 改用深度学习特征后不再需要RGB直方图方案
    
    @staticmethod
    def sort_by_dl_similarity(images: List[Dict], reference_image: Dict) -> List[Dict]:
        """
        按深度学习特征相似度排序（MobileNetV3）
        
        使用深度学习模型提取的特征向量进行相似度计算，
        比传统pHash和直方图方法更能捕捉图像的语义信息。
        
        Args:
            images: 图片列表，需包含 'dl_features' 字段
            reference_image: 参考图片，需包含 'dl_features' 字段
            
        Returns:
            按相似度排序的图片列表（相似度从高到低）
        """
        if not images or not reference_image:
            return images
        
        ref_features = reference_image.get('dl_features')
        if not ref_features:
            logger.warning("参考图片缺少深度学习特征，无法排序")
            return images
        
        try:
            import numpy as np
            from ..dl_feature_extractor import DLFeatureExtractor
            
            # 转换参考特征
            ref_features_array = DLFeatureExtractor.bytes_to_features(ref_features)
            
            # 计算每张图片的相似度
            image_similarities = []
            for img in images:
                img_features = img.get('dl_features')
                if not img_features:
                    # 没有DL特征的图片放到最后
                    image_similarities.append((0.0, img))
                    continue
                
                # 转换特征并计算相似度
                img_features_array = DLFeatureExtractor.bytes_to_features(img_features)
                similarity = DLFeatureExtractor.calculate_similarity(
                    ref_features_array, img_features_array
                )
                
                # 将相似度分数添加到图片字典中
                img['similarity_score'] = similarity
                image_similarities.append((similarity, img))
            
            # 按相似度降序排序
            image_similarities.sort(key=lambda x: x[0], reverse=True)
            sorted_images = [img for _, img in image_similarities]
            
            logger.debug(f"深度学习特征排序完成，共 {len(sorted_images)} 张图片")
            return sorted_images
            
        except Exception as e:
            logger.error(f"深度学习特征排序失败: {e}")
            return images
    
    @staticmethod
    def sort_by_hybrid_similarity(images: List[Dict], reference_image: Dict,
                                  dl_weight: float = 0.8,
                                  phash_weight: float = 0.2) -> List[Dict]:
        """
        混合相似度排序（深度学习 + PHash）
        
        综合使用两种特征：
        1. 深度学习特征（80%）- 语义相似度（物体、场景、构图）
        2. PHash（20%）- 结构相似度（视觉布局）
        
        Args:
            images: 图片列表
            reference_image: 参考图片
            dl_weight: 深度学习特征权重（默认0.8）
            phash_weight: PHash权重（默认0.2）
            
        Returns:
            按混合相似度排序的图片列表
        """
        if not images or not reference_image:
            return images
        
        try:
            import numpy as np
            from ..dl_feature_extractor import DLFeatureExtractor
            from ..image_hash import ImageHashCalculator
            
            # 获取参考图片特征
            ref_dl_features = reference_image.get('dl_features')
            ref_phash = reference_image.get('phash')
            
            if ref_dl_features:
                ref_dl_array = DLFeatureExtractor.bytes_to_features(ref_dl_features)
            else:
                ref_dl_array = None
            
            # 计算每张图片的混合相似度
            image_similarities = []
            dl_count = 0
            phash_count = 0
            
            for img in images:
                total_score = 0.0
                weight_sum = 0.0
                
                # 1. 深度学习特征相似度
                if ref_dl_array is not None and img.get('dl_features'):
                    img_dl_array = DLFeatureExtractor.bytes_to_features(img['dl_features'])
                    dl_sim = DLFeatureExtractor.calculate_similarity(ref_dl_array, img_dl_array)
                    total_score += dl_sim * dl_weight
                    weight_sum += dl_weight
                    dl_count += 1
                
                # 2. PHash相似度
                if ref_phash and img.get('phash'):
                    hamming_dist = ImageSorter.hamming_distance(ref_phash, img['phash'])
                    phash_sim = max(0, 1 - hamming_dist / 256)
                    total_score += phash_sim * phash_weight
                    weight_sum += phash_weight
                    phash_count += 1
                
                # 归一化得分
                final_score = total_score / weight_sum if weight_sum > 0 else 0.0
                
                # 将相似度分数添加到图片字典中
                img['similarity_score'] = final_score
                image_similarities.append((final_score, img))
            
            logger.info(f"[混合排序] 图片特征统计: 有DL特征={dl_count}/{len(images)}, 有PHash={phash_count}/{len(images)}")
            
            # 调试输出前3个结果
            from pathlib import Path
            logger.info(f"[混合排序] 排序前3个: {[(s, Path(img.get('file_path', 'unknown')).name[:20]) for s, img in sorted(image_similarities, key=lambda x: x[0], reverse=True)[:3]]}")
            
            # 按相似度降序排序
            image_similarities.sort(key=lambda x: x[0], reverse=True)
            sorted_images = [img for _, img in image_similarities]
            
            logger.debug(f"混合相似度排序完成，共 {len(sorted_images)} 张图片")
            return sorted_images
            
        except Exception as e:
            logger.error(f"混合相似度排序失败: {e}")
            return images
