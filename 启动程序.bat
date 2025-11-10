@echo off
chcp 65001 > nul
title MEMEFinder - 表情包智能管理工具

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║            MEMEFinder - 表情包智能管理工具                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 正在启动程序...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ✗ 程序运行出错
    echo.
    echo 可能的原因：
    echo   1. Python 未安装或未添加到环境变量
    echo   2. 依赖包未安装（请运行 "一键安装.bat"）
    echo   3. 模型文件未下载（请运行 "一键安装.bat"）
    echo.
    echo 请查看 logs 目录下的日志文件获取详细错误信息
    echo.
    pause
)
