#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令管理DTO模型
定义指令项目的数据传输对象
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class InstructionParameter(BaseModel):
    """指令参数配置模型"""
    name: str  # 参数名称
    label: str  # 参数标签
    description: Optional[str] = None  # 参数描述
    type: str  # 控件类型，如：string, number, boolean,select,select_excelpath,file等
    required: bool = False  # 是否必填
    default_value: Optional[Any] = None  # 默认值
    direction: int = 0  # 参数方向：0-输入参数，1-输出参数，2-回写参数（常用于循环逻辑中的游标变量）
    api_url: Optional[str] = None  # option数据或数据请求接口地址，用于动态加载选项

class InstructionItem(BaseModel):
    """指令项目模型"""
    id: str
    name: str  # 指令名称，如：数据提取、数据写入等
    icon: str  # 指令图标，如：📥、📤等
    description: Optional[str] = None  # 指令描述
    category_id: str  # 所属分类ID
    python_script: Optional[str] = None  # Python脚本代码，用于执行指令逻辑
    sort_order: int = 1  # 排序顺序
    is_active: bool = True  # 是否启用
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    params: List[InstructionParameter] = []  # 参数配置列表
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class InstructionCategory(BaseModel):
    """指令分类模型"""
    id: str
    name: str  # 分类名称，如：数据操作、数据处理、流程控制
    description: Optional[str] = None  # 分类描述
    sort_order: int = 1  # 排序顺序
    is_active: bool = True  # 是否启用
    items: List[InstructionItem] = []  # 该分类下的指令项目
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class InstructionListResponse(BaseModel):
    """指令列表响应模型"""
    categories: List[InstructionCategory]
    total_categories: int
    total_items: int
    
class CreateInstructionCategoryRequest(BaseModel):
    """创建指令分类请求模型"""
    name: str
    description: Optional[str] = None
    sort_order: int = 1
    
class CreateInstructionItemRequest(BaseModel):
    """创建指令项目请求模型"""
    name: str
    icon: str
    description: Optional[str] = None
    category_id: str
    python_script: Optional[str] = None  # Python脚本代码
    sort_order: int = 1
    params: Optional[List[InstructionParameter]] = None

class UpdateInstructionCategoryRequest(BaseModel):
    """更新指令分类请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    
class UpdateInstructionItemRequest(BaseModel):
    """更新指令项目请求模型"""
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    python_script: Optional[str] = None  # Python脚本代码
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    params: Optional[List[InstructionParameter]] = None

class ExecuteInstructionRequest(BaseModel):
    """执行指令请求模型"""
    instruction_id: str  # 指令ID
    script_params: Optional[Dict[str, Any]] = {}  # Python脚本参数
    input_types: Optional[Dict[str, List[str]]] = {}  # 输入类型，t表示文本，e表示表达式

class ExecuteInstructionResponse(BaseModel):
    """执行指令响应模型"""
    instruction_id: str  # 指令ID
    instruction_name: str  # 指令名称
    execution_status: str  # 执行状态：success, error
    result: Optional[Any] = None  # 执行结果
    error_message: Optional[str] = None  # 错误信息
    execution_time: Optional[float] = None  # 执行时间（秒）


class CanvasNode(BaseModel):
    """画布节点模型"""
    id: str  # 节点ID
    instructionId: str  # 指令ID
    name: Optional[str] = None  # 指令名称
    description: Optional[str] = None  # 节点描述
    x: float  # X坐标
    y: float  # Y坐标
    params: Dict[str, Any] = {}  # 节点参数
    input_types: Dict[str, List[str]] = {}  # 输入类型，t表示文本，e表示表达式


class CanvasEdge(BaseModel):
    """画布边模型"""
    id: str  # 边ID
    source: str  # 源节点ID
    target: str  # 目标节点ID
    label: Optional[str] = None  # 边标签文本，用作流程连线标签显示
    logic_express: Optional[str] = None  # 逻辑表达式，用于条件判断


class DataProcessFlow(BaseModel):
    """数据处理流程模型"""
    id: Optional[str] = None  # 流程ID，保存时自动生成
    name: Optional[str] = None  # 流程名称
    description: Optional[str] = None  # 流程描述
    nodes: List[CanvasNode]  # 节点列表
    edges: List[CanvasEdge]  # 边列表
    createdAt: Optional[datetime] = None  # 创建时间
    updatedAt: Optional[datetime] = None  # 更新时间
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SaveDataProcessFlowRequest(BaseModel):
    """保存数据处理流程请求模型"""
    name: str  # 流程名称
    description: Optional[str] = None  # 流程描述
    nodes: List[CanvasNode]  # 节点列表
    edges: List[CanvasEdge]  # 边列表


class SaveDataProcessFlowResponse(BaseModel):
    """保存数据处理流程响应模型"""
    id: str  # 保存后的流程ID
    message: str  # 响应消息
    success: bool = True  # 是否成功
    error: Optional[str] = None  # 错误信息（如果有）


class InstallDependenciesRequest(BaseModel):
    """安装依赖包请求模型"""
    dependencies: Optional[str] = None  # 要安装的依赖包，支持多行输入，每行一个依赖包