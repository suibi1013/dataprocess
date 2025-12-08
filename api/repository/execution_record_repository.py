#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行记录仓储类
实现执行记录的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.execution_record import ExecutionRecord
from entity.execution_result import ExecutionResult


class ExecutionRecordRepository(BaseRepository[ExecutionRecord]):
    """执行记录仓储类"""
    
    TABLE_NAME = "execution_records"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化执行记录仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化执行记录表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            flow_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            error_message TEXT,
            execution_time REAL NOT NULL,
            executed_at TEXT NOT NULL,
            result_data TEXT
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, record: ExecutionRecord) -> bool:
        """添加执行记录
        
        Args:
            record: 执行记录实体
            
        Returns:
            bool: 添加是否成功
        """
        # 将结果数据转换为JSON字符串
        result_data_json = None
        if record.result_data:
            result_data_json = json.dumps({
                "flow_id": record.result_data.flow_id,
                "flow_name": record.result_data.flow_name,
                "final_result": record.result_data.final_result,
                "process_results": record.result_data.process_results,
                "execution_order": record.result_data.execution_order,
                "total_nodes_executed": record.result_data.total_nodes_executed,
                "reached_end_node": record.result_data.reached_end_node
            })
        
        data = {
            "id": record.id,
            "flow_id": record.flow_id,
            "flow_name": record.flow_name,
            "success": 1 if record.success else 0,
            "error_message": record.error_message,
            "execution_time": record.execution_time,
            "executed_at": record.executed_at,
            "result_data": result_data_json
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, record: ExecutionRecord) -> bool:
        """更新执行记录
        
        Args:
            record: 执行记录实体
            
        Returns:
            bool: 更新是否成功
        """
        # 将结果数据转换为JSON字符串
        result_data_json = None
        if record.result_data:
            result_data_json = json.dumps({
                "flow_id": record.result_data.flow_id,
                "flow_name": record.result_data.flow_name,
                "final_result": record.result_data.final_result,
                "process_results": record.result_data.process_results,
                "execution_order": record.result_data.execution_order,
                "total_nodes_executed": record.result_data.total_nodes_executed,
                "reached_end_node": record.result_data.reached_end_node
            })
        
        data = {
            "flow_name": record.flow_name,
            "success": 1 if record.success else 0,
            "error_message": record.error_message,
            "execution_time": record.execution_time,
            "result_data": result_data_json
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (record.id,))
    
    def delete(self, id: str) -> bool:
        """删除执行记录
        
        Args:
            id: 执行记录ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[ExecutionRecord]:
        """根据ID查找执行记录
        
        Args:
            id: 执行记录ID
            
        Returns:
            Optional[ExecutionRecord]: 执行记录实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            # 处理布尔值转换
            result["success"] = bool(result["success"])
            
            # 解析结果数据JSON字符串
            if result["result_data"]:
                result_data_dict = json.loads(result["result_data"])
                result["result_data"] = self.dict_to_model(result_data_dict, ExecutionResult)
            
            return self.dict_to_model(result, ExecutionRecord)
        return None
    
    def find_all(self) -> List[ExecutionRecord]:
        """查找所有执行记录
        
        Returns:
            List[ExecutionRecord]: 执行记录列表
        """
        results = super().find_all(self.TABLE_NAME, None, None)
        records = []
        for result in results:
            # 处理布尔值转换
            result["success"] = bool(result["success"])
            
            # 解析结果数据JSON字符串
            if result["result_data"]:
                result_data_dict = json.loads(result["result_data"])
                result["result_data"] = self.dict_to_model(result_data_dict, ExecutionResult)
            
            records.append(self.dict_to_model(result, ExecutionRecord))
        
        # 按执行时间倒序排序
        records.sort(key=lambda x: x.executed_at, reverse=True)
        return records
    
    def find_by_flow_id(self, flow_id: str) -> List[ExecutionRecord]:
        """根据流程ID查找执行记录
        
        Args:
            flow_id: 流程ID
            
        Returns:
            List[ExecutionRecord]: 执行记录列表
        """
        results = super().find_all(self.TABLE_NAME, "flow_id = ?", (flow_id,))
        records = []
        for result in results:
            # 处理布尔值转换
            result["success"] = bool(result["success"])
            
            # 解析结果数据JSON字符串
            if result["result_data"]:
                result_data_dict = json.loads(result["result_data"])
                result["result_data"] = self.dict_to_model(result_data_dict, ExecutionResult)
            
            records.append(self.dict_to_model(result, ExecutionRecord))
        
        # 按执行时间倒序排序
        records.sort(key=lambda x: x.executed_at, reverse=True)
        return records
