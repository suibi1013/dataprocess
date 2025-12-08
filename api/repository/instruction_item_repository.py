#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令信息仓储类
实现指令信息的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.instruction_item import InstructionItem
from entity.instruction_parameter import InstructionParameter


class InstructionItemRepository(BaseRepository[InstructionItem]):
    """指令信息仓储类"""
    
    TABLE_NAME = "instruction_items"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化指令信息仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化指令信息表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category_id TEXT NOT NULL,
            icon TEXT,
            description TEXT,
            python_script TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES instruction_categories(id)
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, item: InstructionItem) -> bool:
        """添加指令信息
        
        Args:
            item: 指令信息实体
            
        Returns:
            bool: 添加是否成功
        """
        data = {
            "id": item.id,
            "name": item.name,
            "category_id": item.category_id,
            "icon": item.icon,
            "description": item.description,
            "python_script": item.python_script,
            "sort_order": item.sort_order,
            "is_active": 1 if item.is_active else 0,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, item: InstructionItem) -> bool:
        """更新指令信息
        
        Args:
            item: 指令信息实体
            
        Returns:
            bool: 更新是否成功
        """
        data = {
            "name": item.name,
            "category_id": item.category_id,
            "icon": item.icon,
            "description": item.description,
            "python_script": item.python_script,
            "sort_order": item.sort_order,
            "is_active": 1 if item.is_active else 0,
            "updated_at": item.updated_at
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (item.id,))
    
    def delete(self, id: str) -> bool:
        """删除指令信息
        
        Args:
            id: 指令信息ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[InstructionItem]:
        """根据ID查找指令信息
        
        Args:
            id: 指令信息ID
            
        Returns:
            Optional[InstructionItem]: 指令信息实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            return self._convert_result_to_item(result)
        return None
    
    def find_all(self) -> List[InstructionItem]:
        """查找所有指令信息
        
        Returns:
            List[InstructionItem]: 指令信息列表
        """
        results = super().find_all(self.TABLE_NAME)
        items = [self._convert_result_to_item(result) for result in results]
        # 按排序顺序排序
        items.sort(key=lambda x: x.sort_order)
        return items
    
    def find_by_category(self, category_id: str) -> List[InstructionItem]:
        """根据分类ID查找指令信息
        
        Args:
            category_id: 分类ID
            
        Returns:
            List[InstructionItem]: 指令信息列表
        """
        results = super().find_all(self.TABLE_NAME, "category_id = ?", (category_id,))
        items = [self._convert_result_to_item(result) for result in results]
        # 按排序顺序排序
        items.sort(key=lambda x: x.sort_order)
        return items
    
    def find_active(self) -> List[InstructionItem]:
        """查找所有激活的指令信息
        
        Returns:
            List[InstructionItem]: 激活的指令信息列表
        """
        results = super().find_all(self.TABLE_NAME, "is_active = 1")
        items = [self._convert_result_to_item(result) for result in results]
        # 按排序顺序排序
        items.sort(key=lambda x: x.sort_order)
        return items
    
    def _convert_result_to_item(self, result: dict) -> InstructionItem:
        """将查询结果转换为指令信息实体
        
        Args:
            result: 查询结果
            
        Returns:
            InstructionItem: 指令信息实体
        """
        # 处理布尔值转换
        result["is_active"] = bool(result["is_active"])        
                
        return self.dict_to_model(result, InstructionItem)