#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换器基类
定义PPT转换器的通用接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseConverter(ABC):
    """转换器基类"""
    
    @abstractmethod
    def convert_ppt_to_html_with_editor(
        self, 
        ppt_path: str, 
        output_html: Optional[str] = None, 
        config_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将PPT转换为HTML配置
        
        Args:
            ppt_path: PPT文件路径
            output_html: 输出HTML文件路径（可选）
            config_file: 配置文件路径（可选）
            
        Returns:
            转换结果字典
        """
        pass
    
    # @abstractmethod
    # def get_converter_info(self) -> Dict[str, str]:
    #     """
    #     获取转换器信息
        
    #     Returns:
    #         转换器信息字典
    #     """
    #     pass


class ConverterFactory:
    """转换器工厂类"""
    
    _converters = {}
    
    @classmethod
    def register_converter(cls, name: str, converter_class):
        """注册转换器"""
        cls._converters[name] = converter_class
    
    @classmethod
    def create_converter(cls, name: str = 'default') -> BaseConverter:
        """创建转换器实例"""
        if name not in cls._converters:
            # 默认使用PPTConverterWithEditor
            from .ppt_converter import PPTConverterWithEditor
            return PPTConverterWithEditor()
        
        return cls._converters[name]()
    
    @classmethod
    def list_converters(cls) -> list:
        """列出所有可用的转换器"""
        return list(cls._converters.keys())