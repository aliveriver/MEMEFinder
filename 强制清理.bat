@echo off
chcp 65001 > nul
echo ========================================
echo 强制清理 dist 和 build 目录
echo ========================================
echo.

echo [1/6] 尝试结束可能的MEMEFinder进程...
taskkill /F /IM MEMEFinder.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul

echo [2/6] 尝试解除文件占用 (使用handle工具)...
REM 如果安装了handle.exe，可以取消下面的注释
REM handle.exe -p explorer.exe dist\MEMEFinder -c > nul 2>&1
timeout /t 1 /nobreak > nul

echo [3/6] 重启Windows资源管理器...
taskkill /F /IM explorer.exe 2>nul
timeout /t 2 /nobreak > nul
start explorer.exe
timeout /t 3 /nobreak > nul

echo [4/6] 尝试删除dist目录...
if exist dist (
    rd /s /q dist 2>nul
    if exist dist (
        echo    X dist目录删除失败
        echo    请手动删除 dist 文件夹后按任意键继续...
        pause
        rd /s /q dist 2>nul
    ) else (
        echo    √ dist目录已删除
    )
) else (
    echo    √ dist目录不存在
)

echo [5/6] 尝试删除build目录...
if exist build (
    rd /s /q build 2>nul
    if exist build (
        echo    X build目录删除失败，尝试继续...
    ) else (
        echo    √ build目录已删除
    )
) else (
    echo    √ build目录不存在
)

echo [6/6] 删除临时文件...
if exist MEMEFinder.spec del /f /q MEMEFinder.spec 2>nul
if exist *.pyc del /f /q *.pyc 2>nul

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 现在可以重新运行打包了。
echo.
pause
