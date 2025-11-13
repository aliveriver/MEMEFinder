#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型清理脚本 - 清理已下载的 PaddlePaddle 模型
用于测试打包程序的模型下载功能

使用方法:
  python clean_models.py                # 干运行模式，仅显示将要删除的内容
  python clean_models.py --dry-run      # 同上
  python clean_models.py --yes          # 执行实际删除操作
  python clean_models.py --scan         # 深度扫描所有可能的缓存位置
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def get_paddle_cache_dirs():
    """获取 PaddlePaddle 相关的缓存目录"""
    cache_dirs = []
    
    # 用户主目录
    home = Path.home()
    
    # === PaddleX 模型缓存（最重要！）===
    cache_dirs.append(home / '.paddlex')
    
    # === PaddleOCR 模型缓存 ===
    cache_dirs.extend([
        home / '.paddleocr',
        home / '.paddleclas',
        home / 'paddleocr',
    ])
    
    # === PaddleNLP 模型缓存 ===
    cache_dirs.extend([
        home / '.paddlenlp',
        home / 'paddlenlp',
    ])
    
    # === Paddle 通用缓存 ===
    cache_dirs.extend([
        home / '.paddle',
        home / 'paddle',
        home / 'paddle_packages',
    ])
    
    # === AppData 缓存（Windows） ===
    if sys.platform == 'win32':
        appdata_local = home / 'AppData' / 'Local'
        appdata_roaming = home / 'AppData' / 'Roaming'
        
        cache_dirs.extend([
            appdata_local / 'paddle',
            appdata_local / 'paddleocr',
            appdata_local / 'paddlenlp',
            appdata_local / 'paddlex',
            appdata_roaming / 'paddle',
            appdata_roaming / 'paddleocr',
            appdata_roaming / 'paddlenlp',
            appdata_roaming / 'paddlex',
        ])
    
    # === 项目本地模型目录 ===
    project_root = Path(__file__).parent
    cache_dirs.extend([
        project_root / 'models',
        project_root / '.paddleocr',
        project_root / '.paddlenlp',
        project_root / '.paddlex',
        project_root / '.paddle',
    ])
    
    return cache_dirs


