#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller hook for excluding torch/pytorch
排除 PyTorch 框架（约310MB）
"""

# 排除整个 torch 模块
excludedimports = [
    'torch',
    'pytorch',
    'torchvision',
    'torchaudio',
    'torchtext',
]
