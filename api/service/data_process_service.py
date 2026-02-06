#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理流程服务
管理数据处理流程的保存、查询、删除等功能
"""

import os
import json
import uuid
import base64
import ast
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import deque

from config import config
from dto.instruction_dto import DataProcessFlow, SaveDataProcessFlowRequest, SaveDataProcessFlowResponse
from service.base_service import BaseService
from service.result import Result
from repository.instruction_item_repository import InstructionItemRepository
from repository.instruction_parameter_repository import InstructionParameterRepository
from repository.data_process_repository import DataProcessRepository
from repository.execution_record_repository import ExecutionRecordRepository
from utils.python_script_utils import PythonScriptUtils
from utils.common import CommonUtils
from utils.data_heler import data_helper
from utils.json_helper import json_helper
from utils.execution_terminator import execution_terminator
import inspect
import shutil


class DataProcessService(BaseService):
    """数据处理流程服务类"""
    
    def __init__(self, instruction_item_repo: InstructionItemRepository = None, instruction_parameter_repo: InstructionParameterRepository = None, data_process_repo: DataProcessRepository = None, execution_record_repo: ExecutionRecordRepository = None):
        """初始化数据处理流程服务
        
        Args:
            instruction_item_repo: 指令项目仓储实例，将通过依赖注入获取
            instruction_parameter_repo: 指令参数仓储实例，将通过依赖注入获取
            data_process_repo: 数据流程仓储实例，将通过依赖注入获取
            execution_record_repo: 执行记录仓储实例，将通过依赖注入获取
        """
        # 注入仓储实例
        self.instruction_item_repo = instruction_item_repo
        self.instruction_parameter_repo = instruction_parameter_repo
        self.data_process_repo = data_process_repo
        self.execution_record_repo = execution_record_repo    
    
    def _extract_user_functions_from_ast(self, script: str) -> List[str]:
        """通过AST解析提取脚本中所有def定义的函数名称"""
        tree = ast.parse(script)
        func_names = []
        for node in ast.walk(tree):
            # 识别函数定义节点（def）
            if isinstance(node, ast.FunctionDef):
                func_names.append(node.name)
            # 识别异步函数定义节点（async def）
            elif isinstance(node, ast.AsyncFunctionDef):
                func_names.append(node.name)
        return func_names
    
    def _filter_functions_by_params(
        self, 
        globals_env: Dict[str, Any], 
        func_names: List[str], 
        target_params: Dict[str, Any]
    ) -> List[tuple[str, Any]]:
        """筛选参数与target_params完全匹配的函数"""
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
    
    def _convert_params_by_type_annotations(
        self, 
        signature: inspect.Signature, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据函数参数的类型注解转换参数类型"""
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
    
    async def save_data_process_flow(self, flow: DataProcessFlow) -> Result[SaveDataProcessFlowResponse]:
        """
        保存数据处理流程        
        Args:
            flow: 数据处理流程对象            
        Returns:
            Result[SaveDataProcessFlowResponse]: 保存结果
        """
        try:
            from entity.data_process import DataProcess
            from entity.process_node import ProcessNode
            from entity.process_edge import ProcessEdge
            
            # 生成或使用现有ID
            flow_id = flow.id or str(uuid.uuid4())
            
            # 设置时间戳
            now = datetime.now()
            if not flow.createdAt:
                flow.createdAt = now
            flow.updatedAt = now
            
            # 转换为Pydantic实体对象
            nodes = []
            for node in flow.nodes:
                nodes.append(ProcessNode(
                    id=node.id,
                    flow_id=flow_id,  # 添加flow_id字段
                    instruction_id=node.instructionId,
                    name=node.name,
                    description=node.description,
                    x=node.x,
                    y=node.y,
                    params=node.params,
                    input_types=getattr(node, 'input_types', {})  # 添加输入类型字段，默认空字典
                ))
            
            edges = []
            for edge in flow.edges:
                edges.append(ProcessEdge(
                    id=edge.id,
                    flow_id=flow_id,  # 添加flow_id字段
                    source=edge.source,
                    target=edge.target,
                    label=edge.label,
                    logic_express=edge.logic_express
                ))
            
            data_process = DataProcess(
                id=flow_id,
                name=flow.name,
                description=flow.description,
                nodes=nodes,
                edges=edges,
                created_at=flow.createdAt.isoformat() if isinstance(flow.createdAt, datetime) else flow.createdAt,
                updated_at=flow.updatedAt.isoformat() if isinstance(flow.updatedAt, datetime) else flow.updatedAt
            )
            
            # 使用仓储保存流程
            # 检查流程是否已存在（异步执行数据库操作）
            existing_process = await self.data_process_repo.find_by_id(flow_id)
            if existing_process:
                # 流程已存在，使用update方法
                update_result = await self.data_process_repo.update(data_process)
                if update_result:
                    response = SaveDataProcessFlowResponse(
                        id=flow_id,
                        message=f"流程 '{flow.name}' 更新成功",
                        success=True
                    )
                    return Result.success(response)
                else:
                    return Result.fail("更新流程失败，请稍后重试")
            else:
                # 流程不存在，使用add方法
                add_result = await self.data_process_repo.add(data_process)
                if add_result:
                    response = SaveDataProcessFlowResponse(
                        id=flow_id,
                        message=f"流程 '{flow.name}' 保存成功",
                        success=True
                    )
                    return Result.success(response)
                else:
                    return Result.fail("保存流程失败，请稍后重试")
                
        except Exception as e:
            return Result.fail(f"保存流程失败: {str(e)}")
    
    async def get_data_process_flow(self, flow_id: str) -> Result[DataProcessFlow]:
        """
        获取指定的数据处理流程
        
        Args:
            flow_id: 流程ID
            
        Returns:
            Result[DataProcessFlow]: 流程对象
        """
        try:
            # 使用仓储获取流程（异步执行数据库操作）
            process = await self.data_process_repo.find_by_id(flow_id)
            if not process:
                return Result.fail(f"流程ID '{flow_id}' 不存在")
            
            # 转换为DataProcessFlow对象
            flow_dict = {
                "id": process.id,
                "name": process.name,
                "description": process.description,
                "nodes": [{
                    "id": node.id,
                    "instructionId": node.instruction_id,
                    "name": node.name,
                    "description": node.description,
                    "x": node.x,
                    "y": node.y,
                    "params": node.params,
                    "input_types": node.input_types
                } for node in process.nodes],
                "edges": [{
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "logic_express": edge.logic_express
                } for edge in process.edges],
                "createdAt": datetime.fromisoformat(process.created_at),
                "updatedAt": datetime.fromisoformat(process.updated_at)
            }
            
            flow = DataProcessFlow(**flow_dict)
            return Result.success(flow)
            
        except Exception as e:
            return Result.fail(f"获取流程失败: {str(e)}")
    

    
    async def get_all_data_process_flows(self) -> Result[List[DataProcessFlow]]:
        """
        获取所有保存的数据处理流程
        
        Returns:
            Result[List[DataProcessFlow]]: 流程列表
        """
        try:
            # 使用仓储获取所有流程（异步执行数据库操作）
            processes = await self.data_process_repo.find_all()
            flow_list = []
            
            for process in processes:
                # 转换为DataProcessFlow对象
                flow_dict = {
                    "id": process.id,
                    "name": process.name,
                    "description": process.description,
                    "nodes": [{
                        "id": node.id,
                        "instructionId": node.instruction_id,
                        "name": node.name,
                        "description": node.description,
                        "x": node.x,
                        "y": node.y,
                        "params": node.params,
                        "input_types": node.input_types
                    } for node in process.nodes],
                    "edges": [{
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "label": edge.label,
                        "logic_express": edge.logic_express
                    } for edge in process.edges],
                    "createdAt": datetime.fromisoformat(process.created_at),
                    "updatedAt": datetime.fromisoformat(process.updated_at)
                }
                
                flow = DataProcessFlow(**flow_dict)
                flow_list.append(flow)
            
            # 按更新时间倒序排列
            flow_list.sort(key=lambda x: x.updatedAt or x.createdAt or datetime.min, reverse=True)
            
            return Result.success(flow_list)
            
        except Exception as e:
            return Result.fail(f"获取流程失败: {str(e)}")
            
    async def delete_data_process_flow(self, flow_id: str) -> Result[bool]:
        """
        删除指定的数据处理流程
        
        Args:
            flow_id: 流程ID
            
        Returns:
            Result[bool]: 删除结果
        """
        try:
            # 检查流程是否存在（异步执行数据库操作）
            existing_process = await self.data_process_repo.find_by_id(flow_id)
            if not existing_process:
                return Result.fail(f"流程ID '{flow_id}' 不存在")
            
            # 使用仓储删除流程（异步执行数据库操作）
            delete_result = await self.data_process_repo.delete(flow_id)
            if delete_result:
                return Result.success(True)
            else:
                return Result.fail("删除流程失败，请稍后重试")
                
        except Exception as e:
            return Result.fail(f"删除流程失败: {str(e)}")
    def get_flow_execution_order(self, flow: DataProcessFlow, start_node_id: str) -> List[str]:
        """
        获取数据处理流程的执行顺序
        使用深度优先搜索进行拓扑排序
        
        Args:
            flow: 数据处理流程对象
            start_node_id: 开始节点ID
            
        Returns:
            List[str]: 节点ID的执行顺序列表
        """
        # 构建边信息字典：{source: [{target, logic_express}]}
        edges_info: Dict[str, List[Dict[str, str]]] = {}
        for edge in flow.edges:
            if edge.source not in edges_info:
                edges_info[edge.source] = []
            edges_info[edge.source].append({
                'target': edge.target,
                'logic_express': edge.logic_express
            })
        
        # DFS 拓扑排序
        visited = set()
        execution_order = []
        
        def dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            # 先处理所有后继节点
            if node_id in edges_info:
                for edge_info in edges_info[node_id]:
                    # 无论边是否有标签，都添加到执行顺序中
                    # 实际的条件判断将在execute_data_process_flow中进行
                    dfs(edge_info['target'])
            
            # 回溯时加入当前节点（逆序）
            execution_order.append(node_id)
        
        # 从 start_node_id 开始 DFS
        dfs(start_node_id)
        
        return execution_order[::-1]  # 反转得到正确顺序
    
    async def get_nodes_before_target(self, flow: DataProcessFlow, target_node_id: str) -> Result[List[Dict[str, Any]]]:
        """
        获取目标节点之前的所有节点及其变量信息
        
        Args:
            flow: 数据处理流程对象
            target_node_id: 目标节点ID
            
        Returns:
            Result[List[Dict[str, Any]]]: 包含节点信息和变量的列表
        """
        try:
            # 构建节点ID到节点的映射
            node_map = {node.id: node for node in flow.nodes}
            
            # 验证目标节点是否存在
            if target_node_id not in node_map:
                return Result.fail(f"目标节点ID '{target_node_id}' 不存在")
            
            # 构建边的字典表示（反向）
            reverse_edges_dict = {}
            for edge in flow.edges:
                if edge.target not in reverse_edges_dict:
                    reverse_edges_dict[edge.target] = []
                reverse_edges_dict[edge.target].append(edge.source)
            
            # 使用列表收集所有前置节点ID
            before_node_ids = []
            visited = set()
            
            # 使用DFS找到所有可以到达目标节点的前置节点
            def dfs_find_predecessor_ids(current_id):
                # 如果当前节点是目标节点，不添加到前置节点列表
                if current_id == target_node_id:
                    return
                
                if current_id in visited:
                    return
                
                visited.add(current_id)
                
                # 继续递归查找前置节点
                if current_id in reverse_edges_dict:
                    for predecessor_id in reverse_edges_dict[current_id]:
                        dfs_find_predecessor_ids(predecessor_id)
            
            # 从目标节点的所有直接前置节点开始搜索
            if target_node_id in reverse_edges_dict:
                for predecessor_id in reverse_edges_dict[target_node_id]:
                    dfs_find_predecessor_ids(predecessor_id)
            
            # 递归查找所有前置节点
            # 遍历已找到的节点，继续查找它们的前置节点
            visited_copy = visited.copy()
            for current_id in visited_copy:
                if current_id in reverse_edges_dict:
                    for predecessor_id in reverse_edges_dict[current_id]:
                        if predecessor_id not in visited:
                            dfs_find_predecessor_ids(predecessor_id)
            
            # 找到所有没有入边的节点（源节点）
            source_nodes = []
            all_nodes = set(node_map.keys())
            for node_id in visited:
                if node_id not in reverse_edges_dict:
                    source_nodes.append(node_id)
            
            # 计算每个节点到目标节点直接前置节点的层级（从目标节点向前追溯的距离）
            def get_node_level(node_id, reverse_edges, level_cache):
                if node_id in level_cache:
                    return level_cache[node_id]
                
                # 如果节点是目标节点的直接前驱，层级为0
                if target_node_id in reverse_edges and node_id in reverse_edges[target_node_id]:
                    level_cache[node_id] = 0
                    return 0
                
                # 否则，层级 = 所有后继节点层级最大值 + 1
                max_level = 0
                # 查找所有以当前节点为前驱的节点（后继节点）
                for successor_id, predecessors in reverse_edges.items():
                    if node_id in predecessors:
                        if successor_id in visited:
                            level = get_node_level(successor_id, reverse_edges, level_cache)
                            max_level = max(max_level, level + 1)
                
                level_cache[node_id] = max_level
                return max_level
            
            level_cache = {}
            node_levels = {}
            for node_id in visited:
                level = get_node_level(node_id, reverse_edges_dict, level_cache)
                node_levels[node_id] = level
            
            # 按层级降序排序（从目标节点的直接前置节点开始，向源节点方向追溯）
            # 层级相同的按节点ID降序排序确保稳定性
            before_node_ids = sorted(visited, key=lambda x: (-node_levels[x], x), reverse=True)
            
            # 然后获取每个节点的详细信息
            before_nodes = []
            for current_id in before_node_ids:
                # 获取当前节点
                node = node_map[current_id]
                
                # 构建节点信息和变量
                node_info = {
                    "node_id": node.id,
                    "instruction_id": node.instructionId,
                    "node_name": getattr(node, 'name', f'Node {node.id}'),
                    "variables": []
                }
                
                # 收集节点的参数作为变量
                if hasattr(node, 'params') and node.params:
                    # 从数据库获取当前节点指令的参数配置（异步执行数据库操作）
                    instruction_params = await self.instruction_parameter_repo.find_by_instruction_id(node.instructionId)
                    # 构建参数名到label的映射
                    param_labels = {param.name: param.label for param in instruction_params}
                    
                    for param_name, param_value in node.params.items():
                        # 生成变量名格式：{{node.id.paramName}}
                        variable_name = f"{{{{{node.id}.{param_name}}}}}"
                        # 优先使用从数据库获取的label，找不到则回退到参数名
                        variable_label = param_labels.get(param_name, param_name)
                        node_info["variables"].append({
                            "name": variable_name,
                            "label": variable_label,
                            "value": param_value
                        })
                
                before_nodes.append(node_info)
            
            return Result.success(before_nodes)
            
        except Exception as e:
            return Result.fail(f"获取前置节点信息失败: {str(e)}")
    

    
    def record_execution_result(self, flow_id: str, flow_name: str, execution_result: Dict[str, Any], success: bool, error_message: str = None, execution_time: float = 0) -> bool:
        """
        记录流程执行结果和状态
        
        Args:
            flow_id: 流程ID
            flow_name: 流程名称
            execution_result: 执行结果数据
            success: 是否执行成功
            error_message: 错误信息（如果有）
            execution_time: 执行时间（秒）
            
        Returns:
            bool: 记录是否成功
        """
        try:
            from entity.execution_record import ExecutionRecord
            from entity.execution_result import ExecutionResult as ExecutionResultData
            
            # 创建执行结果数据对象
            result_data = ExecutionResultData(
                flow_id=flow_id,
                flow_name=flow_name,
                final_result=execution_result.get('final_result',None) if execution_result else None
            )
            
            # 创建执行记录对象
            exec_record = ExecutionRecord(
                id=str(uuid.uuid4()),
                flow_id=flow_id,
                flow_name=flow_name,
                success=success,
                error_message=error_message,
                execution_time=execution_time,
                executed_at=datetime.now().isoformat(),
                result_data=result_data
            )
            
            # 使用仓储保存执行记录
            return self.execution_record_repo.add(exec_record)
        except Exception as e:
            return False
    
    async def execute_data_process_flow(self, flow: DataProcessFlow, start_node_id: str, end_node_ids: List[str] = None,flow_mode=0) -> Result[Dict[str, Any]]:
        """
        执行数据处理流程
        根据连线标签文本的判断条件，查找满足条件第一条执行路径，作为当前执行流程的唯一有效执行流程
        
        Args:
            flow: 数据处理流程对象
            start_node_id: 开始节点ID
            end_node_ids: 结束节点ID列表，用于控制流程终止
            flow_mode:流程触发模式，0表示调试模式、1表示执行模式，默认为调试模式
            
        Returns:
            Result[Dict[str, Any]]: 执行结果，包含已执行节点的结果和失败信息（如果有）
        """
        # 初始化
        actual_execution_order = [] # 实际执行顺序列表
        processed_final_result = None # 最终执行结果
        current_run_node_io_info = None # 当前执行节点的输入输出信息
        try:
            flow_time_begin=datetime.now()
            flow_status= execution_terminator.STATUS_RUNNING
            # 构建节点ID到节点的映射
            node_map = {node.id: node for node in flow.nodes}
            current_node_id = start_node_id
            
            # 构建正向边信息字典：{source: [{target, logic_express}]}
            edges_info: Dict[str, List[Dict[str, str]]] = {}
            for edge in flow.edges:
                if edge.source not in edges_info:
                    edges_info[edge.source] = []
                edges_info[edge.source].append({
                    'target': edge.target,
                    'logic_express': edge.logic_express
                })
            
            # 创建流程目录，用于保存节点参数信息JSON文件，路径格式为：流程id/flow_time_begin.strftime("%y%m%d%H%M%S")或调试模式debug/节点id.json
            flow_directory = os.path.join(config.DATA_PROCESSES_FOLDER, 'process_flows', flow.id, flow_time_begin.strftime("%y%m%d%H%M%S") if flow_mode else 'debug')
            shutil.rmtree(flow_directory, ignore_errors=True) # 删除目录，适用于flow_mode为调试模式的情况
            os.makedirs(flow_directory, exist_ok=True)
            
            # 重置流程状态和终止标志
            execution_terminator.reset_flow(flow.id)
            # 清空流程所有节点执行状态
            execution_terminator.clear_node_status(flow.id)
            # 设置流程状态为运行中
            execution_terminator.set_flow_status(flow.id, flow_status)
            
            while not current_node_id in end_node_ids or not current_node_id in actual_execution_order:
                import asyncio
                await asyncio.sleep(0.01)
                # 如果当前节点不是结束节点，或没有执行过，就继续执行
                actual_execution_order.append(current_node_id)
                
                execution_time_begin=datetime.now()
                # 获取节点指令脚本 
                current_node = node_map[current_node_id]  
                # 初始化节点参数信息
                current_run_node_io_info = {
                    "node_id": current_node_id,
                    "instruction_id": current_node.instructionId,
                    "flow_mode": flow_mode,
                    "execution_time_begin": execution_time_begin.strftime("%Y-%m-%d %H:%M:%S"),
                    "execution_time_end":None,
                    "params_in":{},
                    "params_ref":{},# 回写参数
                    "params_out":{},
                    "message":""
                }  
                processed_final_result=None
                # 节点运行状态
                node_status_info = {
                    "node_id": current_node_id,
                    "status": 0,  # 0表示运行中，1表示执行成功，2表示执行失败
                    "json_filepath": None,
                    "execution_time_begin": execution_time_begin.strftime("%Y-%m-%d %H:%M:%S"),     
                    "execution_time_end":None,
                    "flow_mode": flow_mode,
                    "message":""
                }
                try:    
                    # 检查是否需要终止执行
                    if execution_terminator.should_terminate(flow.id):
                        current_run_node_io_info["message"]="流程执行被用户终止"
                        current_run_node_io_info["params_in"]=current_node.params if current_node_id in node_map else {}
                        node_status_info["status"]=2
                        # 设置流程状态为终止 
                        flow_status= execution_terminator.STATUS_TERMINATED
                        execution_terminator.set_flow_status(flow.id, flow_status)
                    else:
                        # 设置节点初始状态为运行中
                        execution_terminator.set_node_status(flow.id, current_node_id, node_status_info)                      
                        # 异步获取指令信息（避免阻塞事件循环）
                        instruction_info = await self.instruction_item_repo.find_by_id(current_node.instructionId)                
                        if not instruction_info:
                            raise Exception(f"未找到指令ID: {current_node.instructionId}")                
                        python_script = instruction_info.python_script

                        # 解析当前节点参数中的变量
                        input_types=(current_node.input_types or {}).get('e', [])
                        resolved_params = {}
                        node_params_dict_from_jsons: Dict[str, Any] = {} # 保存到json文件中的，当前节点动态参数相关的参数字典信息，key为节点id，value为json文件中的内容
                        for param_name, param_value in current_node.params.items():
                            # 解析节点参数中的变量
                            if isinstance(param_value, str):
                                result = param_value
                                # 使用正则表达式查找所有{{节点id.变量名}}格式的变量
                                import re
                                matches = re.findall(r'\{\{([^}]*)\}\}', param_value)
                                
                                for match in matches:
                                    if '.' in match:
                                        node_id_part, var_name = match.split('.', 1)
                                        # 从json文件中获取参数值
                                        if node_id_part not in node_params_dict_from_jsons:
                                            node_params_json=json_helper.read_json_file(os.path.join(flow_directory, f"{node_id_part}.json"))
                                            node_params_dict_from_jsons[node_id_part] =  {**node_params_json["params_in"],**node_params_json["params_ref"],  **node_params_json["params_out"]}
                                        placeholder = f"{{{{{match}}}}}"
                                        ref_v=node_params_dict_from_jsons[node_id_part].get(var_name, None)
                                        if placeholder==param_value:
                                            result = ref_v
                                        else:
                                            result = result.replace(placeholder, str(ref_v))
                                resolved_params[param_name] = result
                            else:
                                resolved_params[param_name] = param_value
                            # 如果是表达式类型参数，执行表达式，结果赋值给当前变量
                            if param_name in input_types:
                                # 表达式解析
                                try:
                                    processed_value = eval(resolved_params[param_name])
                                    resolved_params[param_name] = processed_value
                                except Exception as e:
                                    resolved_params[param_name] = param_value 
                        # 获取节点对应指令的参数信息（异步执行数据库操作）
                        input_params = {}
                        back_param_name = None
                        output_param_name = None
                        instruction_parameters = await self.instruction_parameter_repo.find_by_instruction_id(current_node.instructionId)
                        # 遍历指令参数，将解析后的参数变量转换类型，对未同步更新的参数赋予默认值（指令中的参数为最新，以指令为标准）
                        for param in instruction_parameters:
                            if param.direction == 0:  # 输入参数
                                if param.name in resolved_params:
                                    value=resolved_params[param.name]
                                    # 值类型转换
                                    value=data_helper.convert_value(value, param.value_type)
                                    # 存在时，重新赋值
                                    input_params[param.name] = value 
                                else:
                                    # 不存在时，使用指令中参数的默认值
                                    input_params[param.name] = param.default_value                        
                            elif param.direction ==1:  # 输出参数
                                output_param_name = param.name                            
                            elif param.direction ==2:  # 回写参数
                                back_param_name = param.name 
                        
                        # 更新节点输入参数信息
                        current_run_node_io_info["params_in"]=input_params
                        # 执行节点指令脚本（异步执行，避免阻塞事件循环）
                        import asyncio
                        processed_final_result = await asyncio.to_thread(PythonScriptUtils._execute_python_script, python_script, input_params)                    
                        
                        # 回写参数
                        if back_param_name:  # 回写参数
                            temp_key=current_node.params.get(back_param_name,'')                            
                            import re
                            matches = re.findall(r'\{\{([^}]*)\}\}', temp_key)
                            
                            for match in matches:
                                if '.' in match:
                                    node_id_part, var_name = match.split('.', 1)
                                    # 为当前节点的回写参数赋值
                                    current_run_node_io_info["params_ref"]={var_name:processed_final_result}
                                    # 为回写参数中的节点参数赋值
                                    instruction_parameters = await self.instruction_parameter_repo.find_by_instruction_id(node_map[current_node_id].instructionId)                                    
                                    direction = next((item.direction for item in instruction_parameters if item.name == var_name),None)
                                    attr_name="params_ref" if direction == 2 else "params_out" if direction == 1 else "params_in"
                                    node_params_dict_from_jsons[node_id_part][var_name]=processed_final_result
                                    # 更新json文件中的回写参数值
                                    if temp_key and node_params_dict_from_jsons[node_id_part].get(var_name,''):                                        
                                        json_helper.update_json_file(os.path.join(flow_directory, f"{node_id_part}.json"), f"{attr_name}.{var_name}", processed_final_result)

                        # 更新节点输出参数信息
                        if output_param_name:
                            current_run_node_io_info["params_out"]={output_param_name:processed_final_result}
                        current_run_node_io_info["message"]="success"
                        node_status_info["status"]=1
                        node_status_info["message"]="success"
                except Exception as e:
                    # 记录失败节点信息
                    current_run_node_io_info["message"]=str(e)  
                    node_status_info["status"]=2   
                    node_status_info["message"]=str(e)
                finally:
                    execution_time_end=datetime.now()
                    current_run_node_io_info["execution_time_end"]=execution_time_end.strftime("%Y-%m-%d %H:%M:%S")
                    # 每个节点id生成一个JSON文件
                    json_filepath = os.path.join(flow_directory, f"{current_node_id}.json")
                    
                    # 写入JSON文件
                    # serialized_node_io_info = CommonUtils.deep_serialize(current_run_node_io_info)
                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        # json.dump(serialized_node_io_info, f, ensure_ascii=False, indent=2)
                        json.dump(current_run_node_io_info, f, ensure_ascii=False, indent=2)
                    
                    # 更新节点执行状态信息
                    node_status_info["execution_time_end"]=execution_time_end.strftime("%Y-%m-%d %H:%M:%S")
                    node_status_info["json_filepath"]=json_filepath
                    
                    # execution_terminator保存节点状态
                    execution_terminator.set_node_status(flow.id, current_node_id, node_status_info)

                    if node_status_info["status"]==2:
                        # 如果当前节点执行失败,设置流程状态为失败
                        flow_status= execution_terminator.STATUS_FAILED
                        execution_terminator.set_flow_status(flow.id, flow_status)
                        raise Exception(f"节点执行失败: {current_node_id}，错误信息: {current_run_node_io_info["message"]}")
                    # 检查当前节点是否有出边
                    if current_node_id not in edges_info:
                        break
                    
                    # 获取下一个节点
                    next_node_id = self.find_next_node_id(current_node_id,output_param_name, edges_info, node_params_dict_from_jsons,flow_directory)

                    if current_node_id ==next_node_id:
                        break
                    # 更新下一个节点为当前节点
                    current_node_id = next_node_id

            # 3. 处理最终节点的执行结果，特别是文件下载相关            
            # 检查是否是BytesIO类型（可能来自文件下载指令）
            if isinstance(processed_final_result, BytesIO):
                try:
                    # 重置文件指针
                    processed_final_result.seek(0)
                    # 读取内容并进行base64编码
                    file_data = processed_final_result.read()
                    base64_encoded = base64.b64encode(file_data).decode('utf-8')
                    
                    # 尝试从文件名参数或默认值获取文件名
                    file_name = "downloaded_file.bin"
                    
                    # 构建标准的文件流响应格式
                    processed_final_result = {
                        "file_name": file_name,
                        "file_data": base64_encoded,
                        "content_type": "application/octet-stream",
                        "file_size": len(file_data)
                    }
                except Exception as e:
                    print(f"处理文件流失败: {str(e)}")
                    processed_final_result = {"error": str(e)}
            # 检查是否已经是标准的文件流响应格式（来自download_file_to_base64_dict函数）
            elif isinstance(processed_final_result, dict) and "file_data" in processed_final_result:
                # 已经是正确的格式，直接使用
                processed_final_result = processed_final_result
            # 检查是否是错误格式
            elif isinstance(processed_final_result, dict) and "error" in processed_final_result:
                print(f"文件处理错误: {processed_final_result.get('error')}")
                processed_final_result = processed_final_result
            
            # 确保返回有效的结果，而不是空数组或None
            if processed_final_result is None or processed_final_result == []:
                processed_final_result = {"message": "执行成功，但未返回数据"}
            
            # 确保final_result不是空数组
            if "final_result" in locals() and (final_result is None or final_result == []):
                final_result = {"message": "执行成功，但返回数据异常"}
            
            # 使用CommonUtils的深度序列化方法处理结果
            # processed_final_result = CommonUtils.deep_serialize(processed_final_result)    
            
            # 构建最终返回结果
            final_result = {
                "flow_id": flow.id,
                "flow_name": flow.name,
                "final_result": processed_final_result if processed_final_result else current_run_node_io_info,
                "execution_order": actual_execution_order,
                "total_nodes_executed": len(actual_execution_order)
            }
            
            # 执行结束，根据结果设置状态
            if flow_status != execution_terminator.STATUS_FAILED:
                flow_status=execution_terminator.STATUS_COMPLETED
                # 没有失败信息，说明执行成功
                execution_terminator.set_flow_status(flow.id, execution_terminator.STATUS_COMPLETED)
                return Result.success(final_result)
            
            # 执行结束后清除终止标志
            execution_terminator.clear_terminate_flag(flow.id)
            return Result.fail(f"执行流程失败: 未到达结束节点", final_result)                
            
        except Exception as e:            
            error_result = {
                "flow_id": flow.id,
                "flow_name": flow.name,
                "final_result": processed_final_result if processed_final_result else str(e),
                "execution_order": actual_execution_order,
                "total_nodes_executed": len(actual_execution_order)
            }
            
            return Result.fail(f"执行流程失败: {str(e)}", error_result)
    def find_next_node_id(self, current_node_id: str,output_param_name: str, edges_info: Dict[str, List[Dict[str, str]]], node_params_dict_from_jsons: Dict[str, Any], flow_directory: str) -> Optional[str]:
        """
        根据当前节点ID和目标节点ID，返回下一个节点ID
        
        Args:
            current_node_id: 当前节点ID
            output_param_name: 当前节点输出参数属性名
            edges_info: 边信息字典
            node_params_dict_from_jsons: 处理结果字典
            
        Returns:
            Optional[str]: 下一个节点ID，如果未找到则返回None
        """
        # 检查当前节点是否有出边
        if current_node_id not in edges_info:
            print(f"当前节点 {current_node_id} 没有出边，流程结束")
            return None
        
        # 遍历当前节点的所有出边，寻找满足条件的第一条路径
        found_next_node = False
        for edge_info in edges_info[current_node_id]:
            target_node_id = edge_info['target']
            edge_logic_express = edge_info['logic_express']                    
            
            # 如果边没有逻辑表达式，则默认满足条件，返回目标节点ID
            if not edge_logic_express:
                return target_node_id
            else:
                # 替换边逻辑表达式中的变量
                resolved_logic_express = edge_logic_express
                if isinstance(edge_logic_express, str):
                    import re
                    matches = re.findall(r'\{\{([^}]*)\}\}', edge_logic_express)                    
                    for match in matches:
                        if '.' in match:
                            node_id_part, var_name = match.split('.', 1)
                            # 从json文件中获取参数值
                            if node_id_part not in node_params_dict_from_jsons:
                                node_params_json=json_helper.read_json_file(os.path.join(flow_directory, f"{node_id_part}.json"))
                                node_params_dict_from_jsons[node_id_part] =  {**node_params_json["params_in"],**node_params_json["params_ref"],  **node_params_json["params_out"]}
                            placeholder = f"{{{{{match}}}}}"
                            ref_v=node_params_dict_from_jsons[node_id_part].get(var_name, None)
                            resolved_logic_express = resolved_logic_express.replace(placeholder, str(ref_v))
                
                # 构建条件表达式并评估
                try:
                    # 构建条件表达式的上下文环境
                    context = {}
                    condition_satisfied=False
                    # 添加当前节点的输出值到上下文
                    if output_param_name:
                        source_output_key = f"{current_node_id}.{output_param_name}"
                        if source_output_key in node_params_dict_from_jsons[current_node_id]:
                            context['output'] = node_params_dict_from_jsons[current_node_id][source_output_key]
                            context['value'] = node_params_dict_from_jsons[current_node_id][source_output_key]
                    
                    # 检查是否是简单的比较表达式
                    if resolved_logic_express.startswith('==') or resolved_logic_express.startswith('!=') or \
                        resolved_logic_express.startswith('>') or resolved_logic_express.startswith('<') or \
                        resolved_logic_express.startswith('>=') or resolved_logic_express.startswith('<='):
                        # 构建完整的表达式
                        expr = f"value {resolved_logic_express}"
                        print(f"执行条件表达式: {expr}")
                        condition_satisfied = eval(expr, {}, context)
                    else:
                        try:             
                            print(eval(resolved_logic_express, {}, {}))                           
                            condition_satisfied = eval(resolved_logic_express, {}, {})
                        except Exception as e:
                            # 直接比较值
                            if 'value' in context:
                                condition_satisfied = str(context['value']) == resolved_logic_express
                                print(f"直接比较: 值 '{context['value']}' {'==' if condition_satisfied else '!='} 标签 '{resolved_logic_express}'")
                            else:
                                condition_satisfied = False
                                print(f"无法比较: 当前节点没有输出值或表达式错误 ({str(e)})")
                    
                    if condition_satisfied:
                        return target_node_id
                    else:
                        print(f"条件不满足，跳过目标节点 {target_node_id}")
                except Exception as e:
                    print(f"条件表达式解析错误: {str(e)}")
        
        # 如果没有找到满足条件的下一个节点，结束流程
        if not found_next_node:
            return None
    
    async def execute_data_process_flow_by_id(self, flow_id: str) -> Result[Dict[str, Any]]:
        """
        根据流程ID执行数据处理流程
        
        Args:
            flow_id: 流程ID
            
        Returns:
            Result[Dict[str, Any]]: 执行结果
        """
        try:
            # 获取流程信息
            flow_result = await self.get_data_process_flow(flow_id)
            if not flow_result.success:
                return Result.fail(flow_result.error)
            
            flow = flow_result.data
            
            # 构建边的字典表示和节点连接关系
            edges_dict = {}
            source_nodes = set()
            target_nodes = set()
            
            for edge in flow.edges:
                if edge.source not in edges_dict:
                    edges_dict[edge.source] = []
                edges_dict[edge.source].append(edge.target)
                
                source_nodes.add(edge.source)
                target_nodes.add(edge.target)
            
            # 确定开始节点：没有入边的节点（不在target_nodes中的节点）
            node_ids = {node.id for node in flow.nodes}
            start_nodes = [node for node in flow.nodes if node.id not in target_nodes]
            
            if not start_nodes:
                return Result.fail("流程必须包含开始节点（没有入边的节点）")
            if len(start_nodes) > 1:
                return Result.fail("流程只能有一个开始节点（没有入边的节点）")
            
            start_node = start_nodes[0]
            
            # 确定结束节点：没有出边的节点（不在source_nodes中的节点）
            end_nodes = [node for node in flow.nodes if node.id not in source_nodes]
            end_node_ids = [node.id for node in end_nodes]
            
            # 执行流程
            return await self.execute_data_process_flow(flow, start_node.id, end_node_ids)
            
        except Exception as e:
            return Result.fail(f"执行流程失败: {str(e)}")
    
    async def get_execution_history(self, flow_id: str = None) -> Result[List[Dict[str, Any]]]:
        """
        获取流程执行历史
        
        Args:
            flow_id: 可选，流程ID，指定则只返回该流程的执行历史
            
        Returns:
            Result[List[Dict[str, Any]]]: 执行历史记录列表
        """
        try:
            # 使用仓储获取执行历史记录（异步执行数据库操作）
            if flow_id:
                records = await self.execution_record_repo.find_by_flow_id(flow_id)
            else:
                records = await self.execution_record_repo.find_all()
            
            # 转换为字典列表
            history = []
            for record in records:
                record_dict = {
                    "id": record.id,
                    "flow_id": record.flow_id,
                    "flow_name": record.flow_name,
                    "success": record.success,
                    "error_message": record.error_message,
                    "execution_time": record.execution_time,
                    "executed_at": record.executed_at,
                    "result_data": None
                }
                
                # 转换结果数据
                if record.result_data:
                    record_dict["result_data"] = {
                        "flow_id": record.result_data.flow_id,
                        "flow_name": record.result_data.flow_name,
                        "final_result": record.result_data.final_result
                    }
                
                history.append(record_dict)
            
            return Result.success(history)
        except Exception as e:
            return Result.fail(f"获取执行历史失败: {str(e)}")