# 🎭 MEMEFinder - 表情包智能管理工具

基于 OCR 和情绪分析的表情包搜索与管理系统

---

## ✨ 主要特性

- 🔍 **智能OCR识别**: 基于PaddleOCR的高精度文字识别
- 😊 **情绪分析**: 自动分类表情包情绪（正向/负向/中性）
- 🎯 **高效搜索**: 支持关键词和情绪筛选
- 📊 **批量处理**: 快速扫描和处理大量图片
- 💾 **数据持久化**: SQLite数据库存储，支持断点续传
- 🎨 **友好界面**: 简洁直观的图形界面

---

## 🚀 快速开始

### 方式一: 一键安装（推荐）

```bash
# 双击运行
完整安装.bat
```

### 方式二: 手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载OCR模型
python download_ocr_models.py

# 3. (可选) 下载情绪分析模型
python download_senta_models.py

# 4. 启动程序
python main.py
```

---

## 📖 使用说明

### 1. 添加图源

- 点击"图源管理"标签
- 点击"添加文件夹"，选择包含表情包的文件夹
- 系统会自动扫描文件夹中的图片

### 2. 处理图片

- 切换到"处理"标签
- 点击"开始处理"
- 程序会自动进行OCR识别和情绪分析

### 3. 搜索表情包

- 切换到"搜索"标签
- 输入关键词或选择情绪类型
- 点击搜索结果可以打开图片

---

## ⚙️ 性能优化

### 内存优化
- ✅ 连接池管理数据库连接
- ✅ 批量操作减少数据库开销
- ✅ 自动垃圾回收释放内存
- ✅ 图片资源及时释放

### 存储优化
- ✅ 数据库VACUUM优化
- ✅ 旧数据清理功能
- ✅ 模型缓存管理

### 性能提升
- 批量插入比单条插入快 **34倍**
- 批量更新比单条更新快 **40倍**
- 内存占用降低 **60-68%**

详见: [性能优化指南](docs/OPTIMIZATION_GUIDE.md)

---

## 🛠️ 维护工具

### 数据库维护

```bash
# 方式一: 使用批处理脚本
数据库维护.bat

# 方式二: 使用命令行
python db_maintenance.py backup      # 备份数据库
python db_maintenance.py vacuum      # 优化数据库
python db_maintenance.py stats       # 查看统计
python db_maintenance.py full        # 完整维护
```

### 缓存清理

```bash
# 清理Senta模型缓存
清理Senta模型缓存.bat

# 或使用PowerShell
清理Senta缓存.ps1
```

---

## 📊 系统要求

### 最低配置
- **操作系统**: Windows 10+
- **Python**: 3.8+
- **内存**: 4GB
- **磁盘空间**: 2GB (含模型)

### 推荐配置
- **操作系统**: Windows 10/11
- **Python**: 3.9+
- **内存**: 8GB+
- **磁盘空间**: 5GB+
- **GPU**: 支持CUDA的显卡（可选，加速OCR）

---

## 📁 项目结构

```
MEMEFinder/
├── main.py                   # 主程序入口
├── meme_finder_gui.py       # GUI界面
├── db_maintenance.py        # 数据库维护工具
├── requirements.txt         # Python依赖
├── src/
│   ├── core/
│   │   ├── database.py      # 数据库管理（优化版）
│   │   ├── ocr_processor.py # OCR处理器（优化版）
│   │   └── scanner.py       # 文件扫描器
│   ├── gui/
│   │   ├── main_window.py   # 主窗口
│   │   ├── source_tab.py    # 图源管理
│   │   ├── process_tab.py   # 处理标签
│   │   └── search_tab.py    # 搜索标签
│   └── utils/
│       ├── logger.py         # 日志系统
│       └── resource_monitor.py # 资源监控
├── docs/
│   ├── OPTIMIZATION_GUIDE.md # 性能优化指南
│   ├── QUICKSTART.md         # 快速开始
│   └── TROUBLESHOOTING.md    # 故障排查
└── models/                   # 模型文件目录
```

---

## 🔧 配置说明

### OCR 配置
```python
# 在 src/core/ocr_processor.py 中调整
OCRProcessor(
    lang='ch',           # 语言: ch=中文, en=英文
    use_gpu=False,       # 是否使用GPU
    det_side=1536,       # 检测分辨率 (降低可减少内存)
    use_senta=True       # 是否使用Senta情绪分析
)
```

### 数据库配置
```python
# 在 src/core/database.py 中调整
ImageDatabase(
    db_path='meme_finder.db',
    pool_size=5          # 连接池大小
)
```

### 批处理大小
```python
# 根据可用内存调整
BATCH_SIZE = 50   # 4GB内存
BATCH_SIZE = 100  # 8GB内存
BATCH_SIZE = 200  # 16GB+内存
```

---

## 📝 日志系统

### 日志位置
- 日志文件保存在 `logs/` 目录
- 文件名格式: `meme_finder_YYYYMMDD.log`

### 日志级别
- **DEBUG**: 详细调试信息
- **INFO**: 正常运行信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 查看日志
```python
# 实时查看日志
tail -f logs/meme_finder_20251110.log  # Linux/Mac

# Windows使用
Get-Content logs\meme_finder_20251110.log -Wait
```

---

## 🐛 故障排查

### 常见问题

#### 1. 内存占用过高
**解决方案**:
- 降低 `det_side` 参数（如1024）
- 减少批处理大小
- 定期执行数据库VACUUM
- 查看 [性能优化指南](docs/OPTIMIZATION_GUIDE.md)

#### 2. OCR识别失败
**解决方案**:
- 运行 `python download_ocr_models.py` 重新下载模型
- 检查图片格式是否支持（支持jpg, png, bmp等）
- 查看日志文件了解详细错误

#### 3. Senta模型问题
**解决方案**:
- 查看 [Senta问题解决方案](SENTA_问题解决方案.md)
- 运行清理脚本清除缓存
- 如不需要深度学习情绪分析，设置 `use_senta=False`

详见: [故障排查文档](docs/TROUBLESHOOTING.md)

---

## 📚 相关文档

- [快速开始指南](docs/QUICKSTART.md)
- [性能优化指南](docs/OPTIMIZATION_GUIDE.md)
- [故障排查](docs/TROUBLESHOOTING.md)
- [项目总结](docs/PROJECT_SUMMARY.md)
- [Senta模型指南](docs/SENTA_MODEL_GUIDE.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR识别引擎
- [PaddleNLP](https://github.com/PaddlePaddle/PaddleNLP) - 情绪分析模型
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架

---

**最后更新**: 2025-11-10
