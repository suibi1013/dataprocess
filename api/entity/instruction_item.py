#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令信息实体类
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from entity.instruction_parameter import InstructionParameter


class InstructionItem(BaseModel):
    """指令信息实体类"""
    id: str = Field(..., description="指令ID")  # 指令ID
    name: str = Field(..., description="指令名称")  # 指令名称
    category_id: str = Field(..., description="分类ID")  # 分类ID
    icon: Optional[str] = Field(None, description="图标")  # 图标
    description: Optional[str] = Field(None, description="描述")  # 描述
    python_script: Optional[str] = Field(None, description="Python脚本")  # Python脚本
    sort_order: int = Field(0, description="排序顺序")  # 排序顺序
    is_active: bool = Field(True, description="是否激活")  # 是否激活
    created_at: Optional[str] = Field(None, description="创建时间")  # 创建时间
    updated_at: Optional[str] = Field(None, description="更新时间")  # 更新时间
    params: Optional[List[InstructionParameter]] = Field(default_factory=list, description="指令参数列表")  # 指令参数列表
    
    @model_validator(mode='after')
    def set_timestamps(self):
        """设置时间戳"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        # 确保params是列表
        if self.params is None:
            self.params = []
        return self
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }