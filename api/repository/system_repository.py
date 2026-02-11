#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统仓储层
负责系统级数据访问操作
"""

import os

from config import config


class SystemRepository:
    """系统仓储类"""
    
    def __init__(self):
        """初始化系统仓储"""
        # 获取当前文件所在目录作为基础目录
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上两层目录（repository目录的上两层）
        self.base_dir = os.path.dirname(os.path.dirname(self.base_dir))
    
    def get_db_path(self) -> str:
        """
        获取数据库文件路径
        
        Returns:
            str: 数据库文件路径
        """
        return config.DB_PATH
