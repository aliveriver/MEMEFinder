# 快速开始指南

## 📋 目录

1. [开发环境设置](#开发环境设置)
2. [模型文件准备](#模型文件准备)
3. [运行程序](#运行程序)
4. [打包发布](#打包发布)
5. [常见问题](#常见问题)

---

## 🛠️ 开发环境设置

### 1. 克隆项目

```powershell
git clone <repository_url>
cd MEMEFinder
```

### 2. 创建虚拟环境（推荐）

```powershell
# 使用 Anaconda
conda create -n MEME python=3.10
conda activate MEME

# 或使用 venv
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

### 4. GPU 支持（可选）

如果你有 NVIDIA 显卡并想使用 GPU 加速：

```powershell
# 卸载 CPU 版本
pip uninstall onnxruntime

# 安装 GPU 版本
pip install onnxruntime-gpu

# 确保已安装 CUDA 和 cuDNN
```

---

## 📦 模型文件准备

### 方法一：自动复制（推荐）

```powershell
python copy_models.py
```

这个脚本会：
- ✅ 从 RapidOCR 包复制模型文件
- ✅ 从 SnowNLP 包复制数据文件（如果已安装）
- ✅ 自动创建 models 目录

### 方法二：手动下载

如果自动复制失败，可以手动下载：

1. 访问 [RapidOCR GitHub](https://github.com/RapidAI/RapidOCR/tree/main/python/rapidocr_onnxruntime/models)

2. 下载以下文件到 `models/` 目录：
   - `ch_PP-OCRv4_det_infer.onnx`
   - `ch_PP-OCRv4_rec_infer.onnx`
   - `ch_ppocr_mobile_v2.0_cls_infer.onnx`

### 验证模型文件

```powershell
# 检查 models 目录
dir models\*.onnx

# 应该看到至少3个 .onnx 文件
```

---

## 🚀 运行程序

### 启动主程序

```powershell
python main.py
```

### 使用流程

1. **添加图源**
   - 打开"图源管理"标签
   - 点击"➕ 添加图源文件夹"
   - 选择包含图片的文件夹

2. **扫描图片**
   - 点击"🔍 扫描新图片"
   - 等待扫描完成

3. **处理图片**
   - 切换到"图片处理"标签
   - 点击"▶️ 开始处理"
   - 查看处理日志

4. **搜索表情包**
   - 切换到"图片搜索"标签
   - 输入关键词或选择情绪
   - 浏览搜索结果

---

## 📦 打包发布

### 一键打包

```powershell
# 确保模型文件已准备
python copy_models.py

# 一键打包
python build_package.py
```

### 手动打包

```powershell
# 安装 PyInstaller
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller MEMEFinder.spec --clean
```

### 测试打包结果

```powershell
# 运行打包后的程序
.\dist\MEMEFinder\MEMEFinder.exe
```

### 发布准备

```powershell
# 压缩整个文件夹
# 将 dist/MEMEFinder 压缩为 MEMEFinder_v1.0.zip
# 或使用 7-Zip、WinRAR 等工具
```

---

## ❓ 常见问题

### 1. OCR 初始化失败

**问题**：提示"模型文件缺失"

**解决方案**：
```powershell
# 运行模型复制脚本
python copy_models.py

# 检查 models 目录
dir models\*.onnx
```

---

### 2. GPU 未被使用

**问题**：程序使用 CPU 而不是 GPU

**解决方案**：
```powershell
# 1. 检查是否安装 GPU 版本
pip list | findstr onnxruntime

# 2. 如果是 onnxruntime（CPU版本），安装 GPU 版本
pip uninstall onnxruntime
pip install onnxruntime-gpu

# 3. 检查 CUDA 是否安装
nvidia-smi

# 4. 手动启用 GPU
$env:MEMEFINDER_USE_GPU = "1"
python main.py
```

---

### 3. 内存占用过高

**问题**：处理大量图片时内存占用高

**解决方案**：
- 程序会每处理10张图片自动清理内存
- 可以分批处理图片
- 关闭其他占用内存的程序

---

### 4. 打包后体积过大

**问题**：打包文件超过 500MB

**说明**：
- 正常情况下包含模型的打包体积约 200-300MB
- 如果超过 500MB，可能包含了不必要的文件

**优化方法**：
```powershell
# 清理后重新打包
python build_package.py
```

---

### 5. SnowNLP 未安装

**问题**：情绪分析使用关键词方法

**解决方案**（可选）：
```powershell
# 安装 SnowNLP
pip install snownlp

# 复制数据文件
python copy_models.py
```

---

### 6. 统计数字不更新

**问题**：处理图片后未处理数量不变

**解决方案**：
- 这个问题已在最新版本修复
- 确保使用的是最新代码
- 重启程序试试

---

### 7. 图片识别不准确

**问题**：OCR 识别率低

**优化建议**：
1. 确保图片清晰度足够
2. 文字大小适中
3. 避免过于复杂的背景
4. 使用 GPU 加速可能提高处理速度

---

## 🔧 环境变量配置

### GPU 控制

```powershell
# 强制使用 GPU
$env:MEMEFINDER_USE_GPU = "1"

# 强制使用 CPU
$env:MEMEFINDER_USE_GPU = "0"

# 自动检测（默认）
Remove-Item Env:\MEMEFINDER_USE_GPU
```

---

## 📝 开发提示

### 项目结构

```
MEMEFinder/
├── main.py                    # 主程序入口
├── copy_models.py             # 模型复制工具
├── build_package.py           # 打包脚本
├── MEMEFinder.spec            # 打包配置
├── requirements.txt           # Python 依赖
├── models/                    # 模型文件目录
│   ├── *.onnx                # OCR 模型
│   └── snownlp/              # SnowNLP 数据（可选）
├── src/                       # 源代码
│   ├── core/                 # 核心模块
│   │   ├── ocr_engine.py    # OCR 引擎
│   │   ├── text_filter.py   # 文本过滤
│   │   ├── emotion_analyzer.py # 情绪分析
│   │   ├── ocr_processor.py # OCR 处理器（原版）
│   │   └── ocr_processor_refactored.py # 重构版
│   ├── gui/                  # 界面模块
│   └── utils/                # 工具模块
└── docs/                      # 文档
```

### 代码修改

如果你想修改代码：

1. **使用重构后的模块**（推荐）
   ```python
   from src.core.ocr_processor_refactored import OCRProcessor
   ```

2. **单独使用模块**
   ```python
   from src.core.ocr_engine import OCREngine
   from src.core.text_filter import TextFilter
   from src.core.emotion_analyzer import EmotionAnalyzer
   ```

3. **保持向后兼容**
   ```python
   from src.core.ocr_processor import OCRProcessor
   ```

---

## 📚 更多文档

- [Bug 修复说明](BUG_FIXES.md)
- [重构总结](REFACTOR_SUMMARY.md)
- [优化指南](docs/OPTIMIZATION_GUIDE.md)
- [用户指南](docs/USER_GUIDE.md)

---

## 🆘 获取帮助

如果遇到问题：

1. 查看本文档的[常见问题](#常见问题)
2. 查看 [BUG_FIXES.md](BUG_FIXES.md)
3. 提交 Issue 到 GitHub
4. 查看日志文件：`logs/memefinder_*.log`

---

## ✅ 完整流程示例

```powershell
# 1. 克隆项目
git clone <repository_url>
cd MEMEFinder

# 2. 创建环境
conda create -n MEME python=3.10
conda activate MEME

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制模型
python copy_models.py

# 5. 运行程序
python main.py

# 6. 打包（可选）
python build_package.py

# 7. 测试打包结果
.\dist\MEMEFinder\MEMEFinder.exe
```

---

**祝你使用愉快！** 🎉
