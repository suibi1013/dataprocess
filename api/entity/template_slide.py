#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模板页面配置实体类
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TemplateSlide(BaseModel):
    """数据模板页面配置实体类"""
    id: str = Field(..., description="幻灯片配置ID")
    template_id: str = Field(..., description="模板ID")
    slide_index: int = Field(..., description="幻灯片索引")
    width: int = Field(..., description="幻灯片宽度")
    height: int = Field(..., description="幻灯片高度")
    background: str = Field(..., description="幻灯片背景")
    elements: List[Dict[str, Any]] = Field(..., description="幻灯片元素列表")
    data_source_config_info: Optional[Dict[str, Any]] = Field(None, description="数据源配置信息，格式为{'Chart 1':{'element_name': 'Chart 1','element_type': '3','element_type_name': 'msoChart','data_source_path': 'E:\\test.xlsx', 'excel_sheet_name': 'Sheet1', 'excel_cell_range': 'A1:B2'}}")  
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
