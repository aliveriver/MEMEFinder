@echo off
chcp 65001 > nul
title MEMEFinder Release 打包

python build_release.py

if errorlevel 1 (
    echo.
    echo 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 打包成功！
pause
