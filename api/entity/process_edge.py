#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程边实体类
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProcessEdge(BaseModel):
    """流程边实体类"""
    id: str = Field(..., description="边ID")
    flow_id: str = Field(..., description="流程ID", alias="flowId")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: Optional[str] = Field(None, description="边显示标签")
    logic_express:Optional[str] = Field(None, description="逻辑表达式")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
