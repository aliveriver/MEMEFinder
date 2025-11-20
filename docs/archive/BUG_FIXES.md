# Bug 修复说明

## 修复日期：2025年11月15日

## 问题概述

1. ✅ 模型下载到根目录models文件夹 - **已实现**
2. ✅ GPU自动检测和加速 - **已实现**
3. ✅ 主界面未处理图片数字不更新 - **已修复**

---

## 详细修复内容

### 1. 模型路径配置（已实现）

**文件：** `src/core/ocr_processor.py`

**现有功能：**
- 第46-53行：自动检测并使用项目根目录下的 `models` 文件夹
- 第73-88行：设置环境变量，确保模型下载到指定目录
- 第134-184行：配置RapidOCR使用指定的模型路径
- 第222-249行：检查和验证模型文件位置

**说明：**
```python
# 默认使用项目根目录的models文件夹
project_root = Path(__file__).parent.parent.parent
model_dir = project_root / 'models'
```

模型文件将自动下载到 `d:\MEMEFinder\models\` 目录下，包括：
- `ch_PP-OCRv4_det_infer.onnx` - 文本检测模型
- `ch_PP-OCRv4_rec_infer.onnx` - 文本识别模型  
- `ch_ppocr_mobile_v2_cls_infer.onnx` - 方向分类模型

---

### 2. GPU自动检测（已实现）

**文件：** `src/utils/gpu_detector.py`

**现有功能：**
- `detect_gpu()` 函数：检测系统GPU支持情况
  - 检测 CUDA GPU（NVIDIA显卡）
  - 检测 DirectML GPU（Windows通用GPU）
  - 检测 TensorRT（高性能推理）
  
- `should_use_gpu()` 函数：智能判断是否使用GPU
  - 优先级1：环境变量 `MEMEFINDER_USE_GPU`（1/true/yes启用，0/false/no禁用）
  - 优先级2：自动检测GPU是否可用

**文件：** `src/core/ocr_processor.py` (第59-82行)

**现有功能：**
```python
# 自动检测GPU（如果未指定）
if use_gpu is None:
    has_gpu, gpu_info = detect_gpu()
    use_gpu = should_use_gpu()
    if has_gpu:
        logger.info(f"✓ 检测到GPU: {gpu_info}")
        logger.info(f"  将使用GPU加速模式")
    else:
        logger.info("✗ 未检测到GPU，将使用CPU模式")
```

**使用方法：**
1. 自动模式（默认）：系统自动检测GPU并使用
2. 手动启用：设置环境变量 `set MEMEFINDER_USE_GPU=1`
3. 手动禁用：设置环境变量 `set MEMEFINDER_USE_GPU=0`

---

### 3. 主界面统计数字不更新 **[本次修复]**

#### 问题分析
当图片处理完成后，主界面"图源管理"标签页的统计信息（未处理图片数量）没有实时更新。

#### 根本原因
- `ProcessTab` 处理图片后更新了数据库
- 但没有通知 `SourceTab` 刷新统计信息
- 导致界面显示的是旧数据

#### 修复方案

**修改文件1：** `src/gui/process_tab.py`

1. **添加回调函数参数**（第20行）
```python
def __init__(self, parent, db: ImageDatabase, stats_callback=None):
    self.stats_callback = stats_callback  # 用于更新统计信息的回调函数
```

2. **处理完每张图片后更新统计**（第232-237行）
```python
# 更新数据库后，立即更新统计信息
if self.stats_callback:
    try:
        self.frame.after(0, self.stats_callback)
    except Exception:
        pass
```

3. **所有图片处理完成后更新统计**（第257-262行）
```python
# 最后一次更新统计信息
if self.stats_callback:
    try:
        self.frame.after(0, self.stats_callback)
    except Exception:
        pass
```

**修改文件2：** `src/gui/main_window.py`

**传递统计更新回调**（第44行）
```python
# 创建process_tab时传递source_tab的update_statistics方法作为回调
self.process_tab = ProcessTab(
    self.notebook, 
    self.db, 
    stats_callback=self.source_tab.update_statistics
)
```

#### 修复效果
- ✅ 处理每张图片后，界面实时更新未处理数量
- ✅ 所有图片处理完成后，最终统计数据准确
- ✅ 用户可以实时看到处理进度和剩余数量
- ✅ 不需要手动刷新界面

---

## 测试建议

### 1. 测试模型下载
```bash
# 首次运行会自动下载模型到 models 文件夹
python main.py

# 检查模型文件
dir models\*.onnx
```

### 2. 测试GPU检测
```bash
# 查看日志中的GPU检测信息
# 在OCR初始化时会显示：
# ✓ 检测到GPU: CUDA GPU: NVIDIA GeForce RTX 3060, 12288 MiB
# 或
# ✗ 未检测到GPU，将使用CPU模式
```

### 3. 测试统计更新
1. 添加图源并扫描图片
2. 在"图源管理"标签页查看"未处理"数量（例如：100张）
3. 切换到"图片处理"标签页，点击"▶️ 开始处理"
4. 切换回"图源管理"标签页
5. **预期结果：** 未处理数量实时减少（99, 98, 97...）

---

## 技术细节

### 线程安全处理
使用 `frame.after(0, callback)` 确保UI更新在主线程中执行：
```python
self.frame.after(0, self.stats_callback)
```

### 异常处理
所有回调都包含异常捕获，避免更新失败影响主流程：
```python
try:
    self.frame.after(0, self.stats_callback)
except Exception:
    pass  # 静默失败，不影响图片处理
```

---

## 相关文件

### 核心文件
- `src/core/ocr_processor.py` - OCR处理器（模型路径和GPU配置）
- `src/utils/gpu_detector.py` - GPU检测工具

### GUI文件  
- `src/gui/main_window.py` - 主窗口（传递回调）
- `src/gui/process_tab.py` - 图片处理标签页（调用回调）
- `src/gui/source_tab.py` - 图源管理标签页（统计更新）

### 数据库
- `src/core/database.py` - 数据库操作（update_image_data方法）

---

## 环境变量说明

可选的环境变量配置：

```powershell
# 强制启用GPU
$env:MEMEFINDER_USE_GPU = "1"

# 强制禁用GPU
$env:MEMEFINDER_USE_GPU = "0"

# 自定义模型目录（默认为项目根目录的models文件夹）
# 注：当前代码已硬编码使用项目根目录，此变量暂未使用
```

---

## 已知限制

1. **GPU支持**
   - 需要安装 `onnxruntime-gpu` 才能使用CUDA GPU
   - Windows用户可能需要安装CUDA和cuDNN
   - 如果只安装了 `onnxruntime`，将自动使用CPU模式

2. **模型下载**
   - 首次运行需要从网络下载模型（约50-100MB）
   - 如果网络不佳，可能需要多次尝试
   - 可以手动下载模型文件到 `models` 目录

---

## 版本信息

- 修复版本：v1.1
- 修复日期：2025-11-15
- 修复人员：GitHub Copilot
