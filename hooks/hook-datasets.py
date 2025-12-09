#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller hook for excluding datasets and transformers
排除 Hugging Face 生态库
"""

# 排除 Hugging Face 相关模块
excludedimports = [
    'datasets',
    'transformers',
    'tokenizers',
    'huggingface_hub',
]
