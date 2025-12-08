#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令分类实体类
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class InstructionCategory(BaseModel):
    """指令分类实体类"""
    id: str = Field(..., description="分类ID")  # 分类ID
    name: str = Field(..., description="分类名称")  # 分类名称
    description: Optional[str] = Field(None, description="分类描述")  # 分类描述
    sort_order: int = Field(0, description="排序顺序")  # 排序顺序
    is_active: bool = Field(True, description="是否激活")  # 是否激活
    created_at: Optional[str] = Field(None, description="创建时间")  # 创建时间
    updated_at: Optional[str] = Field(None, description="更新时间")  # 更新时间
    
    @model_validator(mode='after')
    def set_timestamps(self):
        """设置时间戳"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        return self
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }