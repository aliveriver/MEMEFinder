#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接池管理模块
"""

import sqlite3
import threading
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import get_logger

logger = get_logger()


class DatabaseConnectionPool:
    """SQLite连接池 - 线程安全"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = []
        self._lock = threading.Lock()
        self._local = threading.local()
        
        logger.debug(f"初始化数据库连接池: {db_path} (大小: {pool_size})")
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        # 使用线程本地存储，避免跨线程使用连接
        if hasattr(self._local, 'conn') and self._local.conn:
            return self._local.conn
        
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._local.conn = conn
                return conn
        
        # 创建新连接
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0  # 30秒超时
        )
        # 优化SQLite性能
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # 平衡安全和性能
        conn.execute("PRAGMA cache_size=-64000")  # 64MB缓存
        conn.execute("PRAGMA temp_store=MEMORY")  # 内存存储临时表
        
        self._local.conn = conn
        logger.debug("创建新数据库连接")
        return conn
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还连接到池"""
        if not conn:
            return
        
        with self._lock:
            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
            else:
                conn.close()
                logger.debug("连接池已满，关闭连接")
        
        if hasattr(self._local, 'conn'):
            self._local.conn = None
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()
            logger.info("已关闭所有数据库连接")
