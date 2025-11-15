@echo off
REM MEMEFinder - 强制CPU模式启动器（打包版本）
REM 如果程序检测到GPU后闪退，请使用此脚本

echo ========================================
echo MEMEFinder - CPU模式
echo ========================================
echo.
echo 正在以CPU模式启动...
echo (禁用GPU，避免崩溃问题)
echo.

REM 设置环境变量强制使用CPU
set MEMEFINDER_FORCE_CPU=1

REM 检测程序文件
if exist "MEMEFinder.exe" (
    echo 找到 MEMEFinder.exe，正在启动...
    MEMEFinder.exe
) else if exist "dist\MEMEFinder\MEMEFinder.exe" (
    echo 找到 dist\MEMEFinder\MEMEFinder.exe，正在启动...
    dist\MEMEFinder\MEMEFinder.exe
) else (
    echo 错误: 未找到 MEMEFinder.exe
    echo 请确保此脚本与 MEMEFinder.exe 在同一目录
    echo.
)

pause
