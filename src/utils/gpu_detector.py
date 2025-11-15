#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检测工具 - 检测系统是否支持GPU加速
"""

import os
from typing import Tuple, Optional


def detect_gpu() -> Tuple[bool, Optional[str]]:
    """
    检测系统是否支持GPU加速
    
    Returns:
        (has_gpu, device_info): 
        - has_gpu: 是否检测到可用的GPU
        - device_info: GPU设备信息（如果有），否则为None
    """
    # 方法1: 检查ONNX Runtime是否支持CUDA
    try:
        import onnxruntime as ort
        
        # 获取可用的执行提供者
        available_providers = ort.get_available_providers()
        
        # 记录所有可用的提供者（用于调试）
        import logging
        logger = logging.getLogger('MEMEFinder')
        logger.debug(f"ONNX Runtime 可用提供者: {available_providers}")
        
        # 检查是否有CUDA执行提供者
        if 'CUDAExecutionProvider' in available_providers:
            # 尝试获取GPU设备信息
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    gpu_info = result.stdout.strip().split('\n')[0]
                    return True, f"CUDA GPU: {gpu_info}"
                else:
                    return True, "CUDA GPU (可用)"
            except:
                # 即使无法获取详细信息，也认为GPU可用（因为提供者存在）
                return True, "CUDA GPU (可用)"
        
        # 检查是否有TensorRT执行提供者
        if 'TensorrtExecutionProvider' in available_providers:
            return True, "TensorRT GPU"
        
        # 检查是否有DirectML执行提供者（Windows上的GPU加速）
        if 'DmlExecutionProvider' in available_providers:
            return True, "DirectML GPU (Windows)"
        
    except ImportError:
        # onnxruntime未安装或无法导入
        pass
    except Exception as e:
        # 其他错误
        pass
    
    # 方法2: 检查环境变量（用户可能手动指定）
    if os.environ.get('MEMEFINDER_USE_GPU', '').lower() in ('1', 'true', 'yes', 'on'):
        return True, "环境变量指定使用GPU"
    
    # 方法3: 检查是否有nvidia-smi命令（简单检测）
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--version'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            # 有nvidia-smi，但可能没有安装onnxruntime-gpu
            logger = logging.getLogger('MEMEFinder')
            logger.warning("检测到NVIDIA驱动，但ONNX Runtime可能未安装GPU版本")
            logger.warning("提示: 请安装 onnxruntime-gpu: pip install onnxruntime-gpu")
            return False, "检测到NVIDIA驱动，但ONNX Runtime可能未安装GPU版本"
    except:
        pass
    
    return False, None


def should_use_gpu() -> bool:
    """
    判断是否应该使用GPU
    
    优先级：
    1. 环境变量 MEMEFINDER_USE_GPU
    2. 自动检测GPU是否可用
    
    Returns:
        bool: 是否使用GPU
    """
    # 首先检查环境变量
    env_use_gpu = os.environ.get('MEMEFINDER_USE_GPU', '').lower()
    if env_use_gpu in ('1', 'true', 'yes', 'on'):
        return True
    elif env_use_gpu in ('0', 'false', 'no', 'off'):
        return False
    
    # 自动检测
    has_gpu, _ = detect_gpu()
    return has_gpu


if __name__ == "__main__":
    # 测试代码
    has_gpu, info = detect_gpu()
    print(f"GPU检测结果: {has_gpu}")
    if info:
        print(f"设备信息: {info}")
    
    should_use = should_use_gpu()
    print(f"是否使用GPU: {should_use}")

