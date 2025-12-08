#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令分类仓储类
实现指令分类的增删改查功能
"""

from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.instruction_category import InstructionCategory


class InstructionCategoryRepository(BaseRepository[InstructionCategory]):
    """指令分类仓储类"""
    
    TABLE_NAME = "instruction_categories"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化指令分类仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化指令分类表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, category: InstructionCategory) -> bool:
        """添加指令分类
        
        Args:
            category: 指令分类实体
            
        Returns:
            bool: 添加是否成功
        """
        data = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "sort_order": category.sort_order,
            "is_active": 1 if category.is_active else 0,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, category: InstructionCategory) -> bool:
        """更新指令分类
        
        Args:
            category: 指令分类实体
            
        Returns:
            bool: 更新是否成功
        """
        data = {
            "name": category.name,
            "description": category.description,
            "sort_order": category.sort_order,
            "is_active": 1 if category.is_active else 0,
            "updated_at": category.updated_at
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (category.id,))
    
    def delete(self, id: str) -> bool:
        """删除指令分类
        
        Args:
            id: 指令分类ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[InstructionCategory]:
        """根据ID查找指令分类
        
        Args:
            id: 指令分类ID
            
        Returns:
            Optional[InstructionCategory]: 指令分类实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            # 处理布尔值转换
            result["is_active"] = bool(result["is_active"])
            return self.dict_to_model(result, InstructionCategory)
        return None
    
    def find_all(self) -> List[InstructionCategory]:
        """查找所有指令分类
        
        Returns:
            List[InstructionCategory]: 指令分类列表
        """
        results = super().find_all(self.TABLE_NAME)
        categories = []
        for result in results:
            # 处理布尔值转换
            result["is_active"] = bool(result["is_active"])
            categories.append(self.dict_to_model(result, InstructionCategory))
        # 按排序顺序排序
        categories.sort(key=lambda x: x.sort_order)
        return categories
    
    def find_active(self) -> List[InstructionCategory]:
        """查找所有激活的指令分类
        
        Returns:
            List[InstructionCategory]: 激活的指令分类列表
        """
        results = super().find_all(self.TABLE_NAME, "is_active = 1")
        categories = []
        for result in results:
            # 处理布尔值转换
            result["is_active"] = bool(result["is_active"])
            categories.append(self.dict_to_model(result, InstructionCategory))
        # 按排序顺序排序
        categories.sort(key=lambda x: x.sort_order)
        return categories