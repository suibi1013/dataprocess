#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行结果实体类
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """执行结果实体类"""
    flow_id: str = Field(..., description="流程ID")
    flow_name: str = Field(..., description="流程名称")
    final_result: Optional[Any] = Field(None, description="最终执行结果")
    process_results: Dict[str, Any] = Field(..., description="流程执行结果详情")
    execution_order: Optional[List[str]] = Field(None, description="实际执行顺序")
    total_nodes_executed: Optional[int] = Field(None, description="实际执行节点数")
    reached_end_node: Optional[bool] = Field(None, description="是否到达结束节点")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }
