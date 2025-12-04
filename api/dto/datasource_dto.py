#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源相关数据传输对象（DTO）定义
用于数据源、Excel上传等操作
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime

class ExcelDataSourceConfig(BaseModel):
    """Excel数据源配置DTO"""
    
    file_name: Optional[str] = Field(None, description="文件名", example="data.xlsx")
    unique_name: Optional[str] = Field(None, description="唯一文件名", example="20240101_123456_data.xlsx")
    file_path: Optional[str] = Field(None, description="文件路径", example="/config_infos/uploads/20240101_123456_data.xlsx")
    file_size: Optional[int] = Field(None, description="文件大小(字节)", example=1024000, gt=0)

class ExcelDataSourceFilesConfig(BaseModel):
    """Excel数据源文件配置DTO，用于嵌套的files结构"""
    files: List[ExcelDataSourceConfig] = Field(..., description="Excel文件列表")

class ApiDataSourceConfig(BaseModel):
    """API数据源配置DTO"""
    url: str = Field(..., description="API地址", example="https://api.example.com/data")
    method: str = Field('GET', description="HTTP方法", example="GET")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    body: Optional[Dict[str, Any]] = Field(None, description="请求体")
    auth_type: Optional[str] = Field(None, description="认证类型", example="bearer")
    auth_config: Optional[Dict[str, str]] = Field(None, description="认证配置")
    timeout: Optional[int] = Field(30, description="超时时间(秒)", ge=1, le=300)
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if v.upper() not in allowed_methods:
            raise ValueError(f"不支持的HTTP方法，支持的方法: {', '.join(allowed_methods)}")
        return v.upper()
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL必须以http://或https://开头")
        return v

class DatabaseDataSourceConfig(BaseModel):
    """数据库数据源配置DTO"""
    db_type: str = Field(..., description="数据库类型", example="mysql")
    host: str = Field(..., description="主机地址", example="localhost")
    port: int = Field(..., description="端口号", example=3306, gt=0, le=65535)
    database: str = Field(..., description="数据库名", example="mydb")
    username: str = Field(..., description="用户名", example="user")
    password: str = Field(..., description="密码")
    query: Optional[str] = Field(None, description="SQL查询", example="SELECT * FROM table")
    connection_string: Optional[str] = Field(None, description="连接字符串")
    connection_timeout: Optional[int] = Field(30, description="连接超时时间(秒)", ge=1, le=300)
    
    @field_validator('db_type')
    @classmethod
    def validate_db_type(cls, v):
        supported_types = ['mysql', 'postgresql', 'sqlite', 'oracle', 'sqlserver']
        if v.lower() not in supported_types:
            raise ValueError(f"不支持的数据库类型，支持的类型: {', '.join(supported_types)}")
        return v.lower()

# 数据源配置联合类型
DataSourceConfigUnion = Union[ExcelDataSourceFilesConfig, ApiDataSourceConfig, DatabaseDataSourceConfig]

class DataSource(BaseModel):
    """通用数据源DTO（保持向后兼容）"""
    id: str = Field(..., description="数据源ID", example="ds_123456")
    user_id: str = Field(..., description="用户ID", example="user_123")
    name: str = Field(..., description="数据源名称", example="销售数据")
    description: Optional[str] = Field(None, description="数据源描述")
    type: str = Field(..., description="数据源类型", example="excel")
    config: DataSourceConfigUnion = Field(..., description="数据源配置")
    created_time: datetime = Field(..., description="创建时间")
    updated_time: datetime = Field(..., description="更新时间")
    is_active: bool = Field(True, description="是否激活")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['excel', 'api', 'database']:
            raise ValueError("不支持的数据源类型")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        config_dict = self.config.dict() if hasattr(self.config, 'dict') else self.config
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'config': config_dict,
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat(),
            'is_active': self.is_active
        }


class CreateDataSourceRequest(BaseModel):
    """创建数据源请求DTO"""
    user_id: str = Field(..., description="用户ID", example="user_123")
    name: str = Field(..., description="数据源名称", example="销售数据")
    description: Optional[str] = Field(None, description="数据源描述")
    type: str = Field(..., description="数据源类型", example="excel")
    config: Dict[str, Any] = Field(..., description="数据源配置")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v:
            raise ValueError("用户ID不能为空")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v:
            raise ValueError("数据源名称不能为空")
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['excel', 'api', 'database']:
            raise ValueError("不支持的数据源类型")
        return v
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        if not v:
            raise ValueError("数据源配置不能为空")
        return v
    
    def validate(self) -> Tuple[bool, str]:
        """验证创建数据源请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)


class UpdateDataSourceRequest(BaseModel):
    """更新数据源请求DTO"""
    name: Optional[str] = Field(None, description="数据源名称")
    description: Optional[str] = Field(None, description="数据源描述")
    config: Optional[Dict[str, Any]] = Field(None, description="数据源配置")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    def model_post_init(self, __context) -> None:
        """至少需要提供一个字段进行更新"""
        if not any([self.name, self.description, self.config, self.is_active is not None]):
            raise ValueError("至少需要提供一个字段进行更新")
    
    def validate(self) -> Tuple[bool, str]:
        """验证更新数据源请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)


