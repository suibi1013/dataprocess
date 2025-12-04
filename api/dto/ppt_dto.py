#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT相关数据传输对象（DTO）定义
用于PPT转换、元素配置等操作
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List


class PPTConversionResult(BaseModel):
    """PPT转换结果DTO"""
    success: bool = Field(..., description="转换是否成功")
    config_data: Optional[Dict[str, Any]] = Field(None, description="配置数据")
    error_message: Optional[str] = Field(None, description="错误消息")
    file_path: Optional[str] = Field(None, description="文件路径")
    config_path: Optional[str] = Field(None, description="配置文件路径")


class ElementPosition(BaseModel):
    """元素位置DTO"""
    left: float = Field(..., description="左边距", example=100.0)
    top: float = Field(..., description="上边距", example=50.0)
    width: float = Field(..., description="宽度", example=200.0, gt=0)
    height: float = Field(..., description="高度", example=100.0, gt=0)


class ElementStyle(BaseModel):
    """元素样式DTO"""
    font_family: str = Field("", description="字体族", example="Arial")
    font_size: str = Field("", description="字体大小", example="14px")
    color: str = Field("", description="文字颜色", example="#000000")
    background_color: str = Field("", description="背景颜色", example="#FFFFFF")
    border: str = Field("", description="边框样式", example="1px solid #000")
    text_align: str = Field("", description="文本对齐", example="left")
    font_style: str = Field("normal", description="字体样式", example="normal")
    font_weight: str = Field("normal", description="字体粗细", example="normal")
    text_decoration: str = Field("none", description="文本装饰", example="none")
    
    @field_validator('font_style')
    @classmethod
    def validate_font_style(cls, v):
        if v not in ['normal', 'italic']:
            raise ValueError("字体样式必须是normal或italic")
        return v
    
    @field_validator('font_weight')
    @classmethod
    def validate_font_weight(cls, v):
        if v not in ['normal', 'bold']:
            raise ValueError("字体粗细必须是normal或bold")
        return v
    
    @field_validator('text_decoration')
    @classmethod
    def validate_text_decoration(cls, v):
        if v not in ['none', 'underline']:
            raise ValueError("文本装饰必须是none或underline")
        return v


class ElementData(BaseModel):
    """元素数据DTO"""
    text_content: str = Field("", description="文本内容")
    table_data: Optional[List[List[str]]] = Field(None, description="表格数据")
    chart_data: Optional[Dict[str, Any]] = Field(None, description="图表数据")
    image_data: str = Field("", description="图片数据")
    original_image_data: str = Field("", description="原始图片数据，用于重置")
    ole_datas: Optional[Dict[str, List[List[str]]]] = Field(None, description="多sheet数据")
    active_cell: Optional[Dict[str, Any]] = Field(None, description="活动单元格信息")
    table_row_heights: Optional[List[float]] = Field(None, description="表格行高信息")
    table_col_widths: Optional[List[float]] = Field(None, description="表格列宽信息")
    data_source_config: Optional[Dict[str, Any]] = Field(None, description="数据源配置信息，包括Excel单元格范围")


class PPTElement(BaseModel):
    """PPT元素DTO"""
    element_id: str = Field(..., description="元素ID", example="elem_123")
    element_name: str = Field(..., description="元素名称", example="标题文本")
    element_type: str = Field(..., description="元素类型", example="text")
    element_type_name: str = Field(..., description="元素类型名称", example="文本框")
    position: ElementPosition = Field(..., description="元素位置")
    style: ElementStyle = Field(..., description="元素样式")
    data: ElementData = Field(..., description="元素数据")
    children: Optional[List['PPTElement']] = Field(None, description="子元素列表")
    
    @field_validator('element_id')
    @classmethod
    def validate_element_id(cls, v):
        if not v:
            raise ValueError("元素ID不能为空")
        return v
    
    @field_validator('element_name')
    @classmethod
    def validate_element_name(cls, v):
        if not v:
            raise ValueError("元素名称不能为空")
        return v


class SlideConfig(BaseModel):
    """幻灯片配置DTO"""
    slide_index: int = Field(..., description="幻灯片索引", example=1, ge=0)
    width: float = Field(..., description="幻灯片宽度", example=1920.0, gt=0)
    height: float = Field(..., description="幻灯片高度", example=1080.0, gt=0)
    background: str = Field(..., description="背景样式", example="#FFFFFF")
    elements: List[PPTElement] = Field(..., description="元素列表")


class PPTConfig(BaseModel):
    """PPT配置DTO"""
    file_path: str = Field(..., description="PPT文件路径", example="/path/to/presentation.pptx")
    total_slides: int = Field(..., description="总幻灯片数", example=10, ge=1)
    slide_width: float = Field(..., description="幻灯片宽度", example=1920.0, gt=0)
    slide_height: float = Field(..., description="幻灯片高度", example=1080.0, gt=0)
    created_time: str = Field(..., description="创建时间", example="2024-01-01 12:00:00")
    slides: List[SlideConfig] = Field(..., description="幻灯片配置列表")
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        if not v:
            raise ValueError("文件路径不能为空")
        return v
    
    @field_validator('created_time')
    @classmethod
    def validate_created_time(cls, v):
        if not v:
            raise ValueError("创建时间不能为空")
        return v
class ConfigUpdateDto(BaseModel):
    template_id: str = Field(..., description="模板id")
    config_data: dict = Field(..., description="配置数据")
