#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板服务层
负责模板相关的业务逻辑处理
遵循分层架构：服务层调用仓储层，仓储层继承基础仓储
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from repository.template_info_repository import TemplateInfoRepository
from repository.template_slide_repository import TemplateSlideRepository
from service.base_service import BaseService
from service.result import Result
from config import config

class TemplateService(BaseService):
    """模板服务类"""
    
    def __init__(self, 
                 template_info_repo: TemplateInfoRepository, 
                 template_slide_repo: TemplateSlideRepository):
        """初始化模板服务
        
        Args:
            template_info_repo: 模板信息仓储实例
            template_slide_repo: 模板幻灯片仓储实例
        """
        super().__init__()
        self.template_info_repo = template_info_repo
        self.template_slide_repo = template_slide_repo
        self.upload_folder = config.UPLOAD_FOLDER
    
    async def get_templates(self) -> Result:
        """获取模板列表
        
        Returns:
            Result: 包含模板列表的响应对象
        """
        try:
            # 调用仓储层获取所有模板信息
            template_infos = await self.template_info_repo.find_all()
            
            # 构建响应数据
            templates = []
            for template_info in template_infos:
                template = {
                    'id': template_info.id,
                    'name': template_info.template_name,
                    'file_name': template_info.file_name,
                    'createTime': template_info.created_at,
                    'status': 'ready'
                }
                templates.append(template)
            
            return Result.success(data={
                'templates': templates
            })
        except Exception as e:
            self._log_error(f"获取模板列表失败: {str(e)}")
            return Result.fail(f"获取模板列表失败: {str(e)}")
    
    async def delete_template(self, template_id: str) -> Result:
        """删除指定模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            Result: 删除结果的响应对象
        """
        try:
            # 检查模板是否存在
            template_info = await self.template_info_repo.find_by_id(template_id)
            if not template_info:
                return Result.fail("模板不存在")
            
            # 删除模板幻灯片配置
            await self.template_slide_repo.delete_by_template_id(template_id)
            
            # 删除模板信息
            await self.template_info_repo.delete(template_id)

            # 删除模板目录及文件             
            import os
            import shutil
            template_dir = os.path.join(config.UPLOAD_FOLDER, template_id)
            if os.path.exists(template_dir):
                shutil.rmtree(template_dir, ignore_errors=True)
            
            return Result.success(message="模板删除成功")
        except Exception as e:
            self._log_error(f"删除模板失败: {str(e)}")
            return Result.fail(f"删除模板失败: {str(e)}")
    
    async def check_config_update(self, file_name: str) -> Result:
        """检查配置更新
        
        Args:
            file_name: 文件名
            
        Returns:
            Result: 检查结果的响应对象
        """
        try:
            # 获取所有模板信息
            template_infos = await self.template_info_repo.find_all()
            
            # 查找匹配的模板
            for template_info in template_infos:
                if file_name in template_info.file_name:
                    # 获取最后更新时间戳
                    import time
                    updated_time = datetime.fromisoformat(template_info.updated_at)
                    mtime = time.mktime(updated_time.timetuple())
                    
                    return Result.success(data={
                        'hasUpdate': True,
                        'configFile': template_info.id + '.json',  # 保持与原接口兼容
                        'lastModified': mtime,
                        'message': '找到匹配的配置文件'
                    })
            
            return Result.success(data={
                'hasUpdate': False,
                'message': '未找到匹配的配置文件'
            })
        except Exception as e:
            self._log_error(f"检查配置更新失败: {str(e)}")
            return Result.fail(f"检查配置更新失败: {str(e)}")