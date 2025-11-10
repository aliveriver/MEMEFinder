# 🎭 MEMEFinder - 表情包智能管理工具# 🎭 MEMEFinder - 表情包智能管理工具



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)基于 OCR 和情绪分析的表情包搜索与管理系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[![PaddlePaddle](https://img.shields.io/badge/PaddlePaddle-3.2.0-blue.svg)](https://www.paddlepaddle.org.cn/)---



基于 OCR 和 AI 情绪分析的表情包搜索与管理系统## ✨ 主要特性



---- 🔍 **智能OCR识别**: 基于PaddleOCR的高精度文字识别

- 😊 **情绪分析**: 自动分类表情包情绪（正向/负向/中性）

## ✨ 主要特性- 🎯 **高效搜索**: 支持关键词和情绪筛选

- 📊 **批量处理**: 快速扫描和处理大量图片

- 🔍 **智能 OCR 识别**: 基于 PaddleOCR 的高精度文字识别- 💾 **数据持久化**: SQLite数据库存储，支持断点续传

- 😊 **AI 情绪分析**: 自动分类表情包情绪（正向/负向/中性）- 🎨 **友好界面**: 简洁直观的图形界面

- 🎯 **高效搜索**: 支持关键词和情绪筛选

- 📊 **批量处理**: 快速扫描和处理大量图片---

- 💾 **数据持久化**: SQLite 数据库存储，支持断点续传

- 🎨 **友好界面**: 简洁直观的图形界面## 🚀 快速开始



---### 方式一: 一键安装（推荐）



## 📦 两种使用方式```bash

# 双击运行

### 方式 A: Windows 开箱即用版（推荐给普通用户）完整安装.bat

```

**无需安装 Python，下载即用！**

### 方式二: 手动安装

#### 1️⃣ 下载发布版本

```bash

前往 [Releases](https://github.com/aliveriver/MEMEFinder/releases) 页面下载最新版本：# 1. 安装依赖

pip install -r requirements.txt

- `MEMEFinder-v1.0.0-Windows-x64.zip`（约 200-300 MB）

# 2. 下载OCR模型

#### 2️⃣ 解压并运行python download_ocr_models.py



```# 3. (可选) 下载情绪分析模型

1. 解压 ZIP 文件到任意位置python download_senta_models.py

2. 双击运行 "下载模型.bat"（首次必须！下载 AI 模型）

3. 双击运行 "MEMEFinder.exe" 或 "启动程序.bat"# 4. 启动程序

```python main.py

```

#### 3️⃣ 开始使用

---

- **添加图源** → **处理图片** → **搜索表情包**

## 📖 使用说明

就这么简单！🎉

### 1. 添加图源

---

- 点击"图源管理"标签

### 方式 B: Python 源码运行（适合开发者）- 点击"添加文件夹"，选择包含表情包的文件夹

- 系统会自动扫描文件夹中的图片

#### 系统要求

### 2. 处理图片

- **Python**: 3.8 或更高版本

- **操作系统**: Windows 10+, Linux, macOS- 切换到"处理"标签

- **内存**: 最低 4GB，推荐 8GB+- 点击"开始处理"

- 程序会自动进行OCR识别和情绪分析

#### 快速安装

### 3. 搜索表情包

##### Windows 用户（一键安装）

- 切换到"搜索"标签

```bash- 输入关键词或选择情绪类型

# 双击运行- 点击搜索结果可以打开图片

一键安装.bat

```---



该脚本会自动：## ⚙️ 性能优化

1. 检查 Python 环境

2. 安装所有依赖### 内存优化

3. 下载 AI 模型- ✅ 连接池管理数据库连接

- ✅ 批量操作减少数据库开销

##### 手动安装（所有平台）- ✅ 自动垃圾回收释放内存

- ✅ 图片资源及时释放

```bash

# 1. 克隆仓库### 存储优化

git clone https://github.com/aliveriver/MEMEFinder.git- ✅ 数据库VACUUM优化

cd MEMEFinder- ✅ 旧数据清理功能

- ✅ 模型缓存管理

# 2. 安装依赖

pip install -r requirements.txt### 性能提升

- 批量插入比单条插入快 **34倍**

# 3. 下载模型- 批量更新比单条更新快 **40倍**

python download_models.py- 内存占用降低 **60-68%**



# 4. 启动程序详见: [性能优化指南](docs/OPTIMIZATION_GUIDE.md)

python main.py

```---



---## 🛠️ 维护工具



## 📖 使用指南### 数据库维护



### 1. 添加图源```bash

# 方式一: 使用批处理脚本

- 点击 **"图源管理"** 标签数据库维护.bat

- 点击 **"添加文件夹"**

- 选择包含表情包的文件夹# 方式二: 使用命令行

- 系统会自动扫描 `.jpg`, `.png`, `.bmp`, `.gif` 等格式python db_maintenance.py backup      # 备份数据库

python db_maintenance.py vacuum      # 优化数据库

### 2. 处理图片python db_maintenance.py stats       # 查看统计

python db_maintenance.py full        # 完整维护

- 切换到 **"处理"** 标签```

- 点击 **"开始处理"**

- 程序会自动进行：### 缓存清理

  - OCR 文字识别

  - 水印过滤```bash

  - AI 情绪分析# 清理Senta模型缓存

清理Senta模型缓存.bat

### 3. 搜索表情包

# 或使用PowerShell

- 切换到 **"搜索"** 标签清理Senta缓存.ps1

- 输入关键词（如："加油"、"开心"）```

- 可选：选择情绪类型（正向/负向/中性）

- 点击搜索结果可以打开图片---



---## 📊 系统要求



## 🛠️ 开发者打包指南### 最低配置

- **操作系统**: Windows 10+

### 打包为可执行文件- **Python**: 3.8+

- **内存**: 4GB

```bash- **磁盘空间**: 2GB (含模型)

# 方式 1: 使用批处理脚本（Windows）

打包程序.bat### 推荐配置

- **操作系统**: Windows 10/11

# 方式 2: 使用 Python 脚本- **Python**: 3.9+

python build_exe.py- **内存**: 8GB+

```- **磁盘空间**: 5GB+

- **GPU**: 支持CUDA的显卡（可选，加速OCR）

打包完成后：

- 输出目录: `dist/MEMEFinder/`---

- 发布包: `dist/MEMEFinder-v1.0.0-Windows-x64.zip`

## 📁 项目结构

### 发布到 GitHub Releases

```

1. 测试 `dist/MEMEFinder/MEMEFinder.exe`MEMEFinder/

2. 将 ZIP 文件上传到 GitHub Releases├── main.py                   # 主程序入口

3. 编写 Release Notes├── meme_finder_gui.py       # GUI界面

├── db_maintenance.py        # 数据库维护工具

---├── requirements.txt         # Python依赖

├── src/

## ⚙️ 配置说明│   ├── core/

│   │   ├── database.py      # 数据库管理（优化版）

### OCR 配置│   │   ├── ocr_processor.py # OCR处理器（优化版）

│   │   └── scanner.py       # 文件扫描器

在 `src/core/ocr_processor.py` 中调整：│   ├── gui/

│   │   ├── main_window.py   # 主窗口

```python│   │   ├── source_tab.py    # 图源管理

OCRProcessor(│   │   ├── process_tab.py   # 处理标签

    lang='ch',           # 语言: ch=中文, en=英文│   │   └── search_tab.py    # 搜索标签

    use_gpu=False,       # 是否使用 GPU（需要 CUDA）│   └── utils/

    det_side=1536,       # 检测分辨率（降低可减少内存）│       ├── logger.py         # 日志系统

    use_senta=True       # 是否使用 AI 情绪分析│       └── resource_monitor.py # 资源监控

)├── docs/

```│   ├── OPTIMIZATION_GUIDE.md # 性能优化指南

│   ├── QUICKSTART.md         # 快速开始

### 性能优化│   └── TROUBLESHOOTING.md    # 故障排查

└── models/                   # 模型文件目录

根据您的内存调整批处理大小：```



```python---

BATCH_SIZE = 50   # 4GB 内存

BATCH_SIZE = 100  # 8GB 内存## 🔧 配置说明

BATCH_SIZE = 200  # 16GB+ 内存

```### OCR 配置

```python

---# 在 src/core/ocr_processor.py 中调整

OCRProcessor(

## 📊 性能表现    lang='ch',           # 语言: ch=中文, en=英文

    use_gpu=False,       # 是否使用GPU

### 优化成果    det_side=1536,       # 检测分辨率 (降低可减少内存)

    use_senta=True       # 是否使用Senta情绪分析

- ✅ 批量插入比单条插入快 **34 倍**)

- ✅ 批量更新比单条更新快 **40 倍**```

- ✅ 内存占用降低 **60-68%**

### 数据库配置

### 处理速度（参考）```python

# 在 src/core/database.py 中调整

| 图片数量 | CPU 模式 | GPU 模式 |ImageDatabase(

|---------|---------|---------|    db_path='meme_finder.db',

| 100 张  | ~5 分钟  | ~2 分钟  |    pool_size=5          # 连接池大小

| 500 张  | ~25 分钟 | ~10 分钟 |)

| 1000 张 | ~50 分钟 | ~20 分钟 |```



*实际速度取决于硬件配置和图片复杂度*### 批处理大小

```python

---# 根据可用内存调整

BATCH_SIZE = 50   # 4GB内存

## 🐛 常见问题BATCH_SIZE = 100  # 8GB内存

BATCH_SIZE = 200  # 16GB+内存

### 1. 程序无法启动```



**源码版**:---

- 检查 Python 版本: `python --version`

- 确保已安装依赖: `pip install -r requirements.txt`## 📝 日志系统

- 查看日志: `logs/meme_finder_YYYYMMDD.log`

### 日志位置

**可执行版**:- 日志文件保存在 `logs/` 目录

- 确保已运行 `下载模型.bat`- 文件名格式: `meme_finder_YYYYMMDD.log`

- 以管理员身份运行

- 检查杀毒软件是否拦截### 日志级别

- **DEBUG**: 详细调试信息

### 2. OCR 识别失败- **INFO**: 正常运行信息

- **WARNING**: 警告信息

- 确保已下载模型（运行 `download_models.py` 或 `下载模型.bat`）- **ERROR**: 错误信息

- 检查图片格式是否支持

- 查看日志文件了解详细错误### 查看日志

```python

### 3. 内存占用过高# 实时查看日志

tail -f logs/meme_finder_20251110.log  # Linux/Mac

- 降低 `det_side` 参数（如 1024 或 960）

- 减少批处理大小# Windows使用

- 关闭其他占用内存的程序Get-Content logs\meme_finder_20251110.log -Wait

- 分批处理图片```



### 4. 情绪分析不准确---



- AI 模型可能需要更多训练数据## 🐛 故障排查

- 可以在 `src/core/ocr_processor.py` 中调整关键词列表

- 欢迎提供反馈改进算法### 常见问题



---#### 1. 内存占用过高

**解决方案**:

## 📁 项目结构- 降低 `det_side` 参数（如1024）

- 减少批处理大小

```- 定期执行数据库VACUUM

MEMEFinder/- 查看 [性能优化指南](docs/OPTIMIZATION_GUIDE.md)

├── main.py                  # 主程序入口

├── download_models.py       # 模型下载脚本#### 2. OCR识别失败

├── build_exe.py            # 打包脚本（PyInstaller）**解决方案**:

├── requirements.txt        # Python 依赖- 运行 `python download_ocr_models.py` 重新下载模型

├── 一键安装.bat             # Windows 一键安装- 检查图片格式是否支持（支持jpg, png, bmp等）

├── 启动程序.bat             # Windows 启动脚本- 查看日志文件了解详细错误

├── 打包程序.bat             # Windows 打包脚本

├── README.md               # 本文档#### 3. Senta模型问题

├── src/**解决方案**:

│   ├── core/- 查看 [Senta问题解决方案](SENTA_问题解决方案.md)

│   │   ├── database.py      # 数据库管理（优化版）- 运行清理脚本清除缓存

│   │   ├── ocr_processor.py # OCR 处理器（优化版）- 如不需要深度学习情绪分析，设置 `use_senta=False`

│   │   └── scanner.py       # 文件扫描器

│   ├── gui/详见: [故障排查文档](docs/TROUBLESHOOTING.md)

│   │   ├── main_window.py   # 主窗口

│   │   ├── source_tab.py    # 图源管理---

│   │   ├── process_tab.py   # 处理标签

│   │   └── search_tab.py    # 搜索标签## 📚 相关文档

│   └── utils/

│       ├── logger.py        # 日志系统- [快速开始指南](docs/QUICKSTART.md)

│       └── resource_monitor.py # 资源监控- [性能优化指南](docs/OPTIMIZATION_GUIDE.md)

├── docs/                   # 详细文档- [故障排查](docs/TROUBLESHOOTING.md)

├── logs/                   # 日志文件（自动创建）- [项目总结](docs/PROJECT_SUMMARY.md)

└── models/                 # AI 模型缓存（自动创建）- [Senta模型指南](docs/SENTA_MODEL_GUIDE.md)

```

---

---

## 🤝 贡献

## 📚 详细文档

欢迎提交 Issue 和 Pull Request！

- [快速开始指南](docs/QUICKSTART.md)

- [性能优化报告](docs/OPTIMIZATION_REPORT.md)---

- [项目总结](docs/PROJECT_SUMMARY.md)

- [开发教程](docs/TUTORIAL.md)## 📄 许可证



---MIT License



## 🔧 技术栈---



- **OCR 引擎**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)## 🙏 致谢

- **情绪分析**: [PaddleNLP](https://github.com/PaddlePaddle/PaddleNLP) Senta

- **深度学习**: [PaddlePaddle](https://www.paddlepaddle.org.cn/)- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR识别引擎

- **GUI 框架**: Tkinter- [PaddleNLP](https://github.com/PaddlePaddle/PaddleNLP) - 情绪分析模型

- **数据库**: SQLite3- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架

- **打包工具**: PyInstaller

---

---

**最后更新**: 2025-11-10

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [PaddlePaddle](https://www.paddlepaddle.org.cn/) - 优秀的深度学习框架
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 强大的 OCR 工具
- [PaddleNLP](https://github.com/PaddlePaddle/PaddleNLP) - 自然语言处理工具包

---

## 📞 联系方式

- **GitHub**: [@aliveriver](https://github.com/aliveriver)
- **Issues**: [提交问题](https://github.com/aliveriver/MEMEFinder/issues)

---

## 📈 更新日志

### v1.0.0 (2025-11-10)

- ✨ 首次发布
- ✅ OCR 文字识别
- ✅ AI 情绪分析
- ✅ 关键词搜索
- ✅ 批量处理
- ✅ 数据持久化
- ✅ 性能优化
- ✅ Windows 可执行文件打包

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给个 Star！**

**Made with ❤️ by aliveriver**

**最后更新**: 2025-11-10

</div>
