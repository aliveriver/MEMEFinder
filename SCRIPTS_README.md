# 📝 脚本文件说明

## 🎯 用户常用脚本（按使用顺序）

### 1️⃣ **强制清理.bat**
清理旧的打包文件，解决文件锁问题
- 结束相关进程
- 重启资源管理器（解除文件锁）
- 删除dist和build目录
- **使用场景：** 第一次打包或完全重建时

### 2️⃣ **一键打包_无清理.bat** ⭐推荐
打包程序为可执行文件（不清理旧文件）
- 使用优化参数打包
- 修复unittest缺失问题
- 创建ZIP压缩包
- **使用场景：** 日常打包，避免文件锁问题

### 3️⃣ **创建安装程序.bat**
创建Windows安装程序
- 使用Inno Setup编译
- 生成专业的安装程序
- 支持自动下载AI模型
- **使用场景：** 创建发布版本

---

## 🐍 Python脚本（高级用户）

### **build_exe.py**
标准PyInstaller打包脚本
- 基础打包功能
- 包含unittest修复
- 基本模块排除

### **build_optimized.py**
优化版打包脚本
- 二进制过滤（移除不必要的DLL）
- 40+模块排除
- UPX压缩
- 文件大小报告

### **download_models.py**
AI模型下载工具
- 独立运行：`python download_models.py`
- 下载PaddleOCR和情感分析模型

---

## 📦 快速开始

### 第一次打包
```batch
.\强制清理.bat
.\一键打包_无清理.bat
```

### 日常重新打包
```batch
.\一键打包_无清理.bat
```

### 创建发布版
```batch
.\一键打包_无清理.bat
.\创建安装程序.bat
```

---

## 📂 输出位置

- **打包结果：** `dist/MEMEFinder/`
- **ZIP压缩包：** `dist/MEMEFinder.zip`
- **安装程序：** `installer/MEMEFinder-Setup-v1.0.0.exe`

---

## ❓ 遇到问题？

查看详细文档：[BUILD_GUIDE.md](BUILD_GUIDE.md)
