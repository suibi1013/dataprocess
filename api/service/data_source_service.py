#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源服务 - 依赖注入版本
负责数据源的创建、更新、删除、查询等核心业务逻辑
支持Excel文件、API接口、数据库三种数据源类型
"""

import os
import uuid
import traceback
import requests
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from utils.excel_helper import ExcelHelper

from config import config

# 移除抽象类导入，直接使用实现类
from dto.datasource_dto import (
    DataSourceConfigUnion, 
    ExcelDataSourceConfig,
    create_data_source_from_dict
)
from dto.common_dto import ApiResponse
from repository.data_source_repository import DataSourceRepository
from entity.data_source import DataSource



class DataSourceConnector:
    """数据源连接器"""
    
    def test_connection(self, data_source_type: str, config: dict) -> tuple[bool, dict]:
        """测试数据源连接"""
        try:
            if data_source_type == 'excel':
                return self._test_excel_connection(config)
            elif data_source_type == 'api':
                return self._test_api_connection(config)
            elif data_source_type == 'database':
                return self._test_database_connection(config)
            else:
                return False, {'error': f'不支持的数据源类型: {data_source_type}'}
        except Exception as e:
            return False, {'error': f'连接测试失败: {str(e)}'}
    
    def _test_excel_connection(self, config: dict) -> tuple[bool, dict]:
        """测试Excel文件连接"""
        try:
            file_path = config.get('file_path')
            if not file_path or not os.path.exists(file_path):
                return False, {'error': 'Excel文件不存在'}
            
            # 这里可以添加更多Excel文件验证逻辑
            return True, {
                'message': 'Excel文件连接成功',
                'file_size': os.path.getsize(file_path),
                'file_path': file_path
            }
        except Exception as e:
            return False, {'error': f'Excel连接测试失败: {str(e)}'}
    
    def _test_api_connection(self, config: dict) -> tuple[bool, dict]:
        """测试API连接"""
        try:
            url = config.get('url')
            method = config.get('method', 'GET').upper()
            headers = config.get('headers', {})
            timeout = config.get('timeout', 10)
            
            if not url:
                return False, {'error': 'API URL不能为空'}
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout
            )
            
            return True, {
                'message': 'API连接成功',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return False, {'error': f'API连接测试失败: {str(e)}'}
    
    def _test_database_connection(self, config: dict) -> tuple[bool, dict]:
        """测试数据库连接"""
        try:
            db_type = config.get('db_type')
            if db_type == 'mysql':
                return self._test_mysql_connection(config)
            elif db_type == 'postgresql':
                return self._test_postgresql_connection(config)
            else:
                return False, {'error': f'不支持的数据库类型: {db_type}'}
        except Exception as e:
            return False, {'error': f'数据库连接测试失败: {str(e)}'}
    
    def _test_mysql_connection(self, config: dict) -> tuple[bool, dict]:
        """测试MySQL连接"""
        try:
            # 这里应该实现真实的MySQL连接测试
            # 暂时返回模拟结果
            return True, {
                'message': 'MySQL连接成功',
                'host': config.get('host'),
                'database': config.get('database')
            }
        except Exception as e:
            return False, {'error': f'MySQL连接失败: {str(e)}'}
    
    def _test_postgresql_connection(self, config: dict) -> tuple[bool, dict]:
        """测试PostgreSQL连接"""
        try:
            # 这里应该实现真实的PostgreSQL连接测试
            # 暂时返回模拟结果
            return True, {
                'message': 'PostgreSQL连接成功',
                'host': config.get('host'),
                'database': config.get('database')
            }
        except Exception as e:
            return False, {'error': f'PostgreSQL连接失败: {str(e)}'}

class DataSourceservice:
    """数据源服务 - 依赖注入版本"""
    
    def __init__(self, data_source_repo: DataSourceRepository = None):
        """初始化数据源服务
        
        Args:
            data_source_repo: 数据源仓储实例，将通过依赖注入获取
        """
        self.data_source_repo = data_source_repo
        self.connector = DataSourceConnector()
        self.storage_folder = config.DATA_SOURCES_FOLDER
        self.excel_files_folder = os.path.join(self.storage_folder, 'excel_files')
    
    async def create_data_source(self, data: Dict[str, Any]) -> ApiResponse[DataSourceConfigUnion]:
        """创建数据源"""
        try:
            # 生成唯一ID
            data_source_id = str(uuid.uuid4())
            
            # 创建数据源实体
            data_source = DataSource(
                id=data_source_id,
                user_id=data.get('user_id', 'default'),
                name=data['name'],
                description=data.get('description'),
                type=data['type'],
                config=data.get('config', {}),
                created_time=datetime.now().isoformat(),
                updated_time=datetime.now().isoformat(),
                is_active=True
            )
            # 创建DTO对象
            data_source_dto = create_data_source_from_dict(data_source.model_dump())
            
            # 保存数据源（异步执行）
            if await self.data_source_repo.add(data_source):
                return ApiResponse(
                    success=True,
                    message='数据源创建成功',
                    data=data_source_dto
                )
            else:
                return ApiResponse(
                    success=False,
                    message='数据源保存失败',
                    data=None
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'创建数据源失败: {str(e)}',
                data=None
            )
    
    async def get_data_source(self, data_source_id: str) -> ApiResponse:
        """获取数据源"""
        try:
            # 获取数据源（异步执行）
            data_source = await self.data_source_repo.find_by_id(data_source_id)
            if data_source:
                # 转换为DTO对象
                data_source_dto = create_data_source_from_dict(data_source.model_dump())
                return ApiResponse(
                    success=True,
                    message='获取数据源成功',
                    data=data_source_dto
                )
            else:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'获取数据源失败: {str(e)}',
                data=None
            )
    
    async def get_user_data_sources(self) -> ApiResponse[List[DataSourceConfigUnion]]:
        """获取用户数据源列表"""
        try:
            # 获取所有数据源（异步执行）
            data_sources = await self.data_source_repo.find_all()
            # 转换为DTO对象列表
            data_sources_dto = [create_data_source_from_dict(ds.model_dump()) for ds in data_sources]
            return ApiResponse(
                success=True,
                message='获取数据源列表成功',
                data={
                    'data_sources': data_sources_dto,
                    'total': len(data_sources)
                }
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'获取数据源列表失败: {str(e)}',
                data=None
            )
    
    async def update_data_source(self, data_source_id: str, data: Dict[str, Any]) -> ApiResponse:
        """更新数据源"""
        try:
            # 获取数据源（异步执行）
            data_source = await self.data_source_repo.find_by_id(data_source_id)
            if not data_source:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
            
            # 更新数据源属性
            if 'name' in data:
                data_source.name = data['name']
            if 'description' in data:
                data_source.description = data['description']
            if 'config' in data:
                data_source.config = data['config']
            if 'is_active' in data:
                data_source.is_active = data['is_active']
            
            data_source.updated_time = datetime.now().isoformat()
            
            # 更新数据源（异步执行）
            if await self.data_source_repo.update(data_source):
                # 转换为DTO对象
                data_source_dto = create_data_source_from_dict(data_source.model_dump())
                return ApiResponse(
                    success=True,
                    message='数据源更新成功',
                    data=data_source_dto
                )
            else:
                return ApiResponse(
                    success=False,
                    message='数据源保存失败',
                    data=None
                )
                
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'更新数据源失败: {str(e)}',
                data=None
            )
    
    async def delete_data_source(self, data_source_id: str) -> ApiResponse[bool]:
        """删除数据源"""
        try:
            # 获取要删除的数据源信息（异步执行）
            data_source = await self.data_source_repo.find_by_id(data_source_id)
            if not data_source:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=False
                )
            
            # 如果是Excel类型数据源，先删除关联的文件
            if data_source.type == 'excel':
                config = data_source.config
                file_list = []
                
                # 处理配置结构
                if isinstance(config, dict) and 'files' in config:
                    file_list = config['files']
                elif isinstance(config, list):
                    file_list = config
                
                for file_info in file_list:
                    file_path = file_info.get('file_path')
                    if file_path:
                        # 检查文件是否存在并删除（异步执行）
                        def remove_file():
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                    print(f"Excel文件已删除: {file_path}")
                                except Exception as e:
                                    print(f"删除Excel文件时出错: {str(e)}")
                        
                        await asyncio.to_thread(remove_file)
            
            # 删除数据源记录（异步执行）
            if await self.data_source_repo.delete(data_source_id):
                return ApiResponse(
                    success=True,
                    message='数据源删除成功',
                    data=True
                )
            else:
                return ApiResponse(
                    success=False,
                    message='数据源删除失败',
                    data=False
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'删除数据源失败: {str(e)}',
                data=False
            )
    
    async def get_data_source_data(self, data_source_id: str, sheet_name: str = None, page: int = 1, page_size: int = 100) -> ApiResponse[Dict[str, Any]]:
        """获取数据源数据"""
        try:
            # 获取数据源信息（异步执行）
            data_source = await self.data_source_repo.find_by_id(data_source_id)
            if not data_source:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
            
            # 转换为字典
            data_source_dict = data_source.model_dump()
            
            # 转换为DTO对象
            data_source_dto = create_data_source_from_dict(data_source_dict)
            
            if data_source_dict['type'] == 'excel':
                result = await self._get_excel_data(data_source_dict, sheet_name, page, page_size)
            elif data_source_dict['type'] == 'api':
                result = await self._get_api_data(data_source_dict, page, page_size)
            elif data_source_dict['type'] == 'database':
                result = await self._get_database_data(data_source_dict, page, page_size)
            else:
                return ApiResponse(
                    success=False,
                    message=f'不支持的数据源类型: {data_source_dict["type"]}',
                    data=None
                )
            
            # 直接返回字典结果包装的ApiResponse
            return ApiResponse(
                success=result['success'],
                message=result['message'],
                data=result['data']
            )
                
        except Exception as e:
            print(f"获取数据源数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源数据失败: {str(e)}',
                data=None
            )
    
    async def get_data_source_range(self, data_source_id: str, sheet_name: str = None, cell_range: str = None) -> ApiResponse[Dict[str, Any]]:
        """获取数据源指定范围的数据"""
        try:
            # 获取数据源信息（异步执行）
            data_source = await self.data_source_repo.find_by_id(data_source_id)
            if not data_source:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
            
            # 转换为字典
            data_source_dict = data_source.model_dump()
            
            if data_source_dict['type'] == 'excel':
                result = await self._get_excel_range_data(data_source_dict, sheet_name, cell_range)
            else:
                return ApiResponse(
                    success=False,
                    message=f'数据源类型 {data_source_dict["type"]} 不支持范围查询',
                    data=None
                )
            
            return ApiResponse(
                success=result['success'],
                message=result['message'],
                data=result['data']
            )
                
        except Exception as e:
            print(f"获取数据源范围数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源范围数据失败: {str(e)}',
                data=None
            )
    

    
    async def get_data_source_by_file_path(self, file_path: str, sheet_name: str, page: int = 1, page_size: int = 100) -> ApiResponse[Dict[str, Any]]:
        """通过文件路径和工作表名获取数据源数据"""
        try:
            # 验证文件是否存在
            if not os.path.exists(file_path):
                return ApiResponse(
                    success=False,
                    message=f'文件不存在: {file_path}',
                    data=None
                )
            
            # 验证文件类型
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return ApiResponse(
                    success=False,
                    message=f'不支持的文件类型: {file_path}',
                    data=None
                )
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 使用ExcelHelper读取Excel文件
            excel_data = await ExcelHelper.read_excel_file(file_path, sheet_name, page_size, offset)
            
            # 检查ExcelHelper返回值
            if not excel_data.get('success') or not excel_data.get('data'):
                return ApiResponse(
                    success=False,
                    message=f'读取Excel文件失败: {excel_data.get("message", "未知错误")}',
                    data=None
                )
            
            # 获取ExcelHelper返回的data部分
            excel_data_content = excel_data.get('data', {})
            
            # 构建直接返回的工作表数据
            sheet_data = {
                'file_name': os.path.basename(file_path),
                'sheet_name': sheet_name,
                'columns': [],
                'rows': [],
                'total_rows': 0,
                'displayed_rows': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
            
            # 从ExcelHelper返回的数据中提取工作表数据
            if excel_data_content.get('data'):
                # 查找对应的工作表数据
                sheet_key = f"{os.path.basename(file_path)}_{sheet_name}"
                if excel_data_content['data'].get(sheet_key):
                    sheet_data = excel_data_content['data'][sheet_key]
                    # 添加分页信息
                    sheet_data['page'] = page
                    sheet_data['page_size'] = page_size
                    sheet_data['total_pages'] = (sheet_data['total_rows'] + page_size - 1) // page_size
            
            return ApiResponse(
                success=True,
                message=f'成功获取文件 {os.path.basename(file_path)} 中工作表 {sheet_name} 的数据',
                data=sheet_data
            )
                
        except Exception as e:
            print(f"通过文件路径获取数据源数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源数据失败: {str(e)}',
                data=None
            )
            
    async def _get_excel_data(self, data_source: Dict[str, Any], sheet_name: str = None, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """获取Excel文件数据 - 使用file_service中的公共方法"""
        try:
            config_data = data_source.get('config', {})
            # 处理多文件数据
            result_data = {
                'files': [],
                'sheets': [],
                'data': {}
            }
            
            # 处理新的嵌套结构和旧的数据结构
            config_list = []
            if isinstance(config_data, dict) and 'files' in config_data:
                # 新的嵌套结构
                config_list = config_data['files']
            elif isinstance(config_data, list):
                # 旧的数据结构
                config_list = config_data
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            for i, config_dict in enumerate(config_list):
                config=ExcelDataSourceConfig(**config_dict)
                file_name = config.unique_name
                file_path=''  
                # 如果file_name已经是完整路径，直接使用；否则拼接excel_files_folder
                if os.path.isabs(config.file_path) or '\\' in config.file_path or '/' in config.file_path:
                    file_path = config.file_path
                else:
                    file_path = os.path.join(self.excel_files_folder, config.file_path)
                
                print(f"尝试读取Excel文件: {config.file_path} -> {file_path}")
                
                # 调用ExcelHelper读取Excel文件
                file_result = await ExcelHelper.read_excel_file(file_path, sheet_name, page_size, offset)
                
                
                if file_result['success'] and file_result['data']:
                    # 获取返回的数据
                    file_data = file_result['data']
                    
                    # 处理文件信息，保留original_file_name
                    for file_info in file_data['files']:
                        # 添加原始文件名信息
                        file_info['file_name'] = config.unique_name
                        file_info['original_file_name'] = config.file_name
                        result_data['files'].append(file_info)
                    
                    # 合并工作表名称（去重）
                    for sheet in file_data['sheets']:
                        if sheet not in result_data['sheets']:
                            result_data['sheets'].append(sheet)
                    
                    # 合并数据，修改键名以匹配原有格式
                    for original_key, sheet_data in file_data['data'].items():
                        # 使用唯一名称生成新的键
                        new_key = f"{file_name}_{sheet_data['sheet_name']}"
                        # 复制数据并确保包含所有必要字段
                        result_data['data'][new_key] = {
                            'file_name': file_name,
                            'sheet_name': sheet_data['sheet_name'],
                            'columns': sheet_data['columns'],
                            'rows': sheet_data['rows'],
                            'total_rows': sheet_data['total_rows'],
                            'displayed_rows': sheet_data['displayed_rows'],
                            'page': page,
                            'page_size': page_size,
                            'total_pages': (sheet_data['total_rows'] + page_size - 1) // page_size
                        }
                else:
                    print(f"读取文件 {file_path} 失败: {file_result.get('message', '未知错误')}")
                    continue
            
            if not result_data['files']:
                return {
                    'success': False,
                    'message': '没有找到可读取的Excel文件',
                    'data': None
                }
            
            return {
                'success': True,
                'message': f'数据获取成功，共处理 {len(result_data["files"])} 个文件',
                'data': result_data
            }
            
        except Exception as e:
            print(f"读取Excel数据失败: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'读取Excel数据失败: {str(e)}',
                'data': None
            }
    
    async def _get_api_data(self, data_source: Dict[str, Any], page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """获取API数据源数据"""
        try:
            config = data_source.get('config', {})
            url = config.get('url')
            method = config.get('method', 'GET')
            headers = config.get('headers', {})
            
            if not url:
                return {
                    'success': False,
                    'message': 'API URL不存在',
                    'data': None
                }
            
            # 使用线程池异步执行requests调用
            import asyncio
            def make_request():
                response = requests.request(method, url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            
            data = await asyncio.to_thread(make_request)
            
            # 计算总数和分页数据
            total_items = len(data) if isinstance(data, list) else 1
            total_pages = (total_items + page_size - 1) // page_size
            
            # 如果返回的是列表，进行分页
            if isinstance(data, list):
                start = (page - 1) * page_size
                end = start + page_size
                data = data[start:end]
            
            return {
                'success': True,
                'message': '数据获取成功',
                'data': {
                    'api_response': data,
                    'total_items': total_items,
                    'displayed_items': len(data) if isinstance(data, list) else 1,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }
            }
            
        except Exception as e:
            print(f"获取API数据失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取API数据失败: {str(e)}',
                'data': None
            }
    
    async def _get_database_data(self, data_source: Dict[str, Any], page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """获取数据库数据"""
        return {
            'success': False,
            'message': '数据库数据源暂未实现',
            'data': None
        }
        
    async def _get_excel_range_data(self, data_source_dict: Dict[str, Any], sheet_name: str = None, cell_range: str = None) -> Dict[str, Any]:
        """获取Excel数据源指定范围的数据"""
        try:
            config = data_source_dict.get('config', {})
            file_path = config.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f'Excel文件不存在: {file_path}',
                    'data': None
                }
            
            # 使用ExcelHelper读取Excel范围数据（异步执行）
            import asyncio
            range_data = await asyncio.to_thread(ExcelHelper._read_excel_range_with_xlwings, file_path, sheet_name, cell_range)
            
            # 处理返回格式差异（excel_helper返回'data'，而原方法期望'table_data'）
            if 'data' in range_data:
                range_data['table_data'] = range_data.pop('data')
            
            # 构建返回数据
            result_data = {
                'success': True,
                'message': 'Excel范围数据读取成功',
                'data': range_data
            }
            return result_data
            
        except Exception as e:
            print(f"读取Excel范围数据失败: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'读取Excel范围数据失败: {str(e)}',
                'data': None
            }

    async def get_excel_file_sheets(self, file_path: str) -> ApiResponse[Dict[str, Any]]:
        """获取Excel文件的sheet名称集合
        
        Args:
            file_path: Excel文件路径
        """
        try:
            # 验证文件是否存在
            if not os.path.exists(file_path):
                return ApiResponse(
                    success=False,
                    message=f'文件不存在: {file_path}',
                    data=None
                )
            
            # 验证文件类型
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return ApiResponse(
                    success=False,
                    message=f'不支持的文件类型: {file_path}',
                    data=None
                )
            
            # 调用ExcelHelper获取sheet名称（异步执行）
            import asyncio
            sheet_names = await asyncio.to_thread(ExcelHelper.get_excel_sheet_names, file_path)
            
            # 获取文件名
            file_name = os.path.basename(file_path)
            if file_name.endswith(('.xlsx', '.xls')):
                file_name = os.path.splitext(file_name)[0]
            
            # 构建返回数据
            result_data = {
                'file': {
                    'file_name': file_name,
                    'file_path': file_path,
                    'sheets': sheet_names
                },
                'sheets': sheet_names
            }
            
            return ApiResponse(
                success=True,
                message=f'成功获取文件 "{file_name}" 的sheet名称集合',
                data=result_data
            )
                
        except Exception as e:
            print(f"获取文件sheet名称失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取文件sheet名称失败: {str(e)}',
                data=None
            )