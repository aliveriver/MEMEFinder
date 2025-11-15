#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU 环境诊断工具

用于诊断为什么 GPU 初始化会超时或失败
"""

import sys
import os
from pathlib import Path

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def check_nvidia_driver():
    """检查 NVIDIA 驱动"""
    print_section("1. NVIDIA 驱动检查")
    
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ NVIDIA 驱动已安装")
            print("\n" + result.stdout)
            return True
        else:
            print("✗ nvidia-smi 命令失败")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("✗ nvidia-smi 未找到")
        print("  NVIDIA 驱动可能未安装")
        return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def check_cuda_availability():
    """检查 CUDA 可用性"""
    print_section("2. CUDA 可用性检查")
    
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        print(f"ONNX Runtime 版本: {ort.__version__}")
        print(f"可用 Providers: {providers}")
        print()
        
        if 'CUDAExecutionProvider' in providers:
            print("✓ CUDAExecutionProvider 可用")
            return True
        else:
            print("✗ CUDAExecutionProvider 不可用")
            print("  这意味着 onnxruntime 检测不到 CUDA")
            return False
            
    except ImportError:
        print("✗ onnxruntime 未安装")
        return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def test_simple_cuda_init():
    """测试简单的 CUDA 初始化"""
    print_section("3. 简单 CUDA 初始化测试")
    
    try:
        import onnxruntime as ort
        import numpy as np
        
        print("创建一个简单的 ONNX Runtime 会话（CUDA）...")
        
        # 创建一个最简单的模型（恒等映射）
        import onnx
        from onnx import helper, TensorProto
        
        # 创建输入输出
        X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1, 3])
        Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1, 3])
        
        # 创建恒等节点
        node = helper.make_node('Identity', ['X'], ['Y'])
        
        # 创建图
        graph = helper.make_graph([node], 'test', [X], [Y])
        
        # 创建模型
        model = helper.make_model(graph)
        
        # 保存到临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
            onnx.save(model, f.name)
            temp_model_path = f.name
        
        try:
            # 尝试使用 CUDA Provider 创建会话
            print("  使用 CUDAExecutionProvider 创建会话...")
            session = ort.InferenceSession(
                temp_model_path,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            
            # 检查实际使用的 Provider
            actual_providers = session.get_providers()
            print(f"  实际使用的 Providers: {actual_providers}")
            
            if 'CUDAExecutionProvider' in actual_providers:
                print("✓ CUDA Provider 成功激活")
                
                # 尝试运行推理
                print("  运行一次推理测试...")
                input_data = np.random.randn(1, 3).astype(np.float32)
                output = session.run(None, {'X': input_data})
                print("✓ 推理成功")
                
                return True
            else:
                print("⚠ CUDA Provider 未激活，降级到 CPU")
                print("  这可能是 CUDA 环境问题")
                return False
                
        finally:
            # 清理临时文件
            os.unlink(temp_model_path)
            
    except ImportError as e:
        print(f"✗ 缺少必要的库: {e}")
        print("  请安装: pip install onnx")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rapidocr_cpu():
    """测试 RapidOCR CPU 模式"""
    print_section("4. RapidOCR CPU 模式测试")
    
    try:
        from rapidocr_onnxruntime import RapidOCR
        import tempfile
        from PIL import Image
        import numpy as np
        
        print("初始化 RapidOCR (CPU 模式)...")
        ocr = RapidOCR(
            det_use_cuda=False,
            cls_use_cuda=False,
            rec_use_cuda=False
        )
        
        print("✓ RapidOCR CPU 初始化成功")
        
        # 创建一个简单的测试图片
        print("创建测试图片...")
        img = Image.new('RGB', (100, 100), color='white')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            test_img_path = f.name
        
        try:
            print("运行 OCR 测试...")
            result = ocr(test_img_path)
            print("✓ OCR 运行成功")
            print(f"  结果: {result}")
            return True
        finally:
            os.unlink(test_img_path)
            
    except ImportError:
        print("✗ rapidocr_onnxruntime 未安装")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rapidocr_gpu_with_timeout():
    """测试 RapidOCR GPU 模式（带超时）"""
    print_section("5. RapidOCR GPU 模式测试（10秒超时）")
    
    try:
        from rapidocr_onnxruntime import RapidOCR
        import threading
        
        print("尝试初始化 RapidOCR (GPU 模式)...")
        print("⚠ 如果卡住超过 10 秒，将放弃此测试")
        
        result_container = {'ocr': None, 'error': None, 'done': False}
        
        def init_gpu():
            try:
                ocr = RapidOCR(
                    det_use_cuda=True,
                    cls_use_cuda=True,
                    rec_use_cuda=True
                )
                result_container['ocr'] = ocr
                result_container['done'] = True
            except Exception as e:
                result_container['error'] = e
                result_container['done'] = True
        
        thread = threading.Thread(target=init_gpu, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        if thread.is_alive():
            print("✗ GPU 初始化超时（10秒）")
            print("  这是问题所在！GPU 初始化会卡住")
            print()
            print("可能的原因:")
            print("  1. CUDA 版本不匹配")
            print("  2. cuDNN 库加载失败")
            print("  3. GPU 驱动问题")
            print("  4. 某些 CUDA 库初始化时死锁")
            print()
            print("建议:")
            print("  • 使用 CPU 模式（稳定可靠）")
            print("  • 或者更新 NVIDIA 驱动")
            return False
        
        if result_container['done']:
            if result_container['error']:
                print(f"✗ GPU 初始化失败: {result_container['error']}")
                return False
            else:
                print("✓ GPU 初始化成功！")
                print("  GPU 功能应该可以正常使用")
                return True
        else:
            print("⚠ 初始化状态未知")
            return False
            
    except ImportError:
        print("✗ rapidocr_onnxruntime 未安装")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "GPU 环境诊断工具" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # 1. 检查 NVIDIA 驱动
    has_nvidia = check_nvidia_driver()
    results.append(("NVIDIA 驱动", has_nvidia))
    
    # 2. 检查 CUDA 可用性
    has_cuda = check_cuda_availability()
    results.append(("CUDA 可用性", has_cuda))
    
    # 3. 简单 CUDA 初始化测试
    if has_cuda:
        cuda_init_ok = test_simple_cuda_init()
        results.append(("简单 CUDA 初始化", cuda_init_ok))
    else:
        print_section("3. 简单 CUDA 初始化测试")
        print("⊘ 跳过（CUDA 不可用）")
        cuda_init_ok = False
    
    # 4. RapidOCR CPU 测试
    cpu_ok = test_rapidocr_cpu()
    results.append(("RapidOCR CPU", cpu_ok))
    
    # 5. RapidOCR GPU 测试
    if has_cuda:
        gpu_ok = test_rapidocr_gpu_with_timeout()
        results.append(("RapidOCR GPU", gpu_ok))
    else:
        print_section("5. RapidOCR GPU 模式测试")
        print("⊘ 跳过（CUDA 不可用）")
        gpu_ok = False
    
    # 总结
    print_section("诊断总结")
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:<30} {status}")
    
    print()
    
    # 给出建议
    print("=" * 70)
    print("  建议")
    print("=" * 70)
    print()
    
    if not has_nvidia:
        print("❌ 未检测到 NVIDIA 驱动")
        print("   建议: 安装最新的 NVIDIA 驱动程序")
        print()
    
    if has_nvidia and not has_cuda:
        print("⚠ NVIDIA 驱动已安装，但 CUDA 不可用")
        print("   可能原因:")
        print("   • onnxruntime-gpu 未安装")
        print("   • CUDA 版本不匹配")
        print("   建议:")
        print("   • pip install onnxruntime-gpu")
        print()
    
    if has_cuda and not gpu_ok:
        print("⚠ CUDA 可用，但 RapidOCR GPU 初始化失败或超时")
        print("   这是当前问题的关键！")
        print()
        print("   可能原因:")
        print("   1. CUDA 版本与 onnxruntime-gpu 不匹配")
        print("      • 打包的程序使用 CUDA 12")
        print("      • 用户机器的 CUDA 版本可能不同")
        print()
        print("   2. cuDNN 库加载问题")
        print("      • cuDNN 版本不匹配")
        print("      • cuDNN 库损坏")
        print()
        print("   3. GPU 驱动问题")
        print("      • 驱动版本过旧")
        print("      • 驱动不稳定")
        print()
        print("   ✅ 推荐解决方案:")
        print("   • 使用 CPU 模式（稳定、快速、可靠）")
        print("   • 启动程序时使用「启动_CPU模式.bat」")
        print("   • 或设置环境变量: set MEMEFINDER_FORCE_CPU=1")
        print()
        print("   📊 性能对比:")
        print("   • 小批量 (< 500 张): CPU 和 GPU 差异不大")
        print("   • 中批量 (500-2000 张): GPU 快 2-3 倍")
        print("   • 大批量 (> 2000 张): GPU 快 3-5 倍")
        print()
    
    if cpu_ok and not gpu_ok:
        print("💡 好消息:")
        print("   CPU 模式工作正常！")
        print("   您可以放心使用 CPU 模式处理图片")
        print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消诊断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")
