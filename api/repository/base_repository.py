#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础仓储类，实现SQLite数据库的增删改查功能，使用连接池模式管理数据库连接
"""

import sqlite3
import json
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Generator
from datetime import datetime
import threading

T = TypeVar('T')


class SQLiteConnectionPool:
    """SQLite连接池类，支持线程安全，每个线程使用自己的连接"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """初始化连接池
        
        Args:
            db_path: SQLite数据库文件路径
            max_connections: 最大连接数
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.thread_local = threading.local()  # 线程本地存储，用于存储每个线程的连接
        self.active_connections = 0  # 活跃连接计数器
        self.lock = threading.Lock()  # 全局锁，用于保护活跃连接计数器
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接，确保每个线程都使用自己的连接，同时限制最大连接数
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        # 如果当前线程已经有连接，直接返回
        if hasattr(self.thread_local, 'connection'):
            return self.thread_local.connection
        
        # 否则，创建新连接并存储到线程本地存储中
        with self.lock:
            # 检查是否超过最大连接数
            if self.active_connections >= self.max_connections:
                raise sqlite3.OperationalError(f"数据库连接池已满，当前活跃连接数: {self.active_connections}，最大连接数: {self.max_connections}")
            
            # 增加活跃连接计数
            self.active_connections += 1
        
        conn = sqlite3.connect(self.db_path)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        self.thread_local.connection = conn
        return conn
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """归还数据库连接
        
        Args:
            conn: 数据库连接对象
        """
        # 检查连接是否属于当前线程
        if hasattr(self.thread_local, 'connection') and self.thread_local.connection == conn:
            with self.lock:
                # 减少活跃连接计数
                self.active_connections -= 1
            
            # 关闭连接
            conn.close()
            # 移除线程本地存储中的连接
            delattr(self.thread_local, 'connection')
    
    def close_all(self) -> None:
        """关闭所有连接
        """
        with self.lock:
            # 重置活跃连接计数
            self.active_connections = 0
        
        # 关闭当前线程的连接
        if hasattr(self.thread_local, 'connection'):
            self.thread_local.connection.close()
            delattr(self.thread_local, 'connection')


class BaseRepository(Generic[T]):
    """基础仓储类，提供SQLite数据库的CRUD操作"""
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        self.db_pool = db_pool
        # 初始化数据库连接
        self._init_db()
    
    def _init_db(self):
        """初始化数据库连接"""
        pass
    
    def model_to_dict(self, model: Any, exclude: set = None) -> Dict[str, Any]:
        """
        将Pydantic模型转换为字典，用于数据库操作
        
        Args:
            model: Pydantic模型实例
            exclude: 需要排除的字段集合
            
        Returns:
            Dict[str, Any]: 转换后的字典
        """
        return model.model_dump(exclude=exclude)
    
    def dict_to_model(self, data: Dict[str, Any], model_class: Any) -> Any:
        """
        将字典转换为Pydantic模型
        
        Args:
            data: 字典数据
            model_class: Pydantic模型类
            
        Returns:
            Any: 转换后的模型实例
        """
        return model_class.model_validate(data)
    
    def execute_query(self, query: str, params: Tuple[Any, ...] = None) -> List[Dict[str, Any]]:
        """执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        conn = None
        try:
            conn = self.db_pool.get_connection()
            conn.row_factory = sqlite3.Row  # 设置行工厂，返回字典形式的结果
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 将查询结果转换为字典列表
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except sqlite3.Error as e:
            print(f"查询数据库失败: {e}")
            return []
        finally:
            if conn:
                self.db_pool.return_connection(conn)
    
    def execute_non_query(self, query: str, params: Tuple[Any, ...] = None) -> bool:
        """执行非查询语句（INSERT、UPDATE、DELETE）
        
        Args:
            query: SQL语句
            params: 查询参数
            
        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = self.db_pool.get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"执行数据库操作失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.db_pool.return_connection(conn)
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """插入数据
        
        Args:
            table: 表名
            data: 要插入的数据
            
        Returns:
            bool: 插入是否成功
        """
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.execute_non_query(query, values)
    
    def update(self, table: str, data: Dict[str, Any], condition: str, params: Tuple[Any, ...] = None) -> bool:
        """更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            condition: WHERE条件
            params: WHERE条件参数
            
        Returns:
            bool: 更新是否成功
        """
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values())
        
        if params:
            values += params
        
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        return self.execute_non_query(query, values)
    
    def delete(self, table: str, condition: str, params: Tuple[Any, ...] = None) -> bool:
        """删除数据
        
        Args:
            table: 表名
            condition: WHERE条件
            params: WHERE条件参数
            
        Returns:
            bool: 删除是否成功
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_non_query(query, params)
    
    def find_by_id(self, table: str, id_value: Any, id_column: str = 'id') -> Optional[Dict[str, Any]]:
        """根据ID查找数据
        
        Args:
            table: 表名
            id_value: ID值
            id_column: ID列名
            
        Returns:
            Optional[Dict[str, Any]]: 查找结果，如果不存在则返回None
        """
        query = f"SELECT * FROM {table} WHERE {id_column} = ?"
        results = self.execute_query(query, (id_value,))
        return results[0] if results else None
    
    def find_all(self, table: str, condition: str = None, params: Tuple[Any, ...] = None) -> List[Dict[str, Any]]:
        """查找所有数据
        
        Args:
            table: 表名
            condition: WHERE条件
            params: WHERE条件参数
            
        Returns:
            List[Dict[str, Any]]: 查找结果列表
        """
        query = f"SELECT * FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        
        return self.execute_query(query, params)
    
    def insert_batch(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
        """批量插入数据
        
        Args:
            table: 表名
            data_list: 要插入的数据列表
            
        Returns:
            bool: 插入是否成功
        """
        if not data_list:
            return True
        
        conn = None
        try:
            conn = self.db_pool.get_connection()
            cursor = conn.cursor()
            
            # 获取数据字段名
            keys = ', '.join(data_list[0].keys())
            placeholders = ', '.join(['?' for _ in data_list[0].values()])
            
            # 构建批量插入SQL语句
            query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
            
            # 准备参数列表
            params_list = [tuple(data.values()) for data in data_list]
            
            # 执行批量插入
            cursor.executemany(query, params_list)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"批量插入数据失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.db_pool.return_connection(conn)
