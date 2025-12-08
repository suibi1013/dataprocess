#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令管理服务
负责指令项目的创建、更新、删除、查询等核心业务逻辑
指令数据以SQLite数据库形式存储
"""

import os
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
import inspect
import ast

from config import config
from repository.instruction_category_repository import InstructionCategoryRepository
from repository.instruction_item_repository import InstructionItemRepository
from repository.instruction_parameter_repository import InstructionParameterRepository
from entity.instruction_category import InstructionCategory as InstructionCategoryEntity
from entity.instruction_item import InstructionItem as InstructionItemEntity
from entity.instruction_parameter import InstructionParameter as InstructionParameterEntity

from dto.instruction_dto import (
    InstructionItem, InstructionCategory, InstructionListResponse, InstructionParameter,
    CreateInstructionCategoryRequest, CreateInstructionItemRequest,
    UpdateInstructionCategoryRequest, UpdateInstructionItemRequest,
    ExecuteInstructionRequest, ExecuteInstructionResponse
)
from dto.common_dto import ApiResponse

class InstructionService:
    """指令管理服务"""
    
    def __init__(self, category_repo: InstructionCategoryRepository, item_repo: InstructionItemRepository, param_repo: InstructionParameterRepository):
        """初始化指令管理服务
        
        Args:
            category_repo: 指令分类仓储实例
            item_repo: 指令项目仓储实例
            param_repo: 指令参数仓储实例
        """
        self.category_repo = category_repo
        self.item_repo = item_repo
        self.param_repo = param_repo
    
    async def get_instruction_by_id(self, instruction_id: str) -> Optional[Dict[str, Any]]:
        """根据指令ID获取指令信息
        
        Args:
            instruction_id: 指令ID
            
        Returns:
            Optional[Dict[str, Any]]: 指令信息，如果不存在则返回None
        """
        try:
            # 使用仓储类获取指令项目实体
            item_entity = self.item_repo.find_by_id(instruction_id)
            if not item_entity:
                return None
            
            # 使用pydantic的model_dump()方法将实体转换为字典
            item_dict = item_entity.model_dump()
            
            # 获取指令参数
            param_entities = self.param_repo.find_by_instruction_id(instruction_id)
            item_dict["params"] = [param.model_dump() for param in param_entities]
            
            return item_dict
        except Exception as e:
            print(f"获取指令信息失败: {str(e)}")
            return None
    
    async def get_instruction_list(self) -> ApiResponse[InstructionListResponse]:
        """获取指令列表"""
        try:
            # 使用仓储类获取所有激活的分类
            category_entities = self.category_repo.find_active()
            # 使用仓储类获取所有指令项目
            item_entities = self.item_repo.find_all()
            
            # 构建分类和项目的关联关系
            categories = []
            for cat_entity in category_entities:
                # 获取该分类下的所有项目
                category_items = []
                for item_entity in item_entities:
                    if item_entity.category_id == cat_entity.id:
                        # 获取指令参数
                        param_entities = self.param_repo.find_by_instruction_id(item_entity.id)
                        
                        # 将实体类参数转换为DTO参数
                        param_dtos = []
                        for param_entity in param_entities:
                            param_dto = InstructionParameter(
                                name=param_entity.name,
                                label=param_entity.label,
                                description=param_entity.description,
                                type=param_entity.type,
                                required=param_entity.required,
                                defaultValue=param_entity.default_value,
                                direction=param_entity.direction,
                                apiUrl=param_entity.api_url
                            )
                            param_dtos.append(param_dto)
                        
                        # 将实体类转换为DTO
                        item_dto = InstructionItem(
                            id=item_entity.id,
                            name=item_entity.name,
                            icon=item_entity.icon,
                            description=item_entity.description,
                            category_id=item_entity.category_id,
                            python_script=item_entity.python_script,
                            sort_order=item_entity.sort_order,
                            is_active=item_entity.is_active,
                            created_at=item_entity.created_at,
                            updated_at=item_entity.updated_at,
                            params=param_dtos
                        )
                        category_items.append(item_dto)
                
                # 将实体类转换为DTO
                category_dto = InstructionCategory(
                    id=cat_entity.id,
                    name=cat_entity.name,
                    description=cat_entity.description,
                    sort_order=cat_entity.sort_order,
                    is_active=cat_entity.is_active,
                    created_at=cat_entity.created_at,
                    updated_at=cat_entity.updated_at,
                    items=category_items
                )
                categories.append(category_dto)
            
            response_data = InstructionListResponse(
                categories=categories,
                total_categories=len(categories),
                total_items=len(item_entities)
            )
            
            return ApiResponse(
                success=True,
                data=response_data,
                message="获取指令列表成功"
            )
            
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"获取指令列表失败: {str(e)}"
            )
    
    async def create_category(self, request: CreateInstructionCategoryRequest) -> ApiResponse[InstructionCategory]:
        """创建指令分类"""
        try:
            # 创建指令分类实体
            category_entity = InstructionCategoryEntity(
                id=str(uuid.uuid4()),
                name=request.name,
                description=request.description,
                sort_order=request.sort_order,
                is_active=True
            )
            
            # 使用仓储类保存分类
            if self.category_repo.add(category_entity):
                # 将实体类转换为DTO
                category_dto = InstructionCategory(
                    id=category_entity.id,
                    name=category_entity.name,
                    description=category_entity.description,
                    sort_order=category_entity.sort_order,
                    is_active=category_entity.is_active,
                    created_at=category_entity.created_at,
                    updated_at=category_entity.updated_at,
                    items=[]
                )
                return ApiResponse(
                    success=True,
                    data=category_dto,
                    message="创建分类成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="保存分类失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"创建分类失败: {str(e)}"
            )
    
    async def create_item(self, request: CreateInstructionItemRequest) -> ApiResponse[InstructionItem]:
        """创建指令项目"""
        try:
            # 验证分类是否存在
            category = self.category_repo.find_by_id(request.category_id)
            if not category:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指定的分类不存在"
                )
            
            # 转换指令参数DTO为实体类
            param_entities = []
            if request.params:
                for param_dto in request.params:
                    param_entity = InstructionParameterEntity(
                        name=param_dto.name,
                        label=param_dto.label,
                        description=param_dto.description,
                        type=param_dto.type,
                        required=param_dto.required,
                        default_value=param_dto.default_value,
                        direction=param_dto.direction,
                        api_url=param_dto.api_url
                    )
                    param_entities.append(param_entity)
            
            # 创建指令项目实体（不包含params属性）
            item_entity = InstructionItemEntity(
                id=str(uuid.uuid4()),
                name=request.name,
                icon=request.icon,
                description=request.description,
                category_id=request.category_id,
                python_script=request.python_script,
                sort_order=request.sort_order,
                is_active=True
            )
            
            # 使用仓储类保存指令项目
            if self.item_repo.add(item_entity):
                # 保存指令参数
                if param_entities:
                    self.param_repo.add_batch(item_entity.id, param_entities)
                
                # 将实体类参数转换为DTO参数
                param_dtos = []
                if param_entities:
                    for param_entity in param_entities:
                        param_dto = InstructionParameter(
                            name=param_entity.name,
                            label=param_entity.label,
                            description=param_entity.description,
                            type=param_entity.type,
                            required=param_entity.required,
                            defaultValue=param_entity.default_value,
                            direction=param_entity.direction,
                            apiUrl=param_entity.api_url
                        )
                        param_dtos.append(param_dto)
                
                # 将实体类转换为DTO，并添加参数
                item_dto = InstructionItem(
                    id=item_entity.id,
                    name=item_entity.name,
                    icon=item_entity.icon,
                    description=item_entity.description,
                    category_id=item_entity.category_id,
                    python_script=item_entity.python_script,
                    sort_order=item_entity.sort_order,
                    is_active=item_entity.is_active,
                    created_at=item_entity.created_at,
                    updated_at=item_entity.updated_at,
                    params=param_dtos
                )
                return ApiResponse(
                    success=True,
                    data=item_dto,
                    message="创建指令项目成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="保存指令项目失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"创建指令项目失败: {str(e)}"
            )
    
    async def update_category(self, category_id: str, request: UpdateInstructionCategoryRequest) -> ApiResponse[InstructionCategory]:
        """更新指令分类"""
        try:
            # 使用仓储类获取分类实体
            category_entity = self.category_repo.find_by_id(category_id)
            if not category_entity:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="分类不存在"
                )
            
            # 更新字段
            if request.name is not None:
                category_entity.name = request.name
            if request.description is not None:
                category_entity.description = request.description
            if request.sort_order is not None:
                category_entity.sort_order = request.sort_order
            if request.is_active is not None:
                category_entity.is_active = request.is_active
            
            # 更新时间
            category_entity.updated_at = datetime.now().isoformat()
            
            # 使用仓储类保存更新
            if self.category_repo.update(category_entity):
                # 将实体类转换为DTO
                category_dto = InstructionCategory(
                    id=category_entity.id,
                    name=category_entity.name,
                    description=category_entity.description,
                    sort_order=category_entity.sort_order,
                    is_active=category_entity.is_active,
                    created_at=category_entity.created_at,
                    updated_at=category_entity.updated_at,
                    items=[]
                )
                return ApiResponse(
                    success=True,
                    data=category_dto,
                    message="更新分类成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="保存分类失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"更新分类失败: {str(e)}"
            )
    
    async def update_item(self, item_id: str, request: UpdateInstructionItemRequest) -> ApiResponse[InstructionItem]:
        """更新指令项目"""
        try:
            # 使用仓储类获取指令项目实体
            item_entity = self.item_repo.find_by_id(item_id)
            if not item_entity:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令项目不存在"
                )
            
            # 如果要更新分类，验证新分类是否存在
            if request.category_id is not None:
                category = self.category_repo.find_by_id(request.category_id)
                if not category:
                    return ApiResponse(
                        success=False,
                        data=None,
                        message="指定的分类不存在"
                    )
            
            # 更新字段
            if request.name is not None:
                item_entity.name = request.name
            if request.icon is not None:
                item_entity.icon = request.icon
            if request.description is not None:
                item_entity.description = request.description
            if request.category_id is not None:
                item_entity.category_id = request.category_id
            if request.sort_order is not None:
                item_entity.sort_order = request.sort_order
            if request.is_active is not None:
                item_entity.is_active = request.is_active
            if request.python_script is not None:
                item_entity.python_script = request.python_script
            
            # 更新时间
            item_entity.updated_at = datetime.now().isoformat()
            
            # 使用仓储类保存更新
            if self.item_repo.update(item_entity):
                # 处理参数更新
                param_entities = []
                if request.params is not None:
                    # 删除原有的所有参数
                    self.param_repo.delete_by_instruction_id(item_id)
                    
                    # 将InstructionParameter对象转换为实体类并保存
                    param_entities = []
                    for param_dto in request.params:
                        param_entity = InstructionParameterEntity(
                            name=param_dto.name,
                            label=param_dto.label,
                            description=param_dto.description,
                            type=param_dto.type,
                            required=param_dto.required,
                            default_value=param_dto.default_value,
                            direction=param_dto.direction,
                            api_url=param_dto.api_url
                        )
                        param_entities.append(param_entity)
                    
                    # 批量保存新参数
                    self.param_repo.add_batch(item_id, param_entities)
                else:
                    # 获取现有参数
                    param_entities = self.param_repo.find_by_instruction_id(item_id)
                
                # 将实体类参数转换为DTO参数
                param_dtos = []
                if param_entities:
                    for param_entity in param_entities:
                        param_dto = InstructionParameter(
                            name=param_entity.name,
                            label=param_entity.label,
                            description=param_entity.description,
                            type=param_entity.type,
                            required=param_entity.required,
                            defaultValue=param_entity.default_value,
                            direction=param_entity.direction,
                            apiUrl=param_entity.api_url
                        )
                        param_dtos.append(param_dto)
                
                # 将实体类转换为DTO
                item_dto = InstructionItem(
                    id=item_entity.id,
                    name=item_entity.name,
                    icon=item_entity.icon,
                    description=item_entity.description,
                    category_id=item_entity.category_id,
                    python_script=item_entity.python_script,
                    sort_order=item_entity.sort_order,
                    is_active=item_entity.is_active,
                    created_at=item_entity.created_at,
                    updated_at=item_entity.updated_at,
                    params=param_dtos
                )
                return ApiResponse(
                    success=True,
                    data=item_dto,
                    message="更新指令项目成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="保存指令项目失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"更新指令项目失败: {str(e)}"
            )
    
    async def delete_category(self, category_id: str) -> ApiResponse[bool]:
        """删除指令分类"""
        try:
            # 使用仓储类删除分类
            if self.category_repo.delete(category_id):
                # 级联删除该分类下的所有指令项目
                # 先获取该分类下的所有指令项目
                items = self.item_repo.find_by_category(category_id)
                for item in items:
                    self.item_repo.delete(item.id)
                
                return ApiResponse(
                    success=True,
                    data=True,
                    message="删除分类成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=False,
                    message="分类不存在或删除失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=False,
                message=f"删除分类失败: {str(e)}"
            )
    
    async def delete_item(self, item_id: str) -> ApiResponse[bool]:
        """删除指令项目"""
        try:
            # 先删除相关的指令参数
            self.param_repo.delete_by_instruction_id(item_id)
            
            # 使用仓储类删除指令项目
            if self.item_repo.delete(item_id):
                return ApiResponse(
                    success=True,
                    data=True,
                    message="删除指令项目成功"
                )
            else:
                return ApiResponse(
                    success=False,
                    data=False,
                    message="指令项目不存在或删除失败"
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                data=False,
                message=f"删除指令项目失败: {str(e)}"
            )
    
    async def execute_instruction(self, request: ExecuteInstructionRequest) -> ApiResponse[ExecuteInstructionResponse]:
        """执行指令"""
        try:
            # 获取指令信息
            item_entity = self.item_repo.find_by_id(request.instruction_id)
            if not item_entity:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令不存在"
                )
            
            # 检查指令是否启用
            if not item_entity.is_active:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令已禁用"
                )
            
            # 获取Python脚本
            python_script = item_entity.python_script
            if not python_script:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令未配置Python脚本"
                )
            
            # 查找direction为1的输出参数
            result_variable_name = ''
            params = item_entity.params
            for param in params:
                if param.direction == 1:
                    result_variable_name = param.name
                    break
            
            # 从script_params中移除result_variable_name参数（如果存在）
            if result_variable_name and result_variable_name in request.script_params:
                del request.script_params[result_variable_name]
            
            # 执行Python脚本
            result = await self._execute_python_script(
                python_script, 
                request.script_params or {}
            )
            return ApiResponse(
                success=True,
                data={result_variable_name: result} if result_variable_name else result,
                message="指令执行成功"
            )
            
        except Exception as e:
            # 获取指令信息以确定result_variable_name（如果需要）
            result_variable_name = ''
            try:
                item_entity = self.item_repo.find_by_id(request.instruction_id)
                if item_entity:
                    params = item_entity.params
                    for param in params:
                        if param.direction == 1:
                            result_variable_name = param.name
                            break
            except:
                pass
            
            return ApiResponse(
                success=False,
                data={result_variable_name: None} if result_variable_name else None,
                message=f"指令执行失败: {str(e)}"
            )

    async def _execute_python_script(self, script: str, params: Dict[str, Any]) -> Any:
        """执行Python脚本（通过AST解析+参数完全匹配定位用户自定义函数）"""
        try:
            # 步骤1：解析脚本AST，提取所有def定义的用户函数名称
            user_func_names = self._extract_user_functions_from_ast(script)
            if not user_func_names:
                raise Exception("未在脚本中找到def定义的用户函数")
            
            # 步骤2：执行脚本，获取全局环境
            globals_env = {
                '__builtins__': __builtins__,
                'inspect': inspect
            }
            exec(script, globals_env)
            
            # 步骤3：筛选参数与params完全匹配的函数
            target_functions = self._filter_functions_by_params(
                globals_env=globals_env,
                func_names=user_func_names,
                target_params=params
            )
            if not target_functions:
                param_keys = list(params.keys())
                raise Exception(f"未找到参数与 {param_keys} 完全匹配的用户函数")
            
            # 步骤4：尝试调用目标函数（默认取第一个匹配的函数）
            name, obj = target_functions[0]
            try:
                # 获取函数参数的类型注解
                sig = inspect.signature(obj)
                # 根据类型注解转换参数类型
                converted_params = self._convert_params_by_type_annotations(sig, params)
                # 使用转换后的参数调用函数
                result = obj(**converted_params)
            except Exception as e:
                raise Exception(f"函数 {name} 调用失败: {str(e)}")
            
            return result
            
        except Exception as e:
            raise Exception(f"脚本执行错误: {str(e)}")
    
    def _convert_params_by_type_annotations(self, signature: inspect.Signature, params: Dict[str, Any]) -> Dict[str, Any]:
        """根据函数参数的类型注解转换参数类型
        
        Args:
            signature: 函数签名对象
            params: 原始参数字典
            
        Returns:
            Dict[str, Any]: 转换类型后的参数字典
        """
        converted_params = {}
        
        for param_name, param in signature.parameters.items():
            # 检查参数是否存在且有类型注解
            if param_name in params and param.annotation != inspect.Parameter.empty:
                param_value = params[param_name]
                # 如果参数值已经是目标类型，则不需要转换
                if isinstance(param_value, param.annotation):
                    converted_params[param_name] = param_value
                    continue
                
                # 尝试根据类型注解进行转换
                try:
                    # 处理常见类型的转换
                    if param.annotation == int:
                        # 尝试将字符串或浮点数转换为整数
                        converted_params[param_name] = int(param_value)
                    elif param.annotation == float:
                        # 尝试将字符串或整数转换为浮点数
                        converted_params[param_name] = float(param_value)
                    elif param.annotation == bool:
                        # 处理布尔值转换，支持字符串"true"/"false"或数字等
                        if isinstance(param_value, str):
                            converted_params[param_name] = param_value.lower() in ('true', 'yes', '1', 't', 'y')
                        else:
                            converted_params[param_name] = bool(param_value)
                    elif param.annotation == str:
                        # 转换为字符串
                        converted_params[param_name] = str(param_value)
                    # 可以根据需要添加更多类型转换逻辑
                    else:
                        # 对于其他类型，尝试直接转换
                        converted_params[param_name] = param.annotation(param_value)
                except (ValueError, TypeError):
                    # 如果转换失败，保留原始值
                    converted_params[param_name] = param_value
            else:
                # 如果参数没有类型注解或不存在于params中，保留原始值（如果存在）
                if param_name in params:
                    converted_params[param_name] = params[param_name]
        
        return converted_params

    def _extract_user_functions_from_ast(self, script: str) -> List[str]:
        """通过AST解析提取脚本中所有def定义的函数名称"""
        tree = ast.parse(script)
        func_names = []
        for node in ast.walk(tree):
            # 识别函数定义节点（def）
            if isinstance(node, ast.FunctionDef):
                func_names.append(node.name)
            # 可选：识别异步函数定义节点（async def）
            elif isinstance(node, ast.AsyncFunctionDef):
                func_names.append(node.name)
        return func_names

    def _filter_functions_by_params(self, globals_env: Dict[str, Any], func_names: List[str], target_params: Dict[str, Any]) -> List[tuple]:
        """筛选参数名称和数量与target_params完全匹配的函数"""
        target_param_keys = set(target_params.keys())
        matched_functions = []
        
        for func_name in func_names:
            obj = globals_env.get(func_name)
            if not obj or not callable(obj):
                continue
            
            # 解析函数参数签名
            try:
                sig = inspect.signature(obj)
                func_param_keys = set(sig.parameters.keys())
                
                # 筛选条件：函数参数与目标参数完全一致（数量和名称都匹配）
                if func_param_keys == target_param_keys:
                    matched_functions.append((func_name, obj))
            except ValueError:
                # 忽略无法解析签名的对象（如内置函数）
                continue
        
        return matched_functions