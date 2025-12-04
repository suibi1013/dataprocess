#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令管理服务
负责指令项目的创建、更新、删除、查询等核心业务逻辑
指令数据以JSON文件形式存储
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
import inspect
import ast

from config import config
from dto.instruction_dto import (
    InstructionItem, InstructionCategory, InstructionListResponse,
    CreateInstructionCategoryRequest, CreateInstructionItemRequest,
    UpdateInstructionCategoryRequest, UpdateInstructionItemRequest,
    ExecuteInstructionRequest, ExecuteInstructionResponse
)
from dto.common_dto import ApiResponse

class InstructionStorage:
    """指令数据存储管理"""
    
    def __init__(self):
        self.storage_folder = config.INSTRUCTIONS_FOLDER
        self.categories_file = os.path.join(self.storage_folder, 'categories.json')
        self.items_file = os.path.join(self.storage_folder, 'items.json')
        
        # 确保目录存在
        os.makedirs(self.storage_folder, exist_ok=True)
        
        # 初始化数据文件
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """初始化数据文件"""
        # if not os.path.exists(self.categories_file):
        #     self._save_categories([])
        # 如果不存在则设置为空列表
        # if not os.path.exists(self.items_file):
        #     self._save_items([])    
        pass
    def _load_categories(self) -> List[Dict[str, Any]]:
        """加载指令分类数据"""
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载分类数据失败: {e}")
            return []
    
    def _save_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """保存指令分类数据"""
        try:
            with open(self.categories_file, 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存分类数据失败: {e}")
            return False
    
    def _load_items(self) -> List[Dict[str, Any]]:
        """加载指令项目数据"""
        try:
            with open(self.items_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载项目数据失败: {e}")
            return []
    
    def _save_items(self, items: List[Dict[str, Any]]) -> bool:
        """保存指令项目数据"""
        try:
            with open(self.items_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存项目数据失败: {e}")
            return False
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        categories = self._load_categories()
        return sorted([cat for cat in categories if cat.get('is_active', True)], 
                     key=lambda x: x.get('sort_order', 0))
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """获取所有项目"""
        items = self._load_items()
        return sorted(items, key=lambda x: x.get('sort_order', 0))
    
    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取分类"""
        categories = self._load_categories()
        for category in categories:
            if category['id'] == category_id:
                return category
        return None
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取项目"""
        items = self._load_items()
        for item in items:
            if item['id'] == item_id:
                return item
        return None
    
    def save_category(self, category: Dict[str, Any]) -> bool:
        """保存分类"""
        categories = self._load_categories()
        
        # 查找是否存在相同ID的分类
        for i, cat in enumerate(categories):
            if cat['id'] == category['id']:
                categories[i] = category
                return self._save_categories(categories)
        
        # 新增分类
        categories.append(category)
        return self._save_categories(categories)
    
    def save_item(self, item: Dict[str, Any]) -> bool:
        """保存项目"""
        items = self._load_items()
        
        # 查找是否存在相同ID的项目
        for i, itm in enumerate(items):
            if itm['id'] == item['id']:
                items[i] = item
                return self._save_items(items)
        
        # 新增项目
        items.append(item)
        return self._save_items(items)
    
    def delete_category(self, category_id: str) -> bool:
        """删除分类（物理删除）"""
        categories = self._load_categories()
        # 过滤掉要删除的分类
        new_categories = [cat for cat in categories if cat['id'] != category_id]
        
        # 如果分类数量没变，说明没有找到要删除的分类
        if len(new_categories) == len(categories):
            return False
        
        # 保存删除后的分类列表
        if self._save_categories(new_categories):
            # 级联删除该分类下的所有项目
            items = self._load_items()
            new_items = [item for item in items if item['category_id'] != category_id]
            self._save_items(new_items)
            return True
        return False
    
    def delete_item(self, item_id: str) -> bool:
        """删除项目（物理删除）"""
        items = self._load_items()
        # 过滤掉要删除的项目
        new_items = [item for item in items if item['id'] != item_id]
        
        # 如果项目数量没变，说明没有找到要删除的项目
        if len(new_items) == len(items):
            return False
        
        # 保存删除后的项目列表
        return self._save_items(new_items)

class InstructionService:
    """指令管理服务"""
    
    def __init__(self):
        self.storage = InstructionStorage()
    
    async def get_instruction_by_id(self, instruction_id: str) -> Optional[Dict[str, Any]]:
        """根据指令ID获取指令信息
        
        Args:
            instruction_id: 指令ID
            
        Returns:
            Optional[Dict[str, Any]]: 指令信息，如果不存在则返回None
        """
        try:
            return self.storage.get_item_by_id(instruction_id)
        except Exception as e:
            print(f"获取指令信息失败: {str(e)}")
            return None
    
    async def get_instruction_list(self) -> ApiResponse[InstructionListResponse]:
        """获取指令列表"""
        try:
            categories_data = self.storage.get_all_categories()
            items_data = self.storage.get_all_items()
            
            # 构建分类和项目的关联关系
            categories = []
            for cat_data in categories_data:
                # 获取该分类下的所有项目
                category_items = [
                    InstructionItem(**item_data) 
                    for item_data in items_data 
                    if item_data['category_id'] == cat_data['id']
                ]
                
                category = InstructionCategory(
                    **cat_data,
                    items=category_items
                )
                categories.append(category)
            
            response_data = InstructionListResponse(
                categories=categories,
                total_categories=len(categories),
                total_items=len(items_data)
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
            now = datetime.now()
            category_data = {
                "id": str(uuid.uuid4()),
                "name": request.name,
                "description": request.description,
                "sort_order": request.sort_order,
                "is_active": True,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            if self.storage.save_category(category_data):
                category = InstructionCategory(**category_data, items=[])
                return ApiResponse(
                    success=True,
                    data=category,
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
            category = self.storage.get_category_by_id(request.category_id)
            if not category:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指定的分类不存在"
                )
            
            now = datetime.now()
            # 将InstructionParameter对象转换为字典
            params_dict = [param.dict() for param in request.params] if request.params else []
            
            item_data = {
                "id": str(uuid.uuid4()),
                "name": request.name,
                "icon": request.icon,
                "description": request.description,
                "category_id": request.category_id,
                "python_script": request.python_script,
                "sort_order": request.sort_order,
                "is_active": True,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "params": params_dict
            }
            
            if self.storage.save_item(item_data):
                item = InstructionItem(**item_data)
                return ApiResponse(
                    success=True,
                    data=item,
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
            category_data = self.storage.get_category_by_id(category_id)
            if not category_data:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="分类不存在"
                )
            
            # 更新字段
            if request.name is not None:
                category_data['name'] = request.name
            if request.description is not None:
                category_data['description'] = request.description
            if request.sort_order is not None:
                category_data['sort_order'] = request.sort_order
            if request.is_active is not None:
                category_data['is_active'] = request.is_active
            
            category_data['updated_at'] = datetime.now().isoformat()
            
            if self.storage.save_category(category_data):
                category = InstructionCategory(**category_data, items=[])
                return ApiResponse(
                    success=True,
                    data=category,
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
            item_data = self.storage.get_item_by_id(item_id)
            if not item_data:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令项目不存在"
                )
            
            # 如果要更新分类，验证新分类是否存在
            if request.category_id is not None:
                category = self.storage.get_category_by_id(request.category_id)
                if not category:
                    return ApiResponse(
                        success=False,
                        data=None,
                        message="指定的分类不存在"
                    )
            
            # 更新字段
            if request.name is not None:
                item_data['name'] = request.name
            if request.icon is not None:
                item_data['icon'] = request.icon
            if request.description is not None:
                item_data['description'] = request.description
            if request.category_id is not None:
                item_data['category_id'] = request.category_id
            if request.sort_order is not None:
                item_data['sort_order'] = request.sort_order
            if request.is_active is not None:
                item_data['is_active'] = request.is_active
            if request.python_script is not None:
                item_data['python_script'] = request.python_script
            if request.params is not None:
                # 将InstructionParameter对象转换为字典
                item_data['params'] = [param.dict() for param in request.params]
            
            item_data['updated_at'] = datetime.now().isoformat()
            
            if self.storage.save_item(item_data):
                item = InstructionItem(**item_data)
                return ApiResponse(
                    success=True,
                    data=item,
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
            if self.storage.delete_category(category_id):
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
            if self.storage.delete_item(item_id):
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
            item = self.storage.get_item_by_id(request.instruction_id)
            if not item:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令不存在"
                )
            
            # 检查指令是否启用
            if not item.get('is_active', True):
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令已禁用"
                )
            
            # 获取Python脚本
            python_script = item.get('python_script')
            if not python_script:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="指令未配置Python脚本"
                )
            
            # 查找direction为1的输出参数
            result_variable_name = ''
            params = item.get('params', [])
            for param in params:
                if param.get('direction') == 1:
                    result_variable_name = param.get('name', '')
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
                item = self.storage.get_item_by_id(request.instruction_id)
                if item:
                    params = item.get('params', [])
                    for param in params:
                        if param.get('direction') == 1:
                            result_variable_name = param.get('name', '')
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