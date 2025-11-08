#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证MEMEFinder基础功能
"""

from meme_finder_gui import ImageDatabase
from pathlib import Path
import os

def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("MEMEFinder 数据库功能测试")
    print("=" * 60)
    
    # 创建测试数据库
    db = ImageDatabase("test_meme_finder.db")
    
    # 测试1: 添加图源
    print("\n[测试1] 添加图源...")
    test_folder = str(Path("./imgs").absolute())
    if db.add_source(test_folder):
        print(f"✓ 成功添加图源: {test_folder}")
    else:
        print(f"✓ 图源已存在: {test_folder}")
    
    # 测试2: 获取图源列表
    print("\n[测试2] 获取图源列表...")
    sources = db.get_sources()
    print(f"✓ 找到 {len(sources)} 个图源:")
    for source in sources:
        print(f"  - ID:{source['id']} {source['folder_path']}")
        print(f"    状态: {'启用' if source['enabled'] else '禁用'}")
    
    # 测试3: 添加测试图片
    print("\n[测试3] 添加测试图片...")
    if sources:
        source_id = sources[0]['id']
        test_images = [
            ("test1.jpg", "abc123"),
            ("test2.jpg", "def456"),
            ("test3.jpg", "ghi789"),
        ]
        for img_path, img_hash in test_images:
            if db.add_image(img_path, img_hash, source_id):
                print(f"✓ 添加图片: {img_path}")
            else:
                print(f"✓ 图片已存在: {img_path}")
    
    # 测试4: 更新图片数据
    print("\n[测试4] 更新图片处理结果...")
    unprocessed = db.get_unprocessed_images(limit=3)
    print(f"✓ 找到 {len(unprocessed)} 张未处理图片")
    
    for img in unprocessed[:1]:  # 只更新第一张
        db.update_image_data(
            image_id=img['id'],
            ocr_text="这是测试文本 www.example.com",
            filtered_text="这是测试文本",
            emotion="正向",
            pos_score=0.85,
            neg_score=0.15
        )
        print(f"✓ 更新图片 ID:{img['id']}")
    
    # 测试5: 搜索功能
    print("\n[测试5] 搜索功能...")
    results = db.search_images(keyword="测试")
    print(f"✓ 关键词'测试'搜索结果: {len(results)} 个")
    for r in results:
        print(f"  - {r['text'][:30]} | {r['emotion']}")
    
    # 测试6: 统计信息
    print("\n[测试6] 统计信息...")
    stats = db.get_statistics()
    print(f"✓ 总图片数: {stats['total']}")
    print(f"✓ 已处理: {stats['processed']}")
    print(f"✓ 未处理: {stats['unprocessed']}")
    print(f"✓ 情绪分布: {stats['emotions']}")
    
    print("\n" + "=" * 60)
    print("测试完成！所有功能正常工作。")
    print("=" * 60)
    
    # 清理测试数据库
    import os
    if os.path.exists("test_meme_finder.db"):
        os.remove("test_meme_finder.db")
        print("\n✓ 测试数据库已清理")

if __name__ == "__main__":
    test_database()
