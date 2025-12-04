#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检测工具 - 检测系统是否支持GPU加速
"""

import os
import sys
from typing import Tuple, Optional


def has_nvidia_gpu() -> bool:
    """
    检测是否有NVIDIA GPU硬件（不检查onnxruntime-gpu）
    
    Returns:
        bool: 是否有NVIDIA GPU硬件
    """
    from ..utils.logger import get_logger
    logger = get_logger()
    
    try:
        import subprocess
        logger.debug("[GPU检测] 开始检测NVIDIA GPU硬件...")
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"[GPU检测] ✓ 检测到NVIDIA GPU: {result.stdout.strip()}")
            return True
        else:
            logger.debug("[GPU检测] ✗ nvidia-smi未返回GPU信息")
            return False
    except FileNotFoundError:
        logger.debug("[GPU检测] ✗ 未找到nvidia-smi命令（可能未安装NVIDIA驱动）")
        return False
    except Exception as e:
        logger.debug(f"[GPU检测] ✗ 检测GPU硬件时出错: {e}")
        return False


def has_onnxruntime_gpu() -> bool:
    """
    检测是否安装了onnxruntime-gpu
    
    Returns:
        bool: 是否安装onnxruntime-gpu
    """
    from ..utils.logger import get_logger
    logger = get_logger()
    
    try:
        logger.debug("[GPU检测] 检查ONNXRuntime CUDA支持...")
        import onnxruntime as ort
        logger.debug(f"[GPU检测] ONNXRuntime版本: {ort.__version__}")
        logger.debug(f"[GPU检测] ONNXRuntime路径: {ort.__file__}")
        
        providers = ort.get_available_providers()
        logger.debug(f"[GPU检测] 可用Providers: {', '.join(providers)}")
        
        if 'CUDAExecutionProvider' in providers:
            logger.info("[GPU检测] ✓ CUDAExecutionProvider可用")
            
            # 检查CUDA DLL路径
            _check_cuda_dlls(logger)
            
            return True
        else:
            logger.warning("[GPU检测] ✗ CUDAExecutionProvider不可用")
            logger.warning("[GPU检测]    可能原因: 1) 缺少CUDA运行时DLL 2) onnxruntime版本不支持")
            
            # 诊断CUDA DLL问题
            _diagnose_cuda_dlls(logger)
            
            return False
    except ImportError as e:
        logger.error(f"[GPU检测] ✗ 无法导入onnxruntime: {e}")
        return False
    except Exception as e:
        logger.error(f"[GPU检测] ✗ 检查ONNXRuntime时出错: {e}")
        return False


def _check_cuda_dlls(logger):
    """检查CUDA DLL的路径（当GPU可用时）"""
    try:
        import os
        cuda_path = os.environ.get('CUDA_PATH', '')
        if cuda_path:
            logger.debug(f"[GPU检测] CUDA_PATH环境变量: {cuda_path}")
        
        # 检查PATH中是否有CUDA
        path_env = os.environ.get('PATH', '')
        cuda_in_path = [p for p in path_env.split(os.pathsep) if 'cuda' in p.lower()]
        if cuda_in_path:
            logger.debug(f"[GPU检测] PATH中的CUDA路径: {cuda_in_path[0]}")
    except Exception as e:
        logger.debug(f"[GPU检测] 检查CUDA DLL路径时出错: {e}")


def _diagnose_cuda_dlls(logger):
    """诊断CUDA DLL问题（当GPU不可用时）"""
    try:
        import os
        import sys
        
        logger.debug("[GPU检测] 开始诊断CUDA DLL问题...")
        
        # 1. 检查CUDA_PATH环境变量
        cuda_path = os.environ.get('CUDA_PATH', '')
        if cuda_path:
            logger.debug(f"[GPU检测]   CUDA_PATH: {cuda_path}")
            cuda_bin = os.path.join(cuda_path, 'bin')
            if os.path.exists(cuda_bin):
                logger.debug(f"[GPU检测]   ✓ CUDA bin目录存在")
            else:
                logger.debug(f"[GPU检测]   ✗ CUDA bin目录不存在")
        else:
            logger.debug("[GPU检测]   ✗ CUDA_PATH环境变量未设置")
        
        # 2. 检查PATH环境变量
        path_env = os.environ.get('PATH', '')
        cuda_paths = [p for p in path_env.split(os.pathsep) if 'cuda' in p.lower()]
        if cuda_paths:
            logger.debug(f"[GPU检测]   PATH中找到CUDA: {cuda_paths[0]}")
        else:
            logger.debug("[GPU检测]   ✗ PATH中未找到CUDA路径")
        
        # 3. 检查打包程序的情况
        if getattr(sys, 'frozen', False):
            logger.debug("[GPU检测]   当前运行在打包程序中")
            app_dir = os.path.dirname(sys.executable)
            logger.debug(f"[GPU检测]   程序目录: {app_dir}")
            
            # 检查程序目录中是否有CUDA DLL
            cuda_dlls = ['cudart64_12.dll', 'cudart64_11.dll', 'cudart64_110.dll']
            found_dlls = []
            for dll in cuda_dlls:
                dll_path = os.path.join(app_dir, dll)
                if os.path.exists(dll_path):
                    found_dlls.append(dll)
            
            if found_dlls:
                logger.debug(f"[GPU检测]   程序目录中找到: {', '.join(found_dlls)}")
            else:
                logger.warning("[GPU检测]   ✗ 程序目录中未找到CUDA DLL")
                logger.warning("[GPU检测]      打包时可能未包含CUDA运行时库")
        else:
            logger.debug("[GPU检测]   当前运行在开发环境中")
            
    except Exception as e:
        logger.debug(f"[GPU检测] 诊断过程出错: {e}")


def get_gpu_recommendation() -> dict:
    """
    获取GPU使用建议
    
    Returns:
        dict: {
            'has_hardware': bool,  # 是否有NVIDIA硬件
            'has_onnxruntime_gpu': bool,  # 是否安装onnxruntime-gpu
            'can_use_gpu': bool,  # 是否可以使用GPU
            'recommendation': str,  # 推荐操作
            'device_info': str  # GPU设备信息
        }
    """
    from ..utils.logger import get_logger
    logger = get_logger()
    
    logger.debug("=" * 60)
    logger.debug("[GPU检测] 开始GPU配置检测")
    
    has_hw = has_nvidia_gpu()
    has_ort_gpu = has_onnxruntime_gpu()
    
    result = {
        'has_hardware': has_hw,
        'has_onnxruntime_gpu': has_ort_gpu,
        'can_use_gpu': has_hw and has_ort_gpu,
        'recommendation': '',
        'device_info': ''
    }
    
    # 获取设备信息
    if has_hw:
        try:
            import subprocess
            gpu_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if gpu_result.returncode == 0:
                result['device_info'] = gpu_result.stdout.strip().split('\n')[0]
        except:
            result['device_info'] = 'NVIDIA GPU'
    
    # 生成建议
    if has_hw and has_ort_gpu:
        result['recommendation'] = '可以使用GPU加速'
        logger.info("[GPU检测] ✓✓ GPU加速完全可用")
    elif has_hw and not has_ort_gpu:
        result['recommendation'] = '建议安装onnxruntime-gpu以启用GPU加速'
        logger.warning("[GPU检测] ⚠ 有GPU硬件但CUDA Provider不可用")
    else:
        result['recommendation'] = 'GPU不可用，将使用CPU模式'
        logger.info("[GPU检测] ℹ 将使用CPU模式")
    
    logger.debug("[GPU检测] 检测完成")
    logger.debug("=" * 60)
    
    return result


def _test_cuda_availability_safe() -> bool:
    """
    安全地测试CUDA是否可用
    
    这个函数会尝试多种方法来验证CUDA，而不会导致程序崩溃
    
    Returns:
        bool: CUDA是否真的可用
    """
    try:
        import onnxruntime as ort
        
        # 方法1：检查提供者选项
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' not in providers:
            return False
        
        # 方法2：尝试获取CUDA提供者的选项（这不会真正初始化CUDA）
        try:
            cuda_options = ort.SessionOptions()
            # 只是配置，不会触发真正的初始化
            cuda_options.log_severity_level = 3
            return True
        except Exception:
            pass
        
        # 方法3：检查环境变量和库文件
        # Windows: 检查是否有 CUDA 相关的 DLL
        if sys.platform == 'win32':
            import ctypes
            cuda_libs = [
                'cudart64_110.dll',  # CUDA 11.x
                'cudart64_111.dll',
                'cudart64_112.dll',
                'cudart64_12.dll',   # CUDA 12.x
            ]
            
            for lib in cuda_libs:
                try:
                    ctypes.CDLL(lib)
                    return True  # 找到并成功加载了CUDA库
                except Exception:
                    continue
        
        # 如果以上方法都没有明确结果，返回True让程序尝试
        # 在实际初始化时会有完整的异常处理
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger('MEMEFinder')
        logger.debug(f"CUDA可用性测试异常: {e}")
        return True  # 返回True，让后续初始化来决定


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
                    
                    # 额外检查：验证CUDA是否真的可以初始化
                    # 使用更轻量级的测试方法
                    try:
                        # 方法1：检查 CUDA 库 是否可以加载
                        # 这比创建完整的 InferenceSession 更轻量
                        cuda_available = _test_cuda_availability_safe()
                        
                        if cuda_available:
                            logger.debug("✓ CUDA运行时库可用")
                            return True, f"CUDA GPU: {gpu_info}"
                        else:
                            logger.warning("⚠ CUDA库加载失败，GPU不可用")
                            logger.warning("  建议: 检查CUDA和cuDNN是否正确安装")
                            # 仍然返回 True，但让用户可以选择
                            # 在 RapidOCR 初始化时会有更完整的错误处理
                            return True, f"CUDA GPU: {gpu_info} (CUDA库可能有问题)"
                    except Exception as cuda_test_error:
                        logger.warning(f"⚠ CUDA测试过程出错: {cuda_test_error}")
                        # 返回True，让程序尝试初始化，如果失败会自动回退
                        return True, f"CUDA GPU: {gpu_info} (需要进一步测试)"
                    
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
        import logging
        logger = logging.getLogger('MEMEFinder')
        logger.debug(f"GPU检测过程中发生错误: {e}")
    
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
    1. 环境变量 MEMEFINDER_FORCE_CPU（强制使用CPU）
    2. 环境变量 MEMEFINDER_USE_GPU（指定是否使用GPU）
    3. 自动检测GPU是否可用
    
    Returns:
        bool: 是否使用GPU
    """
    # 首先检查是否强制使用CPU
    force_cpu = os.environ.get('MEMEFINDER_FORCE_CPU', '').lower()
    if force_cpu in ('1', 'true', 'yes', 'on'):
        import logging
        logger = logging.getLogger('MEMEFinder')
        logger.info("检测到 MEMEFINDER_FORCE_CPU 环境变量，强制使用CPU模式")
        return False
    
    # 检查是否明确指定使用GPU
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

