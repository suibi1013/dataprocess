#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程节点信息仓储类
实现流程节点的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.process_node import ProcessNode


class ProcessNodeRepository(BaseRepository[ProcessNode]):
    """流程节点信息仓储类"""
    
    TABLE_NAME = "process_nodes"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化流程节点信息仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化流程节点表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            instruction_id TEXT NOT NULL,
            name TEXT,
            description TEXT,
            x REAL NOT NULL,
            y REAL NOT NULL,
            params TEXT NOT NULL
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, node: ProcessNode, flow_id: str) -> bool:
        """添加流程节点
        
        Args:
            node: 流程节点实体
            flow_id: 所属流程ID
            
        Returns:
            bool: 添加是否成功
        """
        # 将参数转换为JSON字符串
        params_json = json.dumps(node.params)
        
        data = {
            "id": node.id,
            "flow_id": flow_id,
            "instruction_id": node.instruction_id,
            "name": node.name,
            "description": node.description,
            "x": node.x,
            "y": node.y,
            "params": params_json
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, node: ProcessNode) -> bool:
        """更新流程节点
        
        Args:
            node: 流程节点实体
            
        Returns:
            bool: 更新是否成功
        """
        # 将参数转换为JSON字符串
        params_json = json.dumps(node.params)
        
        data = {
            "instruction_id": node.instruction_id,
            "name": node.name,
            "description": node.description,
            "x": node.x,
            "y": node.y,
            "params": params_json
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (node.id,))
    
    def delete(self, id: str) -> bool:
        """删除流程节点
        
        Args:
            id: 流程节点ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def delete_by_flow_id(self, flow_id: str) -> bool:
        """根据流程ID删除所有节点
        
        Args:
            flow_id: 流程ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "flow_id = ?", (flow_id,))
    
    def find_by_id(self, id: str) -> Optional[ProcessNode]:
        """根据ID查找流程节点
        
        Args:
            id: 流程节点ID
            
        Returns:
            Optional[ProcessNode]: 流程节点实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            # 解析参数JSON字符串
            if result["params"]:
                result["params"] = json.loads(result["params"])
            return self.dict_to_model(result, ProcessNode)
        return None
    
    def find_by_flow_id(self, flow_id: str) -> List[ProcessNode]:
        """根据流程ID查找所有节点
        
        Args:
            flow_id: 流程ID
            
        Returns:
            List[ProcessNode]: 流程节点列表
        """
        results = super().find_all(self.TABLE_NAME, "flow_id = ?", (flow_id,))
        nodes = []
        for result in results:
            # 解析参数JSON字符串
            if result["params"]:
                result["params"] = json.loads(result["params"])
            nodes.append(self.dict_to_model(result, ProcessNode))
        return nodes
