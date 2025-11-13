#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaddleX 运行时补丁 - 简化版本
只设置必要的环境变量，实际问题已通过 OCRProcessor 的最小配置解决
"""

import sys
import os

# ===== 设置环境变量（预防性措施）=====
os.environ['PADDLEX_DISABLE_DEPS_CHECK'] = '1'
os.environ['PADDLEX_SKIP_PLUGIN_CHECK'] = '1'
os.environ['PADDLEX_SKIP_SERVING_CHECK'] = '1'
os.environ['DISABLE_IMPORTLIB_METADATA_CHECK'] = '1'

if getattr(sys, 'frozen', False):
    print("[PaddleX补丁] 检测到打包环境，已设置环境变量")
    print("[PaddleX补丁] 将注入轻量的 fake paddlex 包以避免依赖检查和导入错误")

    import types

    def _ensure_module(name):
        if name in sys.modules:
            return sys.modules[name]
        m = types.ModuleType(name)
        # mark as package if it has submodules
        if '.' not in name:
            m.__path__ = []
        sys.modules[name] = m
        return m

    # Top-level paddlex package
    paddlex_mod = _ensure_module('paddlex')
    # ensure it's treated as a package
    try:
        paddlex_mod.__path__ = []
    except Exception:
        pass

    # minimal submodules that PaddleOCR may import
    inf = _ensure_module('paddlex.inference')
    _ensure_module('paddlex.inference.utils')
    bm = _ensure_module('paddlex.inference.utils.benchmark')
    # provide a no-op benchmark function
    try:
        bm.benchmark = lambda *a, **k: (lambda *x, **y: None)
    except Exception:
        pass

    _ensure_module('paddlex.inference.models')
    _ensure_module('paddlex.modules')
    _ensure_module('paddlex.utils')
    # provide simple pipeline_arguments module used by paddleocr
    try:
        pa = _ensure_module('paddlex.utils.pipeline_arguments')
        pa.custom_type = lambda *a, **k: (lambda x: x)
    except Exception:
        pass

    # provide paddlex.utils.config with AttrDict used by paddleocr
    try:
        cfg = _ensure_module('paddlex.utils.config')
        class AttrDict(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(name)

            def __setattr__(self, name, value):
                self[name] = value

        cfg.AttrDict = AttrDict
    except Exception:
        pass
    # provide paddlex.utils.device with minimal helpers used by paddleocr
    try:
        dev = _ensure_module('paddlex.utils.device')
        dev.get_default_device = lambda *a, **k: 'cpu'
        # return (device_type, device_id) to match paddlex.utils.device.parse_device
        dev.parse_device = lambda s='cpu': ('cpu', 0)
    except Exception:
        pass

    # deps module with DependencyError and noop checks
    deps = _ensure_module('paddlex.utils.deps')
    try:
        class DependencyError(Exception):
            pass
        deps.DependencyError = DependencyError
        deps.check_dependencies = lambda *a, **k: True
        deps.verify_dependencies = lambda *a, **k: True
    except Exception:
        # assignment may fail in some frozen contexts, ignore
        pass

    # ensure create_pipeline doesn't raise
    try:
        paddlex_mod.create_pipeline = lambda *a, **k: None
    except Exception:
        pass
    # provide a minimal create_predictor to satisfy imports like `from paddlex import create_predictor`
    try:
        class _DummyPredictor:
            def __init__(self, *a, **k):
                pass
            def predict(self, *a, **k):
                return None
            def __call__(self, *a, **k):
                return None

        paddlex_mod.create_predictor = lambda *a, **k: _DummyPredictor()
    except Exception:
        pass

    # add minimal classes/attributes on paddlex.inference that paddleocr imports at module-import time
    try:
        class PaddlePredictorOption:
            def __init__(self, *a, **k):
                # default stub options
                self.use_gpu = False
                self.cpu_threads = 1

        inf.PaddlePredictorOption = PaddlePredictorOption
        # stub for load_pipeline_config used by paddleocr pipelines
        try:
            inf.load_pipeline_config = lambda *a, **k: {}
        except Exception:
            pass
    except Exception:
        pass

    print("[PaddleX补丁] 已注入 fake paddlex 包")
else:
    print("[PaddleX补丁] 开发环境")
