#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表情包查找器 - Windows GUI 版本
功能：
1. 选择多个图源文件夹
2. 检测图源更新
3. OCR文本识别
4. 情绪分类（正向/负向/中性）
5. 文本模糊搜索
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading


class ImageDatabase:
    """图片数据库管理"""
    
    def __init__(self, db_path: str = "meme_finder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 图源文件夹表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                added_time TEXT NOT NULL,
                last_scan_time TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        # 图片信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                source_id INTEGER,
                ocr_text TEXT,
                filtered_text TEXT,
                emotion TEXT,
                emotion_positive REAL,
                emotion_negative REAL,
                added_time TEXT NOT NULL,
                processed INTEGER DEFAULT 0,
                FOREIGN KEY (source_id) REFERENCES image_sources(id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON images(file_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emotion ON images(emotion)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed ON images(processed)
        """)
        
        conn.commit()
        conn.close()
    
    def add_source(self, folder_path: str) -> bool:
        """添加图源文件夹"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO image_sources (folder_path, added_time)
                VALUES (?, ?)
            """, (folder_path, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_sources(self) -> List[Dict]:
        """获取所有图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, folder_path, added_time, last_scan_time, enabled
            FROM image_sources
            ORDER BY added_time DESC
        """)
        sources = []
        for row in cursor.fetchall():
            sources.append({
                'id': row[0],
                'folder_path': row[1],
                'added_time': row[2],
                'last_scan_time': row[3],
                'enabled': bool(row[4])
            })
        conn.close()
        return sources
    
    def remove_source(self, source_id: int):
        """删除图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # 删除相关图片
        cursor.execute("DELETE FROM images WHERE source_id = ?", (source_id,))
        # 删除图源
        cursor.execute("DELETE FROM image_sources WHERE id = ?", (source_id,))
        conn.commit()
        conn.close()
    
    def toggle_source(self, source_id: int, enabled: bool):
        """启用/禁用图源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE image_sources 
            SET enabled = ?
            WHERE id = ?
        """, (1 if enabled else 0, source_id))
        conn.commit()
        conn.close()
    
    def update_scan_time(self, source_id: int):
        """更新扫描时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE image_sources 
            SET last_scan_time = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), source_id))
        conn.commit()
        conn.close()
    
    def get_image_hashes(self, source_id: int = None) -> Set[str]:
        """获取已存在的图片哈希值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if source_id:
            cursor.execute("SELECT file_hash FROM images WHERE source_id = ?", (source_id,))
        else:
            cursor.execute("SELECT file_hash FROM images")
        hashes = {row[0] for row in cursor.fetchall()}
        conn.close()
        return hashes
    
    def add_image(self, file_path: str, file_hash: str, source_id: int):
        """添加新图片"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO images (file_path, file_hash, source_id, added_time)
                VALUES (?, ?, ?, ?)
            """, (file_path, file_hash, source_id, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_unprocessed_images(self, limit: int = 100) -> List[Dict]:
        """获取未处理的图片"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, source_id
            FROM images
            WHERE processed = 0
            LIMIT ?
        """, (limit,))
        images = []
        for row in cursor.fetchall():
            images.append({
                'id': row[0],
                'file_path': row[1],
                'source_id': row[2]
            })
        conn.close()
        return images
    
    def update_image_data(self, image_id: int, ocr_text: str, filtered_text: str, 
                         emotion: str, pos_score: float, neg_score: float):
        """更新图片处理结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE images 
            SET ocr_text = ?, filtered_text = ?, emotion = ?,
                emotion_positive = ?, emotion_negative = ?, processed = 1
            WHERE id = ?
        """, (ocr_text, filtered_text, emotion, pos_score, neg_score, image_id))
        conn.commit()
        conn.close()
    
    def search_images(self, keyword: str = "", emotion: str = "") -> List[Dict]:
        """搜索图片"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, file_path, filtered_text, emotion, 
                   emotion_positive, emotion_negative
            FROM images
            WHERE processed = 1
        """
        params = []
        
        if keyword:
            query += " AND (filtered_text LIKE ? OR ocr_text LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if emotion:
            query += " AND emotion = ?"
            params.append(emotion)
        
        query += " ORDER BY added_time DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'file_path': row[1],
                'text': row[2],
                'emotion': row[3],
                'pos_score': row[4],
                'neg_score': row[5]
            })
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总图片数
        cursor.execute("SELECT COUNT(*) FROM images")
        total = cursor.fetchone()[0]
        
        # 已处理数
        cursor.execute("SELECT COUNT(*) FROM images WHERE processed = 1")
        processed = cursor.fetchone()[0]
        
        # 情绪分布
        cursor.execute("""
            SELECT emotion, COUNT(*) 
            FROM images 
            WHERE processed = 1 
            GROUP BY emotion
        """)
        emotions = dict(cursor.fetchall())
        
        conn.close()
        return {
            'total': total,
            'processed': processed,
            'unprocessed': total - processed,
            'emotions': emotions
        }


