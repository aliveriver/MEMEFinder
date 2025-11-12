"""
SnowNLP数据文件补丁
在打包环境中修复SnowNLP数据文件路径问题
"""

import sys
import os
from pathlib import Path

def patch_snownlp_data_path():
    """修复SnowNLP在打包环境中的数据文件路径"""
    
    if not getattr(sys, "frozen", False):
        # 开发环境无需补丁
        return
    
    try:
        import snownlp
        # 在打包环境中，snownlp的数据文件应该在_internal目录
        if hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            snownlp_data_path = meipass / 'snownlp'
            
            # 检查snownlp模块的实际位置
            try:
                snownlp_module_path = Path(snownlp.__file__).parent
                print(f"[补丁] snownlp模块路径: {snownlp_module_path}")
                
                # 检查数据文件是否存在
                stopwords_file = snownlp_module_path / 'normal' / 'stopwords.txt'
                if stopwords_file.exists():
                    print(f"[补丁] ✓ 找到snownlp数据文件: {stopwords_file}")
                else:
                    # 尝试从_internal目录查找
                    alt_path = meipass / 'snownlp' / 'normal' / 'stopwords.txt'
                    if alt_path.exists():
                        print(f"[补丁] ✓ 在备用路径找到数据文件: {alt_path}")
                    else:
                        print(f"[补丁] ✗ 警告: 未找到snownlp数据文件")
                        print(f"[补丁]   尝试路径1: {stopwords_file}")
                        print(f"[补丁]   尝试路径2: {alt_path}")
                        
                        # 列出snownlp目录内容以便调试
                        if snownlp_module_path.exists():
                            print(f"[补丁]   snownlp模块目录内容: {list(snownlp_module_path.iterdir())[:10]}")
            except Exception as e:
                print(f"[补丁] 检查snownlp路径时出错: {e}")
    except ImportError:
        print("[补丁] snownlp未安装，跳过补丁")
    except Exception as e:
        print(f"[补丁] 应用snownlp补丁时出错: {e}")

# 自动应用补丁
if __name__ != "__main__":
    patch_snownlp_data_path()
