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
from repository.data_process_repository import DataProcessRepository
from repository.execution_record_repository import ExecutionRecordRepository
import inspect


class DataProcessService(BaseService):
    """数据处理流程服务类"""
    
    def __init__(self, instruction_item_repo: InstructionItemRepository = None, data_process_repo: DataProcessRepository = None, execution_record_repo: ExecutionRecordRepository = None):
        """初始化数据处理流程服务
        
        Args:
            instruction_item_repo: 指令项目仓储实例，将通过依赖注入获取
            data_process_repo: 数据流程仓储实例，将通过依赖注入获取
            execution_record_repo: 执行记录仓储实例，将通过依赖注入获取
        """
        # 注入仓储实例
        self.instruction_item_repo = instruction_item_repo
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
                    params=node.params
                ))
            
            edges = []
            for edge in flow.edges:
                edges.append(ProcessEdge(
                    id=edge.id,
                    flow_id=flow_id,  # 添加flow_id字段
                    source=edge.source,
                    target=edge.target,
                    label=edge.label
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
            # 检查流程是否已存在
            existing_process = self.data_process_repo.find_by_id(flow_id)
            if existing_process:
                # 流程已存在，使用update方法
                if self.data_process_repo.update(data_process):
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
                if self.data_process_repo.add(data_process):
                    response = SaveDataProcessFlowResponse(
                        id=flow_id,
                        message=f"流程 '{flow.name}' 保存成功",
                        success=True
                    )
                    return Result.success(response)
                else:
                    return Result.fail("保存流程失败，请稍后重试")
                
        except Exception as e:
            print(f"❌ 保存数据处理流程失败: {str(e)}")
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
            # 使用仓储获取流程
            process = self.data_process_repo.find_by_id(flow_id)
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
                    "params": node.params
                } for node in process.nodes],
                "edges": [{
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label
                } for edge in process.edges],
                "createdAt": datetime.fromisoformat(process.created_at),
                "updatedAt": datetime.fromisoformat(process.updated_at)
            }
            
            flow = DataProcessFlow(**flow_dict)
            return Result.success(flow)
            
        except Exception as e:
            print(f"❌ 获取数据处理流程失败: {str(e)}")
            return Result.fail(f"获取流程失败: {str(e)}")
    

    
    async def get_all_data_process_flows(self) -> Result[List[DataProcessFlow]]:
        """
        获取所有保存的数据处理流程
        
        Returns:
            Result[List[DataProcessFlow]]: 流程列表
        """
        try:
            # 使用仓储获取所有流程
            processes = self.data_process_repo.find_all()
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
                        "params": node.params
                    } for node in process.nodes],
                    "edges": [{
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "label": edge.label
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
            print(f"❌ 获取所有数据处理流程失败: {str(e)}")
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
            # 检查流程是否存在
            existing_process = self.data_process_repo.find_by_id(flow_id)
            if not existing_process:
                return Result.fail(f"流程ID '{flow_id}' 不存在")
            
            # 使用仓储删除流程
            if self.data_process_repo.delete(flow_id):
                return Result.success(True)
            else:
                return Result.fail("删除流程失败，请稍后重试")
                
        except Exception as e:
            print(f"❌ 删除数据处理流程失败: {str(e)}")
            return Result.fail(f"删除流程失败: {str(e)}")
    
            # start_node_id = None
            # start_node_id = None
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
        # 构建边信息字典：{source: [{target, label}]}
        edges_info: Dict[str, List[Dict[str, str]]] = {}
        for edge in flow.edges:
            if edge.source not in edges_info:
                edges_info[edge.source] = []
            edges_info[edge.source].append({
                'target': edge.target,
                'label': edge.label
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
            # 读取指令配置文件
            import json
            import os
            instructions_config_path = os.path.join(os.path.dirname(__file__), '../config_infos/instructions/items.json')
            with open(instructions_config_path, 'r', encoding='utf-8') as f:
                instructions_config = json.load(f)
            
            # 构建指令ID到参数配置的映射
            instruction_params_map = {}
            for instruction in instructions_config:
                param_map = {param['name']: param['label'] for param in instruction.get('params', [])}
                instruction_params_map[instruction['id']] = param_map
            
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
            
            # 使用DFS找到所有可以到达目标节点的前置节点
            before_nodes = []
            visited = set()
            
            def dfs_find_predecessors(current_id):
                # 如果当前节点是目标节点，不添加到前置节点列表
                if current_id == target_node_id:
                    return
                
                if current_id in visited:
                    return
                
                visited.add(current_id)
                
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
                    # 获取当前节点指令的参数配置
                    param_labels = instruction_params_map.get(node.instructionId, {})
                    
                    for param_name, param_value in node.params.items():
                        # 生成变量名格式：{{node.id.paramName}}
                        variable_name = f"{{{{{node.id}.{param_name}}}}}"
                        # 优先使用从配置文件获取的label，找不到则回退到参数名
                        variable_label = param_labels.get(param_name, param_name)
                        node_info["variables"].append({
                            "name": variable_name,
                            "label": variable_label,
                            "value": param_value
                        })
                
                before_nodes.append(node_info)
            
            # 从目标节点的所有直接前置节点开始搜索
            if target_node_id in reverse_edges_dict:
                for predecessor_id in reverse_edges_dict[target_node_id]:
                    dfs_find_predecessors(predecessor_id)
            
            # 递归查找所有前置节点
            # 遍历已找到的节点，继续查找它们的前置节点
            i = 0
            while i < len(before_nodes):
                current_id = before_nodes[i]["node_id"]
                if current_id in reverse_edges_dict:
                    for predecessor_id in reverse_edges_dict[current_id]:
                        if predecessor_id not in visited:
                            dfs_find_predecessors(predecessor_id)
                i += 1
            
            return Result.success(before_nodes)
            
        except Exception as e:
            print(f"❌ 获取前置节点信息失败: {str(e)}")
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
                flow_id=execution_result.get('flow_id', flow_id),
                flow_name=execution_result.get('flow_name', flow_name),
                final_result=execution_result.get('final_result'),
                process_results=execution_result.get('process_results', {})
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
            print(f"❌ 记录执行结果失败: {str(e)}")
            return False
    
    async def execute_data_process_flow(self, flow: DataProcessFlow, start_node_id: str, end_node_ids: List[str] = None) -> Result[Dict[str, Any]]:
        """
        执行数据处理流程
        根据连线标签文本的判断条件，查找满足条件第一条执行路径，作为当前执行流程的唯一有效执行流程
        
        Args:
            flow: 数据处理流程对象
            start_node_id: 开始节点ID
            end_node_ids: 结束节点ID列表，用于控制流程终止
            
        Returns:
            Result[Dict[str, Any]]: 执行结果，包含已执行节点的结果和失败信息（如果有）
        """
        try:
            # 构建节点ID到节点的映射
            node_map = {node.id: node for node in flow.nodes}
            
            # 构建正向边信息字典：{source: [{target, label}]}
            edges_info: Dict[str, List[Dict[str, str]]] = {}
            for edge in flow.edges:
                if edge.source not in edges_info:
                    edges_info[edge.source] = []
                edges_info[edge.source].append({
                    'target': edge.target,
                    'label': edge.label
                })
            
            # 初始化结束节点集合
            end_nodes = set(end_node_ids) if end_node_ids else set()
            
            # 1. 设置过程参数字典对象变量，用于保存已经执行的节点输入和输出参数结果信息
            process_results = {}
            execution_result = None
            # 跟踪已执行的节点
            executed_nodes = set()
            # 跟踪实际执行的节点顺序
            actual_execution_order = []
            # 标记是否已经执行到结束节点
            reached_end_node = False
            # 记录失败的节点信息
            failure_node_info = None
            
            # 执行节点的函数
            async def execute_node(node_id):
                nonlocal execution_result, failure_node_info
                node = node_map[node_id]
                print(f"正在执行节点: {node.id}, 指令ID: {node.instructionId}")
                
                try:
                    # 解析当前节点参数中的变量
                    resolved_params = {}
                    for param_name, param_value in node.params.items():
                        if isinstance(param_value, str):
                            result = param_value
                            # 使用正则表达式查找所有{{节点id.变量名}}格式的变量
                            import re
                            matches = re.findall(r'\{\{([^}]*)\}\}', param_value)
                            
                            for match in matches:
                                if '.' in match:
                                    node_id_part, var_name = match.split('.', 1)
                                    ref_key = f"{node_id_part}.{var_name}"
                                    
                                    if ref_key in process_results:
                                        placeholder = f"{{{{{match}}}}}"
                                        result = result.replace(placeholder, str(process_results[ref_key]))
                                        print(f"  - 解析变量 {param_name} 中的 {{node_id.var_name}} -> {ref_key} = {process_results[ref_key]}")
                                    else:
                                        print(f"  - 变量 {ref_key} 未找到")
                            
                            resolved_params[param_name] = result
                        else:
                            resolved_params[param_name] = param_value
                    
                    # 获取当前节点指令信息
                    instruction_info = await self.instruction_service.get_instruction_by_id(node.instructionId)
                    
                    if not instruction_info:
                        raise Exception(f"未找到指令ID: {node.instructionId}")
                    
                    # 获取输入参数值和输出参数名
                    input_params = {}
                    output_param_name = None
                    
                    for param in instruction_info.get('params', []):
                        if param.get('direction') == 0:  # 输入参数
                            if param.get('name') in resolved_params:
                                value=resolved_params[param.get('name')]
                                # 值类型转换
                                match param.get('type'):
                                    case "string":
                                        value=str(value)
                                    case "number":
                                        value=int(value)
                                    case "boolean":
                                        value=bool(value)
                                    case _:  # 默认情况（相当于 default）
                                        pass

                                input_params[param.get('name')] = value                                
                        elif param.get('direction') in [1,2]:  # 输出参数
                            output_param_name = param.get('name') 
                    
                    # 保存输入参数
                    for param_name, param_value in input_params.items():
                        temp_key = f"{node_id}.{param_name}"
                        process_results[temp_key] = param_value
                        print(f"  - 保存输入参数 {temp_key} = {param_value}")

                    python_script = instruction_info.get('python_script', '')
                    
                    # 执行脚本
                    execution_result = await self.instruction_service._execute_python_script(python_script, input_params)                    
                    # 回写参数
                    if param.get('direction') == 2:  # 回写参数
                        temp_key=node.params.get(param.get('name'),'')
                        if temp_key and process_results.get(temp_key[2:-2],''):
                            process_results[temp_key[2:-2]] = execution_result
                    # 保存输出参数
                    if output_param_name:
                        temp_key = f"{node_id}.{output_param_name}"
                        process_results[temp_key] = execution_result
                        print(f"  - 保存输出参数 {temp_key} = {execution_result}")
                    
                    # 标记节点已执行
                    executed_nodes.add(node_id)
                    actual_execution_order.append(node_id)
                    
                    # 检查是否为结束节点
                    if node_id in end_nodes:
                        nonlocal reached_end_node
                        reached_end_node = True
                        print(f"执行到结束节点: {node_id}，流程终止")
                    
                    return True,output_param_name, execution_result
                except Exception as e:
                    # 记录失败节点信息
                    failure_node_info = {
                        "node_id": node_id,
                        "instruction_id": node.instructionId,
                        "error_message": str(e),
                        "error_type": type(e).__name__
                    }
                    print(f"❌ 节点 {node_id} 执行失败: {str(e)}")
                    
                    return False,None,f"❌ 节点 {node_id} 执行失败: {str(e)}"
            
            # 执行开始节点
            is_success,output_param_name, source_output = await execute_node(start_node_id)
            if not is_success:
                raise Exception(source_output)
            # 动态执行路径选择
            current_node_id = start_node_id
            while not reached_end_node:
                # 检查当前节点是否有出边
                if current_node_id not in edges_info:
                    print(f"当前节点 {current_node_id} 没有出边，流程结束")
                    break
                
                # 遍历当前节点的所有出边，寻找满足条件的第一条路径
                found_next_node = False
                for edge_info in edges_info[current_node_id]:
                    target_node_id = edge_info['target']
                    edge_label = edge_info['label']
                    
                    # 如果目标节点已经执行过，跳过
                    if target_node_id in executed_nodes:
                        continue
                    
                    # 如果边没有标签，则默认满足条件，执行目标节点
                    if not edge_label:
                        print(f"边 {current_node_id} -> {target_node_id} 没有标签，默认满足条件")
                        is_success,output_param_name, source_output = await execute_node(target_node_id)
                        if not is_success:
                            raise Exception(source_output)
                        current_node_id = target_node_id
                        found_next_node = True
                        break
                    else:
                        # 替换边标签中的变量
                        resolved_label = edge_label
                        if isinstance(edge_label, str):
                            import re
                            matches = re.findall(r'\{\{([^}]*)\}\}', edge_label)
                            
                            for match in matches:
                                if '.' in match:
                                    node_id_part, var_name = match.split('.', 1)
                                    ref_key = f"{node_id_part}.{var_name}"
                                    
                                    if ref_key in process_results:
                                        placeholder = f"{{{{{match}}}}}"
                                        resolved_label = resolved_label.replace(placeholder, str(process_results[ref_key]))
                                        print(f"  - 解析边标签中的变量: {{node_id.var_name}} -> {ref_key} = {process_results[ref_key]}")
                        
                        # 构建条件表达式并评估
                        try:
                            # 构建条件表达式的上下文环境
                            context = {}
                            condition_satisfied=False
                            # 添加当前节点的输出值到上下文
                            if output_param_name:
                                source_output_key = f"{current_node_id}.{output_param_name}"
                                if source_output_key in process_results:
                                    context['output'] = process_results[source_output_key]
                                    context['value'] = process_results[source_output_key]
                            
                            # 检查是否是简单的比较表达式
                            if resolved_label.startswith('==') or resolved_label.startswith('!=') or \
                               resolved_label.startswith('>') or resolved_label.startswith('<') or \
                               resolved_label.startswith('>=') or resolved_label.startswith('<='):
                                # 构建完整的表达式
                                expr = f"value {resolved_label}"
                                print(f"  - 执行条件表达式: {expr}")
                                condition_satisfied = eval(expr, {}, context)
                            else:
                                try:             
                                    print(eval(resolved_label, {}, {}))                           
                                    condition_satisfied = eval(resolved_label, {}, {})
                                except Exception as e:
                                    # 直接比较值
                                    if 'value' in context:
                                        condition_satisfied = str(context['value']) == resolved_label
                                        print(f"  - 直接比较: 值 '{context['value']}' {'==' if condition_satisfied else '!='} 标签 '{resolved_label}'")
                                    else:
                                        condition_satisfied = False
                                        print(f"  - 无法比较: 当前节点没有输出值或表达式错误 ({str(e)})")
                            
                            if condition_satisfied:
                                print(f"  - 条件满足，执行目标节点 {target_node_id}")
                                # 执行目标节点
                                is_success,output_param_name, source_output = await execute_node(target_node_id)
                                if not is_success:
                                    raise Exception(source_output)
                                current_node_id = target_node_id
                                found_next_node = True
                                break
                            else:
                                print(f"  - 条件不满足，跳过目标节点 {target_node_id}")
                        except Exception as e:
                            print(f"  - 条件表达式解析错误: {str(e)}")
                
                # 如果没有找到满足条件的下一个节点，结束流程
                if not found_next_node:
                    print(f"没有找到满足条件的下一个节点，流程结束")
                    break
            
            # 3. 处理最终节点的执行结果，特别是文件下载相关
            processed_final_result = execution_result
            
            # 检查是否是BytesIO类型（可能来自文件下载指令）
            if isinstance(execution_result, BytesIO):
                try:
                    # 重置文件指针
                    execution_result.seek(0)
                    # 读取内容并进行base64编码
                    file_data = execution_result.read()
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
            elif isinstance(execution_result, dict) and "file_data" in execution_result:
                # 已经是正确的格式，直接使用
                print(f"检测到标准文件流格式: {execution_result.get('file_name', 'unknown')}")
                processed_final_result = execution_result
            # 检查是否是错误格式
            elif isinstance(execution_result, dict) and "error" in execution_result:
                print(f"文件处理错误: {execution_result.get('error')}")
                processed_final_result = execution_result
            
            # 确保返回有效的结果，而不是空数组或None
            if processed_final_result is None or processed_final_result == []:
                print("警告: 检测到空结果，将替换为有效响应")
                processed_final_result = {"message": "执行成功，但未返回数据"}
            
            # 确保final_result不是空数组
            if "final_result" in locals() and (final_result is None or final_result == []):
                print("严重警告: final_result为空，将强制替换")
                final_result = {"message": "执行成功，但返回数据异常"}
            
            # 构建最终返回结果
            final_result = {
                "flow_id": flow.id,
                "flow_name": flow.name,
                "final_result": processed_final_result,
                "process_results": process_results,
                "execution_order": actual_execution_order,
                "total_nodes_executed": len(executed_nodes),
                "reached_end_node": reached_end_node
            }
            if reached_end_node:
                return Result.success(final_result)
            else:
                return Result.fail(f"执行流程失败: 未到达结束节点", final_result)
            
        except Exception as e:
            print(f"❌ 执行数据处理流程失败: {str(e)}")
            
            # 构建错误结果，避免包含可能导致循环引用的复杂数据
            error_result = {
                "flow_id": flow.id,
                "flow_name": flow.name,
                "final_result": f"执行流程（{failure_node_info.get('node_id','')}）失败: {str(e)}",
                # 只保留简单类型的处理结果，避免循环引用
                "process_results": {k: v for k, v in process_results.items() if isinstance(v, (str, int, float, bool, type(None)))},
                "execution_order": actual_execution_order,
                "total_nodes_executed": len(executed_nodes),
                # 只保留错误信息的关键字段
                "reached_end_node": {
                    "node_id": failure_node_info.get('node_id', ''),
                    "error_message": failure_node_info.get('error_message', '')
                }
            }
            
            return Result.fail(f"执行流程失败: {str(e)}", error_result)
    
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
            print(f"❌ 根据ID执行数据处理流程失败: {str(e)}")
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
            # 使用仓储获取执行历史记录
            if flow_id:
                records = self.execution_record_repo.find_by_flow_id(flow_id)
            else:
                records = self.execution_record_repo.find_all()
            
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
                        "final_result": record.result_data.final_result,
                        "process_results": record.result_data.process_results
                    }
                
                history.append(record_dict)
            
            return Result.success(history)
        except Exception as e:
            print(f"❌ 获取执行历史失败: {str(e)}")
            return Result.fail(f"获取执行历史失败: {str(e)}")