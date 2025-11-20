# MEMEFinder — 表情包查找器

基于 **OCR** 和 **情绪分析** 的桌面表情包管理与搜索工具。  
支持批量扫描图片、MD5 去重、OCR 文本提取、情绪分析（可选），并提供 **Windows GUI** 与打包脚本，便于发布为可执行程序。

---

## 📚 完整文档

本项目提供了详细的文档，请查看 **[📚 项目概述](docs/项目概述.md)** 快速了解项目详情。
---

## 📁 主要文件与目录结构

| 文件/目录 | 说明 |
|------------|------|
| `main.py` | 程序入口（启动 GUI） |
| `src/` | 源代码目录（含 `core/`, `gui/`, `utils/`） |
| `scripts/` | 维护、打包和发布脚本 |
| `docs/` | 用户文档、使用指南 |
| `models/` | 模型文件目录（运行时自动下载） |
| `meme_finder.db` | SQLite 数据库文件（自动生成） |
| `requirements.txt` | Python 依赖列表 |
| `LICENSE` | 开源协议 |

---

## ✨ 主要功能

- **图源管理**：添加 / 删除 / 启用 / 禁用文件夹，显示添加时间与最后扫描时间  
- **图片扫描**：递归扫描支持格式（jpg/png/bmp/webp/gif/tiff），自动 MD5 去重与增量扫描  
- **OCR 识别（可选）**：使用 *RapidOCR* 提取图片文字并保存到数据库  
- **情绪分析（可选）**：使用 *SnowNLP* (中文) / *TextBlob* (英文) 对提取文本进行情绪分类  
- **数据存储**：基于 SQLite 数据库，持久化图源与图片信息  
- **GUI 界面**：基于 tkinter，包含三个标签页：
  - 图源管理  
  - 图片处理  
  - 图片搜索  
- **打包支持**：自带 PyInstaller 打包脚本，生成独立 Windows 可执行包  

---

## 🚀 快速开始

### 源码运行（开发者）

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

### 打包发布

项目提供了便捷的打包脚本，位于 `scripts/` 目录：

```bash
python scripts/package_all.py
```

详细说明请参考 [scripts/README.md](scripts/README.md)。

---

## 🧭 基本使用流程

1. 打开「图源管理」 → 点击「添加图源文件夹」，选择包含表情包的目录（可多选）
2. 点击「扫描新图片」进行增量扫描（自动去重）
3. 切换到「图片处理」运行 OCR / 情绪分析任务（可暂停、停止、查看进度）
4. 在「图片搜索」中通过关键词或情绪筛选查看结果，单击可打开图片

---

## 🧩 开发与项目结构

    src/
    ├── core/            # 核心逻辑
    │   ├── database.py  # 数据库管理
    │   ├── scanner.py   # 文件扫描
    │   ├── ocr_engine.py # OCR 引擎封装
    │   ├── emotion_analyzer.py # 情绪分析
    │   └── ocr_processor.py  # OCR + 情绪分析处理流程
    ├── gui/             # 图形界面
    │   ├── main_window.py
    │   ├── source_tab.py
    │   ├── process_tab.py
    │   └── search_tab.py
    └── utils/           # 工具模块（日志与资源监控）

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！
反馈问题时请附上运行日志（位于 `logs/` 目录中）。

---

## 📄 许可证

本项目基于 **MIT License** 开源发布。
详见 [`LICENSE`](LICENSE)。
