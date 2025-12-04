#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入配置
配置所有服务和控制器的依赖关系
"""

from .container import get_container
# 移除抽象接口导入，直接使用实现类
from service.ppt_service import PPTservice
from service.file_service import Fileservice
from service.config_service import Configservice
from service.ppt_conversion_service import PPTConversionservice
from service.data_source_service import DataSourceservice
from service.data_process_service import DataProcessService
from service.instruction_service import InstructionService

def configure_dependencies():
    """配置所有依赖注入关系"""
    container = get_container()
    
    # 注册服务层依赖 - 直接注册实现类
    container.register_singleton(Fileservice, Fileservice)
    container.register_singleton(Configservice, Configservice)
    container.register_singleton(PPTConversionservice, PPTConversionservice)
    container.register_singleton(PPTservice, PPTservice)
    container.register_singleton(DataSourceservice, DataSourceservice)
    
    # 注册服务层依赖 - 直接注册实现类
    container.register_singleton(DataProcessService, DataProcessService)
    container.register_singleton(InstructionService, InstructionService)
    
    return container

def get_configured_container():
    """获取已配置的容器实例"""
    return configure_dependencies()