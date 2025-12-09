# MEMEFinder — 表情包查找器

基于 **OCR** 和 **情绪分析** 的桌面表情包管理与搜索工具。  
支持批量扫描图片、MD5 去重、OCR 文本提取、情绪分析（可选），并提供 **Windows GUI** 与打包脚本，便于发布为可执行程序。

---

## 完整文档

本项目提供了详细的文档，请查看 **[📚 项目概述](docs/项目概述.md)** 快速了解项目详情。
---

## 主要文件与目录结构

| 文件/目录 | 说明 |
|------------|------|
| `main.py` | 程序入口（启动 GUI） |
| `src/` | 源代码目录（含 `core/`, `gui/`, `utils/`） |
| `scripts/` | 维护、打包和发布脚本 |
| `hooks/` | PyInstaller 自定义 hooks（打包配置） |
| `assets/` | 资源文件（应用图标等） |
| `docs/` | 用户文档、使用指南 |
| `models/` | 模型文件目录（运行时自动下载） |
| `meme_finder.db` | SQLite 数据库文件（自动生成） |
| `requirements.txt` | Python 依赖列表 |
| `LICENSE` | 开源协议 |

---

## 主要功能

### 核心功能
- **图源管理**：添加 / 删除 / 启用 / 禁用文件夹，显示添加时间与最后扫描时间  
- **图片扫描**：递归扫描支持格式（jpg/png/bmp/webp/gif/tiff），自动 MD5 去重与增量扫描  
- **OCR 识别（可选）**：使用 *RapidOCR* 提取图片文字并保存到数据库  
- **情绪分析（可选）**：使用 *SnowNLP* (中文) / *TextBlob* (英文) 对提取文本进行情绪分类  
- **深度学习特征提取**：使用 MobileNetV3 提取图片特征，支持以图搜图和智能排序

### 搜索与管理
- **关键词搜索**：通过 OCR 识别的文本搜索表情包
- **🖼️ 以图搜图**：支持本地图片、粘贴板图片和已有图片的相似度搜索
  - 混合相似度算法（深度学习特征 + PHash）
  - 可自定义权重和阈值
  - 支持最大比较数量限制
- **📊 智能排序**：多种排序方式
  - 深度学习相似度排序
  - PHash相似度排序
  - 混合相似度排序（可调权重）
  - RGB颜色排序（按主色调分组）
- **多维度筛选**：支持情感、图源、收藏状态、标签筛选
- **分页显示**：可调整每页显示数量（10/20/50/100）
- **详情查看**：点击图片查看详细信息（OCR文本、情感、标签、文件信息、颜色信息）

### 高级功能
- **🏷️ 自定义标签系统**：
  - 创建带颜色的标签
  - 为图片添加多个标签
  - 按标签筛选搜索
  - 集中管理标签
  
- **❤️ 收藏功能**：
  - 一键收藏/取消收藏
  - 只看收藏筛选
  - 收藏状态持久化

- **✅ 多选操作**：
  - 单击复选框选中
  - Ctrl+点击多选
  - Shift+点击范围选择
  - 单击空白取消全部选择

- **🖱️ 右键批量操作**：
  - 批量收藏/取消收藏（智能显示）
  - 批量编辑标签（添加/移除/替换）
  - 批量编辑情感
  - 批量转移到图源
  - 批量删除（带二次确认）

### 界面特性
- **GUI 界面**：基于 tkinter，包含三个标签页：
  - 📁 图源管理  
  - ⚙️ 图片处理  
  - 🔍 图片搜索  
- **虚拟化渲染**：支持大量图片流畅显示
- **自适应布局**：根据窗口大小自动调整列数
- **详情面板**：实时编辑OCR文本、情感标签、图片标签

### 数据与存储
- **数据存储**：基于 SQLite 数据库，持久化图源与图片信息  
- **打包支持**：自带 PyInstaller 打包脚本，生成独立 Windows 可执行包  

---

## 快速开始

### 开箱即用（普通用户）

