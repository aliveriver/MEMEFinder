@echo off
chcp 65001 > nul
title MEMEFinder - 创建安装程序

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          MEMEFinder - 创建 Windows 安装程序               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 这个脚本将创建一个专业的 Windows 安装程序
echo 安装程序会在用户安装时自动下载 AI 模型
echo.

echo [1/3] 检查 Inno Setup...
echo.

REM 检查常见的 Inno Setup 安装路径
set "ISCC="
where iscc > nul 2>&1
if not errorlevel 1 (
    set "ISCC=iscc"
    goto :iscc_found
)

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :iscc_found
)

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :iscc_found
)

if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    goto :iscc_found
)

echo ✗ 未找到 Inno Setup 命令行编译器 (ISCC.exe)
echo.
echo Inno Setup 已安装，但需要使用命令行编译器
echo.
echo 请手动编译:
echo 1. 打开 "C:\Program Files (x86)\Inno Setup 6\Compil32.exe"
echo 2. 打开文件: installer\setup.iss
echo 3. 点击 "编译" 或按 F9
echo.
pause
exit /b 1

:iscc_found
echo ✓ Inno Setup 已找到: %ISCC%
echo.

echo [2/3] 检查打包文件...
echo.

if not exist "dist\MEMEFinder\MEMEFinder.exe" (
    echo ✗ 找不到可执行文件
    echo.
    echo 请先运行打包脚本：
    echo   打包发布版.bat
    echo.
    echo 或者运行：
    echo   python build_release.py
    pause
    exit /b 1
)

echo ✓ 找到打包文件: dist\MEMEFinder\MEMEFinder.exe

echo.
echo [3/3] 创建安装程序...
echo.

echo 正在使用 Inno Setup 编译安装程序...
"%ISCC%" installer\setup.iss

if errorlevel 1 (
    echo.
    echo ✗ 创建安装程序失败
    echo.
    echo 请检查:
    echo 1. dist\MEMEFinder 目录是否存在
    echo 2. installer\setup.iss 文件是否正确
    echo.
    echo 或者手动编译:
    echo   打开 Compil32.exe 并加载 installer\setup.iss
    echo.
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    创建成功！                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 输出文件: installer\MEMEFinder-Setup-v1.0.0.exe
echo.
echo 这是一个完整的 Windows 安装程序，包含：
echo   ✓ 程序主体（约 600 MB）
echo   ✓ 安装向导（支持中英文）
echo   ✓ 自动下载 AI 模型（安装时可选）
echo   ✓ 桌面快捷方式
echo   ✓ 开始菜单项
echo   ✓ 卸载程序
echo.
echo 用户使用流程：
echo   1. 双击安装程序
echo   2. 选择安装路径
echo   3. 勾选"安装后自动下载 AI 模型"
echo   4. 完成安装后自动下载模型
echo   5. 开始使用
echo.
echo 现在可以将安装程序上传到 GitHub Releases！
echo.
pause
