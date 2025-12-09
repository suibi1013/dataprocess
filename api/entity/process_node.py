#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程节点实体类
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProcessNode(BaseModel):
    """流程节点实体类"""
    id: str = Field(..., description="节点ID")
    flow_id: str = Field(..., description="流程ID", alias="flowId")
    instruction_id: str = Field(..., description="指令ID", alias="instructionId")
    name: Optional[str] = Field(None, description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    x: float = Field(..., description="节点X坐标")
    y: float = Field(..., description="节点Y坐标")
    params: Dict[str, Any] = Field(..., description="节点参数")
    intput_types: Dict[str, List[str]] = Field(default_factory=dict, description="输入类型，t表示文本，e表示表达式", alias="intput_types")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid",  # 禁止额外字段
        "populate_by_name": True  # 允许使用字段别名
    }
