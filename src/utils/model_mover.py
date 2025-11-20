#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型文件移动工具 - 将RapidOCR模型从默认位置移动到项目目录
"""

import shutil
from pathlib import Path
from typing import List, Tuple


def find_rapidocr_models() -> List[Path]:
    """
    查找RapidOCR模型文件的所有可能位置
    
    Returns:
        List[Path]: 包含模型文件的目录列表
    """
    home_dir = Path.home()
    possible_locations = [
        home_dir / '.rapidocr',
        home_dir / '.cache' / 'rapidocr',
        home_dir / '.RapidOCR',
        home_dir / 'AppData' / 'Local' / 'rapidocr',
        home_dir / 'AppData' / 'Local' / '.rapidocr',
    ]
    
    found_locations = []
    for loc in possible_locations:
        if loc.exists():
            onnx_files = list(loc.rglob('*.onnx'))
            if onnx_files:
                found_locations.append(loc)
    
    return found_locations


def move_models_to_target(source_dir: Path, target_dir: Path) -> Tuple[int, int]:
    """
    将模型文件从源目录移动到目标目录
    
    Args:
        source_dir: 源目录
        target_dir: 目标目录
        
    Returns:
        (成功数量, 失败数量)
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    
    onnx_files = list(source_dir.rglob('*.onnx'))
    success_count = 0
    fail_count = 0
    
    for src_file in onnx_files:
        try:
            # 保持相对路径结构
            rel_path = src_file.relative_to(source_dir)
            dst_file = target_dir / rel_path
            
            # 创建目标目录
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果目标文件已存在，跳过
            if dst_file.exists():
                continue
            
            # 复制文件
            shutil.copy2(src_file, dst_file)
            success_count += 1
        except Exception as e:
            print(f"移动文件失败 {src_file}: {e}")
            fail_count += 1
    
    return success_count, fail_count


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    target_dir = project_root / 'models'
    
    print("=" * 60)
    print("RapidOCR 模型文件移动工具")
    print("=" * 60)
    
    # 查找模型文件
    found_locations = find_rapidocr_models()
    
    if not found_locations:
        print("未找到RapidOCR模型文件")
        print("模型将在首次使用时自动下载")
        sys.exit(0)
    
    print(f"\n找到 {len(found_locations)} 个包含模型文件的位置:")
    for i, loc in enumerate(found_locations, 1):
        onnx_files = list(loc.rglob('*.onnx'))
        total_size = sum(f.stat().st_size for f in onnx_files) / (1024 * 1024)
        print(f"  {i}. {loc}")
        print(f"     包含 {len(onnx_files)} 个模型文件，总大小: {total_size:.2f} MB")
    
    # 移动第一个找到的模型目录
    if found_locations:
        source_dir = found_locations[0]
        print(f"\n将模型从 {source_dir} 移动到 {target_dir}")
        
        success, fail = move_models_to_target(source_dir, target_dir)
        
        print(f"\n移动完成:")
        print(f"  成功: {success} 个文件")
        print(f"  失败: {fail} 个文件")
        
        if success > 0:
            print(f"\n✓ 模型文件已移动到: {target_dir}")
        else:
            print(f"\n⚠ 没有移动任何文件（可能已存在）")