class DataSourceResponse(BaseModel):
    """数据源响应DTO"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data_source: Optional[Dict[str, Any]] = Field(None, description="数据源信息")
    error: Optional[str] = Field(None, description="错误信息")


class DataSourceListResponse(BaseModel):
    """数据源列表响应DTO"""
    success: bool = Field(..., description="操作是否成功")
    data_sources: List[Dict[str, Any]] = Field(..., description="数据源列表")
    total: int = Field(..., description="总数量", ge=0)
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)
    error: Optional[str] = Field(None, description="错误信息")


class ExcelFileUploadRequest(BaseModel):
    """Excel文件上传到数据源请求DTO"""
    data_source_id: str = Field(..., description="数据源ID", example="ds_123456")
    file_name: str = Field(..., description="文件名", example="data.xlsx")
    file_size: int = Field(..., description="文件大小(字节)", example=1024000, gt=0)
    file_content: bytes = Field(..., description="文件内容")
    
    @field_validator('data_source_id')
    @classmethod
    def validate_data_source_id(cls, v):
        if not v:
            raise ValueError("数据源ID不能为空")
        return v
    
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
            raise ValueError("文件大小无效")
        if v > 10 * 1024 * 1024:  # 10MB
            raise ValueError("文件大小超过10MB限制")
        return v
    
    @field_validator('file_name')
    @classmethod
    def validate_file_extension(cls, v):
        allowed_extensions = {'.xlsx', '.xls'}
        file_ext = '.' + v.rsplit('.', 1)[-1].lower() if '.' in v else ''
        if file_ext not in allowed_extensions:
            raise ValueError("不支持的文件类型，请上传Excel文件")
        return v
    
    def validate(self) -> Tuple[bool, str]:
        """验证Excel文件上传请求"""
        try:
            self.__class__.validate(self.dict())
            return True, ""
        except ValueError as e:
            return False, str(e)

# 工厂函数和辅助方法
def create_data_source_from_dict(data: Dict[str, Any]) -> DataSource:
    """根据字典数据创建对应类型的数据源实例"""
    data_type = data.get('type', '').lower()
    
    if data_type in ['excel','api','database']:
        return DataSource(**data)
    else:
        raise ValueError(f"不支持的数据源类型: {data_type}")


def create_config_from_dict(config_data: Dict[str, Any], data_type: str) -> DataSourceConfigUnion:
    """根据配置数据和类型创建对应的配置实例"""
    data_type = data_type.lower()
    
    if data_type == 'excel':
        # 检查是否是新的嵌套结构（有files字段）
        if isinstance(config_data, dict) and 'files' in config_data:
            return ExcelDataSourceFilesConfig(**config_data)
        # 兼容旧数据结构（直接是文件列表）
        elif isinstance(config_data, list):
            return ExcelDataSourceFilesConfig(files=config_data)
        # 如果是单个文件配置
        else:
            # 尝试将单个文件配置作为列表处理
            try:
                return ExcelDataSourceFilesConfig(files=[ExcelDataSourceConfig(**config_data)])
            except Exception:
                raise ValueError(f"Excel配置格式无效: {config_data}")
    elif data_type == 'api':
        return ApiDataSourceConfig(**config_data)
    elif data_type == 'database':
        return DatabaseDataSourceConfig(**config_data)
    else:
        raise ValueError(f"不支持的数据源类型: {data_type}")


def validate_data_source_config(config_data: Dict[str, Any], data_type: str) -> Tuple[bool, str]:
    """验证数据源配置"""
    try:
        create_config_from_dict(config_data, data_type)
        return True, "配置验证成功"
    except Exception as e:
        return False, f"配置验证失败: {str(e)}"


def get_supported_data_source_types() -> List[str]:
    """获取支持的数据源类型列表"""
    return ['excel', 'api', 'database']


def is_supported_data_source_type(data_type: str) -> bool:
    """检查是否为支持的数据源类型"""
    return data_type.lower() in get_supported_data_source_types()