#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CUDA DLL 查找和复制工具
用于在用户系统上查找 CUDA 运行时库并复制到 onnxruntime 目录
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Tuple


def find_cuda_installation() -> Optional[str]:
    """
    查找系统上的 CUDA 安装路径
    
    Returns:
        CUDA 安装路径,如果未找到则返回 None
    """
    # 方法1: 检查环境变量
    cuda_path = os.environ.get('CUDA_PATH')
    if cuda_path and os.path.exists(cuda_path):
        return cuda_path
    
    # 方法2: 检查常见安装路径
    common_paths = [
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA',
        r'C:\Program Files (x86)\NVIDIA GPU Computing Toolkit\CUDA',
    ]
    
    for base_path in common_paths:
        if os.path.exists(base_path):
            # 查找最新版本
            versions = []
            for item in os.listdir(base_path):
                version_path = os.path.join(base_path, item)
                if os.path.isdir(version_path):
                    versions.append((item, version_path))
            
            if versions:
                # 按版本号排序,选择最新的
                versions.sort(reverse=True)
                return versions[0][1]
    
    return None


def find_cuda_dlls(cuda_path: str) -> List[Tuple[str, str]]:
    """
    在 CUDA 安装目录中查找所需的 DLL 文件
    
    Args:
        cuda_path: CUDA 安装路径
        
    Returns:
        (DLL名称, 完整路径) 的列表
    """
    required_dlls = [
        # CUDA Runtime
        'cudart64_*.dll',
        # cuBLAS
        'cublas64_*.dll',
        'cublasLt64_*.dll',
        # cuDNN (如果存在)
        'cudnn64_*.dll',
        'cudnn_*_infer64_*.dll',
    ]
    
    bin_path = os.path.join(cuda_path, 'bin')
    if not os.path.exists(bin_path):
        return []
    
    found_dlls = []
    
    # 查找所有匹配的 DLL
    for pattern in required_dlls:
        import glob
        pattern_path = os.path.join(bin_path, pattern)
        matches = glob.glob(pattern_path)
        for dll_path in matches:
            dll_name = os.path.basename(dll_path)
            found_dlls.append((dll_name, dll_path))
    
    return found_dlls


def copy_cuda_dlls_to_onnxruntime(onnxruntime_path: str, cuda_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    将 CUDA DLL 复制到 onnxruntime 的 capi 目录
    
    Args:
        onnxruntime_path: onnxruntime 包的路径
        cuda_path: CUDA 安装路径（可选），如果未指定则自动查找
        
    Returns:
        (是否成功, 消息)
    """
    # 查找 CUDA 安装
    if cuda_path is None:
        print("正在自动查找 CUDA 安装...")
        cuda_path = find_cuda_installation()
        if not cuda_path:
            return False, "未找到 CUDA 安装。请确保已安装 NVIDIA CUDA Toolkit。"
        print(f"找到 CUDA 安装: {cuda_path}")
    else:
        print(f"使用指定的 CUDA 路径: {cuda_path}")
        if not os.path.exists(cuda_path):
            return False, f"指定的 CUDA 路径不存在: {cuda_path}"
    
    # 查找 DLL
    print(f"正在搜索 CUDA DLL 文件...")
    dlls = find_cuda_dlls(cuda_path)
    if not dlls:
        return False, f"在 CUDA 安装目录 {cuda_path} 中未找到所需的 DLL 文件。"
    
    print(f"找到 {len(dlls)} 个 CUDA DLL 文件:")
    for dll_name, dll_path in dlls:
        print(f"  - {dll_name}")
    
    # 确定目标目录
    capi_dir = os.path.join(onnxruntime_path, 'capi')
    print(f"目标目录: {capi_dir}")
    
    if not os.path.exists(capi_dir):
        print(f"创建目录: {capi_dir}")
        try:
            os.makedirs(capi_dir)
        except Exception as e:
            return False, f"无法创建目录 {capi_dir}: {e}"
    
    # 复制 DLL
    copied = []
    failed = []
    
    print("\n开始复制 DLL 文件...")
    for dll_name, dll_path in dlls:
        target_path = os.path.join(capi_dir, dll_name)
        try:
            print(f"  复制: {dll_name} -> {target_path}")
            shutil.copy2(dll_path, target_path)
            # 验证文件已复制
            if os.path.exists(target_path):
                size = os.path.getsize(target_path)
                print(f"    成功 ({size:,} 字节)")
                copied.append(dll_name)
            else:
                print(f"    失败: 文件未创建")
                failed.append(f"{dll_name}: 文件未创建")
        except Exception as e:
            print(f"    失败: {e}")
            failed.append(f"{dll_name}: {e}")
    
    print(f"\n复制完成: {len(copied)} 成功, {len(failed)} 失败")
    
    if failed:
        return False, f"部分 DLL 复制失败:\n" + "\n".join(failed)
    
    if not copied:
        return False, "没有复制任何 DLL 文件。"
    
    return True, f"成功复制 {len(copied)} 个 CUDA DLL 文件:\n" + "\n".join(copied)


if __name__ == "__main__":
    # 测试代码
    cuda_path = find_cuda_installation()
    if cuda_path:
        print(f"找到 CUDA 安装: {cuda_path}")
        dlls = find_cuda_dlls(cuda_path)
        print(f"找到 {len(dlls)} 个 DLL 文件:")
        for name, path in dlls:
            print(f"  - {name}")
    else:
        print("未找到 CUDA 安装")
