#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模板信息实体类
"""

from typing import Optional
from pydantic import BaseModel, Field


class TemplateInfo(BaseModel):
    """数据模板信息实体类"""
    id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    filename: str = Field(..., description="文件名")
    total_slides: int = Field(..., description="幻灯片总数")
    file_path: str = Field(..., description="文件路径")
    slide_width: int = Field(..., description="幻灯片宽度")
    slide_height: int = Field(..., description="幻灯片高度")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
