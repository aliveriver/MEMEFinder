# Scripts 目录说明

此目录包含用于项目打包和维护的辅助脚本。

## 📦 打包脚本

### `package_all.py` ⭐
GPU 版本打包工具（包含 cuDNN 和 CUDA 运行时库）

**功能：**
- 自动打包 MEMEFinder GPU 版本
- 内置 GPU 加速库（cuDNN、cuBLAS等）
- 支持自动降级到 CPU 模式

**使用方法：**
```bash
# 运行打包脚本
python scripts/package_all.py
```

**输出位置：**
- `releases/MEMEFinder_gpu/` - 打包后的程序

**特性：**
- ✅ GPU 加速（自动检测）
- ✅ CPU 自动降级（无 GPU 时）
- ✅ 包含所有必需的运行时库（cuDNN、CUDA）
- ✅ 包含 AI 模型文件

---

## 📝 注意事项

1. **环境依赖**
   - 需要 `MEME` conda 环境
   - 需要安装 PyInstaller：`pip install pyinstaller`
   - 建议安装 cuDNN（用于 GPU 加速）

2. **打包前检查**
   - 确保 `models/` 目录包含 AI 模型文件
   - 确保在项目根目录运行脚本

3. **打包后测试**
   - 检查 `releases/MEMEFinder_gpu/` 目录
   - 运行 `MEMEFinder.exe` 测试程序

---

## 📂 项目结构

```
scripts/
├── package_all.py          # GPU 版本打包脚本（核心）
└── README.md              # 本文件
```
