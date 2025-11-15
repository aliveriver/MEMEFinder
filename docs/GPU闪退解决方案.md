# GPU 闪退问题解决方案

## 问题描述

在使用打包后的 MEMEFinder 程序时，部分 GPU 用户可能遇到程序启动时卡住或闪退的问题。

从日志来看，程序在 "尝试初始化 RapidOCR (GPU 模式)..." 这一步卡住，没有后续输出。

## 原因分析

这是打包程序在某些 GPU 环境下的已知问题，主要原因包括：

1. **CUDA DLL 文件问题**
   - 打包后的程序可能无法正确加载 CUDA 运行库
   - onnxruntime-gpu 依赖的某些 DLL 文件缺失或版本不匹配

2. **GPU 驱动兼容性**
   - GPU 驱动版本与 CUDA 版本不匹配
   - 驱动存在问题或损坏

3. **初始化超时**
   - onnxruntime-gpu 在某些环境下初始化 CUDA 时会卡住

## 解决方案

### v1.0.1 版本改进（已实施）

我们在代码中添加了以下保护措施：

1. **30秒超时机制**
   - GPU 模式初始化超过 30 秒自动终止
   - 自动切换到 CPU 模式

2. **自动降级**
   - GPU 初始化失败时，程序自动切换到 CPU 模式
   - 保证程序正常运行

3. **详细错误提示**
   - 清晰的错误信息和原因分析
   - 明确的解决建议

### 手动禁用 GPU（临时方案）

如果自动降级机制也失败，可以手动禁用 GPU：

#### 方法 1：使用环境变量

在程序启动前设置环境变量：

```powershell
# Windows PowerShell
$env:MEMEFINDER_FORCE_CPU = "1"
.\MEMEFinder.exe

# 或者在 CMD
set MEMEFINDER_FORCE_CPU=1
MEMEFinder.exe
```

#### 方法 2：创建启动脚本

创建一个 `启动_CPU模式.bat` 文件：

```batch
@echo off
set MEMEFINDER_FORCE_CPU=1
start "" "MEMEFinder.exe"
```

双击这个脚本启动程序即可。

#### 方法 3：修改配置文件（待实现）

在程序目录创建 `config.ini` 文件：

```ini
[OCR]
force_cpu = true
```

### CPU 模式性能说明

- **速度**：CPU 模式比 GPU 模式慢 2-3 倍
- **准确度**：完全相同
- **稳定性**：更好，兼容性强
- **适用场景**：
  - 小批量处理（几百张图片）
  - 对速度要求不高的场景
  - GPU 环境不稳定的情况

### 开发版本用户（源码运行）

如果你是从源码运行程序，建议：

1. **使用 CPU 版本 onnxruntime**
   ```bash
   pip uninstall onnxruntime-gpu
   pip install onnxruntime
   ```

2. **或者修复 GPU 环境**
   ```bash
   # 重新安装 onnxruntime-gpu
   pip uninstall onnxruntime onnxruntime-gpu
   pip install onnxruntime-gpu
   
   # 检查 CUDA 版本
   nvidia-smi
   ```

## 未来改进计划

1. **智能检测**
   - 启动时先测试 GPU 是否正常工作
   - 根据测试结果自动选择最佳模式

2. **配置界面**
   - GUI 中添加 GPU/CPU 切换选项
   - 允许用户手动选择运行模式

3. **分发策略**
   - 提供 CPU 专用版本（更小、更稳定）
   - 提供 GPU 专用版本（更快、需要 CUDA）

## 技术细节

### 修改内容

1. **ocr_processor.py**
   - 添加 `_init_rapidocr_with_timeout()` 函数
   - 使用线程 + 超时机制防止卡死
   - 增强错误处理和自动降级逻辑

2. **超时处理流程**
   ```
   尝试 GPU 模式（30秒超时）
   ├── 成功 → 使用 GPU 模式
   ├── 超时 → 切换到 CPU 模式
   └── 错误 → 分析错误类型 → 切换到 CPU 模式
   ```

### 为什么不直接使用 CPU 版本？

保留 GPU 支持的原因：

1. 对于 GPU 环境正常的用户，速度提升显著
2. 处理大批量图片时，GPU 优势明显
3. 自动降级机制保证了稳定性

## 联系支持

如果以上方案都无法解决问题，请：

1. 收集日志文件（位于程序目录的 `logs` 文件夹）
2. 记录你的系统信息：
   - Windows 版本
   - GPU 型号
   - NVIDIA 驱动版本
3. 提交 Issue 或联系开发者

---

**更新日期**: 2025-11-15  
**适用版本**: v1.0.1+
