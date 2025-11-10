@echo off
chcp 65001 > nul
title MEMEFinder - 打包程序

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              MEMEFinder - 打包为可执行文件                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 正在检查 PyInstaller...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo ✗ PyInstaller 未安装，正在安装...
    pip install pyinstaller
)
echo ✓ PyInstaller 已就绪
echo.

echo 开始打包程序...
echo 这可能需要 5-10 分钟，请耐心等待...
echo.

python build_exe.py

if errorlevel 1 (
    echo.
    echo ✗ 打包失败
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    打包完成！                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 输出位置: dist\MEMEFinder\
echo 发布包: dist\MEMEFinder-v1.0.0-Windows-x64.zip
echo.
echo 后续步骤:
echo   1. 测试 dist\MEMEFinder\MEMEFinder.exe 是否正常运行
echo   2. 首次运行需要执行 "下载模型.bat" 下载 AI 模型
echo   3. 将 ZIP 文件上传到 GitHub Releases
echo.
pause
