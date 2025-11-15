@echo off
chcp 65001 >nul
echo ========================================
echo MEMEFinder 多版本打包工具
echo ========================================
echo.
echo 此脚本将构建以下版本:
echo   1. CPU通用版 (适合所有用户)
echo   2. GPU-CUDA11版 (GTX 10/16/20系列)
echo   3. GPU-CUDA12版 (RTX 30/40系列)
echo.
echo 预计耗时: 30-60分钟
echo.
pause

echo.
echo ========================================
echo 开始构建所有版本...
echo ========================================
echo.

python scripts\build_multi_version.py --all

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！
    echo 请查看错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 所有版本构建完成！
echo ========================================
echo.
echo 输出位置: releases\
echo.
echo 生成的版本:
echo   - MEMEFinder_cpu
echo   - MEMEFinder_gpu-cuda11
echo   - MEMEFinder_gpu-cuda12
echo.
echo 下一步:
echo   1. 测试各个版本
echo   2. 压缩打包
echo   3. 上传发布
echo.
pause
