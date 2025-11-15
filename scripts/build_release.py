#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMEFinder Release 打包脚本
完整处理PaddleX依赖的版本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def clean_build():
    """清理构建目录"""
    print_header("清理旧文件")
    
    # 先尝试关闭可能占用文件的程序
    try:
        import subprocess
        # 尝试关闭 MEMEFinder.exe（忽略错误）
        subprocess.run(['taskkill', '/F', '/IM', 'MEMEFinder.exe'], 
                      capture_output=True, timeout=5)
        import time
        time.sleep(1)  # 等待进程完全关闭
    except:
        pass  # 忽略错误
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"删除: {dir_name}/")
            try:
                # 尝试多次删除，处理文件被占用的情况
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        shutil.rmtree(dir_name)
                        break  # 成功删除，退出重试循环
                    except PermissionError as e:
                        if retry < max_retries - 1:
                            print(f"  文件被占用，等待后重试... ({retry + 1}/{max_retries})")
                            import time
                            time.sleep(2)
                        else:
                            # 最后一次尝试：跳过被占用的文件
                            print(f"  警告: 某些文件被占用，尝试跳过...")
                            shutil.rmtree(dir_name, ignore_errors=True)
                            # 如果目录仍然存在，尝试删除未被占用的文件
                            if Path(dir_name).exists():
                                for root, dirs, files in os.walk(dir_name, topdown=False):
                                    for name in files:
                                        try:
                                            os.remove(os.path.join(root, name))
                                        except:
                                            pass
                                    for name in dirs:
                                        try:
                                            os.rmdir(os.path.join(root, name))
                                        except:
                                            pass
                            print(f"  已跳过被占用的文件，继续打包...")
            except Exception as e:
                print(f"  警告: 清理 {dir_name} 时出错: {e}")
                print(f"  将继续打包过程...")
    
    # 不删除 spec 文件，保留配置
    # for spec in Path('.').glob('*.spec'):
    #     print(f"删除: {spec}")
    #     spec.unlink()
    
    print("✓ 清理完成")


def build_exe():
    """使用PyInstaller打包"""
    print_header("开始打包")
    
    # 优先使用spec文件，如果没有则生成
    spec_file = Path('MEMEFinder.spec')
    
    if spec_file.exists():
        print("使用现有的 spec 文件: MEMEFinder.spec")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
    else:
        print("使用命令行参数打包（将生成 spec 文件）")
        
        # 检查哪些补丁文件存在
        patch_files = [
            'paddlex_patch.py',
            'paddle_runtime_patch.py',
            'cv2_patch.py',
            'snownlp_patch.py',
            'snownlp_runtime_patch.py',
            'ocr_model_patch.py',
            'pyclipper_patch.py',
            'stdout_stderr_patch.py'
        ]
        
        existing_patches = []
        for patch in patch_files:
            if Path(patch).exists():
                existing_patches.append(f'--add-data={patch};.')
        
        # PyInstaller 命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '--name=MEMEFinder',
            '--windowed',
            
            # 添加数据文件
            '--add-data=src;src',
            '--add-data=README.md;.',
            '--add-data=LICENSE;.',
        ]
        
        # 添加存在的补丁文件
        cmd.extend(existing_patches)
        
        # 继续添加其他参数
        cmd.extend([
            # 关键：收集PaddleX的所有数据文件
            '--collect-all=paddlex',
            '--collect-all=paddle',
            '--collect-all=paddleocr',
            '--collect-all=paddlenlp',
            '--collect-all=pypdfium2',
            '--collect-all=pyclipper',  # PaddleOCR必需
            '--collect-submodules=paddlex',
            '--collect-submodules=paddle',
            '--collect-submodules=paddleocr',
            '--collect-submodules=paddlenlp',
            '--collect-submodules=pypdfium2',
            '--collect-submodules=pyclipper',  # PaddleOCR必需
            
            # 必需的隐藏导入 - 添加更多paddle相关模块
            '--hidden-import=unittest',
            '--hidden-import=unittest.mock',
            '--hidden-import=doctest',
            '--hidden-import=paddle',
            '--hidden-import=paddle.framework',
            '--hidden-import=paddle.framework.core',
            '--hidden-import=paddle.framework.io',
            '--hidden-import=paddle.fluid',
            '--hidden-import=paddle.fluid.core',
            '--hidden-import=paddle.fluid.framework',
            '--hidden-import=paddle.fluid.io',
            '--hidden-import=paddle.fluid.layers',
            '--hidden-import=paddle.fluid.dygraph',
            '--hidden-import=paddle.fluid.executor',
            '--hidden-import=paddle.fluid.program_guard',
            '--hidden-import=paddleocr',
            '--hidden-import=paddlenlp',
            '--hidden-import=paddlex',
            '--hidden-import=paddlex.inference',
            '--hidden-import=paddlex.inference.pipelines',
            '--hidden-import=paddlex.inference.pipelines.ocr',
            '--hidden-import=paddlex.inference.models',
            '--hidden-import=paddlex.modules',
            '--hidden-import=cv2',
            '--hidden-import=PIL',
            '--hidden-import=numpy',
            '--hidden-import=pandas',  # PaddleX需要
            '--hidden-import=tkinter',
            '--hidden-import=sqlite3',
            '--hidden-import=sklearn',
            '--hidden-import=scipy',
            '--hidden-import=pypdfium2',
            '--hidden-import=pyclipper',  # PaddleOCR需要
            '--hidden-import=shapely',  # PaddleOCR可能需要
            '--hidden-import=imgaug',  # PaddleOCR可能需要
            
            # 只排除开发工具（不排除任何科学计算库）
            '--exclude-module=pytest',
            '--exclude-module=IPython',
            
            'main.py'
        ])
    
    print("执行命令:")
    print(' '.join(cmd))
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n✗ 打包失败")
        return False
    
    print("\n✓ 打包成功")
    return True


