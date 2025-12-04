#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务类
提供所有服务类的基础功能
"""


class BaseService:
    """基础服务类"""
    
    def __init__(self):
        """初始化基础服务"""
        self.service_name = self.__class__.__name__
    
    def _log_info(self, message: str):
        """记录信息日志
        
        Args:
            message: 日志消息
        """
        print(f"ℹ️ [{self.service_name}] {message}")
    
    def _log_error(self, message: str):
        """记录错误日志
        
        Args:
            message: 日志消息
        """
        print(f"❌ [{self.service_name}] {message}")
    
    def _log_success(self, message: str):
        """记录成功日志
        
        Args:
            message: 日志消息
        """
        print(f"✅ [{self.service_name}] {message}")