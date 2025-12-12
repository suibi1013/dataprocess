#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令管理控制器 - FastAPI + 依赖注入版本
处理指令相关的HTTP请求
"""

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from typing import Dict, Any

from service.instruction_service import InstructionService
from dto.instruction_dto import (
    InstructionItem, InstructionCategory, InstructionListResponse, InstructionParameter,
    CreateInstructionCategoryRequest, CreateInstructionItemRequest,
    UpdateInstructionCategoryRequest, UpdateInstructionItemRequest,
    ExecuteInstructionRequest, ExecuteInstructionResponse,
    InstallDependenciesRequest
)
from di.container import inject

# 创建路由器
router = APIRouter(prefix="/api", tags=["Instruction"])

# 路由定义
@router.get("/instructions")
async def get_instruction_list(
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """获取指令列表"""
    try:
        response = await instruction_service.get_instruction_list()
        
        if response.success:
            return {
                "success": True,
                "data": response.data.dict(),
                "message": response.message
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"获取指令列表失败: {str(e)}"
        }

@router.post("/instruction/category/create")
async def create_category(
    request: CreateInstructionCategoryRequest,
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """创建指令分类"""
    try:
        response = await instruction_service.create_category(request)
        
        if response.success:
            return {
                "success": True,
                "data": response.data.dict(),
                "message": response.message
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"创建分类失败: {str(e)}"
        }

@router.post("/instruction/item/create")
async def create_item(
    request: CreateInstructionItemRequest,
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """创建指令项目"""
    try:
        response = await instruction_service.create_item(request)
        
        if response.success:
            return {
                "success": True,
                "data": response.data.dict(),
                "message": response.message
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"创建指令项目失败: {str(e)}"
        }

@router.put("/instruction/category/{category_id}")
async def update_category(
    request: UpdateInstructionCategoryRequest,
    category_id: str = PathParam(..., description="分类ID"),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """更新指令分类"""
    try:
        response = await instruction_service.update_category(category_id, request)
        
        if response.success:
            return {
                "success": True,
                "data": response.data.dict(),
                "message": response.message
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"更新分类失败: {str(e)}"
        }

@router.put("/instruction/item/{item_id}")
async def update_item(
    request: UpdateInstructionItemRequest,
    item_id: str = PathParam(..., description="项目ID"),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """更新指令项目"""
    try:
        response = await instruction_service.update_item(item_id, request)
        
        if response.success:
            return {
                "success": True,
                "data": response.data.dict(),
                "message": response.message
            }
        else:
            return {
                "success": False,
                "data": None,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"更新指令项目失败: {str(e)}"
        }

@router.delete("/instruction/category/{category_id}")
async def delete_category(
    category_id: str = PathParam(..., description="分类ID"),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """删除指令分类"""
    try:
        response = await instruction_service.delete_category(category_id)
        
        return {
            "success": response.success,
            "data": response.data,
            "message": response.message
        }
            
    except Exception as e:
        return {
            "success": False,
            "data": False,
            "message": f"删除分类失败: {str(e)}"
        }

@router.delete("/instruction/item/{item_id}")
async def delete_item(
    item_id: str = PathParam(..., description="项目ID"),
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """删除指令项目"""
    try:
        response = await instruction_service.delete_item(item_id)
        
        return {
            "success": response.success,
            "data": response.data,
            "message": response.message
        }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"删除指令项目失败: {str(e)}"
        }

@router.post("/instruction/execute")
async def execute_instruction(
    request: ExecuteInstructionRequest,
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """执行指令"""
    try:
        response = await instruction_service.execute_instruction(request)
        
        if response.success:
            # 手动构建响应数据，避免dict()序列化问题
            return {
                "success": True,
                "data": response.data,
                "message": response.message
            }
        else:
            # 手动构建错误响应数据
            return {
                "success": False,
                "data": response.data,
                "message": response.message
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"执行指令失败: {str(e)}"
        }

@router.post("/instruction/install-dependencies")
async def install_dependencies(
    request: InstallDependenciesRequest,
    instruction_service: InstructionService = Depends(lambda: inject(InstructionService))
):
    """安装Python依赖包"""
    try:
        response = await instruction_service.install_dependencies(request.dependencies)
        
        return {
            "success": response.success,
            "data": response.data,
            "message": response.message
        }
            
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"安装依赖包失败: {str(e)}"
        }