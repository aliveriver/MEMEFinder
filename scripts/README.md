# Scripts 目录说明

此目录包含用于项目维护、打包和发布的辅助脚本。

## 📦 打包和发布脚本

### Python 脚本
- **`build_package.py`** - 构建发布包
- **`build_release.py`** - 完整的发布构建流程
- **`prepare_release.py`** - 准备发布前的检查和清理

### 批处理脚本
- **`打包发布版.bat`** - Windows 一键打包脚本
- **`准备发布.bat`** - 准备发布环境

## 🛠️ 维护脚本

### Python 脚本
- **`clean_project.py`** - 清理项目临时文件和缓存
- **`db_maintenance.py`** - 数据库维护工具
- **`system_check.py`** - 系统环境检查

### 批处理脚本
- **`清理项目.bat`** - Windows 一键清理项目
- **`数据库维护.bat`** - 数据库维护快捷方式
- **`系统检查.bat`** - 系统环境检查快捷方式

## 🚀 运行脚本

- **`运行_CPU模式.bat`** - 强制使用 CPU 模式运行程序
- **`运行_MEMEFinder_CPU模式.bat`** - MEMEFinder CPU 模式启动

## 使用方法

### Windows 用户
直接双击对应的 `.bat` 文件即可运行。

### 跨平台用户
使用 Python 直接运行对应的 `.py` 脚本：
```bash
python scripts/script_name.py
```

## 注意事项

- 打包脚本需要先安装 PyInstaller：`pip install pyinstaller`
- 部分脚本需要在项目根目录下运行
- 建议在虚拟环境中使用这些脚本
