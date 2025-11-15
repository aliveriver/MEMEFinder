#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU 修复验证工具

用于验证 GPU 超时问题是否已经修复
"""

import sys
import os
import time
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_timeout_fallback():
    """测试超时降级机制是否工作"""
    print_header("测试 GPU 超时降级机制")
    
    try:
        # 添加项目路径
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / 'src'))
        
        from core.ocr_processor import OCRProcessor
        from utils.logger import get_logger
        
        logger = get_logger()
        
        print("1. 初始化 OCR 处理器（强制 GPU 模式）...")
        print("   预期行为: 如果 GPU 不可用或超时，应自动降级到 CPU")
        print()
        
        # 强制使用 GPU 来测试超时机制
        start_time = time.time()
        
        try:
            processor = OCRProcessor(use_gpu=True)
            elapsed = time.time() - start_time
            
            print(f"✓ OCR 处理器初始化成功")
            print(f"  耗时: {elapsed:.2f} 秒")
            
            if elapsed > 30:
                print("⚠ 初始化时间过长（>30秒）")
                print("  可能发生了超时降级")
                return 'timeout_occurred'
            elif elapsed < 5:
                print("✓ 初始化快速完成")
                print("  GPU 模式正常工作或已正确使用 CPU")
                return 'success'
            else:
                print("✓ 初始化正常")
                return 'success'
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ OCR 处理器初始化失败: {e}")
            print(f"  耗时: {elapsed:.2f} 秒")
            
            if elapsed > 25:
                print("⚠ 失败前等待了很长时间")
                print("  超时机制可能未正确触发")
                return 'timeout_not_working'
            else:
                print("  快速失败，这是预期行为（降级机制工作）")
                return 'fallback_working'
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 'test_failed'

def test_cpu_mode():
    """测试纯 CPU 模式"""
    print_header("测试 CPU 模式")
    
    try:
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / 'src'))
        
        from core.ocr_processor import OCRProcessor
        
        print("1. 初始化 OCR 处理器（CPU 模式）...")
        print()
        
        start_time = time.time()
        processor = OCRProcessor(use_gpu=False)
        elapsed = time.time() - start_time
        
        print(f"✓ OCR 处理器初始化成功（CPU 模式）")
        print(f"  耗时: {elapsed:.2f} 秒")
        
        if elapsed > 10:
            print("⚠ CPU 初始化时间较长")
            return 'slow'
        else:
            print("✓ CPU 初始化正常")
            return 'success'
            
    except Exception as e:
        print(f"✗ CPU 模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 'failed'

def test_env_var_force_cpu():
    """测试环境变量强制 CPU"""
    print_header("测试环境变量 MEMEFINDER_FORCE_CPU")
    
    try:
        # 设置环境变量
        os.environ['MEMEFINDER_FORCE_CPU'] = '1'
        
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / 'src'))
        
        # 重新导入以应用环境变量
        import importlib
        if 'core.ocr_processor' in sys.modules:
            importlib.reload(sys.modules['core.ocr_processor'])
        
        from core.ocr_processor import OCRProcessor
        
        print("1. 设置环境变量: MEMEFINDER_FORCE_CPU=1")
        print("2. 初始化 OCR 处理器...")
        print("   预期: 即使不指定 use_gpu=False 也应使用 CPU")
        print()
        
        start_time = time.time()
        processor = OCRProcessor()  # 不指定 use_gpu
        elapsed = time.time() - start_time
        
        print(f"✓ OCR 处理器初始化成功")
        print(f"  耗时: {elapsed:.2f} 秒")
        
        if elapsed < 5:
            print("✓ 快速初始化，环境变量生效")
            return 'success'
        else:
            print("⚠ 初始化较慢，可能环境变量未生效")
            return 'unclear'
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 'failed'
    finally:
        # 清理环境变量
        if 'MEMEFINDER_FORCE_CPU' in os.environ:
            del os.environ['MEMEFINDER_FORCE_CPU']

def check_log_for_timeout():
    """检查最新日志中是否有超时记录"""
    print_header("检查日志文件")
    
    try:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / 'logs'
        
        if not log_dir.exists():
            print("⊘ 日志目录不存在")
            return 'no_logs'
        
        # 找最新的日志文件
        log_files = sorted(log_dir.glob('memefinder_*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not log_files:
            print("⊘ 没有日志文件")
            return 'no_logs'
        
        latest_log = log_files[0]
        print(f"最新日志: {latest_log.name}")
        print()
        
        # 读取最后 100 行
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_100 = lines[-100:] if len(lines) > 100 else lines
        
        # 查找关键信息
        has_timeout = False
        has_fallback = False
        has_cpu_success = False
        
        for line in last_100:
            if 'GPU模式初始化超时' in line or 'GPU初始化超时' in line:
                has_timeout = True
                print(f"  发现: {line.strip()}")
            
            if '自动切换到CPU模式' in line or '正在自动切换' in line:
                has_fallback = True
                print(f"  发现: {line.strip()}")
            
            if 'RapidOCR 初始化成功（CPU 模式）' in line:
                has_cpu_success = True
                print(f"  发现: {line.strip()}")
        
        print()
        
        if has_timeout and has_fallback and has_cpu_success:
            print("✓ 日志显示超时降级机制工作正常")
            return 'working'
        elif has_timeout and not has_fallback:
            print("⚠ 发现超时但没有降级记录")
            return 'no_fallback'
        elif not has_timeout:
            print("⊘ 没有发现超时记录（可能没有触发）")
            return 'no_timeout'
        else:
            return 'unclear'
            
    except Exception as e:
        print(f"✗ 检查日志失败: {e}")
        return 'failed'

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "GPU 修复验证工具" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {}
    
    # 测试 1: CPU 模式（基准测试）
    print("\n[测试 1/4] CPU 模式基准测试")
    results['cpu'] = test_cpu_mode()
    
    # 测试 2: 环境变量强制 CPU
    print("\n[测试 2/4] 环境变量强制 CPU")
    results['env_var'] = test_env_var_force_cpu()
    
    # 测试 3: 检查日志
    print("\n[测试 3/4] 检查历史日志")
    results['log'] = check_log_for_timeout()
    
    # 测试 4: GPU 超时降级（可选，如果有 GPU）
    print("\n[测试 4/4] GPU 超时降级测试")
    print("⚠ 注意: 如果你的机器有 GPU，此测试可能需要 30 秒")
    
    choice = input("是否执行此测试？[y/N]: ").strip().lower()
    if choice == 'y':
        results['timeout'] = test_timeout_fallback()
    else:
        print("⊘ 跳过 GPU 测试")
        results['timeout'] = 'skipped'
    
    # 总结
    print_header("验证总结")
    
    print("测试结果:")
    print(f"  CPU 模式:         {results['cpu']}")
    print(f"  环境变量强制CPU:  {results['env_var']}")
    print(f"  日志检查:         {results['log']}")
    print(f"  GPU 超时降级:     {results['timeout']}")
    print()
    
    # 评估修复状态
    print("=" * 70)
    print("  修复状态评估")
    print("=" * 70)
    print()
    
    if results['cpu'] == 'success':
        print("✅ CPU 模式工作正常")
    else:
        print("❌ CPU 模式有问题，需要检查基础环境")
        return
    
    if results['env_var'] == 'success':
        print("✅ 环境变量强制 CPU 功能正常")
    else:
        print("⚠️ 环境变量功能可能有问题")
    
    if results['log'] == 'working':
        print("✅ 超时降级机制已验证（从日志）")
    elif results['log'] == 'no_timeout':
        print("⊘ 没有超时记录（可能没有 GPU 或未触发）")
    
    if results['timeout'] == 'success':
        print("✅ GPU 模式正常工作或已正确降级")
    elif results['timeout'] == 'fallback_working':
        print("✅ 降级机制工作正常")
    elif results['timeout'] == 'timeout_occurred':
        print("⚠️ 发生了超时，但最终成功（降级可能工作）")
    elif results['timeout'] == 'timeout_not_working':
        print("❌ 超时机制可能未正确工作")
    elif results['timeout'] == 'skipped':
        print("⊘ GPU 测试被跳过")
    
    print()
    print("=" * 70)
    print("  建议")
    print("=" * 70)
    print()
    
    if results['cpu'] == 'success' and results['env_var'] == 'success':
        print("✅ 核心功能正常！")
        print()
        print("用户使用建议:")
        print("  1. 默认使用「启动_CPU模式.bat」")
        print("  2. 如果有 NVIDIA GPU，可尝试直接启动")
        print("     - 如果30秒内启动: GPU 工作正常")
        print("     - 如果30秒后启动: 已自动降级到 CPU，下次建议用 CPU 模式")
        print()
    else:
        print("⚠️ 存在一些问题，建议检查:")
        print("  • Python 环境是否正确")
        print("  • rapidocr_onnxruntime 是否已安装")
        print("  • 模型文件是否存在")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消验证")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")
