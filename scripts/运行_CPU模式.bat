@echo off
REM 强制使用CPU模式运行 MEMEFinder
REM 如果GPU模式有问题，可以使用此脚本

echo ========================================
echo MEMEFinder - CPU模式启动器
echo ========================================
echo.
echo 正在以CPU模式启动程序...
echo （禁用GPU加速，提高兼容性）
echo.

REM 设置环境变量强制使用CPU
set MEMEFINDER_FORCE_CPU=1

REM 启动主程序
python main.py

pause
