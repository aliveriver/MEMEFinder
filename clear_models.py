#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理已下载的 OCR 模型
用于测试打包程序的模型下载功能
"""

import os
import shutil
from pathlib import Path


def clear_rapidocr_models():
    """清理 RapidOCR 的模型缓存"""
    print("=" * 60)
    print("清理 RapidOCR 模型缓存")
    print("=" * 60)
    
    # RapidOCR 模型默认存储位置
    # 通常在用户目录下的 .rapidocr 文件夹
    possible_locations = [
        Path.home() / '.rapidocr',
        Path.home() / '.cache' / 'rapidocr',
        Path(os.path.expanduser('~')) / '.rapidocr',
        Path(os.path.expanduser('~')) / '.cache' / 'rapidocr',
    ]
    
    # 也检查当前项目目录
    project_locations = [
        Path(__file__).parent / 'models' / 'rapidocr',
        Path(__file__).parent / '.rapidocr',
    ]
    
    all_locations = possible_locations + project_locations
    
    deleted_count = 0
    for location in all_locations:
        if location.exists():
            print(f"\n找到模型缓存: {location}")
            try:
                # 显示目录大小
                total_size = sum(f.stat().st_size for f in location.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                print(f"  大小: {size_mb:.2f} MB")
                
                # 列出文件
                files = list(location.rglob('*'))
                if files:
                    print(f"  包含 {len(files)} 个文件/文件夹")
                    for f in files[:5]:  # 只显示前5个
                        print(f"    - {f.name}")
                    if len(files) > 5:
                        print(f"    ... 还有 {len(files) - 5} 个文件")
                
                # 询问是否删除
                confirm = input(f"\n是否删除此目录? (y/n): ").lower().strip()
                if confirm == 'y' or confirm == 'yes':
                    shutil.rmtree(location)
                    print(f"✓ 已删除: {location}")
                    deleted_count += 1
                else:
                    print(f"✗ 跳过: {location}")
            except Exception as e:
                print(f"✗ 删除失败: {e}")
        else:
            print(f"✗ 不存在: {location}")
    
    print("\n" + "=" * 60)
    if deleted_count > 0:
        print(f"✓ 清理完成！删除了 {deleted_count} 个模型缓存目录")
        print("\n下次运行程序时，RapidOCR 会自动下载所需模型")
    else:
        print("未找到或未删除任何模型缓存")
    print("=" * 60)


def clear_snownlp_data():
    """清理 SnowNLP 的数据文件"""
    print("\n" + "=" * 60)
    print("检查 SnowNLP 数据文件")
    print("=" * 60)
    
    try:
        import snownlp
        snownlp_path = Path(snownlp.__file__).parent
        data_path = snownlp_path / 'data'
        
        if data_path.exists():
            print(f"\n找到 SnowNLP 数据目录: {data_path}")
            
            # SnowNLP 的数据文件通常很小，不需要清理
            # 只显示信息
            files = list(data_path.glob('*'))
            print(f"  包含 {len(files)} 个数据文件")
            for f in files[:10]:
                size_kb = f.stat().st_size / 1024
                print(f"    - {f.name} ({size_kb:.1f} KB)")
            
            print("\n注意: SnowNLP 数据文件很小且内置在包中，通常不需要清理")
        else:
            print("✓ SnowNLP 数据目录不存在或已清理")
    except ImportError:
        print("✗ SnowNLP 未安装")
    except Exception as e:
        print(f"✗ 检查 SnowNLP 失败: {e}")


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "模型缓存清理工具" + " " * 27 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 清理 RapidOCR 模型
    clear_rapidocr_models()
    
    # 检查 SnowNLP 数据
    clear_snownlp_data()
    
    print("\n" + "=" * 60)
    print("清理完成！")
    print("\n测试建议：")
    print("1. 运行打包后的 exe: dist\\MEMEFinder\\MEMEFinder.exe")
    print("2. 观察程序是否能自动下载所需的 OCR 模型")
    print("3. 检查 OCR 识别功能是否正常工作")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
