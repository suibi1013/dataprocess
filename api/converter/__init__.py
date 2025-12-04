#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT转换器包

提供PPT文件转换为HTML的功能，支持多种转换器实现。
"""

from .ppt_converter import PPTConverterWithEditor
from .base_converter import BaseConverter, ConverterFactory

# 注册默认转换器
ConverterFactory.register_converter('ppt_html_editor', PPTConverterWithEditor)

# 导出主要类和工厂
__all__ = ['PPTConverterWithEditor', 'BaseConverter', 'ConverterFactory']