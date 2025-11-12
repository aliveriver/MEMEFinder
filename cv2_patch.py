"""
cv2模块补丁
确保cv2在paddlex模块使用之前就被导入和可用
"""

import sys

def patch_cv2_import():
    """确保cv2模块在paddlex使用前就被导入"""
    
    # 尝试导入cv2
    try:
        import cv2
        # 将cv2添加到builtins，这样paddlex内部模块可以直接使用
        import builtins
        if not hasattr(builtins, 'cv2'):
            builtins.cv2 = cv2
        print("[补丁] cv2模块已导入并添加到builtins")
        return True
    except ImportError as e:
        print(f"[补丁] 警告: cv2模块导入失败: {e}")
        return False

# 自动应用补丁
if __name__ != "__main__":
    patch_cv2_import()

