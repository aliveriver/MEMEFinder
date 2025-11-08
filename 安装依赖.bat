@echo off
chcp 65001 >nul
echo ========================================
echo   MEMEFinder - 安装依赖包
echo ========================================
echo.
echo 正在安装Python依赖包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 安装失败！
    echo.
    echo 请检查：
    echo 1. 是否已安装Python 3.8+
    echo 2. 是否可以连接网络
    echo 3. pip是否正常工作
    echo.
) else (
    echo.
    echo ========================================
    echo   安装完成！
    echo ========================================
    echo.
    echo 现在可以运行程序了：
    echo 方式1: 双击 "启动程序.bat"
    echo 方式2: 运行 "python meme_finder_gui.py"
    echo.
)

pause
