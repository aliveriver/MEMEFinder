#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源监控模块 - 监控内存、CPU使用情况
"""

import psutil
import gc
from typing import Dict, Any
from .logger import get_logger

logger = get_logger()


class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取当前内存使用情况
        
        Returns:
            {
                'rss_mb': float,      # 物理内存使用（MB）
                'vms_mb': float,      # 虚拟内存使用（MB）
                'percent': float,     # 内存使用百分比
            }
        """
        mem_info = self.process.memory_info()
        mem_percent = self.process.memory_percent()
        
        return {
            'rss_mb': mem_info.rss / 1024 / 1024,  # 物理内存
            'vms_mb': mem_info.vms / 1024 / 1024,  # 虚拟内存
            'percent': mem_percent
        }
    
    def get_cpu_usage(self) -> float:
        """
        获取CPU使用率（百分比）
        """
        return self.process.cpu_percent(interval=0.1)
    
    def get_system_memory(self) -> Dict[str, Any]:
        """
        获取系统内存信息
        
        Returns:
            {
                'total_mb': float,
                'available_mb': float,
                'used_mb': float,
                'percent': float
            }
        """
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total / 1024 / 1024,
            'available_mb': mem.available / 1024 / 1024,
            'used_mb': mem.used / 1024 / 1024,
            'percent': mem.percent
        }
    
    def force_garbage_collection(self):
        """
        强制执行垃圾回收
        """
        before = self.get_memory_usage()
        gc.collect()
        after = self.get_memory_usage()
        
        freed = before['rss_mb'] - after['rss_mb']
        if freed > 0:
            logger.info(f"垃圾回收: 释放了 {freed:.2f} MB 内存")
        
        return freed
    
    def check_memory_threshold(self, threshold_percent: float = 80.0) -> bool:
        """
        检查内存使用是否超过阈值
        
        Args:
            threshold_percent: 阈值百分比（默认80%）
            
        Returns:
            True: 超过阈值，False: 未超过
        """
        system_mem = self.get_system_memory()
        if system_mem['percent'] > threshold_percent:
            logger.warning(f"系统内存使用率过高: {system_mem['percent']:.1f}%")
            return True
        return False
    
    def log_resource_status(self):
        """
        记录当前资源使用状态
        """
        mem_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        system_mem = self.get_system_memory()
        
        logger.info("=" * 60)
        logger.info("资源使用状态:")
        logger.info(f"  进程内存: {mem_usage['rss_mb']:.2f} MB ({mem_usage['percent']:.1f}%)")
        logger.info(f"  系统内存: {system_mem['used_mb']:.0f}/{system_mem['total_mb']:.0f} MB ({system_mem['percent']:.1f}%)")
        logger.info(f"  CPU使用率: {cpu_usage:.1f}%")
        logger.info("=" * 60)
    
    def get_summary(self) -> str:
        """
        获取资源使用摘要（用于GUI显示）
        """
        mem_usage = self.get_memory_usage()
        system_mem = self.get_system_memory()
        cpu_usage = self.get_cpu_usage()
        
        return (f"内存: {mem_usage['rss_mb']:.1f}MB ({mem_usage['percent']:.1f}%) | "
                f"系统: {system_mem['percent']:.1f}% | "
                f"CPU: {cpu_usage:.1f}%")


# 全局资源监控器实例
_monitor = None


def get_resource_monitor() -> ResourceMonitor:
    """获取全局资源监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
