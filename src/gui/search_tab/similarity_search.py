#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
相似度搜索模块
负责以图搜图和相似度排序功能
"""

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
    
    def __init__(self, parent_frame, renderer, sort_info_label, config_path='version_config.json'):
        """
        初始化相似度搜索
        
        Args:
            parent_frame: 父框架
            renderer: Canvas渲染器
            sort_info_label: 排序信息标签
            config_path: 配置文件路径
        """
        self.frame = parent_frame
        self.renderer = renderer
        self.sort_info_label = sort_info_label
        self.config_path = Path(__file__).parent.parent.parent / config_path
        
        # 以图搜图权重配置（默认值）
        self.dl_weight = 0.8  # 深度学习特征权重
        self.phash_weight = 0.2  # PHash权重
        
        # 相似度排序的参考图片
        self.similarity_reference = None
        
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
                current_phash_weight=self.phash_weight
            )
            
            result = dialog.wait_window()
            
            if result:
                self.dl_weight, self.phash_weight = result
                # 保存权重设置
                self.save_weights()
                # 更新按钮文本显示当前权重
                settings_text = f"⚙️ 权重设置 (DL:{int(self.dl_weight*100)}% PHash:{int(self.phash_weight*100)}%)"
                settings_btn.config(text=settings_text)
        
        # UI组件
        from tkinter import ttk
        ttk.Label(choice_dialog, text="请选择图片来源：", font=('TkDefaultFont', 11, 'bold')).pack(pady=15)
        
        btn_frame = ttk.Frame(choice_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📁 从文件选择", command=select_from_file, width=18).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📋 从剪贴板", command=select_from_clipboard, width=18).pack(side=tk.LEFT, padx=10)
        
        settings_text = f"⚙️ 权重设置 (DL:{int(self.dl_weight*100)}% PHash:{int(self.phash_weight*100)}%)"
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
            
            all_results = all_results_getter()
            if not all_results:
                messagebox.showwarning("提示", "当前没有搜索结果")
                return
            
            # 排序
            sorted_results, sort_method = self._sort_results(all_results, reference_image)
            
            # 保存参考图片
            self.similarity_reference = reference_image
            
            # 更新结果
            all_results_setter(sorted_results)
            
            # 更新排序说明
            img_name = image_path.name
            self.sort_info_label.config(
                text=f"(已按与 {img_name} 的相似度排序)",
                foreground="blue"
            )
            
            # 重新渲染
            render_callback()
            
            messagebox.showinfo("成功", f"已按与 {img_name} 的相似度排序\n使用：{sort_method}")
            
        except Exception as e:
            logger.error(f"以图搜图失败: {e}")
            messagebox.showerror("错误", f"以图搜图失败：{e}")
    
    def sort_by_similarity(self, all_results, reference_path):
        """
        以指定图片为参考进行相似度排序
        
        Args:
            all_results: 结果列表
            reference_path: 参考图片路径
            
        Returns:
            list: 排序后的结果列表
        """
        if not all_results:
            return all_results
        
        try:
            image_path = Path(reference_path)
            if not image_path.exists():
                messagebox.showerror("错误", "参考图片不存在")
                return all_results
            
            # 先尝试从all_results中找到该图片的数据（优先使用数据库特征）
            reference_image = None
            for img in all_results:
                if img.get('file_path') == reference_path:
                    reference_image = img.copy()
                    break
            
            # 如果数据库中有特征，直接使用
            if reference_image and reference_image.get('phash'):
                logger.info("使用数据库中的特征进行相似度排序")
                dl_features = reference_image.get('dl_features')
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
            
            # 保存参考图片
            self.similarity_reference = reference_image
            
            # 排序
            sorted_results, sort_method = self._sort_results(all_results, reference_image)
            
            # 更新排序说明
            ref_name = image_path.name
            self.sort_info_label.config(
                text=f"（已按与 {ref_name} 的相似度排序）",
                foreground="green"
            )
            
            messagebox.showinfo("成功", f"已按与 {ref_name} 的相似度排序\n使用：{sort_method}")
            
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
    
    def open_settings(self):
        """打开以图搜图权重设置对话框"""
        from .similarity_settings_dialog import SimilaritySettingsDialog
        
        dialog = SimilaritySettingsDialog(
            self.frame.winfo_toplevel(),
            current_dl_weight=self.dl_weight,
            current_phash_weight=self.phash_weight
        )
        
        result = dialog.wait_window()
        
        if result:
            self.dl_weight, self.phash_weight = result
            messagebox.showinfo(
                "设置已保存",
                f"以图搜图权重已更新：\n"
                f"深度学习: {int(self.dl_weight*100)}%\n"
                f"PHash: {int(self.phash_weight*100)}%"
            )
            self.save_weights()
    
    def load_weights(self):
        """从配置文件加载以图搜图权重"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.dl_weight = config.get('dl_weight', 0.8)
                    self.phash_weight = config.get('phash_weight', 0.2)
                    logger.debug(f"已加载权重设置: DL={self.dl_weight}, PHash={self.phash_weight}")
        except Exception as e:
            logger.warning(f"加载权重设置失败，使用默认值: {e}")
    
    def save_weights(self):
        """保存以图搜图权重到配置文件"""
        try:
            # 读取现有配置
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新权重
            config['dl_weight'] = self.dl_weight
            config['phash_weight'] = self.phash_weight
            
            # 保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"权重设置已保存: DL={self.dl_weight}, PHash={self.phash_weight}")
        except Exception as e:
            logger.error(f"保存权重设置失败: {e}")
