#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入配置
配置所有服务和控制器的依赖关系
根据不同架构层采用不同的注入模式：
- 数据库实例：连接池模式（单例）
- 仓储层：单例模式
- 服务层和应用层：会话模式

自动注入规则：
- 服务层：自动扫描service目录下文件名以_service为后缀的文件中的服务类，使用会话模式注册
- 仓储层：自动扫描repository目录下文件名以_repository为后缀的文件中的仓储类，使用单例模式注册
"""

import os
import importlib
import inspect
from .container import get_container
from repository.base_repository import SQLiteConnectionPool
from pathlib import Path
from config import config

def auto_register_services(container):
    """自动注册服务层依赖
    
    扫描service目录下所有以_service为后缀的文件，动态导入其中的服务类，并使用会话模式注册
    """
    # 获取service目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_dir = os.path.join(current_dir, "..", "service")
    
    # 遍历service目录
    for filename in os.listdir(service_dir):
        # 只处理以_service.py为后缀的文件
        if filename.endswith("_service.py"):
            # 获取模块名
            module_name = f"service.{filename[:-3]}"  # 移除.py后缀
            
            try:
                # 动态导入模块
                module = importlib.import_module(module_name)
                
                # 获取模块中的所有类
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    # 确保类是在当前模块中定义的
                    if cls.__module__ == module.__name__:
                        # 使用会话模式注册服务
                        container.register_session(cls, cls)
            except Exception as e:
                print(f"✗ 自动注册服务失败 {module_name}: {str(e)}")


def auto_register_repositories(container):
    """自动注册仓储层依赖
    
    扫描repository目录下所有以_repository为后缀的文件，动态导入其中的仓储类，并使用单例模式注册
    """
    # 获取repository目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.join(current_dir, "..", "repository")
    
    # 遍历repository目录
    for filename in os.listdir(repo_dir):
        # 只处理以_repository.py为后缀的文件
        if filename.endswith("_repository.py"):
            # 获取模块名
            module_name = f"repository.{filename[:-3]}"  # 移除.py后缀
            
            try:
                # 动态导入模块
                module = importlib.import_module(module_name)
                
                # 获取模块中的所有类
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    # 确保类是在当前模块中定义的，且不是BaseRepository等基础类
                    if cls.__module__ == module.__name__ and not name.startswith("Base"):
                        # 使用单例模式注册仓储
                        container.register_singleton(cls, cls)
            except Exception as e:
                print(f"✗ 自动注册仓储失败 {module_name}: {str(e)}")


def configure_dependencies():
    """配置所有依赖注入关系"""
    container = get_container()
    
    # 注册数据库连接池（单例模式）
    db_path = config.DB_PATH
    db_pool = SQLiteConnectionPool(db_path, max_connections=10)
    container.register_instance(SQLiteConnectionPool, db_pool)
    
    # 自动注册仓储层依赖（单例模式）
    auto_register_repositories(container)
    
    # 自动注册服务层依赖（会话模式）
    auto_register_services(container)
    
    return container


def get_configured_container():
    """获取已配置的容器实例"""
    return configure_dependencies()