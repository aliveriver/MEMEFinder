# 📦 MEMEFinder 发布指南

本文档说明如何为 Windows 平台创建发布版本（Release）。

---

## 🎯 发布目标

创建一个开箱即用的 Windows 可执行程序包，用户无需安装 Python 环境即可使用。

---

## 📋 准备工作

### 1. 环境检查

```powershell
# 检查 Python 版本
python --version  # 应该是 3.8+

# 检查依赖
pip list | findstr -i "paddlepaddle paddleocr paddlenlp pyinstaller"
```

### 2. 安装打包工具

```powershell
pip install pyinstaller
```

---

## 🔨 打包步骤

### 方法 1: 使用批处理脚本（推荐）

```powershell
# 双击运行或在命令行执行
打包程序.bat
```

这将自动完成以下步骤：
1. 检查/安装 PyInstaller
2. 清理旧的构建文件
3. 创建 PyInstaller 配置
4. 打包程序和依赖
5. 复制文档和脚本
6. 创建 ZIP 发布包

### 方法 2: 手动打包

```powershell
# 1. 清理旧文件
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item *.spec -ErrorAction SilentlyContinue

# 2. 运行打包脚本
python build_exe.py

# 3. 测试可执行文件
cd dist\MEMEFinder
.\MEMEFinder.exe
```

---

## 📂 输出文件

打包成功后，`dist` 目录下将生成：

```
dist/
├── MEMEFinder/                          # 完整程序目录
│   ├── MEMEFinder.exe                   # 主程序
│   ├── 下载模型.bat                      # 首次运行脚本
│   ├── 启动程序.bat                      # 启动快捷方式
│   ├── download_models.py               # 模型下载脚本
│   ├── README.md                        # 用户说明
│   ├── requirements.txt                 # 依赖列表（参考）
│   ├── src/                             # 源代码
│   ├── docs/                            # 文档
│   ├── logs/                            # 日志目录（空）
│   ├── models/                          # 模型目录（空）
│   └── _internal/                       # PyInstaller 依赖
└── MEMEFinder-v1.0.0-Windows-x64.zip   # 发布包
```

---

## 🧪 测试发布版本

### 1. 基础功能测试

```powershell
cd dist\MEMEFinder

# 1. 测试程序启动
.\MEMEFinder.exe

# 2. 测试模型下载
.\下载模型.bat

# 3. 测试完整流程
# - 添加图源
# - 处理图片
# - 搜索表情包
```

### 2. 检查清单

- [ ] 程序能正常启动
- [ ] 界面显示正常
- [ ] 模型下载成功
- [ ] OCR 识别正常
- [ ] 情绪分析正常
- [ ] 搜索功能正常
- [ ] 日志文件生成
- [ ] 数据库创建成功

### 3. 性能测试

- [ ] 内存占用合理（< 2GB）
- [ ] CPU 占用正常
- [ ] 处理速度可接受
- [ ] 无内存泄漏

---

## 🚀 发布到 GitHub Releases

### 1. 创建 Git 标签

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 2. 创建 Release

1. 访问 GitHub 仓库页面
2. 点击 "Releases" → "Create a new release"
3. 选择标签: `v1.0.0`
4. 填写标题: `MEMEFinder v1.0.0 - 首个正式版本`

### 3. 编写 Release Notes

```markdown
## 🎉 MEMEFinder v1.0.0

### ✨ 新特性

- 🔍 智能 OCR 文字识别（基于 PaddleOCR）
- 😊 AI 情绪分析（基于 PaddleNLP Senta）
- 🎯 关键词和情绪筛选
- 📊 批量处理
- 💾 数据持久化
- 🎨 友好的图形界面

### 📦 下载

**Windows 用户（推荐）**:
- [MEMEFinder-v1.0.0-Windows-x64.zip](下载链接)

**开发者**:
- 查看源代码和文档

### 🚀 快速开始

1. 下载并解压 ZIP 文件
2. 双击运行 `下载模型.bat`（首次必须）
3. 双击运行 `MEMEFinder.exe`

### 📊 系统要求

- Windows 10 64位 或更高
- 4GB RAM（推荐 8GB+）
- 3GB 磁盘空间

### 🐛 已知问题

- 首次下载模型需要较长时间
- 大量图片处理时可能占用较多内存

### 📝 完整更新日志

详见 [CHANGELOG.md](链接)
```

### 4. 上传发布文件

1. 拖拽 `MEMEFinder-v1.0.0-Windows-x64.zip` 到 Release 页面
2. 等待上传完成
3. 点击 "Publish release"

---

## 📝 版本号规范

使用语义化版本（Semantic Versioning）:

- **主版本号** (Major): 重大变更，不兼容旧版本
- **次版本号** (Minor): 新功能，向后兼容
- **修订号** (Patch): Bug 修复，向后兼容

示例:
- `v1.0.0` - 首个正式版本
- `v1.1.0` - 新增功能
- `v1.1.1` - 修复 Bug
- `v2.0.0` - 重大更新

---

## 🔄 更新发布

### 修改版本号

1. 更新 `build_exe.py` 中的版本号
2. 更新 `README.md` 中的版本号
3. 更新 `main.py` 中的版本号（如果有）

### 重新打包

```powershell
# 1. 清理旧文件
Remove-Item -Recurse -Force build, dist

# 2. 重新打包
.\打包程序.bat

# 3. 测试
cd dist\MEMEFinder
.\MEMEFinder.exe

# 4. 创建发布包（已自动完成）
```

---

## 📋 发布检查清单

在发布前，确保完成以下检查：

### 代码质量
- [ ] 代码已提交到 Git
- [ ] 没有调试代码（print, console.log 等）
- [ ] 所有测试通过
- [ ] 代码格式化

### 文档
- [ ] README.md 更新
- [ ] 版本号更新
- [ ] CHANGELOG.md 更新
- [ ] 文档中的链接有效

### 打包
- [ ] 清理了临时文件
- [ ] 所有依赖包含在内
- [ ] 文件大小合理
- [ ] ZIP 压缩正常

### 测试
- [ ] 在干净环境测试
- [ ] 首次运行测试
- [ ] 功能测试
- [ ] 性能测试

### 发布
- [ ] Git 标签创建
- [ ] Release Notes 编写
- [ ] 文件上传完成
- [ ] 下载链接测试

---

## 🐛 常见问题

### 1. 打包失败

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```powershell
# 安装缺失的模块
pip install xxx

# 或重新安装所有依赖
pip install -r requirements.txt
```

### 2. 可执行文件过大

**原因**: PyInstaller 打包了所有依赖

**优化**:
- 使用 `--exclude-module` 排除不需要的模块
- 使用 UPX 压缩（已启用）

### 3. 运行时错误

**调试方法**:
1. 查看日志文件
2. 在命令行运行查看错误信息
3. 使用 `console=True` 打包以查看控制台输出

### 4. 模型下载失败

**解决**:
- 检查网络连接
- 使用国内镜像源
- 手动下载模型文件

---

## 📞 获取帮助

遇到问题？

- 查看 [常见问题文档](docs/FAQ.md)
- 提交 [Issue](https://github.com/aliveriver/MEMEFinder/issues)
- 联系维护者

---

## 📚 相关资源

- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [GitHub Releases 指南](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

**最后更新**: 2025-11-10
