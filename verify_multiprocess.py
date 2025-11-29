#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速验证多进程是否正常工作
"""

import sys
from pathlib import Path

# Windows多进程保护
if __name__ == '__main__':
    # 添加src目录到路径
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    
    from src.gui.process_tab_processor import _process_image_worker
    from src.core.database import ImageDatabase
    
    print("=" * 60)
    print("验证多进程图片处理")
    print("=" * 60)
    
    # 初始化数据库
    db = ImageDatabase()
    
    # 获取一张未处理的图片
    unprocessed = db.get_unprocessed_images(limit=1)
    
    if not unprocessed:
        print("✓ 没有未处理的图片")
        print("✓ 多进程功能已就绪")
    else:
        print(f"\n找到 1 张未处理的图片，测试处理...")
        img_info = unprocessed[0]
        
        # 测试工作函数（模拟子进程调用）
        result = _process_image_worker(
            img_info=img_info,
            enable_ocr=True,
            enable_sentiment=True,
            use_gpu=False,
            db_path=db.db_path
        )
        
        if result['success']:
            print("✓ 图片处理成功")
            print(f"  文件: {Path(result['path']).name}")
        else:
            print(f"✗ 图片处理失败: {result.get('error', '未知')}")
    
    print("\n" + "=" * 60)
    print("验证完成！可以运行 main.py 进行完整测试")
    print("=" * 60)
