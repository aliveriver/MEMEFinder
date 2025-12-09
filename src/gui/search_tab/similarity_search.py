#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
相似度搜索模块
负责以图搜图和相似度排序功能
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab
import tempfile
from pathlib import Path
import json

from ...utils.logger import get_logger
from ...core.image_hash import calculate_image_hashes, calculate_dl_features
from ...core.database.image_sorter import ImageSorter

logger = get_logger()


class SimilaritySearch:
    """相似度搜索 - 处理以图搜图和相似度排序"""
    
    def __init__(self, parent_frame, renderer, sort_info_label, db, config_path='version_config.json'):
        """
        初始化相似度搜索
        
        Args:
            parent_frame: 父框架
            renderer: Canvas渲染器
            sort_info_label: 排序信息标签
            db: 数据库实例
            config_path: 配置文件路径
        """
        self.frame = parent_frame
        self.renderer = renderer
        self.sort_info_label = sort_info_label
        self.db = db
        self.config_path = Path(__file__).parent.parent.parent / config_path
        
        # 以图搜图权重配置（默认值）
        self.dl_weight = 0.8  # 深度学习特征权重
        self.phash_weight = 0.2  # PHash权重
        
        # 以图搜图设置（默认值）
        self.max_compare_count = None  # 最大比较数量，None表示不限制
        self.min_similarity_threshold = 0.0  # 最小相似度阈值（0.0-1.0），低于此值不显示
        
        # 相似度排序的参考图片
        self.similarity_reference = None
        
        # 当前是否处于相似度搜索模式
        self.is_similarity_mode = False
        
        # 加载配置
        self.load_weights()
    
    def search_by_image(self, all_results_getter, all_results_setter, render_callback):
        """
        以图搜图（支持文件选择和剪贴板）
        
        Args:
            all_results_getter: 获取当前结果列表的函数
            all_results_setter: 设置结果列表的函数
            render_callback: 重新渲染的回调函数
        """
        # 创建选择对话框
        choice_dialog = tk.Toplevel(self.frame)
        choice_dialog.title("以图搜图")
        choice_dialog.geometry("350x220")
        choice_dialog.transient(self.frame)
        choice_dialog.grab_set()
        
        # 居中显示
        choice_dialog.update_idletasks()
        x = (choice_dialog.winfo_screenwidth() // 2) - (choice_dialog.winfo_width() // 2)
        y = (choice_dialog.winfo_screenheight() // 2) - (choice_dialog.winfo_height() // 2)
        choice_dialog.geometry(f"+{x}+{y}")
        
        selected_path = [None]  # 使用列表以便在内部函数中修改
        
        def select_from_file():
            """从文件选择"""
            file_path = filedialog.askopenfilename(
                title="选择图片",
                filetypes=[
                    ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                    ("所有文件", "*.*")
                ]
            )
            if file_path:
                # 规范化路径格式
                selected_path[0] = os.path.abspath(file_path)
                choice_dialog.destroy()
        
        def select_from_clipboard():
            """从剪贴板获取"""
            try:
                img = ImageGrab.grabclipboard()
                if img is None:
                    messagebox.showwarning("提示", "剪贴板中没有图片")
                    return
                
                # 保存到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                img.save(temp_file.name)
                temp_file.close()
                
                # 规范化路径格式
                selected_path[0] = os.path.abspath(temp_file.name)
                choice_dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"从剪贴板获取图片失败：{e}")
        
        def open_settings():
            """打开设置"""
            from .similarity_settings_dialog import SimilaritySettingsDialog
            
            dialog = SimilaritySettingsDialog(
                choice_dialog,
                current_dl_weight=self.dl_weight,
                current_phash_weight=self.phash_weight,
                current_max_count=self.max_compare_count,
                current_min_threshold=self.min_similarity_threshold
            )
            
            result = dialog.wait_window()
            
            if result:
                # 更新所有设置
                self.dl_weight, self.phash_weight, self.max_compare_count, self.min_similarity_threshold = result
                # 保存设置
                self.save_weights()
                # 更新按钮文本显示当前权重
                settings_text = f"⚙️ 以图搜图设置"
                settings_btn.config(text=settings_text)
        
        # UI组件
        from tkinter import ttk
        ttk.Label(choice_dialog, text="请选择图片来源：", font=('TkDefaultFont', 11, 'bold')).pack(pady=15)
        
        btn_frame = ttk.Frame(choice_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📁 从文件选择", command=select_from_file, width=18).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📋 从剪贴板", command=select_from_clipboard, width=18).pack(side=tk.LEFT, padx=10)
        
        settings_text = f"⚙️ 以图搜图设置"
        settings_btn = ttk.Button(choice_dialog, text=settings_text, command=open_settings, width=40)
        settings_btn.pack(pady=15)
        
        ttk.Button(choice_dialog, text="取消", command=choice_dialog.destroy, width=15).pack(pady=10)
        
        # 等待对话框关闭
        self.frame.wait_window(choice_dialog)
        
        if not selected_path[0]:
            return
        
        # 执行搜索
        self._execute_search(selected_path[0], all_results_getter, all_results_setter, render_callback)
    
    def _execute_search(self, image_path, all_results_getter, all_results_setter, render_callback):
        """执行以图搜图"""
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                messagebox.showerror("错误", "图片文件不存在")
                return
            
            # 计算特征
            messagebox.showinfo("提示", "正在计算图片特征，请稍候...")
            phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v = calculate_image_hashes(image_path)
            
            # 尝试计算深度学习特征
            dl_features = None
            try:
                dl_features = calculate_dl_features(image_path)
                if dl_features:
                    logger.info("✓ 成功提取深度学习特征用于以图搜图")
            except:
                pass
            
            # 构建参考图片对象
            reference_image = {
                'file_path': str(image_path),
                'phash': phash,
                'color_hue_idx': hue_idx,
                'color_lightness': lightness,
                'hsv_h': hsv_h,
                'hsv_s': hsv_s,
                'hsv_v': hsv_v,
                'dl_features': dl_features
            }
            
            # 从数据库获取待比较的图片（全局搜索）
            logger.info(f"开始全局以图搜图，最大比较数量: {self.max_compare_count or '不限制'}")
            all_results = self.db.get_all_images_for_similarity(max_count=self.max_compare_count)
            
            if not all_results:
                messagebox.showwarning("提示", "数据库中没有已处理的图片")
                return
            
            logger.info(f"获取了 {len(all_results)} 张图片进行相似度比较")
            
            # 排序并计算相似度
            sorted_results, sort_method = self._sort_results_with_scores(all_results, reference_image)
            
            # 根据相似度阈值过滤
            if self.min_similarity_threshold > 0.0:
                original_count = len(sorted_results)
                sorted_results = [r for r in sorted_results if r.get('similarity_score', 0.0) >= self.min_similarity_threshold]
                filtered_count = original_count - len(sorted_results)
                logger.info(f"根据相似度阈值 {self.min_similarity_threshold} 过滤掉 {filtered_count} 张图片，剩余 {len(sorted_results)} 张")
            
            if not sorted_results:
                messagebox.showwarning("提示", f"没有找到相似度大于等于 {self.min_similarity_threshold} 的图片")
                return
            
            # 保存参考图片
            self.similarity_reference = reference_image
            
            # 标记为相似度搜索模式
            self.is_similarity_mode = True
            
            # 更新结果
            all_results_setter(sorted_results)
            
            # 更新排序说明
            img_name = image_path.name
            threshold_info = f", 阈值≥{self.min_similarity_threshold}" if self.min_similarity_threshold > 0 else ""
            self.sort_info_label.config(
                text=f"(已按与 {img_name} 的相似度排序{threshold_info}，共 {len(sorted_results)} 张)",
                foreground="blue"
            )
            
            # 重新渲染
            render_callback()
            
            messagebox.showinfo("成功", f"已按与 {img_name} 的相似度排序\\n使用：{sort_method}\\n找到 {len(sorted_results)} 张相似图片")
            
        except Exception as e:
            logger.error(f"以图搜图失败: {e}")
            messagebox.showerror("错误", f"以图搜图失败：{e}")
    
    def search_with_filters(self, filters: dict):
        """
        使用当前参考图片和指定的过滤条件重新搜索
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            list: 排序后的结果列表
        """
        if not self.similarity_reference:
            return []
            
        return self.sort_by_similarity([], self.similarity_reference['file_path'], filters)

    def sort_by_similarity(self, all_results, reference_path, filters=None):
        """
        以指定图片为参考进行相似度排序（全局搜索）
        
        Args:
            all_results: 当前结果列表（用于查找参考图片的缓存特征）
            reference_path: 参考图片路径
            filters: 可选的过滤条件字典
            
        Returns:
            list: 排序后的结果列表
        """
        try:
            image_path = Path(reference_path)
            if not image_path.exists():
                messagebox.showerror("错误", "参考图片不存在")
                return all_results
            
            # 1. 获取参考图片特征
            # 如果self.similarity_reference已经是该图片，直接使用
            if self.similarity_reference and self.similarity_reference.get('file_path') == str(image_path):
                reference_image = self.similarity_reference
            else:
                # 先尝试从all_results中找到该图片的数据（优先使用数据库特征）
                reference_image = None
                if all_results:
                    for img in all_results:
                        if img.get('file_path') == reference_path:
                            reference_image = img.copy()
                            break
                
                # 如果数据库中有特征，直接使用
                if reference_image and reference_image.get('phash'):
                    logger.info("使用数据库中的特征进行相似度排序")
                    dl_features = reference_image.get('dl_features')
                    phash = reference_image.get('phash')
                else:
                    # 否则重新计算特征
                    logger.info("数据库中无特征，重新计算...")
                    phash, hue_idx, lightness, hsv_h, hsv_s, hsv_v = calculate_image_hashes(image_path)
                    
                    # 尝试计算深度学习特征
                    dl_features = None
                    try:
                        dl_features = calculate_dl_features(image_path)
                        if dl_features:
                            logger.info("✓ 成功提取深度学习特征用于相似度排序")
                    except Exception as e:
                        logger.debug(f"深度学习特征提取失败（使用PHash备用方案）: {e}")
                    
                    # 构建参考图片对象
                    reference_image = {
                        'file_path': str(image_path),
                        'phash': phash,
                        'color_hue_idx': hue_idx,
                        'color_lightness': lightness,
                        'hsv_h': hsv_h,
                        'hsv_s': hsv_s,
                        'hsv_v': hsv_v,
                        'dl_features': dl_features
                    }

            # 2. 从数据库获取待比较的图片（全局搜索，带过滤）
            logger.info(f"开始全局以图搜图，最大比较数量: {self.max_compare_count or '不限制'}")
            
            # 准备过滤参数
            kwargs = {'max_count': self.max_compare_count}
            if filters:
                kwargs.update(filters)
                logger.info(f"应用过滤条件: {filters}")
            
            search_results = self.db.get_all_images_for_similarity(**kwargs)
            
            if not search_results:
                if filters:
                    messagebox.showinfo("提示", "在当前过滤条件下没有找到图片")
                else:
                    messagebox.showwarning("提示", "数据库中没有已处理的图片")
                return [] # 返回空列表而不是all_results，因为这是新的搜索
            
            logger.info(f"获取了 {len(search_results)} 张图片进行相似度比较")
            
            # 3. 排序并计算相似度
            sorted_results, sort_method = self._sort_results_with_scores(search_results, reference_image)
            
            # 4. 根据相似度阈值过滤
            if self.min_similarity_threshold > 0.0:
                original_count = len(sorted_results)
                sorted_results = [r for r in sorted_results if r.get('similarity_score', 0.0) >= self.min_similarity_threshold]
                filtered_count = original_count - len(sorted_results)
                logger.info(f"根据相似度阈值 {self.min_similarity_threshold} 过滤掉 {filtered_count} 张图片，剩余 {len(sorted_results)} 张")
            
            if not sorted_results:
                messagebox.showinfo("提示", f"没有找到相似度大于等于 {self.min_similarity_threshold} 的图片")
                return []
            
            # 5. 保存状态
            self.similarity_reference = reference_image
            self.is_similarity_mode = True
            
            # 6. 更新排序说明
            ref_name = image_path.name
            threshold_info = f", 阈值≥{self.min_similarity_threshold}" if self.min_similarity_threshold > 0 else ""
            filter_info = " (已过滤)" if filters else ""
            
            self.sort_info_label.config(
                text=f"(已按与 {ref_name} 的相似度排序{threshold_info}{filter_info}，共 {len(sorted_results)} 张)",
                foreground="blue"
            )
            
            # 只有在没有过滤条件（即首次搜索）时才弹窗，避免每次输入关键词都弹窗
            if not filters:
                messagebox.showinfo("成功", f"已按与 {ref_name} 的相似度排序\\n使用：{sort_method}\\n找到 {len(sorted_results)} 张相似图片")
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"相似度排序失败: {e}")
            messagebox.showerror("错误", f"相似度排序失败：{e}")
            return all_results
    
    def _sort_results(self, results, reference_image):
        """
        根据参考图片排序结果
        
        Returns:
            tuple: (sorted_results, sort_method)
        """
        dl_features = reference_image.get('dl_features')
        phash = reference_image.get('phash')
        
        # 优先使用混合方法
        if dl_features and (self.dl_weight > 0 or (phash and self.phash_weight > 0)):
            sorted_results = ImageSorter.sort_by_hybrid_similarity(
                results, reference_image,
                dl_weight=self.dl_weight, phash_weight=self.phash_weight
            )
            sort_method = f"混合相似度 [深度学习:{int(self.dl_weight*100)}% + PHash:{int(self.phash_weight*100)}%]"
        elif dl_features:
            sorted_results = ImageSorter.sort_by_dl_similarity(results, reference_image)
            sort_method = "深度学习特征相似度"
        elif phash:
            sorted_results = ImageSorter.sort_by_similarity(results, reference_image)
            sort_method = "PHash相似度"
        else:
            messagebox.showwarning("警告", "参考图片缺少特征数据，无法排序")
            return results, "无法排序"
        
        return sorted_results, sort_method
    
    def _sort_results_with_scores(self, results, reference_image):
        """
        根据参考图片排序结果并计算相似度分数
        
        注意：ImageSorter的排序方法已经会自动计算并添加similarity_score字段
        
        Returns:
            tuple: (sorted_results, sort_method)
        """
        # 直接调用原有方法，因为ImageSorter已经计算分数了
        return self._sort_results(results, reference_image)
    
    def open_settings(self):
        """打开以图搜图设置对话框"""
        from .similarity_settings_dialog import SimilaritySettingsDialog
        
        dialog = SimilaritySettingsDialog(
            self.frame.winfo_toplevel(),
            current_dl_weight=self.dl_weight,
            current_phash_weight=self.phash_weight,
            current_max_count=self.max_compare_count,
            current_min_threshold=self.min_similarity_threshold
        )
        
        result = dialog.wait_window()
        
        if result:
            # 更新所有设置
            self.dl_weight, self.phash_weight, self.max_compare_count, self.min_similarity_threshold = result
            
            # 构建提示信息
            info_lines = [
                f"以图搜图配置已更新：",
                f"  权重: DL {int(self.dl_weight*100)}% + PHash {int(self.phash_weight*100)}%",
                f"  最大比较数量: {'不限制' if self.max_compare_count is None else str(self.max_compare_count)}",
                f"  最小相似度阈值: {self.min_similarity_threshold:.2f}"
            ]
            messagebox.showinfo("设置已保存", "\n".join(info_lines))
            self.save_weights()
    
    def load_weights(self):
        """从配置文件加载以图搜图权重和搜索设置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 权重设置
                    self.dl_weight = config.get('dl_weight', 0.8)
                    self.phash_weight = config.get('phash_weight', 0.2)
                    # 搜索设置
                    self.max_compare_count = config.get('max_compare_count', None)
                    self.min_similarity_threshold = config.get('min_similarity_threshold', 0.0)
                    logger.debug(f"已加载配置: DL={self.dl_weight}, PHash={self.phash_weight}, "
                               f"MaxCount={self.max_compare_count}, MinThreshold={self.min_similarity_threshold}")
        except Exception as e:
            logger.warning(f"加载权重设置失败，使用默认值: {e}")
    
    def save_weights(self):
        """保存以图搜图权重和搜索设置到配置文件"""
        try:
            # 读取现有配置
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新权重和搜索设置
            config['dl_weight'] = self.dl_weight
            config['phash_weight'] = self.phash_weight
            config['max_compare_count'] = self.max_compare_count
            config['min_similarity_threshold'] = self.min_similarity_threshold
            
            # 保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"配置已保存: DL={self.dl_weight}, PHash={self.phash_weight}, "
                       f"MaxCount={self.max_compare_count}, MinThreshold={self.min_similarity_threshold}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def exit_similarity_mode(self):
        """退出相似度搜索模式"""
        self.is_similarity_mode = False
        self.similarity_reference = None
        logger.info("已退出相似度搜索模式")
