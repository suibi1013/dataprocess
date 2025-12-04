#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作相关数据传输对象（DTO）定义
用于文件上传、配置保存等操作
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


class UploadFileRequest(BaseModel):
    """文件上传请求DTO"""
    file_name: str = Field(..., description="文件名", example="presentation.pptx")
    file_size: int = Field(..., description="文件大小(字节)", example=1024000, gt=0)
    file_content: bytes = Field(..., description="文件内容")
    
    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, v):
        if not v:
            raise ValueError("文件名不能为空")
        return v
    
    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError("文件大小必须大于0")
        if v > 100 * 1024 * 1024:  # 100MB
            raise ValueError("文件大小不能超过100MB")
        return v
    
    @field_validator('file_name')
    @classmethod
    def validate_file_extension(cls, v):
        allowed_extensions = {'.ppt', '.pptx'}
        file_ext = '.' + v.rsplit('.', 1)[-1].lower() if '.' in v else ''
        if file_ext not in allowed_extensions:
            raise ValueError("不支持的文件类型，请上传PPT文件")
        return v
    
    def validate(self) -> Tuple[bool, str]:
        """验证上传文件请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)


class UploadFileResponse(BaseModel):
    """文件上传响应DTO"""
    success: bool = Field(..., description="上传是否成功")
    message: str = Field(..., description="响应消息")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")
    error: Optional[str] = Field(None, description="错误信息")


class SaveConfigRequest(BaseModel):
    """保存配置请求DTO"""
    filename: str = Field(..., description="文件名", example="config.json")
    config: Dict[str, Any] = Field(..., description="配置数据")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v:
            raise ValueError("文件名不能为空")
        return v
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        if not v:
            raise ValueError("配置数据不能为空")
        return v
    
    def validate(self) -> Tuple[bool, str]:
        """验证保存配置请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)


class SaveConfigResponse(BaseModel):
    """保存配置响应DTO"""
    success: bool = Field(..., description="保存是否成功")
    message: str = Field(..., description="响应消息")
    config_file: Optional[str] = Field(None, description="配置文件路径")
    error: Optional[str] = Field(None, description="错误信息")

class LoadConfigRequest(BaseModel):
    """加载配置请求DTO"""
    filename: str = Field(..., description="文件名", example="config.json")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v:
            raise ValueError("文件名不能为空")
        return v
    
    def validate(self) -> Tuple[bool, str]:
        """验证加载配置请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)


class LoadConfigResponse(BaseModel):
    """加载配置响应DTO"""
    success: bool = Field(..., description="加载是否成功")
    config: Optional[Dict[str, Any]] = Field(None, description="配置数据")
    config_file: Optional[str] = Field(None, description="配置文件路径")
    error: Optional[str] = Field(None, description="错误信息")


class FileInfo(BaseModel):
    """文件信息DTO"""
    original_name: str = Field(..., description="原始文件名", example="presentation.pptx")
    unique_name: str = Field(..., description="唯一文件名", example="20240101_123456_presentation.pptx")
    file_path: str = Field(..., description="文件路径", example="/config_infos/uploads/20240101_123456_presentation.pptx")
    file_size: int = Field(..., description="文件大小(字节)", example=1024000, gt=0)
    upload_time: datetime = Field(..., description="上传时间")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'original_name': self.original_name,
            'unique_name': self.unique_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'upload_time': self.upload_time.isoformat()
        }


class ConfigInfo(BaseModel):
    """配置信息DTO"""
    config_file: str = Field(..., description="配置文件名", example="config.json")
    config_path: str = Field(..., description="配置文件路径", example="/configs/config.json")
    filename: str = Field(..., description="关联的文件名", example="presentation.pptx")
    created_time: datetime = Field(..., description="创建时间")
    config_data: Dict[str, Any] = Field(..., description="配置数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'config_file': self.config_file,
            'config_path': self.config_path,
            'filename': self.filename,
            'created_time': self.created_time.isoformat(),
            'config_data': self.config_data
        }