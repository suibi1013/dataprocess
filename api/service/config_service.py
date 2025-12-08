
import os
import json
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import uuid

from config import config
from entity.template_info import TemplateInfo
from entity.template_slide import TemplateSlide
from repository.template_info_repository import TemplateInfoRepository
from repository.template_slide_repository import TemplateSlideRepository
from repository.base_repository import SQLiteConnectionPool

class Configservice:
    """配置服务 - 依赖注入版本"""
    
    def __init__(self, 
                 template_info_repo: TemplateInfoRepository = None,
                 template_slide_repo: TemplateSlideRepository = None):
        """初始化配置服务
        
        Args:
            template_info_repo: 模板信息仓储实例
            template_slide_repo: 模板幻灯片仓储实例
        """
        self.template_info_repo = template_info_repo
        self.template_slide_repo = template_slide_repo
        
        # 如果没有提供仓储实例，创建默认实例
        if not self.template_info_repo or not self.template_slide_repo:
            # 创建连接池
            db_path = config.DB_PATH
            db_pool = SQLiteConnectionPool(db_path)
            
            if not self.template_info_repo:
                self.template_info_repo = TemplateInfoRepository(db_pool)
            if not self.template_slide_repo:
                self.template_slide_repo = TemplateSlideRepository(db_pool)
    
    async def save_config(self, config_data: Dict[str, Any]) -> str:
        """保存配置"""
        try:
            # 从配置数据中提取模板信息
            config_obj = config_data.get('config', {})
            template_name = config_obj.get('templateName', '')
            filename = config_obj.get('filename', '')
            total_slides = config_obj.get('total_slides', 0)
            file_path = config_obj.get('file_path', '')
            slide_width = config_obj.get('slide_width', 960)
            slide_height = config_obj.get('slide_height', 540)
            slides = config_obj.get('slides', [])
            
            # 生成配置ID
            current_time = datetime.now().isoformat()
            config_id = file_path  # 使用file_path作为配置ID
            
            # 创建TemplateInfo实体
            template_info = TemplateInfo(
                id=config_id,
                template_name=template_name,
                filename=filename,
                total_slides=total_slides,
                file_path=file_path,
                slide_width=slide_width,
                slide_height=slide_height,
                created_at=current_time,
                updated_at=current_time
            )
            
            # 保存模板信息
            self.template_info_repo.add(template_info)
            
            # 保存每个幻灯片配置
            for slide_data in slides:
                # 生成唯一ID
                slide_id = str(uuid.uuid4())
                
                # 创建TemplateSlide实体
                template_slide = TemplateSlide(
                    id=slide_id,
                    template_id=config_id,
                    slide_index=slide_data.get('slide_index', 0),
                    width=slide_data.get('width', slide_width),
                    height=slide_data.get('height', slide_height),
                    background=slide_data.get('background', '#ffffff'),
                    elements=slide_data.get('elements', []),
                    created_at=current_time,
                    updated_at=current_time
                )
                
                # 保存幻灯片配置
                self.template_slide_repo.add(template_slide)
            
            return config_id
        except Exception as e:
            raise Exception(f"保存配置失败: {str(e)}")
    
    async def update_config(self, config_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置"""
        try:
            # 从配置数据中提取模板信息
            config_obj = config_data.get('config', {})
            template_name = config_obj.get('templateName', '')
            filename = config_obj.get('filename', '')
            total_slides = config_obj.get('total_slides', 0)
            file_path = config_obj.get('file_path', '')
            slide_width = config_obj.get('slide_width', 960)
            slide_height = config_obj.get('slide_height', 540)
            slides = config_obj.get('slides', [])
            
            # 获取当前时间
            current_time = datetime.now().isoformat()
            
            # 更新模板信息
            template_info = self.template_info_repo.find_by_id(config_id)
            if not template_info:
                raise FileNotFoundError(f"配置不存在: {config_id}")
            
            # 更新模板信息属性
            template_info.template_name = template_name
            template_info.filename = filename
            template_info.total_slides = total_slides
            template_info.file_path = file_path
            template_info.slide_width = slide_width
            template_info.slide_height = slide_height
            template_info.updated_at = current_time
            
            # 保存更新后的模板信息
            self.template_info_repo.update(template_info)
            
            # 删除原有幻灯片配置
            self.template_slide_repo.delete_by_template_id(config_id)
            
            # 保存新的幻灯片配置
            for slide_data in slides:
                # 生成唯一ID
                slide_id = str(uuid.uuid4())
                
                # 创建TemplateSlide实体
                template_slide = TemplateSlide(
                    id=slide_id,
                    template_id=config_id,
                    slide_index=slide_data.get('slide_index', 0),
                    width=slide_data.get('width', slide_width),
                    height=slide_data.get('height', slide_height),
                    background=slide_data.get('background', '#ffffff'),
                    elements=slide_data.get('elements', []),
                    created_at=current_time,
                    updated_at=current_time
                )
                
                # 保存幻灯片配置
                self.template_slide_repo.add(template_slide)
            
            return config_data
        except Exception as e:
            raise Exception(f"更新配置失败: {str(e)}")
    
    async def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载配置"""
        try:
            # 获取模板信息
            template_info = self.template_info_repo.find_by_id(config_id)
            if not template_info:
                raise FileNotFoundError(f"配置不存在: {config_id}")
            
            # 获取幻灯片配置
            template_slides = self.template_slide_repo.find_by_template_id(config_id)
            
            # 构建配置数据
            config_data = {
                'config': {
                    'id': template_info.id,
                    'templateName': template_info.template_name,
                    'filename': template_info.filename,
                    'total_slides': template_info.total_slides,
                    'file_path': template_info.file_path,
                    'slide_width': template_info.slide_width,
                    'slide_height': template_info.slide_height,
                    'slides': [
                        {
                            'slide_index': slide.slide_index,
                            'width': slide.width,
                            'height': slide.height,
                            'background': slide.background,
                            'elements': slide.elements
                        }
                        for slide in template_slides
                    ]
                }
            }
            
            return config_data
        except Exception as e:
            raise Exception(f"加载配置失败: {str(e)}")