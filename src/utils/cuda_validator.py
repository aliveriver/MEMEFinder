#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CUDA 路径验证工具
用于验证 CUDA 安装路径是否有效并可以被使用
"""

import os
from typing import Dict, List, Tuple
from .cuda_finder import find_cuda_dlls


def validate_cuda_path(cuda_path: str) -> Dict[str, any]:
    """
    验证 CUDA 路径是否有效
    
    Args:
        cuda_path: CUDA 安装路径
        
    Returns:
        验证结果字典:
        {
            'valid': bool,  # 路径是否有效
            'message': str,  # 验证消息
            'dlls': List[Tuple[str, str]],  # 找到的DLL列表
            'cuda_version': str  # CUDA版本(如果能检测到)
        }
    """
    result = {
        'valid': False,
        'message': '',
        'dlls': [],
        'cuda_version': 'Unknown'
    }
    
    # 检查路径是否存在
    if not os.path.exists(cuda_path):
        result['message'] = f"路径不存在: {cuda_path}"
        return result
    
    # 检查是否是目录
    if not os.path.isdir(cuda_path):
        result['message'] = f"路径不是一个目录: {cuda_path}"
        return result
    
    # 检查 bin 目录
    bin_path = os.path.join(cuda_path, 'bin')
    if not os.path.exists(bin_path):
        result['message'] = f"未找到 bin 目录: {bin_path}\n\n请确保选择了正确的 CUDA Toolkit 根目录。"
        return result
    
    # 尝试从路径中提取版本号
    try:
        # CUDA路径通常是: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0
        if 'v' in os.path.basename(cuda_path):
            result['cuda_version'] = os.path.basename(cuda_path)
        elif os.path.exists(os.path.join(cuda_path, 'version.txt')):
            with open(os.path.join(cuda_path, 'version.txt'), 'r') as f:
                result['cuda_version'] = f.read().strip()
    except:
        pass
    
    # 查找必需的 DLL 文件
    dlls = find_cuda_dlls(cuda_path)
    if not dlls:
        result['message'] = (
            f"在 CUDA 安装中未找到必需的 DLL 文件。\n\n"
            f"检查路径: {bin_path}\n\n"
            f"请确保:\n"
            f"  1. CUDA Toolkit 已完整安装\n"
            f"  2. 选择的是正确的 CUDA 根目录\n"
            f"  3. 版本是 11.x 或 12.x"
        )
        return result
    
    # 检查关键 DLL
    dll_names = [dll_name for dll_name, _ in dlls]
    required_patterns = ['cudart64', 'cublas64']
    
    missing = []
    for pattern in required_patterns:
        if not any(pattern in dll for dll in dll_names):
            missing.append(pattern)
    
    if missing:
        result['message'] = (
            f"缺少关键的 CUDA 库:\n"
            f"  {', '.join(missing)}\n\n"
            f"找到的 DLL:\n  " + "\n  ".join(dll_names)
        )
        return result
    
    # 验证成功
    result['valid'] = True
    result['dlls'] = dlls
    result['message'] = f"CUDA 路径有效 (版本: {result['cuda_version']})"
    
    return result


def test_cuda_runtime() -> Dict[str, any]:
    """
    测试 CUDA 运行时是否可用
    
    Returns:
        测试结果字典:
        {
            'available': bool,  # CUDA是否可用
            'providers': List[str],  # 可用的执行提供程序
            'cuda_version': str,  # CUDA版本
            'message': str  # 测试消息
        }
    """
    result = {
        'available': False,
        'providers': [],
        'cuda_version': 'Unknown',
        'message': ''
    }
    
    try:
        import onnxruntime as ort
        
        # 获取可用的提供程序
        result['providers'] = ort.get_available_providers()
        
        # 检查 CUDA 是否可用
        if 'CUDAExecutionProvider' in result['providers']:
            result['available'] = True
            result['message'] = 'CUDA 执行提供程序可用'
            
            # 尝试获取 CUDA 版本
            try:
                # 创建一个简单的会话来测试
                import numpy as np
                session = ort.InferenceSession(
                    None,
                    providers=['CUDAExecutionProvider']
                )
                result['message'] = 'CUDA 运行时测试成功'
            except Exception as e:
                result['message'] = f'CUDA 提供程序存在但测试失败: {e}'
        else:
            result['message'] = f'CUDA 不可用。可用提供程序: {", ".join(result["providers"])}'
    
    except ImportError as e:
        result['message'] = f'onnxruntime 未安装: {e}'
    except Exception as e:
        result['message'] = f'测试失败: {e}'
    
    return result


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        cuda_path = sys.argv[1]
        print(f"验证 CUDA 路径: {cuda_path}")
        print("=" * 60)
        
        result = validate_cuda_path(cuda_path)
        print(f"有效: {result['valid']}")
        print(f"版本: {result['cuda_version']}")
        print(f"消息: {result['message']}")
        
        if result['valid']:
            print(f"\n找到 {len(result['dlls'])} 个 DLL 文件:")
            for dll_name, dll_path in result['dlls']:
                print(f"  • {dll_name}")
    else:
        print("测试 CUDA 运行时...")
        print("=" * 60)
        result = test_cuda_runtime()
        print(f"可用: {result['available']}")
        print(f"提供程序: {', '.join(result['providers'])}")
        print(f"消息: {result['message']}")
