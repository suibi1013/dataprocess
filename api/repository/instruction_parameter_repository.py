#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令参数仓储类
实现指令参数的增删改查功能
"""

from typing import List, Optional
from repository.base_repository import BaseRepository, AsyncSQLiteConnectionPool
from entity.instruction_parameter import InstructionParameter


class InstructionParameterRepository(BaseRepository[InstructionParameter]):
    """指令参数仓储类"""
    
    TABLE_NAME = "instruction_parameters"
    
    def __init__(self, db_pool: AsyncSQLiteConnectionPool):
        """初始化指令参数仓储类
        
        Args:
            db_pool: SQLite连接池实例（异步）
        """
        super().__init__(db_pool)
        # 初始化表结构将在异步任务中执行
    
    async def _init_table(self):
        """初始化指令参数字表结构（异步）"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            instruction_id TEXT NOT NULL,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT,
            display_type TEXT DEFAULT 'string',
            value_type TEXT DEFAULT 'string',
            required INTEGER DEFAULT 0,
            default_value TEXT,
            direction INTEGER DEFAULT 0,
            api_url TEXT,
            event_script TEXT,
            FOREIGN KEY (instruction_id) REFERENCES instruction_items(id) ON DELETE CASCADE
        )
        """
        await self.execute_non_query(create_table_sql)
    
    async def add(self, instruction_id: str, param: InstructionParameter) -> bool:
        """添加指令参数（异步）
        
        Args:
            instruction_id: 指令ID
            param: 指令参数实体
            
        Returns:
            bool: 添加是否成功
        """
        import uuid
        from datetime import datetime
        
        # 生成唯一ID
        param_id = str(uuid.uuid4())
        
        data = {
            "id": param_id,
            "instruction_id": instruction_id,
            "name": param.name,
            "label": param.label,
            "description": param.description,
            "display_type": param.display_type,
            "value_type": param.value_type,
            "required": 1 if param.required else 0,
            "default_value": param.default_value,
            "direction": param.direction,
            "api_url": param.api_url,
            "event_script": param.event_script
        }
        return await self.insert(self.TABLE_NAME, data)
    
    async def add_batch(self, instruction_id: str, params: List[InstructionParameter]) -> bool:
        """批量添加指令参数（异步）
        
        Args:
            instruction_id: 指令ID
            params: 指令参数实体列表
            
        Returns:
            bool: 添加是否成功
        """
        import uuid
        
        if not params:
            return True
        
        data_list = []
        for param in params:
            # 生成唯一ID
            param_id = str(uuid.uuid4())
            
            data = {
                "id": param_id,
                "instruction_id": instruction_id,
                "name": param.name,
                "label": param.label,
                "description": param.description,
                "display_type": param.display_type,
                "value_type": param.value_type,
                "required": 1 if param.required else 0,
                "default_value": param.default_value,
                "direction": param.direction,
                "api_url": param.api_url,
                "event_script": param.event_script
            }
            data_list.append(data)
        
        return await self.insert_batch(self.TABLE_NAME, data_list)
    
    async def update(self, param: InstructionParameter) -> bool:
        """更新指令参数（异步）
        
        Args:
            param: 指令参数实体
            
        Returns:
            bool: 更新是否成功
        """
        data = {
            "name": param.name,
            "label": param.label,
            "description": param.description,
            "display_type": param.display_type,
            "value_type": param.value_type,
            "required": 1 if param.required else 0,
            "default_value": param.default_value,
            "direction": param.direction,
            "api_url": param.api_url,
            "event_script": param.event_script
        }
        return await super().update(self.TABLE_NAME, data, "id = ?", (param.id,))
    
    async def delete(self, id: str) -> bool:
        """删除指令参数（异步）
        
        Args:
            id: 指令参数ID
            
        Returns:
            bool: 删除是否成功
        """
        return await super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    async def delete_by_instruction_id(self, instruction_id: str) -> bool:
        """根据指令ID删除所有相关参数（异步）
        
        Args:
            instruction_id: 指令ID
            
        Returns:
            bool: 删除是否成功
        """
        return await super().delete(self.TABLE_NAME, "instruction_id = ?", (instruction_id,))
    
    async def find_by_id(self, id: str) -> Optional[InstructionParameter]:
        """根据ID查找指令参数（异步）
        
        Args:
            id: 指令参数ID
            
        Returns:
            Optional[InstructionParameter]: 指令参数实体，如果不存在则返回None
        """
        result = await super().find_by_id(self.TABLE_NAME, id)
        if result:
            # 确保id字段是字符串类型
            result["id"] = str(result["id"])
            result["required"] = bool(result["required"])
            return self.dict_to_model(result, InstructionParameter)
        return None
    
    async def find_by_instruction_id(self, instruction_id: str) -> List[InstructionParameter]:
        """根据指令ID查找所有参数（异步）
        
        Args:
            instruction_id: 指令ID
            
        Returns:
            List[InstructionParameter]: 指令参数列表
        """
        results = await super().find_all(self.TABLE_NAME, "instruction_id = ?", (instruction_id,))
        params = []
        for result in results:
            # 确保id字段是字符串类型
            result["id"] = str(result["id"])
            result["required"] = bool(result["required"])
            params.append(self.dict_to_model(result, InstructionParameter))
        return params
    
    async def find_all(self) -> List[InstructionParameter]:
        """查找所有指令参数（异步）
        
        Returns:
            List[InstructionParameter]: 指令参数列表
        """
        results = await super().find_all(self.TABLE_NAME)
        params = []
        for result in results:
            # 确保id字段是字符串类型
            result["id"] = str(result["id"])
            result["required"] = bool(result["required"])
            params.append(self.dict_to_model(result, InstructionParameter))
        return params