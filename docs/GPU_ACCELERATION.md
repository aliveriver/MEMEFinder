# GPU 加速使用说明

## 概述

MEMEFinder 支持使用 GPU 加速 OCR 识别，可以显著提高处理速度。如果您的系统有 NVIDIA GPU 且安装了 CUDA 和 cuDNN，可以通过以下方式启用 GPU 加速。

## 前提条件

1. **NVIDIA GPU**：支持 CUDA 的 NVIDIA 显卡
2. **CUDA 工具包**：已安装 CUDA（推荐版本 11.2+）
3. **cuDNN**：已安装 cuDNN（与 CUDA 版本匹配）
4. **GPU 版本的 PaddlePaddle**：如果使用打包版本，需要确保打包时包含了 GPU 版本的 PaddlePaddle

## 启用 GPU 加速

### 方法 1：环境变量（推荐）

在启动程序前设置环境变量：

**Windows (CMD):**
```cmd
set MEMEFINDER_USE_GPU=1
python main.py
```

**Windows (PowerShell):**
```powershell
$env:MEMEFINDER_USE_GPU="1"
python main.py
```

**Linux/macOS:**
```bash
export MEMEFINDER_USE_GPU=1
python main.py
```

### 方法 2：修改代码

在 `src/gui/process_tab.py` 中，修改 `OCRProcessor` 的初始化：

```python
# 修改前
self.ocr_processor = OCRProcessor()

# 修改后
self.ocr_processor = OCRProcessor(use_gpu=True)
```

## 验证 GPU 是否启用

启动程序后，查看日志输出：

- **GPU 启用成功**：日志会显示 `✓ 使用 GPU 进行 OCR 识别（加速模式）`
- **GPU 不可用**：日志会显示 `使用 CPU 进行 OCR 识别` 或相关的警告信息

## 故障排除

### 问题 1：GPU 未启用，但系统有 GPU

**可能原因：**
1. 环境变量未设置或设置错误
2. PaddlePaddle 未编译 CUDA 支持
3. CUDA/cuDNN 未正确安装

**解决方法：**
1. 检查环境变量是否正确设置：`echo $MEMEFINDER_USE_GPU`（Linux/macOS）或 `echo %MEMEFINDER_USE_GPU%`（Windows）
2. 检查 PaddlePaddle 是否支持 CUDA：
   ```python
   import paddle
   print(paddle.is_compiled_with_cuda())  # 应该返回 True
   ```
3. 检查 CUDA 是否正确安装：`nvidia-smi`

### 问题 2：GPU 启用后程序崩溃

**可能原因：**
1. CUDA 版本不匹配
2. cuDNN 版本不匹配
3. GPU 驱动过旧

**解决方法：**
1. 确保 CUDA 和 cuDNN 版本与 PaddlePaddle 要求匹配
2. 更新 GPU 驱动到最新版本
3. 如果问题持续，回退到 CPU 模式（不设置环境变量或设置为 0）

### 问题 3：打包版本无法使用 GPU

**可能原因：**
打包版本默认使用 CPU 版本的 PaddlePaddle

**解决方法：**
1. 使用 GPU 版本的 PaddlePaddle 重新打包
2. 确保打包时包含了 CUDA 和 cuDNN 库
3. 或者在打包后，手动安装 GPU 版本的 PaddlePaddle

## 性能对比

- **CPU 模式**：处理速度较慢，适合小批量处理
- **GPU 模式**：处理速度可提升 3-10 倍（取决于 GPU 型号和图片大小）

## 注意事项

1. **内存占用**：GPU 模式会占用 GPU 显存，确保有足够的显存（推荐 2GB+）
2. **批量处理**：GPU 模式在处理大批量图片时优势更明显
3. **兼容性**：如果 GPU 不可用，程序会自动回退到 CPU 模式，不会报错
4. **打包环境**：在打包环境中，默认使用 CPU 模式以避免 CUDA 库加载错误。如果需要使用 GPU，需要确保打包版本包含 GPU 支持

## 环境变量说明

| 环境变量 | 值 | 说明 |
|---------|-----|------|
| `MEMEFINDER_USE_GPU` | `1`, `true`, `yes`, `on` | 启用 GPU |
| `MEMEFINDER_USE_GPU` | `0`, `false`, `no`, `off` | 禁用 GPU（默认） |
| `MEMEFINDER_USE_GPU` | 未设置 | 使用 CPU（默认） |

## 技术细节

程序会按以下顺序检测和设置设备：

1. **检查用户设置**：读取 `MEMEFINDER_USE_GPU` 环境变量
2. **检查 CUDA 编译支持**：检查 PaddlePaddle 是否编译了 CUDA 支持
3. **运行时 GPU 检测**：尝试设置 GPU 并创建测试 tensor 验证
4. **自动回退**：如果 GPU 不可用，自动回退到 CPU 模式

在打包环境中，程序会：
1. 默认设置 CPU 模式（避免 CUDA 库加载错误）
2. 如果用户启用 GPU，清除 CPU 强制设置
3. 检测 GPU 可用性并设置设备

