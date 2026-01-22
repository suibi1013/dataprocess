#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础仓储类，实现SQLite数据库的增删改查功能，使用连接池模式管理数据库连接
"""

import json
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic
from datetime import datetime
import asyncio
import threading

# 导入异步SQLite库
import aiosqlite

T = TypeVar('T')


class AsyncSQLiteConnectionPool:
    """异步SQLite连接池类，支持异步操作，每个任务使用自己的连接"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """初始化连接池
        
        Args:
            db_path: SQLite数据库文件路径
            max_connections: 最大连接数
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)  # 使用信号量限制并发连接数
    
    async def get_connection(self) -> aiosqlite.Connection:
        """获取异步数据库连接
        
        Returns:
            aiosqlite.Connection: 数据库连接对象
        """
        await self.semaphore.acquire()
        try:
            conn = await aiosqlite.connect(self.db_path)
            # 启用外键约束
            await conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            self.semaphore.release()
            raise
    
    async def return_connection(self, conn: aiosqlite.Connection) -> None:
        """归还数据库连接
        
        Args:
            conn: 数据库连接对象
        """
        try:
            await conn.close()
        finally:
            self.semaphore.release()
    
    async def close_all(self) -> None:
        """关闭所有连接（信号量会自动处理）"""
        pass


# 保留原有的同步连接池，确保向后兼容
import sqlite3

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
    """基础仓储类，提供SQLite数据库的CRUD操作（支持异步和同步）"""
    
    def __init__(self, db_pool: AsyncSQLiteConnectionPool):
        """初始化仓储类
        
        Args:
            db_pool: SQLite连接池实例（异步）
        """
        self.db_pool = db_pool
    
    # 初始化数据库连接的方法已移除，表初始化将在首次数据库操作时自动处理
    
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
    
    async def execute_query(self, query: str, params: Tuple[Any, ...] = None) -> List[Dict[str, Any]]:
        """执行查询语句（异步）
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        conn = None
        try:
            conn = await self.db_pool.get_connection()
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            # 获取列名
            columns = [column[0] for column in cursor.description]
            # 将查询结果转换为字典列表
            results = [dict(zip(columns, row)) for row in rows]
            await cursor.close()
            return results
        except Exception as e:
            print(f"查询数据库失败: {e}")
            return []
        finally:
            if conn:
                await self.db_pool.return_connection(conn)
    
    async def execute_non_query(self, query: str, params: Tuple[Any, ...] = None) -> bool:
        """执行非查询语句（INSERT、UPDATE、DELETE）
        
        Args:
            query: SQL语句
            params: 查询参数
            
        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = await self.db_pool.get_connection()
            await conn.execute(query, params or ())
            await conn.commit()
            return True
        except Exception as e:
            print(f"执行数据库操作失败: {e}")
            if conn:
                await conn.rollback()
            return False
        finally:
            if conn:
                await self.db_pool.return_connection(conn)
    
    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
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
        return await self.execute_non_query(query, values)
    
    async def update(self, table: str, data: Dict[str, Any], condition: str, params: Tuple[Any, ...] = None) -> bool:
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
        return await self.execute_non_query(query, values)
    
    async def delete(self, table: str, condition: str, params: Tuple[Any, ...] = None) -> bool:
        """删除数据
        
        Args:
            table: 表名
            condition: WHERE条件
            params: WHERE条件参数
            
        Returns:
            bool: 删除是否成功
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        return await self.execute_non_query(query, params)
    
    async def find_by_id(self, table: str, id_value: Any, id_column: str = 'id') -> Optional[Dict[str, Any]]:
        """根据ID查找数据
        
        Args:
            table: 表名
            id_value: ID值
            id_column: ID列名
            
        Returns:
            Optional[Dict[str, Any]]: 查找结果，如果不存在则返回None
        """
        query = f"SELECT * FROM {table} WHERE {id_column} = ?"
        results = await self.execute_query(query, (id_value,))
        return results[0] if results else None
    
    async def find_all(self, table: str, condition: str = None, params: Tuple[Any, ...] = None) -> List[Dict[str, Any]]:
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
        
        return await self.execute_query(query, params)
    
    async def insert_batch(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
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
            conn = await self.db_pool.get_connection()
            
            # 获取数据字段名
            keys = ', '.join(data_list[0].keys())
            placeholders = ', '.join(['?' for _ in data_list[0].values()])
            
            # 构建批量插入SQL语句
            query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
            
            # 准备参数列表
            params_list = [tuple(data.values()) for data in data_list]
            
            # 执行批量插入
            await conn.executemany(query, params_list)
            await conn.commit()
            return True
        except Exception as e:
            print(f"批量插入数据失败: {e}")
            if conn:
                await conn.rollback()
            return False
        finally:
            if conn:
                await self.db_pool.return_connection(conn)
