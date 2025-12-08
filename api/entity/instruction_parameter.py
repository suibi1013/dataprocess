#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令参数实体类
"""

from typing import Optional
from pydantic import BaseModel, Field


class InstructionParameter(BaseModel):
    """指令参数实体类"""
    name: str = Field(..., description="参数名称")  # 参数名称
    label: str = Field(..., description="参数标签")  # 参数标签
    description: Optional[str] = Field(None, description="参数描述")  # 参数描述
    type: str = Field("string", description="参数类型")  # 参数类型
    required: bool = Field(False, description="是否必填")  # 是否必填
    default_value: Optional[str] = Field(None, description="默认值")  # 默认值
    direction: int = Field(0, description="方向：0-输入参数，1-输出参数")  # 方向
    api_url: Optional[str] = Field(None, description="API URL，用于动态加载选项")  # API URL
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }