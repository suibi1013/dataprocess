#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源实体类
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DataSource(BaseModel):
    """数据源实体类"""
    id: str = Field(..., description="数据源ID")
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="数据源名称")
    description: Optional[str] = Field(None, description="数据源描述")
    type: str = Field(..., description="数据源类型")
    config: Dict[str, Any] = Field(..., description="数据源配置")
    created_time: str = Field(..., description="创建时间")
    updated_time: str = Field(..., description="更新时间")
    is_active: bool = Field(..., description="是否激活")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
