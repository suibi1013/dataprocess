#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据流程实体类
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from entity.process_node import ProcessNode
from entity.process_edge import ProcessEdge


class DataProcess(BaseModel):
    """数据流程实体类"""
    id: str = Field(..., description="流程ID")
    name: str = Field(..., description="流程名称")
    description: Optional[str] = Field(None, description="流程描述")
    created_at: str = Field(..., description="创建时间", alias="createdAt")
    updated_at: str = Field(..., description="更新时间", alias="updatedAt")
    
    # 非数据库字段，通过关联表获取
    nodes: List[ProcessNode] = Field(default_factory=list, description="流程节点列表")
    edges: List[ProcessEdge] = Field(default_factory=list, description="流程边列表")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
