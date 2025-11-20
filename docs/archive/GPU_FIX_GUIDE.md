# GPU模式闪退问题解决方案

## 问题描述

在某些系统上，MEMEFinder检测到GPU后会立即闪退，而CPU模式可以正常运行。

## 根本原因

1. **ONNX Runtime GPU版本不兼容**
   - 安装了 `onnxruntime` 而不是 `onnxruntime-gpu`
   - CUDA版本与onnxruntime-gpu版本不匹配

2. **CUDA库问题**
   - CUDA Toolkit版本不正确
   - cuDNN库缺失或版本不对

3. **GPU驱动问题**
   - NVIDIA驱动版本过旧
   - GPU驱动损坏

## 解决方案

### 方案1：使用改进后的版本（推荐）

最新代码已添加了自动回退机制：
- 如果GPU初始化失败，程序会自动切换到CPU模式
- 不再会因为GPU问题导致程序崩溃

**操作步骤：**
1. 使用更新后的代码重新打包程序
2. 运行时，如果GPU模式失败，会自动使用CPU模式

### 方案2：诊断GPU问题

运行GPU诊断工具：

```bash
python test_gpu_diagnosis.py
```

这会告诉你具体哪个环节出了问题。

### 方案3：强制使用CPU模式

如果不需要GPU加速，可以强制使用CPU模式：

**开发环境：**
在 `main.py` 或环境变量中设置：
```python
os.environ['MEMEFINDER_FORCE_CPU'] = '1'
```

**打包后的程序：**
创建一个批处理文件 `run_cpu.bat`:
```batch
@echo off
set MEMEFINDER_FORCE_CPU=1
MEMEFinder.exe
```

### 方案4：修复GPU环境（高级）

#### 4.1 检查CUDA版本

```bash
nvidia-smi
```

查看 "CUDA Version" 字段。

#### 4.2 安装正确的onnxruntime-gpu

根据CUDA版本选择：

**CUDA 11.x:**
```bash
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu
```

**CUDA 12.x:**
```bash
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu
```

#### 4.3 验证安装

```bash
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

应该看到 `['CUDAExecutionProvider', 'CPUExecutionProvider']`

## 代码改进说明

### 新增的保护机制

1. **GPU可用性预检查**
   - 在初始化RapidOCR之前，先检查CUDA是否真的可用
   - 避免盲目使用GPU模式

2. **初始化异常捕获**
   - 捕获GPU初始化过程中的所有异常
   - 提供详细的错误信息

3. **自动回退到CPU**
   - 如果GPU模式初始化失败，自动切换到CPU模式
   - 用户无需手动干预

4. **详细日志输出**
   - 记录GPU检测和初始化的每一步
   - 便于诊断问题

### 修改的文件

1. `src/core/ocr_processor.py` - 主OCR处理器
2. `src/core/ocr_engine.py` - OCR引擎
3. `src/utils/gpu_detector.py` - GPU检测工具
4. `test_gpu_diagnosis.py` - GPU诊断工具（新增）

## 测试建议

### GPU用户

1. 先运行诊断工具：`python test_gpu_diagnosis.py`
2. 如果GPU测试通过，可以使用GPU模式
3. 如果GPU测试失败，程序会自动使用CPU模式

### CPU用户

1. 不需要任何特殊设置
2. 程序会自动检测并使用CPU模式

## 性能对比

| 模式 | 速度 | 稳定性 | 适用场景 |
|------|------|--------|----------|
| GPU  | 快   | 中等   | 大量图片处理 |
| CPU  | 慢   | 高     | 少量图片、兼容性优先 |

## 常见问题

### Q: 为什么检测到GPU但还是用CPU？

A: 可能原因：
- GPU初始化测试失败（自动回退）
- 设置了强制CPU模式的环境变量

### Q: 如何确认当前使用的是CPU还是GPU？

A: 查看日志输出：
```
✓ RapidOCR 初始化成功
  配置模式: GPU/CPU
  实际设备: GPU (CUDA)/CPU
```

### Q: GPU模式比CPU慢？

A: 少量图片时可能出现这种情况，因为：
- GPU初始化有开销
- 小批量数据传输的开销大于计算开销
- 建议批量处理时使用GPU

## 技术细节

### GPU初始化流程

```
1. 检测ONNX Runtime可用提供者
   ├─ 有CUDAExecutionProvider → 继续
   └─ 没有 → 使用CPU模式

2. 尝试创建GPU会话
   ├─ 成功 → 使用GPU模式
   └─ 失败 → 记录错误，回退到CPU

3. 验证实际设备
   └─ 从session.get_providers()确认
```

### 异常处理策略

```python
try:
    # 尝试GPU模式
    ocr = RapidOCR(use_cuda=True)
except Exception as e:
    logger.error(f"GPU失败: {e}")
    if original_use_gpu:
        # 回退到CPU
        ocr = RapidOCR(use_cuda=False)
        logger.info("已切换到CPU模式")
```

## 更新日志

### 2025-11-15
- ✅ 添加GPU初始化失败自动回退机制
- ✅ 添加详细的GPU诊断日志
- ✅ 创建GPU诊断工具
- ✅ 改进错误提示信息
- ✅ 防止GPU模式下的程序崩溃

## 反馈

如果问题仍然存在，请提供：
1. 运行 `test_gpu_diagnosis.py` 的完整输出
2. GPU型号和驱动版本（nvidia-smi输出）
3. CUDA版本
4. Python版本和依赖包版本（pip list）
