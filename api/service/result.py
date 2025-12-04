#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务结果类
用于统一服务层的响应格式
"""

from typing import Generic, Optional, TypeVar, Any, Dict

T = TypeVar('T')


class Result(Generic[T]):
    """服务结果类，用于统一响应格式"""
    
    def __init__(self, success: bool, data: Optional[T] = None, message: str = "", error: Optional[str] = None):
        """
        初始化结果对象
        
        Args:
            success: 是否成功
            data: 响应数据
            message: 响应消息
            error: 错误信息（如果有）
        """
        self.success = success
        self.data = data
        self.message = message
        self.error = error or ("" if success else message)
    
    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "操作成功") -> 'Result[T]':
        """
        创建成功结果
        
        Args:
            data: 响应数据
            message: 响应消息
            
        Returns:
            Result[T]: 成功结果对象
        """
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def fail(cls, error: str, data: Optional[T] = None) -> 'Result[T]':
        """
        创建失败结果
        
        Args:
            error: 错误信息
            data: 响应数据（如果有）
            
        Returns:
            Result[T]: 失败结果对象
        """
        return cls(success=False, data=data, message="", error=error)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的结果
        """
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error
        }