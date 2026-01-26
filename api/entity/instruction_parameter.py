#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令参数实体类
"""

from typing import Optional
from pydantic import BaseModel, Field


class InstructionParameter(BaseModel):
    """指令参数实体类"""
    id: Optional[str] = Field(None, description="参数ID")  # 参数ID
    instruction_id: Optional[str] = Field(None, description="指令ID")  # 指令ID
    name: str = Field(..., description="参数名称")  # 参数名称
    label: str = Field(..., description="参数标签")  # 参数标签
    description: Optional[str] = Field(None, description="参数描述")  # 参数描述
    display_type: str = Field("string", description="控件显示类型")  # 控件显示类型，包括文本/表达式string、数字number、布尔开关boolean、下拉单选select_radio、数据源选择select_excelpath、文件上传file_upload、按钮事件button_event
    value_type: str = Field("string", description="参数值类型")  # 参数值类型,包括字符串string、整数int、小数float、布尔boolean、文件file、字典dict、列表list、表格数据tabledata（包含value、style属性）、任意类型any
    required: bool = Field(False, description="是否必填")  # 是否必填
    default_value: Optional[str] = Field(None, description="默认值")  # 默认值
    direction: int = Field(0, description="方向：0-输入参数，1-输出参数")  # 方向
    api_url: Optional[str] = Field(None, description="option数据或数据请求接口地址，用于动态加载选项")  # option数据或数据请求接口地址
    event_script: Optional[str] = Field(None, description="事件脚本")
    
    model_config = {
        "from_attributes": True,  # 允许从ORM模型创建
        "extra": "forbid"  # 禁止额外字段
    }