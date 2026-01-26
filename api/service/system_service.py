#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务层
实现系统级功能的业务逻辑，依赖于系统仓储层
"""

from service.base_service import BaseService
from repository.system_repository import SystemRepository


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
    
    def backup_database(self) -> dict:
        """
        备份数据库
        
        Returns:
            dict: 备份结果，包含备份文件路径和信息
        """
        try:
            result = self.system_repository.backup_database()
            if result["success"]:
                self._log_info("数据库备份成功")
            else:
                self._log_error(f"数据库备份失败: {result['message']}")
            return result
        except Exception as e:
            self._log_error(f"数据库备份失败: {str(e)}")
            return {
                "success": False,
                "message": f"数据库备份失败: {str(e)}"
            }
    
    def restore_database(self, backup_file_path: str) -> dict:
        """
        还原数据库
        
        Args:
            backup_file_path: 备份文件路径
            
        Returns:
            dict: 还原结果
        """
        try:
            self._log_info(f"开始还原数据库，备份文件路径: {backup_file_path}")
            result = self.system_repository.restore_database(backup_file_path)
            if result["success"]:
                self._log_info("数据库还原成功")
            else:
                self._log_error(f"数据库还原失败: {result['message']}")
            return result
        except Exception as e:
            self._log_error(f"数据库还原失败: {str(e)}")
            return {
                "success": False,
                "message": f"数据库还原失败: {str(e)}"
            }
    
    def get_backup_list(self) -> dict:
        """
        获取备份文件列表
        
        Returns:
            dict: 备份文件列表
        """
        try:
            result = self.system_repository.get_backup_list()
            if result["success"]:
                self._log_info(f"获取备份列表成功，共 {len(result['data'])} 个备份文件")
            else:
                self._log_error(f"获取备份列表失败: {result['message']}")
            return result
        except Exception as e:
            self._log_error(f"获取备份列表失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取备份列表失败: {str(e)}"
            }
    
    def delete_backup(self, backup_filename: str) -> dict:
        """
        删除备份文件
        
        Args:
            backup_filename: 备份文件名
            
        Returns:
            dict: 删除结果
        """
        try:
            self._log_info(f"开始删除备份文件: {backup_filename}")
            result = self.system_repository.delete_backup(backup_filename)
            if result["success"]:
                self._log_info(f"备份文件 {backup_filename} 删除成功")
            else:
                self._log_error(f"备份文件 {backup_filename} 删除失败: {result['message']}")
            return result
        except Exception as e:
            self._log_error(f"备份文件 {backup_filename} 删除失败: {str(e)}")
            return {
                "success": False,
                "message": f"备份文件删除失败: {str(e)}"
            }
    
    def upload_and_restore(self, file_content: bytes, filename: str) -> dict:
        """
        上传备份文件并还原数据库
        
        Args:
            file_content: 备份文件内容
            filename: 备份文件名
            
        Returns:
            dict: 还原结果
        """
        try:
            self._log_info(f"开始上传并还原备份文件: {filename}")
            
            # 保存临时文件
            temp_file_path = self.system_repository.save_temp_file(file_content, filename)
            
            try:
                # 还原数据库
                result = self.restore_database(temp_file_path)
                return result
            finally:
                # 无论还原成功与否，都删除临时文件
                self.system_repository.delete_temp_file(temp_file_path)
        except Exception as e:
            self._log_error(f"上传并还原备份文件失败: {str(e)}")
            return {
                "success": False,
                "message": f"上传并还原失败: {str(e)}"
            }
    
    def get_backup_dir(self) -> str:
        """
        获取备份目录路径
        
        Returns:
            str: 备份目录路径
        """
        return self.system_repository.get_backup_dir()
    
    def get_temp_dir(self) -> str:
        """
        获取临时目录路径
        
        Returns:
            str: 临时目录路径
        """
        return self.system_repository.get_temp_dir()
