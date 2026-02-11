#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理控制器
处理系统级别的功能
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from service.system_service import SystemService
from di.container import inject

# 创建APIRouter实例
router = APIRouter(prefix="/api", tags=["System"])


class ValidateLicenseRequest(BaseModel):
    """验证授权码请求模型"""
    license_key: str


# 验证授权码接口
@router.post("/system/license/validate")
async def validate_license(
    request: ValidateLicenseRequest,
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    验证授权码接口
    
    输入参数：
    - license_key: 授权码
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    - data: 授权码验证数据，包含过期日期、自定义字符串和剩余天数等
    """
    result = system_service.validate_license(request.license_key)
    return result
