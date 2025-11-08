@echo off
chcp 65001 >nul
echo ========================================
echo   MEMEFinder - 表情包查找器
echo ========================================
echo.
echo 正在启动GUI程序...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序启动失败！
    echo.
    echo 可能的原因：
    echo 1. 未安装Python
    echo 2. 未安装依赖包
    echo.
    echo 解决方法：
    echo pip install -r requirements.txt
    echo.
    pause
)
