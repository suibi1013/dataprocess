#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用数据传输对象（DTO）定义
用于通用响应、健康检查等操作
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

# 定义泛型类型变量
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """通用API响应DTO"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: Optional[str] = Field(None, description="响应时间戳")
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)
    
    @classmethod
    def success_response(cls, data: Optional[T] = None, message: str = "操作成功") -> 'ApiResponse[T]':
        """创建成功响应"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str = "操作失败", data: Optional[T] = None) -> 'ApiResponse[T]':
        """创建错误响应"""
        return cls(success=False, message=message, data=data)


class HealthCheckResponse(BaseModel):
    """健康检查响应DTO"""
    status: str = Field(..., description="服务状态", example="healthy")
    message: str = Field(..., description="状态消息", example="Service is running")
    timestamp: str = Field(..., description="检查时间戳", example="2024-01-01T00:00:00")


class ServerInfoResponse(BaseModel):
    """服务器信息响应DTO"""
    service: str = Field(..., description="服务名称", example="ppt2html")
    version: str = Field(..., description="服务版本", example="1.0.0")
    supported_formats: List[str] = Field(..., description="支持的文件格式", example=["pptx", "ppt"])
    max_file_size_mb: int = Field(..., description="最大文件大小(MB)", example=100, gt=0)
    upload_folder: str = Field(..., description="上传文件夹路径", example="/config_infos/uploads")


class ErrorResponse(BaseModel):
    """错误响应DTO"""
    success: bool = Field(False, description="操作是否成功")
    error: str = Field("", description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    timestamp: Optional[str] = Field(None, description="错误发生时间")
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)