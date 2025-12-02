#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加收藏字段
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str = "meme_finder.db"):
    """为数据库添加is_favorite字段"""
    
    print(f"开始迁移数据库: {db_path}")
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_favorite' in columns:
            print("✓ is_favorite 字段已存在，无需迁移")
            conn.close()
            return True
        
        print("正在添加 is_favorite 字段...")
        
        # 添加is_favorite字段
        cursor.execute("""
            ALTER TABLE images 
            ADD COLUMN is_favorite INTEGER DEFAULT 0
        """)
        
        print("✓ is_favorite 字段添加成功")
        
        # 创建索引
        print("正在创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_favorite ON images(is_favorite)
        """)
        
        print("✓ 索引创建成功")
        
        # 提交更改
        conn.commit()
        
        # 验证
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_favorite' in columns:
            print("✓ 迁移验证成功")
            
            # 统计信息
            cursor.execute("SELECT COUNT(*) FROM images")
            total_images = cursor.fetchone()[0]
            print(f"✓ 数据库共有 {total_images} 张图片")
            print(f"✓ 所有图片的 is_favorite 默认值已设置为 0（未收藏）")
            
            conn.close()
            return True
        else:
            print("❌ 迁移验证失败")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    db_path = "meme_finder.db"
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print("=" * 60)
    print("数据库迁移脚本 - 添加收藏功能")
    print("=" * 60)
    print()
    
    success = migrate_database(db_path)
    
    print()
    print("=" * 60)
    if success:
        print("🎉 迁移完成！现在可以使用收藏功能了。")
    else:
        print("⚠️  迁移失败，请检查错误信息。")
    print("=" * 60)
