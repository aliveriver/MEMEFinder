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
        available = original_is_dep_available(dep, check_version=check_version)
        if available:
            return available

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

        return available

    deps.is_dep_available = patched_is_dep_available
    deps.is_dep_available.cache_clear = patched_is_dep_available.cache_clear  # type: ignore[attr-defined]

    # 清理缓存确保新逻辑生效
    if hasattr(deps.is_extra_available, "cache_clear"):
        deps.is_extra_available.cache_clear()  # type: ignore[attr-defined]

    print("[补丁] PaddleX依赖检查已增强（打包环境）")


def apply_all_patches():
    """应用所有必要的补丁"""
    patch_paddlex_deps()


# 自动应用补丁
if __name__ != "__main__":
    apply_all_patches()