def check_output():
    """检查输出文件"""
    print_header("检查输出")
    
    exe_path = Path('dist/MEMEFinder/MEMEFinder.exe')
    
    if not exe_path.exists():
        print("✗ 找不到 MEMEFinder.exe")
        return False
    
    # 计算大小
    total_size = 0
    file_count = 0
    
    dist_dir = Path('dist/MEMEFinder')
    for file in dist_dir.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
            file_count += 1
    
    size_mb = total_size / (1024 * 1024)
    
    print(f"✓ 可执行文件: {exe_path}")
    print(f"✓ 总文件数: {file_count}")
    print(f"✓ 总大小: {size_mb:.2f} MB")
    
    return True


def create_release_package():
    """创建发布包"""
    print_header("创建发布包")
    
    dist_dir = Path('dist/MEMEFinder')
    
    # 复制README到dist
    readme_src = Path('README.md')
    if readme_src.exists():
        shutil.copy2(readme_src, dist_dir / 'README.txt')
        print("✓ 复制 README.md")
    
    # 复制LICENSE
    license_src = Path('LICENSE')
    if license_src.exists():
        shutil.copy2(license_src, dist_dir / 'LICENSE.txt')
        print("✓ 复制 LICENSE")
    
    # 创建启动批处理
    launcher_bat = dist_dir / '启动MEMEFinder.bat'
    launcher_bat.write_text(
        '@echo off\n'
        'chcp 65001 > nul\n'
        'title MEMEFinder\n'
        'cd /d "%~dp0"\n'
        'if not exist "MEMEFinder.exe" (\n'
        '    echo 错误: 找不到 MEMEFinder.exe\n'
        '    pause\n'
        '    exit /b 1\n'
        ')\n'
        'start "" "MEMEFinder.exe"\n',
        encoding='utf-8'
    )
    print("✓ 创建 启动MEMEFinder.bat")
    
    # 创建CPU模式启动批处理
    cpu_launcher_bat = dist_dir / '启动_CPU模式.bat'
    cpu_launcher_bat.write_text(
        '@echo off\n'
        'REM MEMEFinder CPU模式启动脚本\n'
        'REM\n'
        'REM 如果你在使用GPU模式时遇到闪退或卡死问题，\n'
        'REM 可以使用此脚本强制使用CPU模式启动程序\n'
        '\n'
        'echo ================================================\n'
        'echo   MEMEFinder - CPU 模式启动\n'
        'echo ================================================\n'
        'echo.\n'
        'echo 正在以 CPU 模式启动 MEMEFinder...\n'
        'echo 注意: CPU 模式比 GPU 模式慢 2-3 倍\n'
        'echo.\n'
        '\n'
        'REM 设置环境变量强制使用CPU模式\n'
        'set MEMEFINDER_FORCE_CPU=1\n'
        '\n'
        'REM 启动程序\n'
        'start "" "%~dp0MEMEFinder.exe"\n'
        '\n'
        'echo.\n'
        'echo 程序已启动！\n'
        'echo 如需恢复 GPU 模式，请直接双击 MEMEFinder.exe\n'
        'echo.\n'
        'pause\n',
        encoding='utf-8'
    )
    print("✓ 创建 启动_CPU模式.bat")
    
    # 创建使用说明文件
    usage_txt = dist_dir / '使用说明.txt'
    usage_content = """═══════════════════════════════════════════════════════
    MEMEFinder - 表情包查找器
    使用说明
═══════════════════════════════════════════════════════

【快速开始】

1. 首次使用（必须）：
   - 双击运行 "启动MEMEFinder.bat" 或直接运行 "MEMEFinder.exe"
   - 程序首次运行时会自动下载 AI 模型（需要网络连接）
   - 模型下载可能需要 5-15 分钟，请耐心等待

2. 日常使用：
   - 双击 "启动MEMEFinder.bat" 或 "MEMEFinder.exe" 启动程序
   - 在「图源管理」中添加表情包文件夹
   - 点击「扫描新图片」扫描图片
   - 在「图片处理」中运行 OCR 识别
   - 在「图片搜索」中搜索表情包

【重要提示】

✓ 首次运行需要网络连接以下载 AI 模型
✓ 模型文件会保存在程序目录的 models 文件夹中
✓ 模型下载后可以离线使用
✓ 建议将程序放在固定位置，不要随意移动

【系统要求】

- Windows 10/11 64位
- 至少 4GB 内存
- 至少 3GB 可用磁盘空间
- 首次需要网络连接

【常见问题】

Q: 程序无法启动？
A: 请确保系统是 Windows 10/11 64位，并检查是否有杀毒软件拦截

Q: 程序启动时卡住或闪退（GPU用户）？
A: 这可能是GPU环境兼容性问题，请使用「启动_CPU模式.bat」启动程序
   CPU模式稳定性更好，速度略慢但不影响正常使用

Q: OCR 识别失败？
A: 请确保已下载模型（首次运行会自动下载），检查网络连接

Q: 程序运行缓慢？
A: 首次运行需要初始化，后续会更快。大量图片处理需要时间

【获取帮助】

更多信息请查看 README.txt 文件
或访问项目主页：https://github.com/aliveriver/MEMEFinder

═══════════════════════════════════════════════════════
"""
    usage_txt.write_text(usage_content, encoding='utf-8')
    print("✓ 创建 使用说明.txt")
    
    # 创建空目录（如果不存在）
    (dist_dir / 'logs').mkdir(exist_ok=True)
    (dist_dir / 'models').mkdir(exist_ok=True)
    print("✓ 创建 logs 和 models 目录")
    
    # 创建ZIP包
    print("\n正在创建 ZIP 压缩包...")
    output_name = 'MEMEFinder-v1.0.0-Windows-x64'
    
    # 检查源目录是否存在
    if not dist_dir.exists():
        print(f"✗ 错误: 源目录不存在: {dist_dir}")
        return
    
    # 检查可执行文件是否存在
    exe_file = dist_dir / 'MEMEFinder.exe'
    if not exe_file.exists():
        print(f"✗ 警告: 可执行文件不存在: {exe_file}")
        print("   ZIP包将不包含主程序")
    
    try:
        # 确保dist目录存在
        dist_parent = Path('dist')
        dist_parent.mkdir(exist_ok=True)
        
        # 创建ZIP包
        zip_base = dist_parent / output_name
        zip_path = Path(f'{zip_base}.zip')
        
        # 如果ZIP已存在，先删除
        if zip_path.exists():
            print(f"删除已存在的ZIP: {zip_path}")
            zip_path.unlink()
        
        print(f"正在打包: {dist_dir.absolute()} -> {zip_path.absolute()}")
        
        # 使用绝对路径确保正确
        zip_base_abs = zip_base.absolute()
        dist_parent_abs = dist_parent.absolute()
        
        print(f"  源目录: {dist_dir.absolute()}")
        print(f"  输出文件: {zip_path.absolute()}")
        
        shutil.make_archive(
            str(zip_base_abs),
            'zip',
            str(dist_parent_abs),
            'MEMEFinder'
        )
        
        # 验证ZIP文件
        if zip_path.exists():
            zip_size = zip_path.stat().st_size / (1024 * 1024)
            print(f"✓ ZIP包创建成功: {zip_path.absolute()}")
            print(f"✓ ZIP包大小: {zip_size:.2f} MB")
        else:
            print(f"✗ 错误: ZIP文件未创建: {zip_path}")
            print("  请检查是否有写入权限")
            
    except Exception as e:
        print(f"✗ 创建ZIP包时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ 发布包创建完成")


