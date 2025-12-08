#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据流程仓储类
实现数据流程的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.data_process import DataProcess
from entity.process_node import ProcessNode
from entity.process_edge import ProcessEdge


class DataProcessRepository(BaseRepository[DataProcess]):
    """数据流程仓储类"""
    
    TABLE_NAME = "data_processes"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化数据流程仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化数据流程表结构"""
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
        self.execute_non_query(create_processes_table)
        
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
            FOREIGN KEY (flow_id) REFERENCES {self.TABLE_NAME}(id) ON DELETE CASCADE
        )
        """
        self.execute_non_query(create_nodes_table)
        
        # 创建流程边表
        create_edges_table = f"""
        CREATE TABLE IF NOT EXISTS process_edges (
            id TEXT PRIMARY KEY,
            flow_id TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            label TEXT,
            FOREIGN KEY (flow_id) REFERENCES {self.TABLE_NAME}(id) ON DELETE CASCADE
        )
        """
        self.execute_non_query(create_edges_table)
    
    def add(self, process: DataProcess) -> bool:
        """添加数据流程
        
        Args:
            process: 数据流程实体
            
        Returns:
            bool: 添加是否成功
        """
        # 开始事务
        conn = self.db_pool.get_connection()
        try:
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
            cursor = conn.cursor()
            cursor.execute(process_sql, process_params)
            
            # 插入流程节点
            node_sql = """
            INSERT INTO process_nodes (id, flow_id, instruction_id, name, description, x, y, params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(node.params)
                )
                cursor.execute(node_sql, node_params)
            
            # 插入流程边
            edge_sql = """
            INSERT INTO process_edges (id, flow_id, source, target, label)
            VALUES (?, ?, ?, ?, ?)
            """
            for edge in process.edges:
                edge_params = (
                    edge.id,
                    process.id,
                    edge.source,
                    edge.target,
                    edge.label
                )
                cursor.execute(edge_sql, edge_params)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"添加数据流程失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            self.db_pool.return_connection(conn)
    
    def update(self, process: DataProcess) -> bool:
        """更新数据流程
        
        Args:
            process: 数据流程实体
            
        Returns:
            bool: 更新是否成功
        """
        # 开始事务
        conn = self.db_pool.get_connection()
        try:
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
            cursor = conn.cursor()
            cursor.execute(process_sql, process_params)
            
            # 删除旧的节点和边
            cursor.execute("DELETE FROM process_nodes WHERE flow_id = ?", (process.id,))
            cursor.execute("DELETE FROM process_edges WHERE flow_id = ?", (process.id,))
            
            # 插入新的节点
            node_sql = """
            INSERT INTO process_nodes (id, flow_id, instruction_id, name, description, x, y, params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(node.params)
                )
                cursor.execute(node_sql, node_params)
            
            # 插入新的边
            edge_sql = """
            INSERT INTO process_edges (id, flow_id, source, target, label)
            VALUES (?, ?, ?, ?, ?)
            """
            for edge in process.edges:
                edge_params = (
                    edge.id,
                    process.id,
                    edge.source,
                    edge.target,
                    edge.label
                )
                cursor.execute(edge_sql, edge_params)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"更新数据流程失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            self.db_pool.return_connection(conn)
    
    def delete(self, id: str) -> bool:
        """删除数据流程
        
        Args:
            id: 数据流程ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def find_by_id(self, id: str) -> Optional[DataProcess]:
        """根据ID查找数据流程
        
        Args:
            id: 数据流程ID
            
        Returns:
            Optional[DataProcess]: 数据流程实体，如果不存在则返回None
        """
        # 查询流程基本信息
        process_result = super().find_by_id(self.TABLE_NAME, id)
        if not process_result:
            return None
        
        # 查询流程节点
        nodes_sql = "SELECT * FROM process_nodes WHERE flow_id = ?"
        nodes_results = self.execute_query(nodes_sql, (id,))
        
        # 查询流程边
        edges_sql = "SELECT * FROM process_edges WHERE flow_id = ?"
        edges_results = self.execute_query(edges_sql, (id,))
        
        # 构建节点列表
        nodes = []
        for node_result in nodes_results:
            nodes.append(ProcessNode(
                id=node_result["id"],
                flow_id=node_result["flow_id"],
                instruction_id=node_result["instruction_id"],
                name=node_result["name"],
                description=node_result["description"],
                x=node_result["x"],
                y=node_result["y"],
                params=json.loads(node_result["params"])
            ))
        
        # 构建边列表
        edges = []
        for edge_result in edges_results:
            edges.append(ProcessEdge(
                id=edge_result["id"],
                flow_id=edge_result["flow_id"],
                source=edge_result["source"],
                target=edge_result["target"],
                label=edge_result["label"]
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
    
    def find_all(self) -> List[DataProcess]:
        """查找所有数据流程
        
        Returns:
            List[DataProcess]: 数据流程列表
        """
        # 查询所有流程
        processes_results = super().find_all(self.TABLE_NAME)
        
        # 构建流程列表
        processes = []
        for process_result in processes_results:
            process = self.find_by_id(process_result["id"])
            if process:
                processes.append(process)
        
        return processes
