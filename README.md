
# MEMEFinder — 表情包查找器

基于 **OCR** 和 **情绪分析** 的桌面表情包管理与搜索工具。  
支持批量扫描图片、MD5 去重、OCR 文本提取、情绪分析（可选），并提供 **Windows GUI** 与打包脚本，便于发布为可执行程序。

---

## 📁 主要文件与目录结构

| 文件/目录 | 说明 |
|------------|------|
| `main.py` | 程序入口（启动 GUI） |
| `src/` | 源代码目录（含 `core/`, `gui/`, `utils/`） |
| `download_models.py` | 模型下载脚本 |
| `build_exe.py` / `一键打包_无清理.bat` | 打包为可执行程序 |
| `requirements.txt` | Python 依赖列表 |
| `docs/` | 使用说明、打包与结构文档 |
| `imgs/` | 示例图片 |
| `models/` | 模型文件目录（运行或下载后填充） |
| `logs/` | 运行日志 |
| Windows 辅助脚本 | `安装依赖.bat`、`启动程序.bat`、`创建安装程序.bat` 等 |

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

### 源码运行

1. 安装依赖（在 PowerShell 中执行）：
   ```bash
   pip install -r requirements.txt
    ````

2. （可选）下载模型：

   ```bash
   python download_models.py
   ```

   或运行发布包内的 **下载模型.bat**

3. 启动程序：

   ```bash
   python main.py
   ```

   或双击 **启动程序.bat**

---

### 可执行包运行

1. 解压发布包 `dist/MEMEFinder/`
2. **首次运行前** 建议执行 `下载模型.bat` 下载模型文件
3. 双击 `MEMEFinder.exe` 启动程序

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

* 使用内置脚本或批处理打包：

  ```bash
    python build_exe.py

    或运行 **一键打包_无清理.bat**
* 发布前可运行 **强制清理.bat** 清除旧构建

* 打包输出位于 `dist/MEMEFinder/`

* 可使用 **Inno Setup** 生成安装程序（相关脚本在 `installer/` 目录中）

---

## 🧰 常见问题（FAQ）

| 问题         | 解决方案                                                      |
| ---------- | --------------------------------------------------------- |
| 程序无法启动     | 确认 Python 版本 ≥ 3.8 且依赖已安装                                 |
| OCR/情绪分析异常 | 确认模型已下载至 `models/`（可运行 `download_models.py` 或 `下载模型.bat`） |
| 打包报错       | 运行清理脚本并确认 PyInstaller 与 Python 版本兼容                       |

---

## 📚 更多文档

* 使用与教程：[`docs/QUICKSTART.md`](docs/QUICKSTART.md)、[`docs/TUTORIAL.md`](docs/TUTORIAL.md)
* 打包说明：[`docs/PACKAGING_SUMMARY.md`](docs/PACKAGING_SUMMARY.md)、[`docs/RELEASE_GUIDE.md`](docs/RELEASE_GUIDE.md)
* 项目结构与概览：[`docs/STRUCTURE.md`](docs/STRUCTURE.md)、[`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md)

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！
反馈问题时请附上运行日志（位于 `logs/` 目录中）。

---

## 📄 许可证

本项目基于 **MIT License** 开源发布。
详见 [`LICENSE`](LICENSE)。

---


