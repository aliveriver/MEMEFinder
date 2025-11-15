# Git提交顺序快速指南

## 🚀 一键提交脚本

创建 `git_commit_all.bat`：

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo MEMEFinder Git 提交助手
echo ========================================
echo.

echo 步骤1: 清理项目...
python scripts\clean_project.py

echo.
echo 步骤2: 查看状态...
git status

echo.
echo 步骤3: 添加文件...
pause

REM 核心配置
git add .gitignore
git add requirements.txt
git add main.py
git add LICENSE

REM 源代码
git add src/

REM 文档
git add README.md
git add 版本选择指南.md
git add 多版本解决方案总结.md
git add 打包检查清单.md
git add 项目结构优化.md
git add 发布完整教程.md
git add docs/

REM 脚本和测试
git add scripts/
git add test/

REM 打包配置
git add MEMEFinder.spec
git add installer/

echo.
echo 步骤4: 查看将要提交的文件...
git status

echo.
set /p commit_msg="请输入提交信息: "

echo.
echo 步骤5: 提交...
git commit -m "%commit_msg%"

echo.
echo ✅ 提交完成！
echo.
echo 下一步:
echo   git push origin main
echo.
pause
```

## 📝 标准提交顺序

### 第一次提交：项目初始化

```bash
# 1. 清理项目
python scripts\clean_project.py

# 2. 添加基础配置
git add .gitignore
git add LICENSE
git add README.md
git add requirements.txt

# 3. 提交
git commit -m "chore: 初始化项目配置文件"
```

### 第二次提交：核心代码

```bash
# 添加主程序和源代码
git add main.py
git add src/

# 提交
git commit -m "feat: 添加核心功能模块

- OCR处理器
- 数据库管理
- 文件扫描
- GUI界面"
```

### 第三次提交：文档

```bash
# 添加所有文档
git add docs/
git add 版本选择指南.md
git add 多版本解决方案总结.md
git add 打包检查清单.md
git add 项目结构优化.md
git add 发布完整教程.md
git add GIT_COMMIT_GUIDE.md
git add PROJECT_ORGANIZATION.md

# 提交
git commit -m "docs: 添加完整项目文档

- 用户指南和快速开始
- 多版本发布指南
- 开发者文档
- GPU使用说明"
```

### 第四次提交：工具脚本

```bash
# 添加脚本
git add scripts/

# 提交
git commit -m "feat: 添加构建和维护工具

- 多版本构建脚本
- 版本推荐工具
- 项目维护脚本
- 批处理快捷方式"
```

### 第五次提交：测试

```bash
# 添加测试
git add test/

# 提交
git commit -m "test: 添加测试套件

- 多版本构建测试
- 依赖检查
- 打包应用测试"
```

### 第六次提交：打包配置

```bash
# 添加打包配置
git add MEMEFinder.spec
git add installer/

# 提交
git commit -m "build: 添加打包配置

- PyInstaller配置
- Inno Setup安装程序配置"
```

### 最终推送

```bash
# 查看提交历史
git log --oneline

# 推送到远程
git push origin main

# 如果是首次推送
git push -u origin main
```

## 🔍 提交前检查

### 检查将要提交的文件

```bash
# 查看状态
git status

# 查看将要添加的文件
git status --short

# 查看被忽略的文件（确保正确）
git status --ignored
```

### 检查差异

```bash
# 查看所有更改
git diff

# 查看已暂存的更改
git diff --staged
```

### 验证.gitignore

```bash
# 检查特定文件是否被忽略
git check-ignore -v build/
git check-ignore -v releases/
git check-ignore -v *.db
git check-ignore -v *.log
git check-ignore -v models/*.onnx
```

## ❌ 不应该提交的文件

确保这些文件/目录在.gitignore中：

```
build/              # 构建临时文件
dist/               # PyInstaller输出
releases/           # 多版本发布文件
__pycache__/        # Python缓存
*.pyc              # Python字节码
*.log              # 日志文件
*.db               # 数据库文件
*.db-shm           # 数据库临时文件
*.db-wal           # 数据库WAL文件
logs/              # 日志目录
imgs/              # 测试图片
models/*.onnx      # 模型文件（大文件）
models/snownlp/    # SnowNLP数据
推荐版本.txt        # 临时生成文件
src/version_config.json  # 构建时生成
MEMEFinder_*.spec  # 动态生成的spec
```

## ✅ 应该提交的文件

```
src/               # 源代码
docs/              # 文档
scripts/           # 脚本
test/              # 测试
main.py            # 主程序
requirements.txt   # 依赖
MEMEFinder.spec    # PyInstaller模板
.gitignore         # Git配置
LICENSE            # 许可证
README.md          # 项目说明
版本选择指南.md     # 用户指南
多版本解决方案总结.md  # 技术总结
打包检查清单.md     # 发布清单
项目结构优化.md     # 结构说明
发布完整教程.md     # 发布教程
installer/setup.iss  # 安装程序配置
```

## 🔧 常用Git命令

### 撤销操作

```bash
# 撤销未暂存的更改
git checkout -- <file>

# 撤销已暂存的文件
git reset HEAD <file>

# 修改最后一次提交
git commit --amend

# 回退到上一次提交
git reset --soft HEAD^
```

### 查看历史

```bash
# 查看提交历史
git log

# 简洁查看
git log --oneline

# 查看文件历史
git log <file>

# 查看某次提交的详情
git show <commit-hash>
```

### 分支操作

```bash
# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature
```

## 📋 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具变动
- `perf`: 性能优化
- `build`: 构建系统

### 示例

```bash
# 新功能
git commit -m "feat(ocr): 添加GPU加速支持"

# 修复
git commit -m "fix(gui): 修复搜索框不响应问题"

# 文档
git commit -m "docs: 更新多版本使用指南"

# 重构
git commit -m "refactor(core): 优化数据库查询性能"
```

## 🎯 快速命令备忘

```bash
# 一键清理+查看状态
python scripts\clean_project.py && git status

# 添加所有已跟踪文件的更改
git add -u

# 查看将要提交什么
git diff --staged --name-only

# 提交并推送
git commit -m "your message" && git push

# 查看远程仓库
git remote -v
```

## 🚨 注意事项

1. **永远不要提交敏感信息**
   - API密钥
   - 密码
   - 个人数据

2. **大文件使用Git LFS**
   - 模型文件
   - 大型数据集

3. **每次提交前运行测试**
   ```bash
   python test/test_multi_version.py
   ```

4. **保持提交原子性**
   - 一次提交只做一件事
   - 提交信息清晰明了

5. **定期推送**
   ```bash
   git push origin main
   ```
