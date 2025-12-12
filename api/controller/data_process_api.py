#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理流程API控制器 - FastAPI + 依赖注入版本
处理数据处理流程的相关API请求
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Set, Any, Optional
import logging
import time
import json
from service.data_process_service import DataProcessService
from service.instruction_service import InstructionService
from dto.instruction_dto import (
    DataProcessFlow,
    SaveDataProcessFlowRequest,
    SaveDataProcessFlowResponse,
    CanvasNode,
    CanvasEdge
)
from di.container import inject
from utils.common import execution_terminator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/data-process",
    tags=["data-process"],
    responses={404: {"description": "Not found"}},
)

@router.post("/save", response_model=SaveDataProcessFlowResponse)
async def save_data_process_flow(
    flow_data: dict,  # 直接接受字典格式，让Pydantic自动转换
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> SaveDataProcessFlowResponse:
    """
    保存数据处理流程
    
    Args:
        flow_data: 流程数据，包含节点和边信息
        
    Returns:
        SaveDataProcessFlowResponse: 保存结果响应
    """
    try:
        # 创建DataProcessFlow对象
        flow = DataProcessFlow(**flow_data)
        
        # 调用服务保存流程
        result = await data_process_service.save_data_process_flow(flow)
        
        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存流程失败: {str(e)}")

@router.post("/save-basic-info", response_model=SaveDataProcessFlowResponse)
async def save_basic_info(
    basic_info: dict,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> SaveDataProcessFlowResponse:
    """
    保存流程基本信息（名称和描述）
    保留现有的节点和边信息，只更新基本信息
    
    Args:
        basic_info: 包含流程ID、名称和描述等基本信息
        
    Returns:
        SaveDataProcessFlowResponse: 保存结果响应
    """
    try:
        # 获取流程ID
        flow_id = basic_info.get('id')
        
        if not flow_id:
            raise HTTPException(status_code=400, detail="缺少流程ID")
        
        # 获取现有的流程信息
        existing_flow_result = await data_process_service.get_data_process_flow(flow_id)
        
        if not existing_flow_result.success:
            raise HTTPException(status_code=404, detail=existing_flow_result.error)
        
        # 获取现有流程对象
        existing_flow = existing_flow_result.data
        
        # 更新基本信息，保留原有节点和边数据
        if 'name' in basic_info:
            existing_flow.name = basic_info['name']
        
        # 更新描述信息
        if 'description' in basic_info:
            existing_flow.description = basic_info['description']
        
        # 直接使用更新后的现有流程对象
        
        # 保存更新后的流程
        result = await data_process_service.save_data_process_flow(existing_flow)
        
        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存流程基本信息失败: {str(e)}")


@router.get("/list", response_model=List[dict])
async def get_all_data_process_flows(
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> List[dict]:
    """
    获取所有保存的数据处理流程列表
    
    Returns:
        List[dict]: 流程列表
    """
    result = await data_process_service.get_all_data_process_flows()
    
    if result.success:
        # 转换为字典格式返回
        return [flow.dict() for flow in result.data]
    else:
        raise HTTPException(status_code=400, detail=result.error)


@router.get("/{flow_id}", response_model=dict)
async def get_data_process_flow(
    flow_id: str,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> dict:
    """
    获取指定的数据处理流程详情
    
    Args:
        flow_id: 流程ID
        
    Returns:
        dict: 流程详情
    """
    result = await data_process_service.get_data_process_flow(flow_id)
    
    if result.success:
        return result.data.dict()
    else:
        raise HTTPException(status_code=404, detail=result.error)

@router.post("/get-previous-nodes")
async def get_previous_nodes_with_variables(
    request_data: dict,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> dict:
    """
    获取指定节点之前的所有节点及其变量信息
    
    Args:
        request_data: 包含flow对象和target_node_id的请求数据
        
    Returns:
        dict: 包含前置节点信息和变量的响应
    """
    try:
        # 从请求数据中提取flow对象和target_node_id
        flow_data = request_data.get('flow', {})
        target_node_id = request_data.get('target_node_id', '')
        
        if not flow_data or not target_node_id:
            raise HTTPException(status_code=400, detail="缺少必要参数：flow或target_node_id")
        
        # 创建DataProcessFlow对象
        flow = DataProcessFlow(**flow_data)
        
        # 调用服务获取前置节点信息
        result = await data_process_service.get_nodes_before_target(flow, target_node_id)
        
        if result.success:
            # 构建响应
            all_variables = []
            for node_info in result.data:
                all_variables.extend(node_info['variables'])
            
            return {
                "success": True,
                "data": {
                    "previous_nodes": result.data,
                    "variables": all_variables
                },
                "message": "获取前置节点和变量信息成功"
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取前置节点信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取前置节点信息失败: {str(e)}")


@router.post("/execute")
async def execute_data_process_flow(
    flow_data: dict,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService)),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
) -> dict:
    """
    执行数据处理流程
    
    Args:
        flow_data: 流程数据，包含节点和边信息
        
    Returns:
        dict: 执行结果
    """
    try:
        # 创建DataProcessFlow对象
        flow = DataProcessFlow(**flow_data)
        
        # 1. 节点存在性检查
        if not flow.nodes:
            raise HTTPException(status_code=400, detail="画布中不存在流程节点，请添加节点后再执行")
        
        # 2. 构建边的字典表示和节点连接关系
        edges_dict = {}
        source_nodes = set()
        target_nodes = set()
        connections = set()
        
        for edge in flow.edges:
            # 检查自环连接
            if edge.source == edge.target:
                raise HTTPException(status_code=400, detail=f"节点 {edge.source} 存在自环连接")
            
            # 检查重复连接
            connection_key = f"{edge.source}->{edge.target}"
            if connection_key in connections:
                raise HTTPException(status_code=400, detail=f"存在重复连接: {edge.source} -> {edge.target}")
            connections.add(connection_key)
            
            # 构建边的字典
            if edge.source not in edges_dict:
                edges_dict[edge.source] = []
            edges_dict[edge.source].append(edge.target)
            
            source_nodes.add(edge.source)
            target_nodes.add(edge.target)
        
        # 3. 确定开始节点和结束节点（基于入度和出度）
        node_ids = {node.id for node in flow.nodes}
        
        # 开始节点：没有入边的节点（不在target_nodes中的节点）
        start_nodes = [node for node in flow.nodes if node.id not in target_nodes]
        if not start_nodes:
            raise HTTPException(status_code=400, detail="流程必须包含开始节点（没有入边的节点）")
        if len(start_nodes) > 1:
            raise HTTPException(status_code=400, detail="流程只能有一个开始节点（没有入边的节点）")
        start_node = start_nodes[0]
        
        # 结束节点：没有出边的节点（不在source_nodes中的节点）
        end_nodes = [node for node in flow.nodes if node.id not in source_nodes]
        if not end_nodes:
            raise HTTPException(status_code=400, detail="流程必须包含结束节点（没有出边的节点）")
        # 允许多个结束节点
        end_node_ids = [node.id for node in end_nodes]
        
        # 4. 检查开始节点必须有出边（除非流程中只有一个节点）
        if len(flow.nodes) > 1 and (start_node.id not in edges_dict or not edges_dict[start_node.id]):
            raise HTTPException(status_code=400, detail="开始节点必须有出边")
        
        # 5. 检查所有结束节点必须有入边（除非流程中只有一个节点）
        if len(flow.nodes) > 1:
            for end_node in end_nodes:
                if end_node.id not in target_nodes:
                    raise HTTPException(status_code=400, detail=f"结束节点 {end_node.id} 必须有入边")
        
        # 6. 检查孤立节点（除非流程中只有一个节点）
        if len(flow.nodes) > 1:
            connected_nodes = source_nodes.union(target_nodes)
            isolated_nodes = node_ids - connected_nodes
            
            if isolated_nodes:
                raise HTTPException(status_code=400, detail=f"存在孤立节点: {', '.join(isolated_nodes)}")
        
        # 7. 路径有效性验证 - 使用深度优先搜索检查是否存在从开始节点到至少一个结束节点的路径
        # 对于单个节点流程，直接视为有效路径
        if len(flow.nodes) > 1:
            visited = set()
            found_path_to_end = False
            
            def dfs(node_id):
                nonlocal found_path_to_end
                if node_id in end_node_ids:
                    found_path_to_end = True
                    return True
                
                if node_id in visited:
                    return False
                
                visited.add(node_id)
                
                if node_id in edges_dict:
                    for next_node in edges_dict[node_id]:
                        if dfs(next_node):
                            return True
                
                return False
            
            dfs(start_node.id)
            
            if not found_path_to_end:
                raise HTTPException(status_code=400, detail="不存在从开始节点到任何结束节点的完整路径")
        
        # 8. 节点属性检查
        for node in flow.nodes:
            # 根据节点的instructionId获取指令信息
            instruction_item = await instruction_service.get_instruction_by_id(node.instructionId)
            if not instruction_item:
                raise HTTPException(status_code=400, detail=f"节点 {node.id} 引用的指令不存在")
            
            # 获取指令的参数配置
            instruction_params = instruction_item.get('params', [])
            
            # 检查必填参数
            for param in instruction_params:
                # 只检查required为True的参数
                if param.get('required', False):
                    param_name = param.get('name')
                    # 检查节点参数中是否已定义该必填参数
                    if param_name not in node.params:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"{node.id}节点{param.get('label', param_name)}参数未填写"
                        )
        
        # 9. 验证通过后执行流程并记录日志
        start_time = time.time()
        logger.info(f"开始执行流程: {flow.name}, ID: {flow.id}")
        
        # 按流程顺序获取并执行Python脚本和参数
        # 执行流程，传递结束节点ID列表
        end_node_ids = [node.id for node in end_nodes]
        execution_result = await data_process_service.execute_data_process_flow(flow, start_node.id, end_node_ids)
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 3)
        
        if execution_result.success:
            logger.info(f"流程执行成功: {flow.name}, 耗时: {execution_time}秒")
            # 构建与instruction/execute接口一致的返回格式
            return {
                "success": True,
                "data": {
                    "result": execution_result.data,
                    "execution_time": execution_time
                },
                "message": execution_result.message or "流程执行成功"
            }
        else:
            logger.error(f"流程执行失败: {flow.name}, 错误: {execution_result.error}")
            # 构建错误响应，与instruction/execute接口保持一致
            return {
                "success": False,
                "data": {
                    "result": execution_result.data,
                    "execution_time": execution_time
                },
                "message": execution_result.error or "流程执行失败"
            }
            
    except HTTPException as http_ex:
        # 将HTTPException转换为与instruction/execute接口一致的错误响应
        return {
            "success": False,
            "data": None,
            "message": http_ex.detail or "请求参数错误"
        }
    except Exception as e:
        logger.error(f"执行流程时发生错误: {str(e)}")
        # 返回与instruction/execute接口一致的错误响应格式
        return {
            "success": False,
            "data": None,
            "message": f"执行流程失败: {str(e)}"
        }


@router.post("/execute-by-id/{flow_id}")
async def execute_data_process_flow_by_id(
    flow_id: str,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService)),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
) -> dict:
    """
    根据流程ID执行数据处理流程
    
    Args:
        flow_id: 流程ID
        
    Returns:
        dict: 执行结果
    """
    try:
        # 获取流程信息
        flow_result = await data_process_service.get_data_process_flow(flow_id)
        if not flow_result.success:
            return {
                "success": False,
                "data": None,
                "message": flow_result.error or f"未找到ID为{flow_id}的流程"
            }
        
        flow = flow_result.data
        
        # 验证流程结构
        if not flow.nodes:
            return {
                "success": False,
                "data": None,
                "message": "流程中不存在节点，无法执行"
            }
        
        # 构建边的字典表示和节点连接关系
        edges_dict = {}
        source_nodes = set()
        target_nodes = set()
        connections = set()
        
        for edge in flow.edges:
            # 检查自环连接
            if edge.source == edge.target:
                return {
                    "success": False,
                    "data": None,
                    "message": f"节点 {edge.source} 存在自环连接"
                }
            
            # 检查重复连接
            connection_key = f"{edge.source}->{edge.target}"
            if connection_key in connections:
                return {
                    "success": False,
                    "data": None,
                    "message": f"存在重复连接: {edge.source} -> {edge.target}"
                }
            connections.add(connection_key)
            
            # 构建边的字典
            if edge.source not in edges_dict:
                edges_dict[edge.source] = []
            edges_dict[edge.source].append(edge.target)
            
            source_nodes.add(edge.source)
            target_nodes.add(edge.target)
        
        # 确定开始节点和结束节点（基于入度和出度）
        node_ids = {node.id for node in flow.nodes}
        
        # 开始节点：没有入边的节点（不在target_nodes中的节点）
        start_nodes = [node for node in flow.nodes if node.id not in target_nodes]
        if not start_nodes:
            return {
                "success": False,
                "data": None,
                "message": "流程必须包含开始节点（没有入边的节点）"
            }
        if len(start_nodes) > 1:
            return {
                "success": False,
                "data": None,
                "message": "流程只能有一个开始节点（没有入边的节点）"
            }
        
        # 结束节点：没有出边的节点（不在source_nodes中的节点）
        end_nodes = [node for node in flow.nodes if node.id not in source_nodes]
        if not end_nodes:
            return {
                "success": False,
                "data": None,
                "message": "流程必须包含结束节点（没有出边的节点）"
            }
        
        # 节点属性检查
        for node in flow.nodes:
            # 根据节点的instructionId获取指令信息
            instruction_item = await instruction_service.get_instruction_by_id(node.instructionId)
            if not instruction_item:
                return {
                    "success": False,
                    "data": None,
                    "message": f"节点 {node.id} 引用的指令不存在"
                }
            
            # 获取指令的参数配置
            instruction_params = instruction_item.get('params', [])
            
            # 检查必填参数
            for param in instruction_params:
                # 只检查required为True的参数
                if param.get('required', False):
                    param_name = param.get('name')
                    # 检查节点参数中是否已定义该必填参数
                    if param_name not in node.params:
                        return {
                            "success": False,
                            "data": None,
                            "message": f"{node.id}节点{param.get('label', param_name)}参数未填写"
                        }
        
        # 记录开始时间
        start_time = time.time()
        logger.info(f"开始执行流程: {flow.name}, ID: {flow.id}")
        
        # 调用服务层执行流程
        execution_result = await data_process_service.execute_data_process_flow_by_id(flow_id)
        
        # 计算执行时间
        end_time = time.time()
        execution_time = round(end_time - start_time, 3)
        
        # 记录执行结果
        result_data = execution_result.data if execution_result.success else None
        error_msg = execution_result.error if not execution_result.success else None
        
        # 记录到执行历史
        data_process_service.record_execution_result(
            flow_id=flow_id,
            flow_name=flow.name,
            execution_result=result_data,
            success=execution_result.success,
            error_message=error_msg,
            execution_time=execution_time
        )
        
        if execution_result.success:
            logger.info(f"流程执行成功: {flow.name}, 耗时: {execution_time}秒")
            return {
                "success": True,
                "data": {
                    "result": execution_result.data,
                    "execution_time": execution_time
                },
                "message": execution_result.message or "流程执行成功"
            }
        else:
            logger.error(f"流程执行失败: {flow.name}, 错误: {execution_result.error}")
            return {
                "success": False,
                "data": {
                    "result": execution_result.data,
                    "execution_time": execution_time
                },
                "message": execution_result.error or "流程执行失败"
            }
            
    except Exception as e:
        logger.error(f"根据ID执行流程时发生错误: {str(e)}")
        
        # 尝试获取流程信息以记录失败历史
        try:
            flow_result = await data_process_service.get_data_process_flow(flow_id)
            if flow_result.success:
                data_process_service.record_execution_result(
                    flow_id=flow_id,
                    flow_name=flow_result.data.name,
                    execution_result=None,
                    success=False,
                    error_message=str(e),
                    execution_time=0
                )
        except:
            pass
        
        return {
            "success": False,
            "data": None,
            "message": f"执行流程失败: {str(e)}"
        }

