"""
PaddleX 依赖检查补丁
在 PyInstaller 打包环境中增强依赖检测，避免缺失元数据导致的误报
"""

import sys
from functools import lru_cache
from importlib import import_module

from packaging.requirements import InvalidRequirement, Requirement


# 映射需要特殊处理的依赖到其可直接导入的模块名
DEPENDENCY_IMPORT_MAP = {
    "opencv-contrib-python": "cv2",
    "opencv-python": "cv2",
    "pypdfium2": "pypdfium2",
    "python-bidi": "bidi",
    "scikit-learn": "sklearn",
}


def patch_paddlex_deps():
    """在打包环境中增强 PaddleX 的依赖可用性判定"""

    if not getattr(sys, "frozen", False):
        # 开发环境无需补丁
        return

    try:
        import paddlex.utils.deps as deps
    except ImportError:
        # paddlex 未安装，忽略
        return

    original_is_dep_available = deps.is_dep_available

    if hasattr(original_is_dep_available, "cache_clear"):
        original_is_dep_available.cache_clear()

    @lru_cache()
    def patched_is_dep_available(dep, /, check_version=False):
        # 先调用原始函数
        available = original_is_dep_available(dep, check_version=check_version)
        
        # 如果原始函数已经确认可用，直接返回
        if available:
            return available

        # 否则，进入我们的备用检查逻辑（直接导入）
        # 即使 check_version=True，但在 frozen 环境下元数据缺失，
        # 原始函数很可能返回 False，所以我们必须继续执行
        
        package_name = dep
        try:
            package_name = Requirement(dep).name
        except InvalidRequirement:
            pass

        version_note = (
            "（未校验版本）" if check_version else ""
        )

        candidates = []
        mapped = DEPENDENCY_IMPORT_MAP.get(package_name)
        if mapped:
            candidates.append(mapped)

        hyphen_free = package_name.replace("-", "_")
        candidates.extend([package_name, hyphen_free])

        tried = set()
        for module_name in candidates:
            if not module_name or module_name in tried:
                continue
            tried.add(module_name)
            try:
                import_module(module_name)
            except Exception:
                continue

            print(f"[补丁] 通过直接导入确认依赖可用: {dep}{version_note}")
            return True

        # 如果所有尝试都失败了，返回原始的 `available` 结果 (False)
        return available

    deps.is_dep_available = patched_is_dep_available
    deps.is_dep_available.cache_clear = patched_is_dep_available.cache_clear  # type: ignore[attr-defined]

    # 清理缓存确保新逻辑生效
    if hasattr(deps.is_extra_available, "cache_clear"):
        deps.is_extra_available.cache_clear()  # type: ignore[attr-defined]

    print("[补丁] PaddleX依赖检查已增强（打包环境）")


def ensure_cv2_import():
    """
    确保 cv2 在 PaddleX 初始化前被正确导入
    
    通过多种方式确保 cv2 在所有 PaddleX 模块中都可用：
    1. 注入到 builtins，使其在所有模块中全局可用
    2. 使用导入钩子在模块加载时注入
    3. 预先导入并缓存关键模块
    """
    if not getattr(sys, "frozen", False):
        return
    
    try:
        # 首先确保 cv2 被导入
        import cv2
        print(f"[补丁] cv2 版本: {cv2.__version__}")
        
        # 方法1: 将 cv2 注入到 builtins，使其在所有模块中全局可用
        import builtins
        if not hasattr(builtins, 'cv2'):
            builtins.cv2 = cv2
            print("[补丁] 已将 cv2 注入到 builtins（全局可用）")
        
        # 方法2: 使用 import hook 来拦截 paddlex 模块的导入
        import importlib.abc
        
        # 需要注入 cv2 的所有 PaddleX 模块模式
        MODULES_NEED_CV2_PATTERNS = [
            'paddlex.inference.common',
            'paddlex.inference.models.common',
        ]
        
        class CV2InjectorFinder(importlib.abc.MetaPathFinder):
            """为 PaddleX 模块注入 cv2 的导入查找器"""
            
            def find_spec(self, fullname, path, target=None):
                # 检查是否是需要注入 cv2 的模块
                should_inject = any(
                    fullname.startswith(pattern) 
                    for pattern in MODULES_NEED_CV2_PATTERNS
                )
                
                if should_inject:
                    # 先让默认的查找器找到模块
                    for finder in sys.meta_path:
                        if finder is self:
                            continue
                        if hasattr(finder, 'find_spec'):
                            spec = finder.find_spec(fullname, path, target)
                            if spec is not None:
                                # 包装 loader 来注入 cv2
                                original_loader = spec.loader
                                
                                class CV2InjectingLoader:
                                    def __init__(self, original_loader):
                                        self.original_loader = original_loader
                                    
                                    def create_module(self, spec):
                                        if hasattr(self.original_loader, 'create_module'):
                                            return self.original_loader.create_module(spec)
                                        return None
                                    
                                    def exec_module(self, module):
                                        # 在执行模块代码前注入 cv2
                                        if not hasattr(module, 'cv2'):
                                            module.cv2 = cv2
                                        self.original_loader.exec_module(module)
                                        print(f"[补丁] 已将 cv2 注入到 {module.__name__}")
                                
                                spec.loader = CV2InjectingLoader(original_loader)
                                return spec
                
                return None
        
        # 将查找器添加到 meta_path 的开头
        finder = CV2InjectorFinder()
        # 检查是否已经安装（避免重复）
        if not any(isinstance(f, CV2InjectorFinder) for f in sys.meta_path):
            sys.meta_path.insert(0, finder)
            print(f"[补丁] 已安装 cv2 导入钩子")
        
    except ImportError as e:
        print(f"[警告] 无法导入 cv2: {e}")
    except Exception as e:
        print(f"[警告] cv2 补丁安装失败: {e}")


def apply_all_patches():
    """应用所有必要的补丁"""
    ensure_cv2_import()
    patch_paddlex_deps()


# 自动应用补丁
if __name__ != "__main__":
    apply_all_patches()
