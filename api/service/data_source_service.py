#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源服务 - 依赖注入版本
负责数据源的创建、更新、删除、查询等核心业务逻辑
支持Excel文件、API接口、数据库三种数据源类型
"""

import os
import json
import uuid
import traceback
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from utils.excel_helper import ExcelHelper

from config import config

# 移除抽象类导入，直接使用实现类
from dto.datasource_dto import (DataSourceConfigUnion,ExcelDataSourceConfig,
    create_data_source_from_dict
)
from dto.common_dto import ApiResponse

class DataSourceStorage:
    """数据源存储管理"""
    
    def __init__(self):
        self.storage_folder = config.DATA_SOURCES_FOLDER
        self.data_sources_file = os.path.join(self.storage_folder, 'data_sources.json')
        self.excel_files_folder = os.path.join(self.storage_folder, 'excel_files')
        
        # 确保目录存在
        os.makedirs(self.storage_folder, exist_ok=True)
        os.makedirs(self.excel_files_folder, exist_ok=True)
        
        # 初始化数据源文件
        if not os.path.exists(self.data_sources_file):
            self._save_data_sources({})
    
    def dict_to_dto(self, data_source_dict: Dict[str, Any]) -> DataSourceConfigUnion:
        """将字典转换为DTO对象"""
        return create_data_source_from_dict(data_source_dict)
    
    def dto_to_dict(self, data_source_dto: DataSourceConfigUnion) -> Dict[str, Any]:
        """将DTO对象转换为字典"""
        return {
            'id': data_source_dto.id,
            'user_id': data_source_dto.user_id,
            'name': data_source_dto.name,
            'description': data_source_dto.description,
            'type': data_source_dto.type,
            'config': data_source_dto.config.to_dict() if hasattr(data_source_dto.config, 'to_dict') else data_source_dto.config.__dict__,
            'created_time': data_source_dto.created_time,
            'updated_time': data_source_dto.updated_time,
            'is_active': data_source_dto.is_active
        }
    
    def get_data_source_dto(self, data_source_id: str) -> Optional[DataSourceConfigUnion]:
        """获取单个数据源并返回DTO对象"""
        data_source_dict = self.get_data_source(data_source_id)
        if data_source_dict:
            return self.dict_to_dto(data_source_dict)
        return None
    
    def save_data_source_dto(self, data_source_dto: DataSourceConfigUnion) -> bool:
        """保存DTO对象格式的数据源"""
        data_source_dict = self.dto_to_dict(data_source_dto)
        return self.save_data_source(data_source_dict)
    
    def get_user_data_sources_dto(self, page: int = 1, page_size: int = 20) -> Tuple[List[DataSourceConfigUnion], int]:
        """获取用户的数据源列表并返回DTO对象列表"""
        data_sources_dict, total = self.get_user_data_sources(page, page_size)
        data_sources_dto = [self.dict_to_dto(ds) for ds in data_sources_dict]
        return data_sources_dto, total
    
    def _load_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """加载所有数据源"""
        try:
            with open(self.data_sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载数据源失败: {str(e)}")
            return {}
    
    def _save_data_sources(self, data_sources: Dict[str, Dict[str, Any]]) -> bool:
        """保存所有数据源"""
        try:
            with open(self.data_sources_file, 'w', encoding='utf-8') as f:
                json.dump(data_sources, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存数据源失败: {str(e)}")
            return False
    
    def save_data_source(self, data_source: Dict[str, Any]) -> bool:
        """保存单个数据源"""
        data_sources = self._load_data_sources()
        data_sources[data_source['id']] = data_source
        return self._save_data_sources(data_sources)
    
    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """获取单个数据源"""
        data_sources = self._load_data_sources()
        if data_source_id not in data_sources:
            return None
        
        return data_sources[data_source_id]
    
    def get_user_data_sources(self, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的数据源列表"""
        data_sources = self._load_data_sources()
        user_sources = []
        
        for data in data_sources.values():
            user_sources.append(data)
            # if data.get('user_id') == user_id:
            #     user_sources.append(data)
        
        # 分页
        total = len(user_sources)
        start = (page - 1) * page_size
        end = start + page_size
        return user_sources[start:end], total
    
    def delete_data_source(self, data_source_id: str) -> bool:
        """删除数据源"""
        data_sources = self._load_data_sources()
        if data_source_id not in data_sources:
            return False
        
        # 获取要删除的数据源信息
        data_source = data_sources[data_source_id]
        
        # 如果是Excel类型数据源，先删除关联的文件
        if data_source.get('type') == 'excel':
            config = data_source.get('config', {})
            file_list=config.get('files',[])
            for file_info in file_list:
                file_path = file_info.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"✅ Excel文件已删除: {file_path}")
                    except Exception as e:
                        print(f"⚠️ 删除Excel文件时出错: {str(e)}")
                        # 即使文件删除失败，也继续删除数据源记录
        
        # 删除数据源记录
        del data_sources[data_source_id]
        return self._save_data_sources(data_sources)

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
    
    def __init__(self):
        self.storage = DataSourceStorage()
        self.connector = DataSourceConnector()
    
    async def create_data_source(self, data: Dict[str, Any]) -> ApiResponse[DataSourceConfigUnion]:
        """创建数据源"""
        try:
            # 生成唯一ID
            data_source_id = str(uuid.uuid4())
            
            # 创建数据源字典
            data_source_dict = {
                'id': data_source_id,
                'user_id': data.get('user_id', 'default'),
                'name': data['name'],
                'description': data.get('description'),
                'type': data['type'],
                'config': data.get('config', {}),
                'created_time': datetime.now().isoformat(),
                'updated_time': datetime.now().isoformat(),
                'is_active': True
            }
            # 创建DTO对象
            data_source_dto = create_data_source_from_dict(data_source_dict)
            
            # 保存数据源（存储层仍使用字典）
            if self.storage.save_data_source(data_source_dict):
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
    
    async def get_data_source(self, data_source_id: str) -> DataSourceConfigUnion:
        """获取数据源"""
        try:
            data_source_dict = self.storage.get_data_source(data_source_id)
            if data_source_dict:
                # 转换为DTO对象
                data_source_dto = create_data_source_from_dict(data_source_dict)
                return {
                    'success':True,
                    'message':'获取数据源成功',
                    'data_source':data_source_dto
                }
            else:
                return {
                    'success':False,
                    'message':'数据源不存在',
                    'data_source':None
                }
        except Exception as e:
            return {
                    'success':False,
                    'message':f'获取数据源失败: {str(e)}',
                    'data_source':None
                }
    
    async def get_user_data_sources(self) -> ApiResponse[List[DataSourceConfigUnion]]:
        """获取用户数据源列表"""
        try:
            data_sources_dict, total = self.storage.get_user_data_sources()
            # 转换为DTO对象列表
            data_sources_dto = [create_data_source_from_dict(ds) for ds in data_sources_dict]
            return ApiResponse(
                success=True,
                message='获取数据源列表成功',
                data={
                    'data_sources': data_sources_dto,
                    'total': total
                }
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'获取数据源列表失败: {str(e)}',
                data=None
            )
    
    async def update_data_source(self, data_source_id: str, data: Dict[str, Any]) -> DataSourceConfigUnion:
        """更新数据源"""
        try:
            data_source_dict = self.storage.get_data_source(data_source_id)
            if not data_source_dict:
                return {
                    'success':False,
                    'message':'数据源不存在',
                    'data':None
                }
            
            # 更新数据源属性
            if 'name' in data:
                data_source_dict['name'] = data['name']
            if 'description' in data:
                data_source_dict['description'] = data['description']
            if 'config' in data:
                data_source_dict['config'] = data['config']
            if 'is_active' in data:
                data_source_dict['is_active'] = data['is_active']
            
            data_source_dict['updated_time'] = datetime.now().isoformat()
            
            if self.storage.save_data_source(data_source_dict):
                # 转换为DTO对象
                data_source_dto = create_data_source_from_dict(data_source_dict)
                return {
                    'success':True,
                    'message':'数据源更新成功',
                    'data':data_source_dto
                }
            else:
                return {
                    'success':False,
                    'message':'数据源保存失败',
                    'data':None
                }
                
        except Exception as e:
            return {
                    'success':False,
                    'message':f'更新数据源失败: {str(e)}',
                    'data':None
                }
    
    async def delete_data_source(self, data_source_id: str) -> ApiResponse[bool]:
        """删除数据源"""
        try:
            if self.storage.delete_data_source(data_source_id):
                return ApiResponse(
                    success=True,
                    message='数据源删除成功',
                    data=True
                )
            else:
                return ApiResponse(
                    success=False,
                    message='数据源删除失败或不存在',
                    data=False
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                message=f'删除数据源失败: {str(e)}',
                data=False
            )
    
    async def get_data_source_data(self, data_source_id: str, sheet_name: str = None, limit: int = 100) -> ApiResponse[Dict[str, Any]]:
        """获取数据源数据"""
        try:
            # 获取数据源信息
            data_source_dict = self.storage.get_data_source(data_source_id)
            if not data_source_dict:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
            
            # 转换为DTO对象
            data_source_dto = create_data_source_from_dict(data_source_dict)
            
            if data_source_dict['type'] == 'excel':
                result = await self._get_excel_data(data_source_dict, sheet_name, limit)
            elif data_source_dict['type'] == 'api':
                result = await self._get_api_data(data_source_dict, limit)
            elif data_source_dict['type'] == 'database':
                result = await self._get_database_data(data_source_dict, limit)
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
            print(f"❌ 获取数据源数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源数据失败: {str(e)}',
                data=None
            )
    
    async def get_data_source_range(self, data_source_id: str, sheet_name: str = None, cell_range: str = None) -> ApiResponse[Dict[str, Any]]:
        """获取数据源指定范围的数据"""
        try:
            # 获取数据源信息
            data_source_dict = self.storage.get_data_source(data_source_id)
            if not data_source_dict:
                return ApiResponse(
                    success=False,
                    message='数据源不存在',
                    data=None
                )
            
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
            print(f"❌ 获取数据源范围数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源范围数据失败: {str(e)}',
                data=None
            )
    

    
    async def get_data_source_by_file_path(self, file_path: str, sheet_name: str, limit: int = 100) -> ApiResponse[Dict[str, Any]]:
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
            
            # 使用ExcelHelper读取Excel文件
            excel_data = await ExcelHelper.read_excel_file(file_path, sheet_name, limit)
            
            # 构建结果数据
            result_data = {
                'files': [{
                    'filename': os.path.basename(file_path),
                    'file_path': file_path,
                    'original_filename': os.path.basename(file_path),
                    'sheets': excel_data.get('sheet_names', [])
                }],
                'sheets': excel_data.get('sheet_names', []),
                'data': {
                    f"{os.path.basename(file_path)}_{sheet_name}": {
                        'filename': os.path.basename(file_path),
                        'sheet_name': sheet_name,
                        'columns': excel_data.get('columns', []),
                        'rows': excel_data.get('rows', []),
                        'total_rows': excel_data.get('total_rows', 0),
                        'displayed_rows': len(excel_data.get('rows', []))
                    }
                }
            }
                
            return ApiResponse(
                success=True,
                message=f'成功获取文件 {os.path.basename(file_path)} 中工作表 {sheet_name} 的数据',
                data=result_data
            )
                
        except Exception as e:
            print(f"❌ 通过文件路径获取数据源数据失败: {str(e)}")
            traceback.print_exc()
            return ApiResponse(
                success=False,
                message=f'获取数据源数据失败: {str(e)}',
                data=None
            )
            
    async def _get_excel_data(self, data_source: Dict[str, Any], sheet_name: str = None, limit: int = 100) -> Dict[str, Any]:
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
            
            for i, config_dict in enumerate(config_list):
                config=ExcelDataSourceConfig(**config_dict)
                filename = config.unique_name
                file_path=''  
                # 如果filename已经是完整路径，直接使用；否则拼接excel_files_folder
                if os.path.isabs(config.file_path) or '\\' in config.file_path or '/' in config.file_path:
                    file_path = config.file_path
                else:
                    file_path = os.path.join(self.storage.excel_files_folder, config.file_path)
                
                print(f"🔍 尝试读取Excel文件: {config.file_path} -> {file_path}")
                
                # 调用ExcelHelper读取Excel文件
                file_result = await ExcelHelper.read_excel_file(file_path, sheet_name, limit)
                
                
                if file_result['success'] and file_result['data']:
                    # 获取返回的数据
                    file_data = file_result['data']
                    
                    # 处理文件信息，保留original_filename
                    for file_info in file_data['files']:
                        # 添加原始文件名信息
                        file_info['filename'] = config.unique_name
                        file_info['original_filename'] = config.file_name
                        result_data['files'].append(file_info)
                    
                    # 合并工作表名称（去重）
                    for sheet in file_data['sheets']:
                        if sheet not in result_data['sheets']:
                            result_data['sheets'].append(sheet)
                    
                    # 合并数据，修改键名以匹配原有格式
                    for original_key, sheet_data in file_data['data'].items():
                        # 使用唯一名称生成新的键
                        new_key = f"{filename}_{sheet_data['sheet_name']}"
                        # 复制数据并确保包含所有必要字段
                        result_data['data'][new_key] = {
                            'filename': filename,
                            'sheet_name': sheet_data['sheet_name'],
                            'columns': sheet_data['columns'],
                            'rows': sheet_data['rows'],
                            'total_rows': sheet_data['total_rows'],
                            'displayed_rows': sheet_data['displayed_rows']
                        }
                else:
                    print(f"❌ 读取文件 {file_path} 失败: {file_result.get('message', '未知错误')}")
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
            print(f"❌ 读取Excel数据失败: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'读取Excel数据失败: {str(e)}',
                'data': None
            }
    
    async def _get_api_data(self, data_source: Dict[str, Any], limit: int = 100) -> Dict[str, Any]:
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
            
            response = requests.request(method, url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 如果返回的是列表，限制数量
            if isinstance(data, list) and len(data) > limit:
                data = data[:limit]
            
            return {
                'success': True,
                'message': '数据获取成功',
                'data': {
                    'api_response': data,
                    'total_items': len(data) if isinstance(data, list) else 1,
                    'displayed_items': len(data) if isinstance(data, list) else 1
                }
            }
            
        except Exception as e:
            print(f"❌ 获取API数据失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取API数据失败: {str(e)}',
                'data': None
            }
    
    async def _get_database_data(self, data_source: Dict[str, Any], limit: int = 100) -> Dict[str, Any]:
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
            
            # 使用ExcelHelper读取Excel范围数据
            range_data = ExcelHelper._read_excel_range_with_xlwings(file_path, sheet_name, cell_range)
            
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
            print(f"❌ 读取Excel范围数据失败: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'读取Excel范围数据失败: {str(e)}',
                'data': None
            }        