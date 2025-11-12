@echo off
chcp 65001 > nul
title MEMEFinder 一键打包工具
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          MEMEFinder 一键打包工具                        ║
echo ║          自动打包为可执行程序                            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM 检查 Python 环境
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ✗ 错误: 未找到 Python 环境
    echo 请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo ✓ Python 环境正常
echo.

REM 检查 PyInstaller
echo [2/4] 检查 PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠ PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo ✗ PyInstaller 安装失败
        echo 请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
    echo ✓ PyInstaller 安装成功
) else (
    echo ✓ PyInstaller 已安装
)
echo.

REM 检查依赖
echo [3/4] 检查项目依赖...
if not exist "requirements.txt" (
    echo ⚠ 警告: 未找到 requirements.txt
) else (
    echo ✓ 找到依赖文件
)
echo.

REM 执行打包
echo [4/4] 开始打包...
echo.
python build_release.py

if errorlevel 1 (
    echo.
    echo ✗ 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                   打包完成！                            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 输出位置: dist\MEMEFinder\
echo 发布包: dist\MEMEFinder-v1.0.0-Windows-x64.zip
echo.
echo 下一步:
echo 1. 测试 dist\MEMEFinder\MEMEFinder.exe 是否可以正常运行
echo 2. 确认所有功能正常
echo 3. 将 ZIP 包分发给用户
echo.
pause


