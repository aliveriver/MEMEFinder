# PyInstaller Hooks 说明

本目录包含 MEMEFinder 项目的 PyInstaller 自定义 hooks，用于在打包过程中正确处理第三方库的依赖、数据文件和二进制文件。

---

## 什么是 PyInstaller Hook？

PyInstaller Hook 是一种特殊的 Python 脚本，用于告诉 PyInstaller 如何正确打包特定的第三方库。当某些库的依赖关系比较复杂，或者包含数据文件、动态链接库等资源时，PyInstaller 可能无法自动识别，这时就需要自定义 hook 来指导打包过程。

---

## Hook 文件列表

### 1. `hook-onnxruntime.py`

**作用**：处理 ONNX Runtime 的打包配置

**主要功能**：
- ✅ 收集 ONNX Runtime 的数据文件和必要的 DLL
- ❌ **排除 CUDA 相关的 DLL**（如 `cublas`, `cudnn`, `cudart` 等）
- 🎯 让打包后的程序使用系统安装的 CUDA 库，而不是打包 CUDA DLL

**为什么要排除 CUDA DLL？**
- CUDA 库文件非常大（数百 MB），会显著增加打包体积
- 使用系统 CUDA 可以确保与用户的 GPU 驱动兼容
- 支持 GPU 加速的同时保持较小的发布包体积

**关键配置**：
```python
# 排除的 CUDA DLL 模式
cuda_dll_patterns = [
    'cublas', 'cublaslt', 'cudnn', 'cudart', 'cufft',
    'curand', 'cusolver', 'cusparse', 'nvrtc', 'nvcuda',
    'nvjitlink'
]
```

---

### 2. `hook-rapidocr_onnxruntime.py`

**作用**：处理 RapidOCR 库的打包配置

**主要功能**：
- ✅ 收集 RapidOCR 的所有数据文件
- ✅ 收集 RapidOCR 的所有子模块
- ✅ 打包 RapidOCR 自带的 `.onnx` 模型文件

**打包内容**：
- RapidOCR 库内置的 OCR 模型（位于 `rapidocr_onnxruntime/models/`）
- 相关的配置文件和数据文件

**注意事项**：
> ⚠️ 这个 hook 只会打包 RapidOCR **库自带的模型**，不会打包项目根目录 `models/` 文件夹中的自定义模型。

---

### 3. `hook-snownlp.py`

**作用**：处理 SnowNLP 中文情感分析库的打包配置

**主要功能**：
- ✅ 收集 SnowNLP 的 Python 代码
- ❌ **排除 SnowNLP 的数据文件**（分词模型、情感分析模型等）
- 🎯 减小打包体积，数据文件由用户在运行时按需安装

**当前配置**：
```python
datas = []  # 空列表 = 不包含数据文件
hiddenimports = ['snownlp.sentiment']
```

**影响**：
- ✅ 减小打包体积（SnowNLP 数据文件约 10+ MB）
- ⚠️ 打包后的程序无法直接使用情感分析功能
- 💡 需要用户手动安装 SnowNLP 或将数据文件放到指定位置

**如果需要打包 SnowNLP 数据**，可以修改为：
```python
from PyInstaller.utils.hooks import collect_all
datas, binaries, hiddenimports = collect_all('snownlp')
```

---

### 4. `hook-tkinter.py`

**作用**：修复 Tkinter GUI 库的打包问题

**主要功能**：
- ✅ 收集 Tcl/Tk 运行时库（`tcl86t.dll`, `tk86t.dll`）
- ✅ 收集 Tcl/Tk 的数据文件（脚本、配置等）
- 🔧 解决 Tcl/Tk 版本冲突问题

**为什么需要这个 hook？**
- Tkinter 依赖于 Tcl/Tk 库，但 PyInstaller 可能无法正确识别版本
- Conda 环境中的 Tcl/Tk 路径比较特殊，需要手动指定
- 确保打包后的 GUI 界面能正常显示

**收集的文件**：
- `tcl86t.dll` / `tk86t.dll` - 核心动态链接库
- `tcl8.6/` - Tcl 脚本库
- `tk8.6/` - Tk 组件库

---

## Hook 的执行顺序

PyInstaller 在打包时会按以下顺序处理：

1. **自动分析**：PyInstaller 自动分析代码依赖
2. **内置 hooks**：执行 PyInstaller 自带的 hooks
3. **自定义 hooks**：执行本目录中的自定义 hooks（通过 `--hookspath` 参数指定）
4. **Spec 文件配置**：应用 `.spec` 文件中的配置（优先级最高）

---

## 如何使用这些 Hooks

在打包脚本 `scripts/package_all.py` 中，通过以下方式启用这些 hooks：

```python
a = Analysis(
    ['main.py'],
    hookspath=['hooks'],  # 指定 hooks 目录
    # ... 其他配置
)
```

---

## 调试 Hooks

如果打包过程中遇到问题，可以查看 hooks 的输出信息：

```bash
python -m PyInstaller --clean --noconfirm MEMEFinder.spec
```

每个 hook 都会输出调试信息，例如：
```
[HOOK-onnxruntime] 添加了 15 个DLL，排除了 8 个CUDA DLL
[HOOK-rapidocr] 找到 3 个模型文件
[HOOK-tkinter] 收集了 2 个二进制文件
```

---

## 常见问题

### Q1: 为什么打包后程序无法使用 GPU 加速？

**A**: 检查系统是否安装了兼容的 NVIDIA GPU 驱动和 CUDA 运行时。由于 `hook-onnxruntime.py` 排除了 CUDA DLL，程序依赖系统的 CUDA 安装。

### Q2: 为什么打包后 SnowNLP 情感分析不工作？

**A**: 当前配置下 SnowNLP 的数据文件不会被打包。可以：
- 修改 `hook-snownlp.py` 以包含数据文件
- 或在程序启动时提示用户下载数据文件

### Q3: 如何添加新的 hook？

**A**: 在本目录创建 `hook-<package_name>.py` 文件，参考现有 hooks 的格式编写。

---

## 相关文档

- [PyInstaller Hooks 官方文档](https://pyinstaller.org/en/stable/hooks.html)
- [打包脚本说明](../scripts/README.md)
- [项目概述](../docs/项目概述.md)

---

*最后更新: 2025-11-25*
