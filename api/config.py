#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置文件
"""

import os
from dataclasses import dataclass
from typing import Set


@dataclass
class AppConfig:
    """应用配置类"""
    
    # 服务器配置
    SCHEME:str='http'
    HOST: str = '127.0.0.1'
    PORT: int = 5001
    DEBUG: bool = True
    THREADED: bool = True
    
    # 文件上传配置
    UPLOAD_FOLDER: str = 'config_infos/uploads'
    TEMPLATES_FOLDER: str = 'config_infos/templates'  # 模板管理模块配置信息
    DATA_SOURCES_FOLDER: str = 'config_infos/data_sources'  # 数据源模块配置信息
    INSTRUCTIONS_FOLDER: str = 'config_infos/instructions'  # 指令管理模块配置信息
    DATA_PROCESSES_FOLDER: str = 'config_infos/data_processes'  # 数据处理流程模块配置信息
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: Set[str] = None
    
    # 应用信息
    SERVICE_NAME: str = 'PPT Upload Server'
    VERSION: str = '2.0.0'
    
    def __post_init__(self):
        if self.ALLOWED_EXTENSIONS is None:
            self.ALLOWED_EXTENSIONS = {'ppt', 'pptx'}
        
        # 确保目录存在
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.TEMPLATES_FOLDER, exist_ok=True)
        os.makedirs(self.DATA_SOURCES_FOLDER, exist_ok=True)
        os.makedirs(self.INSTRUCTIONS_FOLDER, exist_ok=True)
        os.makedirs(self.DATA_PROCESSES_FOLDER, exist_ok=True)


# 全局配置实例
config:AppConfig = AppConfig()


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def get_config() -> AppConfig:
        """获取配置"""
        return config
    
    @staticmethod
    def update_config(**kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    @staticmethod
    def get_max_file_size_mb() -> int:
        """获取最大文件大小（MB）"""
        return config.MAX_FILE_SIZE // (1024 * 1024)
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """检查文件是否允许上传"""
        if not filename or '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in config.ALLOWED_EXTENSIONS