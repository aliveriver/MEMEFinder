#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试打包后的程序是否能正常初始化OCR
"""

import subprocess
import time
from pathlib import Path

def test_packaged_app():
    """测试打包后的应用"""
    exe_path = Path('dist/MEMEFinder/MEMEFinder.exe')
    
    if not exe_path.exists():
        print(f"✗ 找不到可执行文件: {exe_path}")
        return False
    
    print("=" * 60)
    print("  测试打包后的 MEMEFinder")
    print("=" * 60)
    print(f"\n✓ 找到可执行文件: {exe_path}")
    print(f"✓ 文件大小: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    
    print("\n正在启动程序...(将在5秒后自动关闭)")
    print("请观察：")
    print("  1. 是否出现加载窗口")
    print("  2. 是否有 'DependencyError' 错误")
    print("  3. OCR是否成功初始化")
    print("\n" + "=" * 60)
    
    # 启动程序
    proc = subprocess.Popen(
        [str(exe_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # 等待5秒
    time.sleep(5)
    
    # 关闭程序
    try:
        proc.terminate()
        proc.wait(timeout=3)
        print("\n✓ 程序已关闭")
    except:
        proc.kill()
        print("\n✓ 程序已强制关闭")
    
    # 检查输出
    stdout, stderr = proc.communicate()
    
    if b'DependencyError' in stderr or b'dependency error' in stderr.lower():
        print("\n✗ 检测到 DependencyError！问题仍然存在")
        print(f"错误输出:\n{stderr.decode('utf-8', errors='ignore')}")
        return False
    
    print("\n✓ 未检测到 DependencyError")
    print("\n测试建议：手动运行程序并检查：")
    print(f"  {exe_path}")
    
    return True

if __name__ == '__main__':
    success = test_packaged_app()
    input("\n按回车退出...")
    exit(0 if success else 1)
