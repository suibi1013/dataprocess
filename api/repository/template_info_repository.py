#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模板信息仓储类
实现数据模板信息的增删改查功能
"""

from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.template_info import TemplateInfo


class TemplateInfoRepository(BaseRepository[TemplateInfo]):
    """数据模板信息仓储类"""
    
    TABLE_NAME = "template_infos"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化数据模板信息仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化数据模板信息表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            template_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            total_slides INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            slide_width INTEGER NOT NULL,
            slide_height INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, template_info: TemplateInfo) -> bool:
        """添加数据模板信息
        
        Args:
            template_info: 数据模板信息实体
            
        Returns:
            bool: 添加是否成功
        """
        data = {
            "id": template_info.id,
            "template_name": template_info.template_name,
            "filename": template_info.filename,
            "total_slides": template_info.total_slides,
            "file_path": template_info.file_path,
            "slide_width": template_info.slide_width,
            "slide_height": template_info.slide_height,
            "created_at": template_info.created_at,
            "updated_at": template_info.updated_at
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, template_info: TemplateInfo) -> bool:
        """更新数据模板信息
        
        Args:
            template_info: 数据模板信息实体
            
        Returns:
            bool: 更新是否成功
        """
        data = {
            "template_name": template_info.template_name,
            "filename": template_info.filename,
            "total_slides": template_info.total_slides,
            "file_path": template_info.file_path,
            "slide_width": template_info.slide_width,
            "slide_height": template_info.slide_height,
            "updated_at": template_info.updated_at
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (template_info.id,))
    
    def delete(self, id: str) -> bool:
        """删除数据模板信息
        
        Args:
            id: 数据模板信息ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[TemplateInfo]:
        """根据ID查找数据模板信息
        
        Args:
            id: 数据模板信息ID
            
        Returns:
            Optional[TemplateInfo]: 数据模板信息实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            return self.dict_to_model(result, TemplateInfo)
        return None
    
    def find_all(self) -> List[TemplateInfo]:
        """查找所有数据模板信息
        
        Returns:
            List[TemplateInfo]: 数据模板信息列表
        """
        results = super().find_all(self.TABLE_NAME)
        return [self.dict_to_model(result, TemplateInfo) for result in results]
    
    def find_by_filename(self, filename: str) -> Optional[TemplateInfo]:
        """根据文件名查找数据模板信息
        
        Args:
            filename: 文件名
            
        Returns:
            Optional[TemplateInfo]: 数据模板信息实体，如果不存在则返回None
        """
        results = super().find_all(self.TABLE_NAME, "filename = ?", (filename,))
        if results:
            return self.dict_to_model(results[0], TemplateInfo)
        return None
