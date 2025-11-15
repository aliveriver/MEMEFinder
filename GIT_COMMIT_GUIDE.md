# Git 提交指南

## 📋 本次整理的提交建议

本次项目整理涉及大量文件的移动、删除和配置更新。建议分批次提交，以便于回溯和理解。

### 提交方案 1: 一次性提交（推荐）

如果你想快速提交所有更改：

```bash
# 1. 查看所有更改
git status

# 2. 添加所有更改
git add .

# 3. 提交
git commit -m "refactor: 重组项目结构，优化文档和脚本组织

- 创建 scripts/ 目录，整理所有维护和发布脚本
- 创建 docs/archive/ 目录，归档历史开发文档
- 移动用户文档到 docs/ 目录
- 删除过时的测试脚本和临时文件
- 更新和优化 .gitignore
- 更新主 README.md，改进文档导航
- 添加各目录的 README 说明文档

详见 PROJECT_ORGANIZATION.md"

# 4. 推送到远程
git push
```

### 提交方案 2: 分批提交（更清晰）

如果你希望提交历史更清晰：

#### 第一步：目录创建和配置更新
```bash
git add scripts/ docs/archive/
git add .gitignore
git commit -m "feat: 创建 scripts/ 和 docs/archive/ 目录，优化 .gitignore"
```

#### 第二步：文件移动
```bash
git add scripts/*.py scripts/*.bat
git add docs/*.md
git add docs/archive/*.md
git commit -m "refactor: 重组脚本和文档到对应目录"
```

#### 第三步：删除过时文件
```bash
git add -u
git commit -m "chore: 删除过时的测试脚本和临时文件"
```

#### 第四步：文档更新
```bash
git add README.md PROJECT_ORGANIZATION.md GIT_COMMIT_GUIDE.md
git add scripts/README.md docs/archive/README.md
git commit -m "docs: 更新主 README 和添加各目录说明文档"
```

#### 第五步：推送
```bash
git push
```

## 📝 提交消息规范

本项目建议使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 类型说明
- **feat**: 新功能
- **fix**: 修复 Bug
- **docs**: 文档更新
- **style**: 代码格式调整（不影响功能）
- **refactor**: 重构（不是新功能也不是修复）
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建、工具、依赖等
- **ci**: CI/CD 配置

### 示例
```
feat: 添加图片批量导出功能
fix: 修复 OCR 在特殊字符时崩溃的问题
docs: 更新 GPU 使用指南
refactor: 重组项目目录结构
chore: 更新依赖版本
```

## 🔍 提交前检查清单

在提交前，请确认：

- [ ] 所有文件已正确移动到目标目录
- [ ] 没有遗留的临时文件或敏感信息
- [ ] .gitignore 正确配置
- [ ] README 文档准确无误
- [ ] 脚本路径引用已更新（如果需要）
- [ ] 运行 `git status` 确认所有更改符合预期

## 🚫 注意事项

### 确保不提交以下内容：
- [ ] 数据库文件（*.db）
- [ ] 日志文件（*.log）
- [ ] 临时文件（*.tmp, *.temp）
- [ ] 构建输出（build/, dist/）
- [ ] 个人配置（.env）
- [ ] 大型模型文件（models/）
- [ ] 测试图片（imgs/）

这些已在 `.gitignore` 中配置，但请再次确认。

## 📊 检查更改

### 查看将要提交的文件
```bash
git status
```

### 查看具体更改内容
```bash
git diff
```

### 查看已暂存的更改
```bash
git diff --staged
```

### 撤销某个文件的更改（如果需要）
```bash
git checkout -- <file>
```

## 🔄 推送后的工作

提交并推送后：

1. **通知团队成员**
   - 告知新的目录结构
   - 分享 PROJECT_ORGANIZATION.md
   - 更新相关文档链接

2. **更新 CI/CD**（如果有）
   - 检查构建脚本路径
   - 更新部署配置

3. **验证**
   - 克隆新版本到临时目录
   - 确认所有功能正常
   - 检查文档链接是否有效

## 💡 常用 Git 命令参考

```bash
# 查看状态
git status

# 查看历史
git log --oneline

# 查看某个文件的历史
git log --follow <file>

# 撤销上一次提交（保留更改）
git reset --soft HEAD~1

# 修改上一次提交消息
git commit --amend

# 查看远程仓库
git remote -v

# 拉取最新代码
git pull

# 推送到远程
git push
```

## 🆘 遇到问题？

### 提交时出现冲突
```bash
# 查看冲突文件
git status

# 解决冲突后
git add <resolved-file>
git commit
```

### 推送被拒绝
```bash
# 先拉取远程更改
git pull --rebase

# 解决冲突后推送
git push
```

### 需要回滚
```bash
# 查看历史找到目标提交
git log --oneline

# 回滚到某个提交（保留更改）
git reset --soft <commit-hash>

# 回滚到某个提交（丢弃更改）
git reset --hard <commit-hash>
```

---

**准备好了吗？开始提交你的整理成果吧！** 🚀
