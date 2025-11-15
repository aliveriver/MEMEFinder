@echo off
REM MEMEFinder CPU模式启动脚本
REM 
REM 如果你在使用GPU模式时遇到闪退或卡死问题，
REM 可以使用此脚本强制使用CPU模式启动程序

echo ================================================
echo   MEMEFinder - CPU 模式启动
echo ================================================
echo.
echo 正在以 CPU 模式启动 MEMEFinder...
echo 注意: CPU 模式比 GPU 模式慢 2-3 倍
echo.

REM 设置环境变量强制使用CPU模式
set MEMEFINDER_FORCE_CPU=1

REM 启动程序
start "" "%~dp0MEMEFinder.exe"

echo.
echo 程序已启动！
echo 如需恢复 GPU 模式，请直接双击 MEMEFinder.exe
echo.
pause
