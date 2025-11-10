@echo off
chcp 65001 > nul
title MEMEFinder - 一键安装

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                MEMEFinder - 一键安装脚本                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [1/3] 检查 Python 环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo ✗ 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✓ Python 已安装
echo.

echo [2/3] 安装 Python 依赖包...
echo 这可能需要几分钟时间，请耐心等待...
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo ✗ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo.
echo ✓ 依赖安装完成
echo.

echo [3/3] 下载 AI 模型...
echo 这可能需要 5-15 分钟，取决于网速...
echo.
python download_models.py
echo.

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    安装完成！                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 现在可以运行 MEMEFinder 了！
echo.
echo 启动方式：
echo   1. 双击 "启动程序.bat"
echo   2. 或者在命令行运行: python main.py
echo.
pause
