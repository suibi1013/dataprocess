#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源仓储类
实现数据源的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.data_source import DataSource


class DataSourceRepository(BaseRepository[DataSource]):
    """数据源仓储类"""
    
    TABLE_NAME = "data_sources"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化数据源仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化数据源表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL,
            config TEXT NOT NULL,
            created_time TEXT NOT NULL,
            updated_time TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, data_source: DataSource) -> bool:
        """添加数据源
        
        Args:
            data_source: 数据源实体
            
        Returns:
            bool: 添加是否成功
        """
        # 将配置转换为JSON字符串
        config_json = json.dumps(data_source.config)
        
        data = {
            "id": data_source.id,
            "user_id": data_source.user_id,
            "name": data_source.name,
            "description": data_source.description,
            "type": data_source.type,
            "config": config_json,
            "created_time": data_source.created_time,
            "updated_time": data_source.updated_time,
            "is_active": 1 if data_source.is_active else 0
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, data_source: DataSource) -> bool:
        """更新数据源
        
        Args:
            data_source: 数据源实体
            
        Returns:
            bool: 更新是否成功
        """
        # 将配置转换为JSON字符串
        config_json = json.dumps(data_source.config)
        
        data = {
            "name": data_source.name,
            "description": data_source.description,
            "type": data_source.type,
            "config": config_json,
            "updated_time": data_source.updated_time,
            "is_active": 1 if data_source.is_active else 0
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (data_source.id,))
    
    def delete(self, id: str) -> bool:
        """删除数据源
        
        Args:
            id: 数据源ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[DataSource]:
        """根据ID查找数据源
        
        Args:
            id: 数据源ID
            
        Returns:
            Optional[DataSource]: 数据源实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            return self._convert_result_to_source(result)
        return None
    
    def find_all(self) -> List[DataSource]:
        """查找所有数据源
        
        Returns:
            List[DataSource]: 数据源列表
        """
        results = super().find_all(self.TABLE_NAME)
        sources = [self._convert_result_to_source(result) for result in results]
        # 按更新时间倒序排序
        sources.sort(key=lambda x: x.updated_time, reverse=True)
        return sources
    
    def find_by_type(self, type: str) -> List[DataSource]:
        """根据类型查找数据源
        
        Args:
            type: 数据源类型
            
        Returns:
            List[DataSource]: 数据源列表
        """
        results = super().find_all(self.TABLE_NAME, "type = ?", (type,))
        sources = [self._convert_result_to_source(result) for result in results]
        # 按更新时间倒序排序
        sources.sort(key=lambda x: x.updated_time, reverse=True)
        return sources
    
    def find_active(self) -> List[DataSource]:
        """查找所有激活的数据源
        
        Returns:
            List[DataSource]: 激活的数据源列表
        """
        results = super().find_all(self.TABLE_NAME, "is_active = 1")
        sources = [self._convert_result_to_source(result) for result in results]
        # 按更新时间倒序排序
        sources.sort(key=lambda x: x.updated_time, reverse=True)
        return sources
    
    def _convert_result_to_source(self, result: dict) -> DataSource:
        """将查询结果转换为数据源实体
        
        Args:
            result: 查询结果
            
        Returns:
            DataSource: 数据源实体
        """
        # 处理布尔值转换
        result["is_active"] = bool(result["is_active"])
        
        # 解析配置JSON字符串
        if result["config"]:
            result["config"] = json.loads(result["config"])
        
        return self.dict_to_model(result, DataSource)
