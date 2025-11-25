#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理打包后的CUDA DLLs
从打包构建中删除CUDA相关的DLL文件，让应用使用系统的CUDA安装
"""

from pathlib import Path
import sys

def clean_cuda_dlls(dist_dir):
    """从打包目录中删除CUDA DLLs"""
    print(f"\n正在清理CUDA DLLs (使用系统CUDA)...")
    print(f"目标目录: {dist_dir}")
    
    cuda_dll_patterns = [
        '*cublas*.dll', '*cublaslt*.dll', '*cudnn*.dll', '*cudart*.dll',
        '*cufft*.dll', '*curand*.dll', '*cusolver*.dll', '*cusparse*.dll',
        '*nvrtc*.dll', '*nvcuda*.dll', '*nvjitlink*.dll'
    ]
    
    removed_count = 0
    removed_size = 0
    
    for pattern in cuda_dll_patterns:
        for dll_file in Path(dist_dir).rglob(pattern):
            try:
                file_size = dll_file.stat().st_size
                dll_file.unlink()
                removed_count += 1
                removed_size += file_size
                print(f"  ✓ 删除: {dll_file.name} ({file_size / (1024*1024):.1f} MB)")
            except Exception as e:
                print(f"  ✗ 无法删除 {dll_file.name}: {e}")
    
    if removed_count > 0:
        print(f"\n✅ 已删除 {removed_count} 个CUDA DLL，节省 {removed_size / (1024*1024):.1f} MB")
    else:
        print("\n⚠️  未找到需要删除的CUDA DLL")
    
    return removed_count, removed_size

if __name__ == "__main__":
    # 默认目标目录
    default_dir = Path(__file__).parent.parent / "releases" / "MEMEFinder"
    
    if len(sys.argv) > 1:
        dist_dir = Path(sys.argv[1])
    else:
        dist_dir = default_dir
    
    if not dist_dir.exists():
        print(f"错误: 目录不存在: {dist_dir}")
        sys.exit(1)
    
    count, size = clean_cuda_dlls(dist_dir)
    
    if count > 0:
        print(f"\n📦 打包后大小减少约 {size / (1024*1024*1024):.2f} GB")
