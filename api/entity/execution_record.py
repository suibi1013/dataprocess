#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行记录实体类
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from entity.execution_result import ExecutionResult


class ExecutionRecord(BaseModel):
    """执行记录实体类"""
    id: str = Field(..., description="执行记录ID")
    flow_id: str = Field(..., description="流程ID")
    flow_name: str = Field(..., description="流程名称")
    success: bool = Field(..., description="是否执行成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间（秒）")
    executed_at: str = Field(..., description="执行时间")
    result_data: Optional[ExecutionResult] = Field(None, description="执行结果数据")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }
