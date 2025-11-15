@echo off
chcp 65001 >nul
cls

echo ========================================
echo MEMEFinder Git 提交助手
echo ========================================
echo.
echo 此脚本将帮助您按正确顺序提交代码
echo.
pause

REM 步骤1: 清理项目
echo.
echo [1/6] 清理项目临时文件...
echo ========================================
python scripts\clean_project.py
if %errorlevel% neq 0 (
    echo ❌ 清理失败！
    pause
    exit /b 1
)
echo ✅ 清理完成
echo.

REM 步骤2: 查看当前状态
echo [2/6] 查看当前Git状态...
echo ========================================
git status
echo.
pause

REM 步骤3: 添加文件
echo [3/6] 添加文件到Git...
echo ========================================

echo 添加核心配置文件...
git add .gitignore
git add requirements.txt
git add main.py
git add LICENSE

echo 添加源代码...
git add src/

echo 添加文档...
git add README.md
git add 版本选择指南.md
git add 多版本解决方案总结.md
git add 打包检查清单.md
git add 项目结构优化.md
git add 发布完整教程.md
git add Git提交快速指南.md
git add GIT_COMMIT_GUIDE.md
git add PROJECT_ORGANIZATION.md
git add docs/

echo 添加脚本和测试...
git add scripts/
git add test/

echo 添加打包配置...
git add MEMEFinder.spec
git add installer/

echo ✅ 文件添加完成
echo.

REM 步骤4: 显示将要提交的文件
echo [4/6] 查看将要提交的文件...
echo ========================================
git status
echo.
echo 上面显示的文件将被提交
echo.
pause

REM 步骤5: 输入提交信息
echo [5/6] 输入提交信息...
echo ========================================
echo.
echo 建议的提交信息格式:
echo   feat: 添加新功能
echo   fix: 修复问题
echo   docs: 更新文档
echo   chore: 项目维护
echo.
set /p commit_msg="请输入提交信息: "

if "%commit_msg%"=="" (
    echo ❌ 提交信息不能为空！
    pause
    exit /b 1
)

REM 步骤6: 执行提交
echo.
echo [6/6] 提交到本地仓库...
echo ========================================
git commit -m "%commit_msg%"

if %errorlevel% neq 0 (
    echo ❌ 提交失败！
    pause
    exit /b 1
)

echo ✅ 提交成功！
echo.

REM 询问是否推送
echo ========================================
echo 是否推送到远程仓库？
echo ========================================
set /p push_choice="推送到远程? (y/n): "

if /i "%push_choice%"=="y" (
    echo.
    echo 正在推送...
    git push origin main
    
    if %errorlevel% neq 0 (
        echo.
        echo ⚠️ 推送失败，可能需要先设置远程仓库或拉取更新
        echo.
        echo 手动推送命令:
        echo   git push origin main
        echo.
        echo 或者如果是首次推送:
        echo   git push -u origin main
    ) else (
        echo ✅ 推送成功！
    )
) else (
    echo.
    echo ℹ️ 跳过推送，您可以稍后手动推送:
    echo   git push origin main
)

echo.
echo ========================================
echo 🎉 完成！
echo ========================================
echo.
echo 提交摘要:
git log -1 --oneline
echo.
echo 下一步建议:
echo   1. 查看GitHub仓库确认提交
echo   2. 继续开发或准备发布
echo   3. 运行测试: python test\test_multi_version.py
echo.
pause
