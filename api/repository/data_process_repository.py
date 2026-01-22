#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据流程仓储类
实现数据流程的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, AsyncSQLiteConnectionPool, SQLiteConnectionPool
from entity.data_process import DataProcess
from entity.process_node import ProcessNode
from entity.process_edge import ProcessEdge


class DataProcessRepository(BaseRepository[DataProcess]):
    """数据流程仓储类"""
    
    TABLE_NAME = "data_processes"
    
    def __init__(self, db_pool: AsyncSQLiteConnectionPool):
        """初始化数据流程仓储类
        
        Args:
            db_pool: SQLite连接池实例（异步）
        """
        super().__init__(db_pool)
        # 初始化表结构将在异步任务中执行
    
    async def _init_table(self):
        """初始化数据流程表结构（异步）"""
        # 创建数据流程表
        create_processes_table = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        await self.execute_non_query(create_processes_table)
        
        # 创建流程节点表
        create_nodes_table = f"""
        CREATE TABLE IF NOT EXISTS process_nodes (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            instruction_id TEXT NOT NULL,
            name TEXT,
            description TEXT,
            x REAL NOT NULL,
            y REAL NOT NULL,
            params TEXT NOT NULL,
            input_types TEXT NOT NULL,
            FOREIGN KEY (flow_id) REFERENCES {self.TABLE_NAME}(id) ON DELETE CASCADE
        )
        """
        await self.execute_non_query(create_nodes_table)
        
        # 创建流程边表
        create_edges_table = f"""
        CREATE TABLE IF NOT EXISTS process_edges (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            label TEXT,
            logic_express TEXT,
            FOREIGN KEY (flow_id) REFERENCES {self.TABLE_NAME}(id) ON DELETE CASCADE
        )
        """
        await self.execute_non_query(create_edges_table)
    
    async def add(self, process: DataProcess) -> bool:
        """添加数据流程（异步）
        
        Args:
            process: 数据流程实体
            
        Returns:
            bool: 添加是否成功
        """
        # 开始事务（使用连接池的异步连接）
        conn = None
        try:
            conn = await self.db_pool.get_connection()
            
            # 插入流程基本信息
            process_sql = f"""
            INSERT INTO {self.TABLE_NAME} (id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """
            process_params = (
                process.id,
                process.name,
                process.description,
                process.created_at,
                process.updated_at
            )
            await conn.execute(process_sql, process_params)
            
            # 插入流程节点
            node_sql = """
            INSERT INTO process_nodes (id, flow_id, instruction_id, name, description, x, y, params,input_types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for node in process.nodes:
                node_params = (
                    node.id,
                    process.id,
                    node.instruction_id,
                    node.name,
                    node.description,
                    node.x,
                    node.y,
                    json.dumps(node.params),
                    json.dumps(node.input_types)
                )
                await conn.execute(node_sql, node_params)
            
            # 插入流程边
            edge_sql = """
            INSERT INTO process_edges (id, flow_id, source, target, label, logic_express)
            VALUES (?, ?, ?, ?, ?, ?)   
            """
            for edge in process.edges:
                edge_params = (
                    edge.id,
                    process.id,
                    edge.source,
                    edge.target,
                    edge.label,
                    edge.logic_express
                )
                await conn.execute(edge_sql, edge_params)
            
            await conn.commit()
            return True
        except Exception as e:
            print(f"添加数据流程失败: {str(e)}")
            if conn:
                await conn.rollback()
            return False
        finally:
            if conn:
                await self.db_pool.return_connection(conn)
    
    async def update(self, process: DataProcess) -> bool:
        """更新数据流程（异步）
        
        Args:
            process: 数据流程实体
            
        Returns:
            bool: 更新是否成功
        """
        # 开始事务（使用连接池的异步连接）
        conn = None
        try:
            conn = await self.db_pool.get_connection()
            
            # 更新流程基本信息
            process_sql = f"""
            UPDATE {self.TABLE_NAME} 
            SET name = ?, description = ?, updated_at = ?
            WHERE id = ?
            """
            process_params = (
                process.name,
                process.description,
                process.updated_at,
                process.id
            )
            await conn.execute(process_sql, process_params)
            
            # 删除旧的节点和边
            await conn.execute("DELETE FROM process_nodes WHERE flow_id = ?", (process.id,))
            await conn.execute("DELETE FROM process_edges WHERE flow_id = ?", (process.id,))
            
            # 插入新的节点
            node_sql = """
            INSERT INTO process_nodes (id, flow_id, instruction_id, name, description, x, y, params,input_types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for node in process.nodes:
                node_params = (
                    node.id,
                    process.id,
                    node.instruction_id,
                    node.name,
                    node.description,
                    node.x,
                    node.y,
                    json.dumps(node.params),
                    json.dumps(node.input_types)
                )
                await conn.execute(node_sql, node_params)
            
            # 插入新的边
            edge_sql = """
            INSERT INTO process_edges (id, flow_id, source, target, label, logic_express)
            VALUES (?, ?, ?, ?, ?, ?)   
            """
            for edge in process.edges:
                edge_params = (
                    edge.id,
                    process.id,
                    edge.source,
                    edge.target,
                    edge.label,
                    edge.logic_express
                )
                await conn.execute(edge_sql, edge_params)
            
            await conn.commit()
            return True
        except Exception as e:
            print(f"更新数据流程失败: {str(e)}")
            if conn:
                await conn.rollback()
            return False
        finally:
            if conn:
                await self.db_pool.return_connection(conn)
    
    async def delete(self, id: str) -> bool:
        """删除数据流程（异步）
        
        Args:
            id: 数据流程ID
            
        Returns:
            bool: 删除是否成功
        """
        return await super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    async def find_by_id(self, id: str) -> Optional[DataProcess]:
        """根据ID查找数据流程（异步）
        
        Args:
            id: 数据流程ID
            
        Returns:
            Optional[DataProcess]: 数据流程实体，如果不存在则返回None
        """
        # 查询流程基本信息（异步）
        process_result = await super().find_by_id(self.TABLE_NAME, id)
        if not process_result:
            return None
        
        # 查询流程节点（异步）
        nodes_sql = "SELECT * FROM process_nodes WHERE flow_id = ?"
        nodes_results = await self.execute_query(nodes_sql, (id,))
        
        # 查询流程边（异步）
        edges_sql = "SELECT * FROM process_edges WHERE flow_id = ?"
        edges_results = await self.execute_query(edges_sql, (id,))
        
        # 构建节点列表
        nodes = []
        for node_result in nodes_results:
            # 安全解析params
            params = {}
            if node_result["params"]:
                try:
                    params = json.loads(node_result["params"])
                except (json.JSONDecodeError, TypeError):
                    params = {}
            
            # 安全解析intput_types
            input_types = {"e": [], "t": []}
            if node_result["input_types"]:
                try:
                    input_types = json.loads(node_result["input_types"])
                    # 确保格式正确
                    if not isinstance(input_types, dict):
                        input_types = {"e": [], "t": []}
                    if not isinstance(input_types.get("e"), list):
                        input_types["e"] = []
                    if not isinstance(input_types.get("t"), list):
                        input_types["t"] = []
                except (json.JSONDecodeError, TypeError):
                    input_types = {"e": [], "t": []}
            
            nodes.append(ProcessNode(
                id=node_result["id"],
                flow_id=node_result["flow_id"],
                instruction_id=node_result["instruction_id"],
                name=node_result["name"],
                description=node_result["description"],
                x=node_result["x"],
                y=node_result["y"],
                params=params,
                input_types=input_types
            ))
        
        # 构建边列表
        edges = []
        for edge_result in edges_results:
            edges.append(ProcessEdge(
                id=edge_result["id"],
                flow_id=edge_result["flow_id"],
                source=edge_result["source"],
                target=edge_result["target"],
                label=edge_result["label"],
                logic_express=edge_result["logic_express"]
            ))
        
        # 构建数据流程对象
        return DataProcess(
            id=process_result["id"],
            name=process_result["name"],
            description=process_result["description"],
            nodes=nodes,
            edges=edges,
            created_at=process_result["created_at"],
            updated_at=process_result["updated_at"]
        )
    
    async def find_all(self) -> List[DataProcess]:
        """查找所有数据流程（异步）
        
        Returns:
            List[DataProcess]: 数据流程列表
        """
        # 查询所有流程（异步）
        processes_results = await super().find_all(self.TABLE_NAME)
        
        # 构建流程列表
        processes = []
        for process_result in processes_results:
            process = await self.find_by_id(process_result["id"])
            if process:
                processes.append(process)
        
        return processes
