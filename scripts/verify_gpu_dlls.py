#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证打包后的程序是否包含所有必要的 ONNX Runtime GPU DLL

使用方法：
    python scripts/verify_gpu_dlls.py
"""

import sys
from pathlib import Path

def check_source_dlls():
    """检查源环境中的 ONNX Runtime DLL"""
    print("\n" + "=" * 70)
    print("  检查源环境中的 ONNX Runtime DLL")
    print("=" * 70 + "\n")
    
    try:
        import onnxruntime as ort
        ort_path = Path(ort.__file__).parent
        
        print(f"ONNX Runtime 版本: {ort.__version__}")
        print(f"安装路径: {ort_path}")
        print(f"支持的 Providers: {ort.get_available_providers()}")
        print()
        
        # 检查 capi 目录
        capi_path = ort_path / 'capi'
        if capi_path.exists():
            dll_files = list(capi_path.glob('*.dll'))
            print(f"✓ capi 目录存在: {capi_path}")
            print(f"  找到 {len(dll_files)} 个 DLL 文件:")
            
            for dll in sorted(dll_files):
                size_mb = dll.stat().st_size / (1024 * 1024)
                print(f"    - {dll.name:<40} ({size_mb:.2f} MB)")
            
            return dll_files
        else:
            print(f"✗ capi 目录不存在: {capi_path}")
            return []
            
    except ImportError:
        print("✗ onnxruntime 未安装")
        return []
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return []

def check_packaged_dlls():
    """检查打包后的程序中的 DLL"""
    print("\n" + "=" * 70)
    print("  检查打包后程序中的 ONNX Runtime DLL")
    print("=" * 70 + "\n")
    
    dist_dir = Path('dist/MEMEFinder')
    if not dist_dir.exists():
        print(f"✗ 打包目录不存在: {dist_dir}")
        print("  请先运行打包命令: python scripts/build_release.py")
        return []
    
    print(f"打包目录: {dist_dir}")
    print()
    
    # 查找所有 DLL 文件
    all_dlls = list(dist_dir.rglob('*.dll'))
    
    # 筛选 onnxruntime 相关的 DLL
    ort_dlls = [dll for dll in all_dlls if 'onnxruntime' in dll.name.lower()]
    cuda_dlls = [dll for dll in all_dlls if any(x in dll.name.lower() for x in ['cuda', 'cublas', 'cudnn', 'tensorrt'])]
    
    print(f"总共找到 {len(all_dlls)} 个 DLL 文件")
    print()
    
    if ort_dlls:
        print(f"✓ 找到 {len(ort_dlls)} 个 ONNX Runtime DLL:")
        for dll in sorted(ort_dlls):
            rel_path = dll.relative_to(dist_dir)
            size_mb = dll.stat().st_size / (1024 * 1024)
            print(f"    - {rel_path} ({size_mb:.2f} MB)")
    else:
        print("✗ 未找到 ONNX Runtime DLL")
    
    print()
    
    if cuda_dlls:
        print(f"✓ 找到 {len(cuda_dlls)} 个 CUDA 相关 DLL:")
        for dll in sorted(cuda_dlls):
            rel_path = dll.relative_to(dist_dir)
            size_mb = dll.stat().st_size / (1024 * 1024)
            print(f"    - {rel_path} ({size_mb:.2f} MB)")
    else:
        print("⚠ 未找到 CUDA 相关 DLL")
        print("  注意: 如果目标机器没有安装 CUDA，程序将自动使用 CPU 模式")
    
    return ort_dlls + cuda_dlls

def compare_dlls(source_dlls, packaged_dlls):
    """比较源环境和打包后的 DLL"""
    print("\n" + "=" * 70)
    print("  对比分析")
    print("=" * 70 + "\n")
    
    source_names = {dll.name for dll in source_dlls}
    packaged_names = {dll.name for dll in packaged_dlls}
    
    missing = source_names - packaged_names
    extra = packaged_names - source_names
    common = source_names & packaged_names
    
    print(f"源环境 DLL 数量: {len(source_names)}")
    print(f"打包后 DLL 数量: {len(packaged_names)}")
    print(f"共同 DLL 数量: {len(common)}")
    print()
    
    if missing:
        print(f"⚠ 缺失的 DLL ({len(missing)} 个):")
        for name in sorted(missing):
            print(f"    - {name}")
        print()
        print("  建议: 这些 DLL 可能导致 GPU 功能不可用")
        print("        需要在 spec 文件中手动添加")
    else:
        print("✓ 所有源环境的 DLL 都已包含在打包中")
    
    print()
    
    if extra:
        print(f"额外的 DLL ({len(extra)} 个):")
        for name in sorted(extra):
            print(f"    - {name}")
    
    return len(missing) == 0

def check_critical_dlls(packaged_dlls):
    """检查关键 DLL 是否存在"""
    print("\n" + "=" * 70)
    print("  关键 DLL 检查")
    print("=" * 70 + "\n")
    
    critical_dlls = {
        'onnxruntime.dll': 'ONNX Runtime 核心库',
        'onnxruntime_providers_shared.dll': 'ONNX Runtime Providers 共享库',
        'onnxruntime_providers_cuda.dll': 'CUDA Provider（GPU加速必需）',
    }
    
    packaged_names = {dll.name for dll in packaged_dlls}
    
    all_ok = True
    for dll_name, description in critical_dlls.items():
        if dll_name in packaged_names:
            print(f"✓ {dll_name:<40} {description}")
        else:
            print(f"✗ {dll_name:<40} {description} - 缺失！")
            all_ok = False
    
    print()
    
    if all_ok:
        print("✓ 所有关键 DLL 都已包含")
        print("  GPU 功能应该可以正常工作（如果目标机器有 CUDA）")
    else:
        print("✗ 缺少关键 DLL")
        print("  GPU 功能可能不可用，程序将自动降级到 CPU 模式")
    
    return all_ok

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ONNX Runtime GPU DLL 验证工具" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # 1. 检查源环境
    source_dlls = check_source_dlls()
    
    # 2. 检查打包后的程序
    packaged_dlls = check_packaged_dlls()
    
    # 3. 对比分析
    if source_dlls and packaged_dlls:
        all_included = compare_dlls(source_dlls, packaged_dlls)
    else:
        all_included = False
    
    # 4. 检查关键 DLL
    if packaged_dlls:
        critical_ok = check_critical_dlls(packaged_dlls)
    else:
        critical_ok = False
    
    # 5. 总结
    print("\n" + "=" * 70)
    print("  总结")
    print("=" * 70 + "\n")
    
    if critical_ok and all_included:
        print("✓ 验证通过！")
        print("  所有必要的 ONNX Runtime GPU DLL 都已正确打包")
        print("  打包的程序应该支持 GPU 加速")
        print()
        print("注意事项:")
        print("  1. 目标机器需要安装 NVIDIA GPU 驱动")
        print("  2. 如果 CUDA 运行库不可用，程序会自动降级到 CPU 模式")
        print("  3. 用户可以使用「启动_CPU模式.bat」强制使用 CPU 模式")
    elif critical_ok:
        print("⚠ 部分验证通过")
        print("  关键 DLL 已包含，但可能缺少部分辅助 DLL")
        print("  GPU 功能可能可用，但建议测试验证")
    else:
        print("✗ 验证失败")
        print("  打包的程序缺少关键的 GPU DLL")
        print()
        print("修复建议:")
        print("  1. 确保已安装 onnxruntime-gpu: pip install onnxruntime-gpu")
        print("  2. 检查 MEMEFinder.spec 文件中的 binaries 配置")
        print("  3. 重新运行打包命令: python scripts/build_release.py")
        print("  4. 如果问题持续，打包的程序将只支持 CPU 模式")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")
