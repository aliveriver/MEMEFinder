#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存管理工具
负责内存监控、分析和优化
"""

import gc
import tracemalloc
from ...utils.logger import get_logger

logger = get_logger()


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, enable_profiling=False):
        """
        初始化内存监控器
        
        Args:
            enable_profiling: 是否启用详细的内存分析（生产环境建议关闭以节省600-700MB内存）
        """
        self._memory_profiling = enable_profiling
        
        if self._memory_profiling:
            tracemalloc.start()
            logger.info("内存分析已启动")
    
    def print_memory_status(self, label="内存状态", log_callback=None):
        """
        打印详细的内存使用状态（增强版）
        包含：实际物理内存、Python对象统计、内存分配详情
        注意：这些信息只记录到日志文件，不显示在UI上
        
        Args:
            label: 状态标签
            log_callback: 日志回调函数，用于输出到UI
        """
        try:
            import psutil
            import os
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            # 准备日志输出函数
            def log(msg, show_in_ui=False, log_level='debug'):
                if log_callback:
                    log_callback(msg, show_in_ui=show_in_ui)
                if log_level == 'debug':
                    logger.debug(msg)
                else:
                    logger.info(msg)
            
            # 只记录到日志文件，不显示在UI
            log(f"\n{'='*70}", show_in_ui=False)
            log(f"📊 {label}", show_in_ui=False)
            log(f"{'='*70}", show_in_ui=False)
            
            # 1. 实际物理内存使用
            rss_mb = mem_info.rss / 1024 / 1024
            vms_mb = mem_info.vms / 1024 / 1024
            log(f"📦 实际物理内存 (RSS): {rss_mb:.1f} MB", show_in_ui=False)
            log(f"📦 虚拟内存 (VMS): {vms_mb:.1f} MB", show_in_ui=False)
            
            # 2. Python GC统计
            gc_stats = gc.get_stats()
            gc_count = gc.get_count()
            log(f"\n🗑️  垃圾回收统计:", show_in_ui=False)
            log(f"  - 代数统计: Gen0={gc_count[0]}, Gen1={gc_count[1]}, Gen2={gc_count[2]}", show_in_ui=False)
            
            # 3. Python对象统计
            import sys
            obj_count = len(gc.get_objects())
            log(f"  - Python对象总数: {obj_count:,}", show_in_ui=False)
            
            # 4. 如果启用了tracemalloc，显示详细分配
            if self._memory_profiling and tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                # 总内存
                total = sum(stat.size for stat in top_stats)
                log(f"\n💾 Tracemalloc追踪的内存: {total / 1024 / 1024:.1f} MB", show_in_ui=False)
                
                # 前10个最大分配
                log(f"\n📈 内存占用 Top 10:", show_in_ui=False)
                for index, stat in enumerate(top_stats[:10], 1):
                    frame = stat.traceback[0]
                    filename = frame.filename
                    
                    # 简化路径
                    if 'MEMEFinder' in filename:
                        short_name = '...' + filename.split('MEMEFinder')[-1]
                    elif 'site-packages' in filename:
                        short_name = '...' + filename.split('site-packages')[-1]
                    else:
                        short_name = filename[-50:]
                    
                    log(
                        f"  {index}. {short_name}:{frame.lineno} - "
                        f"{stat.size / 1024 / 1024:.1f} MB ({stat.count:,} 对象)",
                        show_in_ui=False
                    )
            
            log(f"{'='*70}\n", show_in_ui=False)
            
        except Exception as e:
            logger.error(f"内存状态打印失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    @staticmethod
    def force_garbage_collection():
        """
        强制垃圾回收
        多次GC确保主进程内存彻底清理
        
        Returns:
            回收的对象总数
        """
        logger.info("主进程开始强制垃圾回收...")
        
        # 先清理第0代（最快）
        collected0 = gc.collect(0)
        logger.debug(f"GC generation 0: 回收了 {collected0} 个对象")
        
        # 再清理第1代
        collected1 = gc.collect(1)
        logger.debug(f"GC generation 1: 回收了 {collected1} 个对象")
        
        # 最后清理第2代（最彻底）
        collected2 = gc.collect(2)
        logger.debug(f"GC generation 2: 回收了 {collected2} 个对象")
        
        total_collected = collected0 + collected1 + collected2
        logger.info(f"主进程总共回收了 {total_collected} 个对象")
        
        return total_collected
    
    @staticmethod
    def cleanup_numpy_cache():
        """清理NumPy/OpenCV缓存"""
        try:
            import numpy as np
            # 清理NumPy内部缓存
            np._core._get_handler_cache().clear()
            logger.debug("NumPy缓存已清理")
        except Exception as e:
            logger.debug(f"NumPy缓存清理失败: {e}")
