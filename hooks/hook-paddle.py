#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller hook for excluding paddle/paddlepaddle
排除 PaddlePaddle 框架（约783MB）
"""

# 排除整个 paddle 模块
excludedimports = [
    'paddle',
    'paddlepaddle', 
    'paddlex',
    'paddlenlp',
    'paddleocr',
]
