#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canvas渲染器模块
"""

import io
import os
from tkinter import font as tkfont
from PIL import Image, ImageTk


class CanvasRenderer:
    """Canvas渲染器 - 负责图片列表的虚拟化渲染"""
    
    def __init__(self, canvas, thumb_size_var, thumb_padding=20):
        """
        Args:
            canvas: Canvas控件
            thumb_size_var: 缩略图大小变量
            thumb_padding: 缩略图间距
        """
        self.canvas = canvas
        self.thumb_size_var = thumb_size_var
        self.thumb_padding = thumb_padding
        
        # Canvas Items 引用
        self.canvas_items = {}  # {key: [item_ids]}
        self.image_refs = {}    # {key: PhotoImage}
        self.item_paths = {}    # {key: file_path}
        self.event_rects = {}   # {key: (x1, y1, x2, y2)}
        
        # 布局参数
        self.cell_height = 200
        self.cell_width = 140
        self.cols = 4
        
        # 字体对象
        self.text_font = tkfont.Font(family="TkDefaultFont", size=9)
        self.emotion_font = tkfont.Font(family="TkDefaultFont", size=8)
    
    def clear_all(self):
        """清空所有Canvas内容"""
        self.canvas.delete('all')
        self.canvas_items.clear()
        self.image_refs.clear()
        self.item_paths.clear()
        self.event_rects.clear()
    
    def calculate_layout(self, canvas_width):
        """计算布局参数"""
        thumb_side = int(self.thumb_size_var.get())
        cell_width = thumb_side + self.thumb_padding
        cols = max(1, canvas_width // cell_width)
        cell_height = self._calculate_cell_height(thumb_side)
        
        self.cols = cols
        self.cell_width = cell_width
        self.cell_height = cell_height
        
        return cols, cell_width, cell_height
    
    def _calculate_cell_height(self, thumb_side):
        """精确计算单元格高度"""
        top_padding = 10
        image_height = thumb_side
        image_text_gap = 10
        line_height = self.text_font.metrics('linespace')
        text_height = line_height * 2 + 5
        text_emotion_gap = 8
        emotion_height = self.emotion_font.metrics('linespace') + 4
        bottom_padding = 15
        
        total_height = (top_padding + image_height + image_text_gap + 
                       text_height + text_emotion_gap + emotion_height + bottom_padding)
        
        return total_height
    
    def set_scrollregion(self, total_rows):
        """设置滚动区域"""
        canvas_width = max(400, self.canvas.winfo_width())
        total_height = total_rows * self.cell_height + 50
        self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height))
    
    def get_visible_range(self):
        """计算可见行范围"""
        try:
            canvas_top = self.canvas.canvasy(0)
            canvas_bottom = self.canvas.canvasy(self.canvas.winfo_height())
            
            first_visible_row = max(0, int(canvas_top / self.cell_height) - 2)
            last_visible_row = int(canvas_bottom / self.cell_height) + 2
            
            return first_visible_row, last_visible_row
        except:
            return 0, 10
    
    def render_visible_items(self, results, selected_items, favorite_cache):
        """渲染可见项"""
        if not results:
            return
        
        first_row, last_row = self.get_visible_range()
        
        # 计算需要渲染的项目
        items_to_render = set()
        for idx in range(len(results)):
            r = idx // self.cols
            if first_row <= r <= last_row:
                items_to_render.add(idx)
        
        # 删除不可见的Canvas Items
        to_remove = []
        for key in list(self.canvas_items.keys()):
            try:
                idx = int(key.split('_')[-1])
                if idx not in items_to_render:
                    to_remove.append(key)
            except:
                pass
        
        for key in to_remove:
            if key in self.canvas_items:
                for item_id in self.canvas_items[key]:
                    self.canvas.delete(item_id)
                del self.canvas_items[key]
            
            self.image_refs.pop(key, None)
            self.item_paths.pop(key, None)
            self.event_rects.pop(key, None)
        
        # 渲染新项目
        MAX_THUMB_SIZE = 150
        thumb_side = min(int(self.thumb_size_var.get()), MAX_THUMB_SIZE)
        
        for idx in items_to_render:
            r = idx // self.cols
            c = idx % self.cols
            key = f"{r}_{c}_{idx}"
            
            if key in self.canvas_items:
                continue
            
            result = results[idx]
            file_path = result.get('file_path') or ''
            
            # 计算布局位置
            cell_x = c * self.cell_width
            cell_y = r * self.cell_height
            center_x = cell_x + self.cell_width // 2
            
            items = []
            
            # 1. 背景矩形
            bg_rect = self.canvas.create_rectangle(
                cell_x + 5, cell_y + 5,
                cell_x + self.cell_width - 5, cell_y + self.cell_height - 5,
                fill='white', outline='#ddd', width=1, tags=key
            )
            items.append(bg_rect)
            
            # 2. 缩略图
            image_y = cell_y + 10
            imgtk = self._load_thumbnail(file_path, thumb_side)
            if imgtk:
                img_id = self.canvas.create_image(
                    center_x, image_y + thumb_side // 2,
                    image=imgtk, tags=key
                )
                items.append(img_id)
                self.image_refs[key] = imgtk
            else:
                text_id = self.canvas.create_text(
                    center_x, image_y + thumb_side // 2,
                    text='(无法加载)', fill='gray', font=self.text_font, tags=key
                )
                items.append(text_id)
            
            # 3. 文本
            text_y = image_y + thumb_side + 10
            raw_text = result['text'] or ''
            text_max_width = self.cell_width - 20
            truncated_text = self._truncate_text(raw_text, text_max_width, max_lines=2)
            
            text_id = self.canvas.create_text(
                center_x, text_y, text=truncated_text, fill='black',
                font=self.text_font, width=text_max_width, anchor='n', tags=key
            )
            items.append(text_id)
            
            # 4. 情绪标签
            emotion_bottom_offset = 10
            emotion_height = self.emotion_font.metrics('linespace')
            emotion_y = cell_y + self.cell_height - emotion_bottom_offset - emotion_height
            
            emotion = result['emotion'] or '未分类'
            emotion_color = {'正向': 'green', '负向': 'red', '中性': 'blue'}.get(emotion, 'gray')
            emotion_id = self.canvas.create_text(
                center_x, emotion_y, text=emotion, fill=emotion_color,
                font=self.emotion_font, anchor='n', tags=key
            )
            items.append(emotion_id)
            
            # 5. 复选框
            checkbox_size = 16
            checkbox_x = cell_x + self.cell_width - 8 - checkbox_size
            checkbox_y = cell_y + 8
            
            checkbox_bg = self.canvas.create_rectangle(
                checkbox_x, checkbox_y,
                checkbox_x + checkbox_size, checkbox_y + checkbox_size,
                fill='white', outline='#999', width=2,
                tags=(key, f'{key}_checkbox')
            )
            items.append(checkbox_bg)
            
            if file_path in selected_items:
                check_mark = self.canvas.create_text(
                    checkbox_x + checkbox_size // 2,
                    checkbox_y + checkbox_size // 2,
                    text='✓', fill='#1976d2', font=('TkDefaultFont', 12, 'bold'),
                    tags=(key, f'{key}_checkbox')
                )
                items.append(check_mark)
            
            # 6. 爱心图标
            heart_size = 20
            heart_x = cell_x + 8
            heart_y = cell_y + 8
            
            is_favorite = favorite_cache.get(file_path, result.get('is_favorite', False))
            
            if is_favorite:
                heart_text = '❤'
                heart_color = '#ff4757'
                heart_font = ('Segoe UI Emoji', 16, 'normal')
            else:
                heart_text = '♥'
                heart_color = '#dfe4ea'
                heart_font = ('Segoe UI Emoji', 16, 'normal')
            
            heart_id = self.canvas.create_text(
                heart_x + heart_size // 2, heart_y + heart_size // 2,
                text=heart_text, fill=heart_color, font=heart_font,
                tags=(key, f'{key}_favorite')
            )
            items.append(heart_id)
            
            # 保存
            self.canvas_items[key] = items
            self.item_paths[key] = file_path
            self.event_rects[key] = (
                cell_x + 5, cell_y + 5,
                cell_x + self.cell_width - 5, cell_y + self.cell_height - 5
            )
    
    def _load_thumbnail(self, file_path, thumb_side):
        """加载缩略图"""
        try:
            if not file_path or not os.path.exists(file_path):
                return None
            
            img = Image.open(file_path)
            img.thumbnail((thumb_side, thumb_side), Image.Resampling.LANCZOS)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img.close()
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=70, optimize=True)
            buffer.seek(0)
            img.close()
            del img
            
            compressed_img = Image.open(buffer)
            imgtk = ImageTk.PhotoImage(compressed_img)
            compressed_img.close()
            buffer.close()
            
            return imgtk
        except Exception as e:
            return None
    
    def _truncate_text(self, text, max_width, max_lines=2):
        """截断文本确保不超过指定行数和宽度"""
        if not text:
            return "(无文本)"
        
        words = text.replace('\n', ' ').split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            width = self.text_font.measure(test_line)
            
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = word
                
                if len(lines) >= max_lines - 1:
                    while self.text_font.measure(current_line + "...") > max_width and len(current_line) > 0:
                        current_line = current_line[:-1]
                    lines.append(current_line + "...")
                    break
        else:
            if current_line:
                lines.append(current_line)
        
        return '\n'.join(lines[:max_lines])
    
    def update_checkbox_display(self, key, is_selected):
        """更新复选框显示"""
        if key not in self.canvas_items or key not in self.event_rects:
            return
        
        # 删除旧的复选框
        for item_id in self.canvas.find_withtag(f'{key}_checkbox'):
            self.canvas.delete(item_id)
        
        # 重新绘制
        x1, y1, x2, y2 = self.event_rects[key]
        checkbox_size = 16
        checkbox_x = x2 - 8 - checkbox_size
        checkbox_y = y1 + 3
        
        self.canvas.create_rectangle(
            checkbox_x, checkbox_y,
            checkbox_x + checkbox_size, checkbox_y + checkbox_size,
            fill='white', outline='#999', width=2,
            tags=(key, f'{key}_checkbox')
        )
        
        if is_selected:
            self.canvas.create_text(
                checkbox_x + checkbox_size // 2,
                checkbox_y + checkbox_size // 2,
                text='✓', fill='#1976d2', font=('TkDefaultFont', 12, 'bold'),
                tags=(key, f'{key}_checkbox')
            )
    
    def update_favorite_display(self, key, is_favorite):
        """更新爱心显示"""
        if key not in self.canvas_items or key not in self.event_rects:
            return
        
        # 删除旧的爱心
        for item_id in self.canvas.find_withtag(f'{key}_favorite'):
            self.canvas.delete(item_id)
        
        # 重新绘制
        x1, y1, x2, y2 = self.event_rects[key]
        heart_size = 20
        heart_x = x1 + 3
        heart_y = y1 + 3
        
        if is_favorite:
            heart_text = '❤'
            heart_color = '#ff4757'
            heart_font = ('Segoe UI Emoji', 16, 'normal')
        else:
            heart_text = '♥'
            heart_color = '#dfe4ea'
            heart_font = ('Segoe UI Emoji', 16, 'normal')
        
        self.canvas.create_text(
            heart_x + heart_size // 2, heart_y + heart_size // 2,
            text=heart_text, fill=heart_color, font=heart_font,
            tags=(key, f'{key}_favorite')
        )
    
    def update_hover_highlight(self, key, is_hover):
        """更新悬停高亮"""
        if key and key in self.canvas_items:
            bg_rect = self.canvas_items[key][0]
            if is_hover:
                self.canvas.itemconfig(bg_rect, fill='#e3f2fd', outline='#1976d2', width=2)
            else:
                self.canvas.itemconfig(bg_rect, fill='white', outline='#ddd', width=1)
    
    def get_item_at_pos(self, x, y):
        """获取鼠标位置的item key"""
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        for key, (x1, y1, x2, y2) in self.event_rects.items():
            if x1 <= canvas_x <= x2 and y1 <= canvas_y <= y2:
                return key
        return None
    
    def is_click_on_checkbox(self, key, x, y):
        """判断点击是否在复选框区域"""
        if key not in self.event_rects:
            return False
        
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        x1, y1, x2, y2 = self.event_rects[key]
        checkbox_size = 16
        checkbox_x = x2 - 8 - checkbox_size
        checkbox_y = y1 + 3
        
        return (checkbox_x <= canvas_x <= checkbox_x + checkbox_size and
                checkbox_y <= canvas_y <= checkbox_y + checkbox_size)
    
    def is_click_on_favorite(self, key, x, y):
        """判断点击是否在爱心区域"""
        if key not in self.event_rects:
            return False
        
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        x1, y1, x2, y2 = self.event_rects[key]
        heart_size = 20
        heart_x = x1 + 3
        heart_y = y1 + 3
        
        return (heart_x <= canvas_x <= heart_x + heart_size and
                heart_y <= canvas_y <= heart_y + heart_size)