@router.get("/execution-history/{flow_id}")
async def get_execution_history(
    flow_id: str,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> dict:
    """
    获取指定流程的执行历史
    
    Args:
        flow_id: 流程ID
        
    Returns:
        dict: 执行历史记录
    """
    try:
        result = await data_process_service.get_execution_history(flow_id)
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": "获取执行历史成功"
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": result.error or "获取执行历史失败"
            }
            
    except Exception as e:
        logger.error(f"获取执行历史时发生错误: {str(e)}")
        return {
            "success": False,
            "data": None,
            "message": f"获取执行历史失败: {str(e)}"
        }

@router.delete("/flows/{flow_id}")
async def delete_data_process_flow(
    flow_id: str,
    data_process_service: DataProcessService = Depends(lambda: inject(DataProcessService))
) -> dict:
    """
    删除指定的数据处理流程
    
    Args:
        flow_id: 流程ID
        
    Returns:
        dict: 删除结果
    """
    result = await data_process_service.delete_data_process_flow(flow_id)
    
    if result.success:
        return {"message": result.message}
    else:
        raise HTTPException(status_code=404, detail=result.error)


@router.post("/execute/terminate")
async def terminate_data_process_flow(
    terminate_request: Dict[str, str]
) -> dict:
    """
    终止正在执行的数据处理流程
    
    Args:
        terminate_request: 包含流程ID的请求体，格式为 {"flow_id": "流程ID"}
        
    Returns:
        dict: 终止操作的响应结果
    """
    try:
        # 获取流程ID
        flow_id = terminate_request.get("flow_id")
        
        if not flow_id:
            raise HTTPException(status_code=400, detail="缺少必要参数: flow_id")
        
        # 设置终止标志
        execution_terminator.set_terminate_flag(flow_id)
        
        logger.info(f"已设置流程 {flow_id} 的终止标志")
        
        # 返回成功响应
        return {
            "success": True,
            "message": f"已成功发送终止信号到流程 {flow_id}",
            "data": {
                "flow_id": flow_id,
                "terminate_status": "requested"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"终止流程 {flow_id} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"终止流程失败: {str(e)}")


@router.get("/execute/status/{flow_id}")
async def get_flow_execution_status(
    flow_id: str
) -> dict:
    """
    查询指定流程的执行状态
    
    Args:
        flow_id: 流程ID
        
    Returns:
        dict: 流程执行状态响应
    """
    try:
        # 获取流程状态
        status = execution_terminator.get_flow_status(flow_id)
        
        logger.info(f"查询流程 {flow_id} 的执行状态: {status}")
        
        # 返回成功响应
        return {
            "success": True,
            "message": f"成功查询流程 {flow_id} 的执行状态",
            "data": {
                "flow_id": flow_id,
                "status": status,
                "status_text": {
                    "idle": "空闲",
                    "running": "运行中",
                    "completed": "执行完成",
                    "failed": "执行失败",
                    "terminated": "已终止"
                }[status]
            }
        }
        
    except Exception as e:
        logger.error(f"查询流程 {flow_id} 状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询流程状态失败: {str(e)}")


@router.get("/execute/status")
async def get_all_flows_execution_status() -> dict:
    """
    查询所有流程的执行状态
    
    Returns:
        dict: 所有流程执行状态响应
    """
    try:
        # 获取所有流程状态
        all_statuses = execution_terminator.get_all_flow_statuses()
        
        # 构建包含状态文本的响应数据
        formatted_statuses = {}
        status_text_map = {
            "idle": "空闲",
            "running": "运行中",
            "completed": "执行完成",
            "failed": "执行失败",
            "terminated": "已终止"
        }
        
        for flow_id, status in all_statuses.items():
            formatted_statuses[flow_id] = {
                "status": status,
                "status_text": status_text_map[status]
            }
        
        logger.info(f"查询所有流程的执行状态，共 {len(all_statuses)} 个流程")
        
        # 返回成功响应
        return {
            "success": True,
            "message": "成功查询所有流程的执行状态",
            "data": {
                "flow_statuses": formatted_statuses,
                "total_flows": len(all_statuses)
            }
        }
        
    except Exception as e:
        logger.error(f"查询所有流程状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询所有流程状态失败: {str(e)}")