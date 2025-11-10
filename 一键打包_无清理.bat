@echo off
chcp 65001 > nul
echo ========================================
echo MEMEFinder 优化打包（无清理模式）
echo ========================================
echo.
echo 注意：此脚本不会清理dist目录
echo 如果需要清理，请先运行"强制清理.bat"
echo.

echo [1/2] 开始打包...
python -m PyInstaller ^
    --noconfirm ^
    --name MEMEFinder ^
    --windowed ^
    --add-data "src;src" ^
    --add-data "README.md;." ^
    --collect-data paddlex ^
    --hidden-import unittest ^
    --hidden-import unittest.mock ^
    --hidden-import doctest ^
    --hidden-import paddleocr ^
    --hidden-import paddlenlp ^
    --hidden-import paddle ^
    --hidden-import cv2 ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import tkinter ^
    --hidden-import sqlite3 ^
    --exclude-module matplotlib ^
    --exclude-module scipy ^
    --exclude-module jupyter ^
    --exclude-module IPython ^
    --exclude-module pytest ^
    --exclude-module sphinx ^
    --exclude-module notebook ^
    --upx-dir . ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 打包成功！
    echo.
    
    echo [2/2] 计算文件大小...
    for /f %%A in ('powershell -command "(Get-ChildItem -Path 'dist\MEMEFinder' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"') do set SIZE=%%A
    echo 打包大小: %SIZE% MB
    echo.
    
    echo [3/3] 创建ZIP压缩包...
    powershell -command "Compress-Archive -Path 'dist\MEMEFinder\*' -DestinationPath 'dist\MEMEFinder.zip' -Force"
    
    if exist dist\MEMEFinder.zip (
        for %%A in (dist\MEMEFinder.zip) do set ZIPSIZE=%%~zA
        set /a ZIPSIZE_MB=ZIPSIZE/1048576
        echo ✓ ZIP创建成功！大小: !ZIPSIZE_MB! MB
    )
    
    echo.
    echo ========================================
    echo 所有任务完成！
    echo ========================================
    echo.
    echo 输出位置: dist\MEMEFinder\
    echo ZIP文件: dist\MEMEFinder.zip
    echo.
) else (
    echo.
    echo ✗ 打包失败！
    echo.
)

pause
