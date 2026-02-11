#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务层
实现系统级功能的业务逻辑，依赖于系统仓储层
"""

from service.base_service import BaseService
from repository.system_repository import SystemRepository
from utils.system_tool import SystemTool


class SystemService(BaseService):
    """系统服务类"""
    
    def __init__(self, system_repository: SystemRepository):
        """
        初始化系统服务
        
        Args:
            system_repository: 系统仓储实例
        """
        super().__init__()
        self.system_repository = system_repository
    
    def validate_license(self, license_key: str) -> dict:
        """
        验证授权码
        
        Args:
            license_key: 授权码
            
        Returns:
            dict: 验证结果，包含success、message和data字段
        """
        try:
            self._log_info(f"开始验证授权码: {license_key}")
            
            # 调用系统工具类的验证方法
            result = SystemTool.validate_license_key(license_key)
            
            if result["success"]:
                self._log_info("授权码验证成功")
            else:
                self._log_error(f"授权码验证失败: {result['message']}")
            
            return result
        except Exception as e:
            self._log_error(f"验证授权码失败: {str(e)}")
            return {
                "success": False,
                "message": f"验证授权码失败: {str(e)}",
                "data": None
            }