class MemeFinderGUI:
    """表情包查找器GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("表情包查找器 - MEMEFinder")
        self.root.geometry("1000x700")
        
        # 数据库
        self.db = ImageDatabase()
        
        # 图片扩展名
        self.img_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif', '.tiff'}
        
        # 创建界面
        self.create_widgets()
        
        # 加载图源列表
        self.refresh_sources()
        
        # 更新统计信息
        self.update_statistics()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建笔记本（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 图源管理标签页
        self.create_source_tab()
        
        # 图片处理标签页
        self.create_process_tab()
        
        # 图片搜索标签页
        self.create_search_tab()
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_source_tab(self):
        """创建图源管理标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="图源管理")
        
        # 顶部按钮区
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="➕ 添加图源文件夹", 
                  command=self.add_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除选中", 
                  command=self.remove_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新列表", 
                  command=self.refresh_sources).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 扫描新图片", 
                  command=self.scan_sources).pack(side=tk.LEFT, padx=5)
        
        # 图源列表
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ('路径', '添加时间', '最后扫描', '状态')
        self.source_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        # 设置列
        self.source_tree.heading('#0', text='ID')
        self.source_tree.column('#0', width=50)
        for col in columns:
            self.source_tree.heading(col, text=col)
        
        self.source_tree.column('路径', width=400)
        self.source_tree.column('添加时间', width=150)
        self.source_tree.column('最后扫描', width=150)
        self.source_tree.column('状态', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.source_tree.yview)
        self.source_tree.configure(yscrollcommand=scrollbar.set)
        
        self.source_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self.source_menu = tk.Menu(self.root, tearoff=0)
        self.source_menu.add_command(label="打开文件夹", command=self.open_source_folder)
        self.source_menu.add_command(label="启用/禁用", command=self.toggle_source)
        self.source_menu.add_separator()
        self.source_menu.add_command(label="删除", command=self.remove_source)
        
        self.source_tree.bind("<Button-3>", self.show_source_menu)
        
        # 统计信息区
        stats_frame = ttk.LabelFrame(frame, text="统计信息", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.StringVar(value="总图片: 0 | 已处理: 0 | 未处理: 0")
        ttk.Label(stats_frame, textvariable=self.stats_text, font=('Arial', 10)).pack()
    
    def create_process_tab(self):
        """创建图片处理标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="图片处理")
        
        # 顶部按钮区
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="▶️ 开始处理", 
                  command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏸️ 暂停", 
                  command=self.pause_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹️ 停止", 
                  command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        
        # 进度信息
        progress_frame = ttk.LabelFrame(frame, text="处理进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack()
        
        # 日志输出
        log_frame = ttk.LabelFrame(frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 处理状态
        self.processing = False
        self.processing_thread = None
    
    def create_search_tab(self):
        """创建图片搜索标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="图片搜索")
        
        # 搜索条件区
        search_frame = ttk.LabelFrame(frame, text="搜索条件", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 关键词搜索
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_keyword = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_keyword, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 情绪筛选
        ttk.Label(search_frame, text="情绪:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.search_emotion = tk.StringVar()
        emotion_combo = ttk.Combobox(search_frame, textvariable=self.search_emotion, 
                                     values=['', '正向', '负向', '中性'], width=10, state='readonly')
        emotion_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        emotion_combo.set('')
        
        # 搜索按钮
        ttk.Button(search_frame, text="🔍 搜索", 
                  command=self.search_images).grid(row=0, column=4, padx=10)
        
        # 结果列表
        result_frame = ttk.LabelFrame(frame, text="搜索结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ('文本内容', '情绪', '正向分数', '负向分数', '图片路径')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        for col in columns:
            self.result_tree.heading(col, text=col)
        
        self.result_tree.column('文本内容', width=300)
        self.result_tree.column('情绪', width=80)
        self.result_tree.column('正向分数', width=100)
        self.result_tree.column('负向分数', width=100)
        self.result_tree.column('图片路径', width=300)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击打开图片
        self.result_tree.bind("<Double-1>", self.open_image)
    
    # ==================== 图源管理功能 ====================
    
    def add_source(self):
        """添加图源文件夹"""
        folder = filedialog.askdirectory(title="选择图源文件夹")
        if folder:
            if self.db.add_source(folder):
                messagebox.showinfo("成功", f"已添加图源：{folder}")
                self.refresh_sources()
                self.update_statistics()
            else:
                messagebox.showwarning("警告", "该文件夹已存在")
    
    def remove_source(self):
        """删除选中的图源"""
        selected = self.source_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的图源")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的图源吗？\n这将同时删除该图源的所有图片记录。"):
            for item in selected:
                source_id = int(self.source_tree.item(item)['text'])
                self.db.remove_source(source_id)
            self.refresh_sources()
            self.update_statistics()
            messagebox.showinfo("成功", "已删除选中的图源")
    
    def refresh_sources(self):
        """刷新图源列表"""
        # 清空列表
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        
        # 重新加载
        sources = self.db.get_sources()
        for source in sources:
            status = "✓ 启用" if source['enabled'] else "✗ 禁用"
            last_scan = source['last_scan_time'] or "未扫描"
            self.source_tree.insert('', tk.END, text=source['id'],
                                   values=(source['folder_path'], 
                                          source['added_time'][:19],
                                          last_scan[:19] if last_scan != "未扫描" else last_scan,
                                          status))
    
    def show_source_menu(self, event):
        """显示右键菜单"""
        item = self.source_tree.identify_row(event.y)
        if item:
            self.source_tree.selection_set(item)
            self.source_menu.post(event.x_root, event.y_root)
    
    def open_source_folder(self):
        """打开图源文件夹"""
        selected = self.source_tree.selection()
        if selected:
            item = selected[0]
            folder_path = self.source_tree.item(item)['values'][0]
            if os.path.exists(folder_path):
                os.startfile(folder_path)
            else:
                messagebox.showerror("错误", "文件夹不存在")
    
    def toggle_source(self):
        """启用/禁用图源"""
        selected = self.source_tree.selection()
        if selected:
            item = selected[0]
            source_id = int(self.source_tree.item(item)['text'])
            status = self.source_tree.item(item)['values'][3]
            enabled = "✗" in status
            self.db.toggle_source(source_id, enabled)
            self.refresh_sources()
    
    def scan_sources(self):
        """扫描图源中的新图片"""
        self.log_message("开始扫描图源...")
        
        sources = self.db.get_sources()
        enabled_sources = [s for s in sources if s['enabled']]
        
        if not enabled_sources:
            messagebox.showwarning("警告", "没有启用的图源")
            return
        
        total_new = 0
        for source in enabled_sources:
            folder_path = source['folder_path']
            if not os.path.exists(folder_path):
                self.log_message(f"[警告] 文件夹不存在: {folder_path}")
                continue
            
            self.log_message(f"扫描: {folder_path}")
            
            # 获取已存在的图片哈希
            existing_hashes = self.db.get_image_hashes(source['id'])
            
            # 扫描文件夹
            new_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.img_extensions:
                        file_path = os.path.join(root, file)
                        file_hash = self.calculate_file_hash(file_path)
                        
                        if file_hash not in existing_hashes:
                            if self.db.add_image(file_path, file_hash, source['id']):
                                new_count += 1
                                existing_hashes.add(file_hash)
            
            self.db.update_scan_time(source['id'])
            self.log_message(f"  发现新图片: {new_count} 张")
            total_new += new_count
        
        self.refresh_sources()
        self.update_statistics()
        self.log_message(f"扫描完成！共发现 {total_new} 张新图片")
        messagebox.showinfo("完成", f"扫描完成！\n发现新图片: {total_new} 张")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"error_{os.path.basename(file_path)}"
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.db.get_statistics()
        emotions = stats['emotions']
        emotion_str = " | ".join([f"{k}: {v}" for k, v in emotions.items()])
        
        text = f"总图片: {stats['total']} | 已处理: {stats['processed']} | 未处理: {stats['unprocessed']}"
        if emotion_str:
            text += f" | {emotion_str}"
        
        self.stats_text.set(text)
    
    # ==================== 图片处理功能 ====================
    
    def start_processing(self):
        """开始处理图片"""
        if self.processing:
            messagebox.showinfo("提示", "正在处理中...")
            return
        
        unprocessed = self.db.get_unprocessed_images(limit=1)
        if not unprocessed:
            messagebox.showinfo("提示", "没有待处理的图片")
            return
        
        self.processing = True
        self.log_message("=" * 50)
        self.log_message("准备开始处理图片...")
        self.log_message("注意: OCR和情绪分析功能将在下一步实现")
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
    
    def stop_processing(self):
        """停止处理"""
        if self.processing:
            self.processing = False
            self.log_message("[停止] 处理已停止")
    
    def process_images_thread(self):
        """处理图片的线程（占位实现）"""
        self.log_message("[INFO] 开始处理...")
        
        # TODO: 在后续步骤中实现OCR和情绪分析
        # 这里只是示例代码
        import time
        for i in range(5):
            if not self.processing:
                break
            self.log_message(f"[{i+1}/5] 模拟处理...")
            time.sleep(1)
        
        self.processing = False
        self.log_message("[完成] 处理结束")
        self.update_statistics()
    
    # ==================== 图片搜索功能 ====================
    
    def search_images(self):
        """搜索图片"""
        keyword = self.search_keyword.get().strip()
        emotion = self.search_emotion.get()
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 搜索
        results = self.db.search_images(keyword, emotion)
        
        # 显示结果
        for result in results:
            text = result['text'][:50] + '...' if result['text'] and len(result['text']) > 50 else result['text']
            self.result_tree.insert('', tk.END, values=(
                text or '(无文本)',
                result['emotion'] or '未分类',
                f"{result['pos_score']:.2f}" if result['pos_score'] else 'N/A',
                f"{result['neg_score']:.2f}" if result['neg_score'] else 'N/A',
                result['file_path']
            ))
        
        self.status_bar.config(text=f"找到 {len(results)} 个结果")
    
    def open_image(self, event):
        """打开选中的图片"""
        selected = self.result_tree.selection()
        if selected:
            item = selected[0]
            file_path = self.result_tree.item(item)['values'][4]
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                messagebox.showerror("错误", "图片文件不存在")
    
    # ==================== 辅助功能 ====================
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()


def main():
    root = tk.Tk()
    app = MemeFinderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
