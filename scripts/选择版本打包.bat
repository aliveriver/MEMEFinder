@echo off
chcp 65001 >nul
cls

:menu
echo ========================================
echo MEMEFinder 版本选择打包工具
echo ========================================
echo.
echo 请选择要打包的版本:
echo.
echo [1] CPU通用版 (推荐，适合所有用户)
echo [2] GPU-CUDA11版 (GTX 10/16/20系列)
echo [3] GPU-CUDA12版 (RTX 30/40系列)
echo [4] 打包所有版本
echo [0] 退出
echo.
set /p choice="请输入选项 (0-4): "

if "%choice%"=="1" goto build_cpu
if "%choice%"=="2" goto build_cuda11
if "%choice%"=="3" goto build_cuda12
if "%choice%"=="4" goto build_all
if "%choice%"=="0" goto end

echo 无效选项，请重新选择
timeout /t 2 >nul
cls
goto menu

:build_cpu
echo.
echo ========================================
echo 正在构建 CPU通用版...
echo ========================================
echo.
python scripts\build_multi_version.py --version cpu
goto check_result

:build_cuda11
echo.
echo ========================================
echo 正在构建 GPU-CUDA11版...
echo ========================================
echo.
python scripts\build_multi_version.py --version gpu-cuda11
goto check_result

:build_cuda12
echo.
echo ========================================
echo 正在构建 GPU-CUDA12版...
echo ========================================
echo.
python scripts\build_multi_version.py --version gpu-cuda12
goto check_result

:build_all
echo.
echo ========================================
echo 正在构建所有版本...
echo ========================================
echo.
python scripts\build_multi_version.py --all
goto check_result

:check_result
if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！
    pause
) else (
    echo.
    echo ✅ 构建成功！
    echo 输出位置: releases\
    pause
)
cls
goto menu

:end
echo.
echo 再见！
timeout /t 1 >nul
exit /b 0