def check_dependencies():
    """检查依赖"""
    print_header("检查依赖")
    
    missing = []
    
    # 检查paddle
    try:
        import paddle
        print(f"✓ paddle 已安装")
    except ImportError:
        print("✗ paddle 未安装")
        missing.append("paddlepaddle")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装")
        missing.append("pyinstaller")
    
    if missing:
        print(f"\n✗ 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        return False
    
    return True


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MEMEFinder Release 打包工具" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # 检查依赖
    if not check_dependencies():
        input("\n按回车退出...")
        sys.exit(1)
    
    # 执行构建流程
    try:
        # 1. 清理
        clean_build()
        
        # 2. 打包
        if not build_exe():
            input("\n按回车退出...")
            sys.exit(1)
        
        # 3. 检查
        if not check_output():
            input("\n按回车退出...")
            sys.exit(1)
        
        # 4. 创建发布包
        create_release_package()
        
        # 完成
        print_header("打包完成")
        print("输出目录: dist/MEMEFinder/")
        print("发布包: dist/MEMEFinder-v1.0.0-Windows-x64.zip")
        print("\n后续步骤:")
        print("1. 测试 dist/MEMEFinder/MEMEFinder.exe")
        print("2. 确认程序可以正常运行")
        print("3. 上传 ZIP 包到 GitHub Releases")
        
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车退出...")


if __name__ == '__main__':
    main()