def get_dir_size(path):
    """计算目录大小"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"



def scan_cache_dirs(cache_dirs, verbose=False):
    """扫描缓存目录"""
    found_dirs = []
    
    if verbose:
        print("\n扫描中...")
    
    for cache_dir in cache_dirs:
        if verbose:
            print(f"  检查: {cache_dir}", end="")
        
        if cache_dir.exists() and cache_dir.is_dir():
            size = get_dir_size(cache_dir)
            if size > 0:  # 只记录非空目录
                found_dirs.append({
                    'path': cache_dir,
                    'size': size,
                    'size_str': format_size(size)
                })
                if verbose:
                    print(f" ✓ [{format_size(size)}]")
            else:
                if verbose:
                    print(" (空)")
        else:
            if verbose:
                print(" (不存在)")
    
    return found_dirs


def deep_scan_paddle_files():
    """深度扫描所有 Paddle 相关文件"""
    print_header("深度扫描模式")
    print("正在搜索所有 Paddle 相关目录...\n")
    
    home = Path.home()
    paddle_patterns = ['*paddle*', '*Paddle*', '*PADDLE*']
    
    found = {}  # 使用字典去重
    
    # 搜索用户主目录（只搜索第一层）
    print(f"扫描: {home}")
    for pattern in paddle_patterns:
        for item in home.glob(pattern):
            if item.is_dir() and item not in found:
                size = get_dir_size(item)
                if size > 0:
                    found[item] = size
                    print(f"  ✓ {item.name}: {format_size(size)}")
    
    # 搜索 AppData (Windows)
    if sys.platform == 'win32':
        appdata_dirs = [
            home / 'AppData' / 'Local',
            home / 'AppData' / 'Roaming',
        ]
        
        for appdata in appdata_dirs:
            if appdata.exists():
                print(f"\n扫描: {appdata}")
                for pattern in paddle_patterns:
                    for item in appdata.glob(pattern):
                        if item.is_dir() and item not in found:
                            size = get_dir_size(item)
                            if size > 0:
                                found[item] = size
                                print(f"  ✓ {item.name}: {format_size(size)}")
    
    # 项目目录
    project_root = Path(__file__).parent
    print(f"\n扫描: {project_root}")
    for pattern in paddle_patterns:
        for item in project_root.glob(pattern):
            if item.is_dir() and item not in found:
                size = get_dir_size(item)
                if size > 0:
                    found[item] = size
                    print(f"  ✓ {item.name}: {format_size(size)}")
    
    return [(path, size) for path, size in found.items()]



def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)




def clean_models(dry_run=True, verbose=False):
    """清理模型缓存"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "PaddlePaddle 模型清理工具" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # 获取所有可能的缓存目录
    cache_dirs = get_paddle_cache_dirs()
    
    # 扫描
    print_header("正在扫描缓存目录")
    found_dirs = scan_cache_dirs(cache_dirs, verbose=verbose)
    
    if not found_dirs:
        print("\n✓ 未发现任何 PaddlePaddle 模型缓存")
        print("  所有缓存目录都是空的或不存在")
        print("\n提示: 使用 --scan 参数进行深度扫描")
        return
    
    # 显示找到的目录
    print_header("发现以下缓存目录")
    total_size = 0
    
    for idx, item in enumerate(found_dirs, 1):
        print(f"\n{idx}. {item['path']}")
        print(f"   大小: {item['size_str']}")
        
        # 显示目录内容概览
        try:
            subdirs = [d for d in item['path'].iterdir() if d.is_dir()]
            if subdirs and len(subdirs) <= 10:
                print(f"   包含: {', '.join(d.name for d in subdirs[:5])}" + 
                      ("..." if len(subdirs) > 5 else ""))
        except:
            pass
        
        total_size += item['size']
    
    print(f"\n总计: {len(found_dirs)} 个目录, {format_size(total_size)}")
    
    # 执行删除
    if dry_run:
        print_header("干运行模式 (DRY RUN)")
        print("\n以上目录将被删除 (当前仅预览，未实际删除)")
        print("\n如需实际删除，请运行:")
        print("  python clean_models.py --yes")
    else:
        print_header("⚠️  警告：即将删除缓存")
        print(f"\n将删除 {len(found_dirs)} 个目录，共 {format_size(total_size)}")
        
        # 二次确认
        confirm = input("\n确定要删除吗? (输入 YES 继续): ")
        if confirm != "YES":
            print("\n✗ 已取消")
            return
        
        print_header("正在删除缓存")
        
        success_count = 0
        fail_count = 0
        freed_size = 0
        
        for item in found_dirs:
            try:
                print(f"\n正在删除: {item['path']}")
                shutil.rmtree(item['path'])
                print(f"✓ 已删除 ({item['size_str']})")
                success_count += 1
                freed_size += item['size']
            except Exception as e:
                print(f"✗ 删除失败: {e}")
                fail_count += 1
        
        print_header("清理完成")
        print(f"\n✓ 成功删除: {success_count} 个目录")
        if fail_count > 0:
            print(f"✗ 删除失败: {fail_count} 个目录")
        print(f"✓ 释放空间: {format_size(freed_size)}")
        
        print("\n现在可以重新运行 download_models.py 来测试模型下载功能")



def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='清理 PaddlePaddle 模型缓存，用于测试模型下载功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python clean_models.py              # 仅预览，不删除
  python clean_models.py --dry-run    # 同上
  python clean_models.py --yes        # 执行删除（会二次确认）
  python clean_models.py --scan       # 深度扫描所有 Paddle 相关目录
  python clean_models.py -v           # 详细模式，显示扫描过程
        """
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='执行实际删除操作（不加此参数则为干运行模式）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，仅显示将要删除的内容（默认行为）'
    )
    
    parser.add_argument(
        '--scan', '-s',
        action='store_true',
        help='深度扫描模式，搜索所有可能的 Paddle 相关目录'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细模式，显示扫描过程'
    )
    
    args = parser.parse_args()
    
    try:
        # 深度扫描模式
        if args.scan:
            found = deep_scan_paddle_files()
            
            if found:
                total_size = sum(size for _, size in found)
                print_header("扫描完成")
                print(f"\n找到 {len(found)} 个 Paddle 相关目录")
                print(f"总大小: {format_size(total_size)}")
                print("\n使用 clean_models.py --yes 清理这些目录")
            else:
                print("\n✓ 未发现任何 Paddle 相关目录")
            
            return
        
        # 普通清理模式
        dry_run = not args.yes
        clean_models(dry_run=dry_run, verbose=args.verbose)
        
        if not dry_run:
            print("\n✓ 清理完成！")
            print("\n后续步骤:")
            print("  1. 运行: python download_models.py")
            print("  2. 测试模型下载功能")
            print("  3. 运行: python main.py")
            print("  4. 测试打包后的程序")
        
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if not sys.flags.interactive:
        input("\n按回车键退出...")


if __name__ == '__main__':
    main()
