#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程边信息仓储类
实现流程边的增删改查功能
"""

from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.process_edge import ProcessEdge


class ProcessEdgeRepository(BaseRepository[ProcessEdge]):
    """流程边信息仓储类"""
    
    TABLE_NAME = "process_edges"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化流程边信息仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化流程边表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            label TEXT
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, edge: ProcessEdge, flow_id: str) -> bool:
        """添加流程边
        
        Args:
            edge: 流程边实体
            flow_id: 所属流程ID
            
        Returns:
            bool: 添加是否成功
        """
        data = {
            "id": edge.id,
            "flow_id": flow_id,
            "source": edge.source,
            "target": edge.target,
            "label": edge.label
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, edge: ProcessEdge) -> bool:
        """更新流程边
        
        Args:
            edge: 流程边实体
            
        Returns:
            bool: 更新是否成功
        """
        data = {
            "source": edge.source,
            "target": edge.target,
            "label": edge.label
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (edge.id,))
    
    def delete(self, id: str) -> bool:
        """删除流程边
        
        Args:
            id: 流程边ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def delete_by_flow_id(self, flow_id: str) -> bool:
        """根据流程ID删除所有边
        
        Args:
            flow_id: 流程ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "flow_id = ?", (flow_id,))
    
    def find_by_id(self, id: str) -> Optional[ProcessEdge]:
        """根据ID查找流程边
        
        Args:
            id: 流程边ID
            
        Returns:
            Optional[ProcessEdge]: 流程边实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            return self.dict_to_model(result, ProcessEdge)
        return None
    
    def find_by_flow_id(self, flow_id: str) -> List[ProcessEdge]:
        """根据流程ID查找所有边
        
        Args:
            flow_id: 流程ID
            
        Returns:
            List[ProcessEdge]: 流程边列表
        """
        results = super().find_all(self.TABLE_NAME, "flow_id = ?", (flow_id,))
        edges = [self.dict_to_model(result, ProcessEdge) for result in results]
        return edges
