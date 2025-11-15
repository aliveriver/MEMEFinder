#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CUDA 版本检测工具

用途：
1. 检测系统安装的 CUDA 版本
2. 检测 onnxruntime-gpu 支持的 CUDA 版本
3. 验证兼容性
4. 提供版本选择建议
"""

import os
import sys
import subprocess
from pathlib import Path


def get_nvidia_smi_cuda_version():
    """通过 nvidia-smi 获取 CUDA 驱动版本"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=driver_version,cuda_version', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                parts = output.split(',')
                if len(parts) >= 2:
                    driver_version = parts[0].strip()
                    cuda_version = parts[1].strip()
                    return cuda_version, driver_version
    except FileNotFoundError:
        return None, "nvidia-smi 未找到（可能未安装 NVIDIA 驱动）"
    except Exception as e:
        return None, f"检测失败: {e}"
    
    return None, "无法获取版本信息"


def get_nvcc_version():
    """通过 nvcc 获取 CUDA 工具包版本"""
    try:
        result = subprocess.run(
            ['nvcc', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout
            # 查找版本号 (例如: "release 11.8, V11.8.89")
            import re
            match = re.search(r'release\s+(\d+\.\d+)', output)
            if match:
                return match.group(1)
    except FileNotFoundError:
        return None
    except Exception:
        return None
    
    return None


def get_onnxruntime_cuda_version():
    """检测 onnxruntime-gpu 支持的 CUDA 版本"""
    try:
        import onnxruntime as ort
        
        # 检查是否有 GPU 支持
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' not in providers:
            return None, "onnxruntime-gpu 未安装或不支持 CUDA"
        
        # 尝试获取 CUDA 版本信息
        # onnxruntime 包的元数据中可能包含版本信息
        version_info = ort.__version__
        
        # 尝试创建一个简单的 CUDA session 来测试
        try:
            # 创建一个最小的模型来测试 CUDA
            import numpy as np
            
            # 创建一个简单的 identity 模型
            from onnxruntime import InferenceSession, SessionOptions
            
            # 如果能成功创建 CUDA provider，说明版本匹配
            opts = SessionOptions()
            # 注意：这里不实际创建 session，只是检查 provider
            
            # 从 DLL 文件名推断版本（如果是打包后的环境）
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                # 开发环境
                import onnxruntime
                base_path = Path(onnxruntime.__file__).parent
            
            # 查找 CUDA DLL
            cuda_dlls = list(base_path.rglob('cudart64_*.dll'))
            if cuda_dlls:
                # 从文件名提取版本 (例如: cudart64_110.dll -> 11.0)
                dll_name = cuda_dlls[0].name
                import re
                match = re.search(r'cudart64_(\d+)\.dll', dll_name)
                if match:
                    version_code = match.group(1)
                    # 110 -> 11.0, 120 -> 12.0
                    major = version_code[:-1] if len(version_code) > 2 else version_code[0]
                    minor = version_code[-1]
                    return f"{major}.{minor}", f"onnxruntime {version_info}"
            
            return "未知", f"onnxruntime {version_info} (有 CUDA 支持)"
            
        except Exception as e:
            return "未知", f"onnxruntime {version_info} (测试失败: {e})"
            
    except ImportError:
        return None, "onnxruntime 未安装"
    except Exception as e:
        return None, f"检测失败: {e}"


def check_cuda_compatibility(system_version, ort_version):
    """检查 CUDA 版本兼容性"""
    if not system_version or not ort_version:
        return False, "版本信息不完整"
    
    try:
        # 提取主版本号
        sys_major = int(float(system_version))
        ort_major = int(float(ort_version))
        
        if sys_major == ort_major:
            return True, "版本完全匹配 ✓"
        elif sys_major > ort_major:
            # 系统 CUDA 版本更新，通常向后兼容
            return True, f"系统 CUDA {sys_major}.x 向后兼容 onnxruntime CUDA {ort_major}.x ✓"
        else:
            # 系统 CUDA 版本较旧，可能不兼容
            return False, f"系统 CUDA {sys_major}.x 可能不兼容 onnxruntime CUDA {ort_major}.x ✗"
    except:
        return False, "版本格式无法解析"


def get_recommendation(system_version, ort_version, compatible):
    """根据检测结果提供建议"""
    recommendations = []
    
    if not system_version:
        recommendations.append("❌ 未检测到 NVIDIA GPU 或驱动")
        recommendations.append("   建议：使用 CPU 版本")
        return recommendations
    
    if not ort_version:
        recommendations.append("❌ onnxruntime-gpu 未正确安装")
        recommendations.append("   建议：")
        recommendations.append("   1. 使用 CPU 版本（最稳定）")
        if system_version:
            sys_major = int(float(system_version))
            if sys_major >= 12:
                recommendations.append(f"   2. 安装 CUDA 12.x 版本: pip install onnxruntime-gpu")
            else:
                recommendations.append(f"   2. 安装 CUDA 11.x 版本: pip install onnxruntime-gpu==1.15.1")
        return recommendations
    
    if compatible:
        recommendations.append("✅ CUDA 版本兼容")
        recommendations.append("   可以使用 GPU 版本")
    else:
        recommendations.append("⚠️  CUDA 版本可能不兼容")
        recommendations.append("   建议：")
        recommendations.append("   1. 使用 CPU 版本（推荐，避免问题）")
        
        sys_major = int(float(system_version))
        recommendations.append(f"   2. 或下载与系统匹配的 GPU 版本（CUDA {sys_major}.x）")
    
    return recommendations


def main():
    """主函数"""
    print("=" * 70)
    print("CUDA 版本检测工具")
    print("=" * 70)
    print()
    
    # 1. 检测系统 CUDA 版本
    print("【1】检测系统 CUDA 版本...")
    print("-" * 70)
    
    cuda_version, driver_version = get_nvidia_smi_cuda_version()
    nvcc_version = get_nvcc_version()
    
    if cuda_version:
        print(f"✓ CUDA 驱动版本: {cuda_version}")
        print(f"  驱动版本: {driver_version}")
    else:
        print(f"✗ {driver_version}")
    
    if nvcc_version:
        print(f"✓ CUDA 工具包版本: {nvcc_version}")
    else:
        print("✗ CUDA 工具包未安装（这是正常的，不影响 GPU 使用）")
    
    system_cuda = cuda_version or nvcc_version
    
    print()
    
    # 2. 检测 onnxruntime-gpu 版本
    print("【2】检测 onnxruntime-gpu CUDA 版本...")
    print("-" * 70)
    
    ort_cuda, ort_info = get_onnxruntime_cuda_version()
    
    if ort_cuda:
        print(f"✓ onnxruntime CUDA 版本: {ort_cuda}")
        print(f"  {ort_info}")
    else:
        print(f"✗ {ort_info}")
    
    print()
    
    # 3. 兼容性检查
    print("【3】兼容性检查...")
    print("-" * 70)
    
    if system_cuda and ort_cuda:
        compatible, msg = check_cuda_compatibility(system_cuda, ort_cuda)
        print(f"系统 CUDA: {system_cuda}")
        print(f"onnxruntime CUDA: {ort_cuda}")
        print(f"兼容性: {msg}")
    else:
        compatible = False
        print("✗ 无法进行兼容性检查（版本信息不完整）")
    
    print()
    
    # 4. 提供建议
    print("【4】使用建议...")
    print("-" * 70)
    
    recommendations = get_recommendation(system_cuda, ort_cuda, compatible)
    for rec in recommendations:
        print(rec)
    
    print()
    print("=" * 70)
    print("版本说明:")
    print("  • CPU 版本：适用于所有用户，无需 GPU，稳定可靠")
    print("  • GPU CUDA 11.x：适用于 RTX 20/30 系列及部分 40 系列")
    print("  • GPU CUDA 12.x：适用于 RTX 40 系列及最新显卡")
    print("=" * 70)
    
    # 返回状态码
    if not system_cuda:
        return 2  # 无 GPU
    elif not compatible:
        return 1  # 版本不兼容
    else:
        return 0  # 一切正常


if __name__ == '__main__':
    sys.exit(main())