1. **下载压缩包**:

   [下载](https://github.com/aliveriver/MEMEFinder/releases)

2. **解压运行**

   解压后直接运行exe文件即可

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

详细说明请参考 [脚本说明](scripts/README.md)。

---

## 基本使用流程

### 首次使用

1. **添加图源** 
   - 打开「图源管理」标签页
   - 点击「添加图源文件夹」
   - 选择包含表情包的目录（可多选）

2. **扫描图片**
   - 点击「扫描新图片」进行增量扫描
   - 系统会自动 MD5 去重

3. **处理图片**（可选）
   - 切换到「图片处理」标签页
   - 运行 OCR 识别提取文字
   - 运行情绪分析（可暂停、停止、查看进度）

4. **搜索使用**
   - 切换到「图片搜索」标签页
   - 通过关键词、情感、图源、收藏状态筛选
   - 单击图片查看详情
   - 双击图片打开文件

### 高级功能使用

#### 标签管理
1. 在搜索页面顶部点击「🔖 管理标签」
2. 创建自定义标签（设置名称和颜色）
3. 选择图片后在详情面板或右键菜单编辑标签
4. 使用标签筛选查找相关图片

#### 批量操作
1. 使用复选框、Ctrl+点击、Shift+点击选择多张图片
2. 右键点击选中的图片
3. 选择批量操作：
   - ❤️ 收藏/💔 取消收藏
   - 🏷️ 编辑标签（添加/移除/替换）
   - 😊 编辑情感
   - 📁 转移到图源
   - 🗑️ 删除

#### 收藏与筛选
1. 点击图片左上角的爱心图标收藏
2. 在搜索条件区勾选「❤ 只看收藏」
3. 只显示已收藏的图片

#### 以图搜图
1. 点击搜索工具栏的「📷 以图搜图」按钮
2. 选择搜索方式：
   - **选择本地图片**：从文件系统选择参考图片
   - **粘贴图片**：使用剪贴板中的图片（截图后直接粘贴）
   - **使用当前选中图片**：使用已选中的图片作为参考
3. 系统会根据相似度排序显示结果
4. 可在「⚙️ 以图搜图设置」中调整：
   - 相似度算法权重（深度学习/PHash）
   - 最小相似度阈值
   - 最大比较数量

#### 智能排序
1. 在搜索工具栏选择排序方式：
   - **深度学习排序**：基于深度学习特征的智能相似度
   - **PHash排序**：基于感知哈希的相似度
   - **混合排序**：结合两种算法（可调权重）
   - **颜色排序**：按RGB主色调分组排序
2. 选择参考图片后应用排序
3. 排序信息会显示在界面顶部

---

## 开发与项目结构

    src/
    ├── core/                # 核心逻辑
    │   ├── scanner.py       # 文件扫描
    │   ├── image_hash.py    # 图片哈希和颜色特征计算（PHash/RGB/DL特征）
    │   ├── dl_model_manager.py      # 深度学习模型管理器
    │   ├── dl_feature_extractor.py  # 深度学习特征提取器
    │   ├── database/        # 数据库模块（模块化设计）
    │   │   ├── database.py          # 主数据库类
    │   │   ├── connection_pool.py   # 连接池管理
    │   │   ├── schema.py            # 数据库表结构
    │   │   ├── source_manager.py    # 图源管理
    │   │   ├── image_manager.py     # 图片操作
    │   │   ├── search_manager.py    # 搜索查询
    │   │   ├── image_sorter.py      # 图片排序（相似度/颜色）
    │   │   ├── state_manager.py     # 应用状态
    │   │   └── tag_manager.py       # 标签管理
    │   └── ocr/             # OCR 模块（模块化设计）
    │       ├── ocr_engine.py        # OCR 引擎封装
    │       ├── processor.py         # OCR 处理器主入口
    │       ├── sentiment_analyzer.py # 情感分析
    │       └── text_processor.py    # 文本提取与过滤
    ├── gui/                 # 图形界面
    │   ├── main_window.py   # 主窗口
    │   ├── source_tab.py    # 图源管理页
    │   ├── loading_window.py # 加载窗口
    │   ├── tag_manager_dialog.py # 标签管理对话框
    │   ├── process_tab/     # 图片处理页（模块化）
    │   │   ├── main.py              # 主标签页类
    │   │   ├── gpu.py               # GPU检测
    │   │   ├── image_processor.py   # 图片处理器
    │   │   └── memory_utils.py      # 内存管理
    │   └── search_tab/      # 图片搜索页（模块化）
    │       ├── search_tab.py        # 主协调器
    │       ├── search_toolbar.py    # 搜索工具栏
    │       ├── search_filters.py    # 搜索过滤器
    │       ├── similarity_search.py # 以图搜图
    │       ├── similarity_settings_dialog.py # 相似度设置对话框
    │       ├── canvas_renderer.py   # 虚拟化渲染
    │       ├── detail_panel.py      # 详情面板
    │       ├── detail_widgets.py    # 详情组件
    │       ├── event_handlers.py    # 事件处理
    │       ├── context_menu.py      # 右键菜单
    │       ├── batch_tag_editor.py  # 批量标签编辑
    │       ├── batch_emotion_editor.py # 批量情感编辑
    │       ├── batch_move_dialog.py # 批量移动对话框
    │       ├── tag_selector_dialog.py # 标签选择对话框
    │       ├── checkbox_dropdown.py # 复选框下拉菜单
    │       ├── pagination_control.py # 分页控制
    │       └── icon_manager.py      # 图标管理
    └── utils/               # 工具模块
        ├── logger.py        # 日志记录
        ├── resource_path.py # 资源路径管理
        ├── model_manager.py # 模型管理
        ├── resource_monitor.py # 资源监控
        ├── gpu_detector.py  # GPU 检测
        ├── gpu_installer.py # GPU 安装配置
        ├── cuda_finder.py   # CUDA 路径查找
        └── cuda_validator.py # CUDA 验证

---

## 贡献与反馈

欢迎提交 Issue 或 Pull Request！
反馈问题时请附上运行日志（位于 `logs/` 目录中）。

---

## 许可证

本项目基于 **MIT License** 开源发布。
详见 [`LICENSE`](LICENSE)。

---

*希望能帮到你，喜欢MEME的人*

*如果觉得该项目有用，请点一点star。这是我们维护、开发的动力。*


