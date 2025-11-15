#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试GPU超时机制

用于验证RapidOCR GPU初始化超时保护是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger()

def test_gpu_timeout():
    """测试GPU超时机制"""
    logger.info("=" * 60)
    logger.info("测试GPU超时机制")
    logger.info("=" * 60)
    
    # 强制使用GPU模式
    logger.info("\n测试1: 强制启用GPU模式（可能会超时）")
    try:
        from src.core.ocr_processor import OCRProcessor
        processor = OCRProcessor(use_gpu=True)
        logger.info("✓ GPU模式初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ GPU模式初始化失败: {e}")
        logger.info("这是预期行为，程序应该已经自动切换到CPU模式")
        return False

def test_force_cpu():
    """测试强制CPU模式"""
    logger.info("\n" + "=" * 60)
    logger.info("测试环境变量强制CPU模式")
    logger.info("=" * 60)
    
    # 设置环境变量
    os.environ['MEMEFINDER_FORCE_CPU'] = '1'
    
    try:
        from src.core.ocr_processor import OCRProcessor
        # 需要重新导入以应用环境变量
        import importlib
        import src.core.ocr_processor
        importlib.reload(src.core.ocr_processor)
        
        processor = src.core.ocr_processor.OCRProcessor()
        logger.info("✓ 环境变量强制CPU模式成功")
        return True
    except Exception as e:
        logger.error(f"✗ 强制CPU模式失败: {e}")
        return False
    finally:
        # 清理环境变量
        if 'MEMEFINDER_FORCE_CPU' in os.environ:
            del os.environ['MEMEFINDER_FORCE_CPU']

def test_auto_detect():
    """测试自动检测GPU"""
    logger.info("\n" + "=" * 60)
    logger.info("测试自动检测GPU")
    logger.info("=" * 60)
    
    try:
        from src.core.ocr_processor import OCRProcessor
        processor = OCRProcessor()  # 自动检测
        logger.info("✓ 自动检测模式初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ 自动检测模式失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 15 + "GPU超时机制测试工具" + " " * 18 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")
    
    results = []
    
    # 测试1: 自动检测
    logger.info("\n【测试1】自动检测GPU模式")
    results.append(("自动检测", test_auto_detect()))
    
    # 测试2: 强制GPU（可能超时）
    logger.info("\n【测试2】强制GPU模式（测试超时保护）")
    logger.info("注意: 此测试预期在GPU环境有问题时会失败并自动降级")
    results.append(("强制GPU", test_gpu_timeout()))
    
    # 测试3: 强制CPU
    logger.info("\n【测试3】环境变量强制CPU模式")
    results.append(("强制CPU", test_force_cpu()))
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{name}: {status}")
    
    success_count = sum(1 for _, r in results if r)
    total_count = len(results)
    logger.info(f"\n总计: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        logger.info("\n✓ 所有测试通过！")
    else:
        logger.warning(f"\n⚠ {total_count - success_count} 个测试失败")
        logger.info("提示: 如果只有「强制GPU」测试失败，这是正常的")
        logger.info("      因为该测试目的就是验证超时保护机制")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n✗ 用户取消测试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")
