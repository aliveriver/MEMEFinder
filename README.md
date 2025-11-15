
# MEMEFinder — 表情包查找器

基于 **OCR** 和 **情绪分析** 的桌面表情包管理与搜索工具。  
支持批量扫描图片、MD5 去重、OCR 文本提取、情绪分析（可选），并提供 **Windows GUI** 与打包脚本，便于发布为可执行程序。

---

## 📁 主要文件与目录结构

| 文件/目录 | 说明 |
|------------|------|
| `main.py` | 程序入口（启动 GUI） |
| `src/` | 源代码目录（含 `core/`, `gui/`, `utils/`） |
| `scripts/` | 维护、打包和发布脚本 |
| `docs/` | 用户文档、使用指南 |
| `test/` | 测试代码 |
| `installer/` | 安装程序配置 |
| `requirements.txt` | Python 依赖列表 |
| `models/` | 模型文件目录（运行时自动下载） |
| `logs/` | 运行日志 |
| `LICENSE` | 开源协议 |

---

## ✨ 主要功能

- **图源管理**：添加 / 删除 / 启用 / 禁用文件夹，显示添加时间与最后扫描时间  
- **图片扫描**：递归扫描支持格式（jpg/png/bmp/webp/gif/tiff），自动 MD5 去重与增量扫描  
- **OCR 识别（可选）**：使用 *PaddleOCR* 提取图片文字并保存到数据库  
- **情绪分析（可选）**：使用 *PaddleNLP Senta* 对提取文本进行情绪分类  
- **数据存储**：基于 SQLite 数据库，持久化图源与图片信息  
- **GUI 界面**：基于 tkinter，包含三个标签页：
  - 图源管理  
  - 图片处理  
  - 图片搜索  
- **打包支持**：自带 PyInstaller 打包脚本与批处理，生成独立 Windows 可执行包  

---

## 🚀 快速开始

详细的快速入门指南请查看 [docs/QUICK_START.md](docs/QUICK_START.md)

### 源码运行

1. **克隆项目**：
   ```bash
   git clone <repository-url>
   cd MEMEFinder
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **启动程序**：
   ```bash
   python main.py
   ```

   模型文件会在首次使用时自动下载。

### 快捷脚本（Windows）

项目提供了便捷的批处理脚本，位于 `scripts/` 目录：

- **`运行_CPU模式.bat`** - 使用 CPU 模式运行（适合无 GPU 或 GPU 驱动问题）
- **`系统检查.bat`** - 检查系统环境和依赖
- **`清理项目.bat`** - 清理临时文件和缓存

---

## 🧭 基本使用流程

1. 打开「图源管理」 → 点击「添加图源文件夹」，选择包含表情包的目录（可多选）
2. 点击「扫描新图片」进行增量扫描（自动去重）
3. 切换到「图片处理」运行 OCR / 情绪分析任务（可暂停、停止、查看进度）
4. 在「图片搜索」中通过关键词或情绪筛选查看结果，双击可打开图片或所在文件夹

---

## 🧩 开发与项目结构

    src/
    ├── core/            # 核心逻辑
    │   ├── database.py  # 数据库管理
    │   ├── scanner.py   # 文件扫描
    │   └── ocr_processor.py  # OCR + 情绪分析
    ├── gui/             # 图形界面
    │   ├── main_window.py
    │   ├── source_tab.py
    │   ├── process_tab.py
    │   └── search_tab.py
    └── utils/           # 工具模块（日志与资源监控）

---

## 🧱 打包与发布

开发者可以使用 `scripts/` 目录中的脚本进行项目打包：

### Windows 打包

```bash
# 方式 1: 使用批处理脚本
scripts\打包发布版.bat

# 方式 2: 使用 Python 脚本
python scripts/build_release.py
```

### 打包准备

在打包前，建议运行准备脚本：

```bash
python scripts/prepare_release.py
```

打包输出位于 `dist/MEMEFinder/`

详细的打包说明请查看 [scripts/README.md](scripts/README.md)

---

## 🧰 常见问题（FAQ）

| 问题 | 解决方案 |
| ---------- | --------------------------------------------------------- |
| 程序无法启动 | 确认 Python 版本 ≥ 3.8 且依赖已安装，运行 `scripts/系统检查.bat` |
| GPU 相关问题 | 查看 [docs/GPU使用指南.md](docs/GPU使用指南.md) 或使用 CPU 模式 |
| OCR/情绪分析异常 | 模型会自动下载，如有问题请检查网络连接 |
| 打包报错 | 运行 `scripts/清理项目.bat` 后重试 |

更多问题请查看 [docs/](docs/) 目录下的相关文档。

---

## 📚 文档导航

### 用户文档
- **[快速开始](docs/QUICK_START.md)** - 5分钟上手指南
- **[用户指南](docs/USER_GUIDE.md)** - 完整使用教程
- **[GPU 使用指南](docs/GPU使用指南.md)** - GPU 加速配置
- **[GPU 快速指南](docs/GPU快速指南.md)** - GPU 快速入门
- **[GPU 闪退修复](docs/GPU闪退修复指南.md)** - GPU 问题解决

### 开发文档
- **[优化指南](docs/OPTIMIZATION_GUIDE.md)** - 性能优化建议
- **[脚本说明](scripts/README.md)** - 维护和打包脚本
- **[历史文档](docs/archive/)** - 开发历史记录

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！
反馈问题时请附上运行日志（位于 `logs/` 目录中）。

---

## 📄 许可证

本项目基于 **MIT License** 开源发布。
详见 [`LICENSE`](LICENSE)。

---


