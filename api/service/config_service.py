
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
from service.base_service import BaseService
from dto.template_dto import ConfigSaveDto

class Configservice(BaseService):
    """配置服务 - 依赖注入版本"""
    
    def __init__(self, 
                 template_info_repo: TemplateInfoRepository,
                 template_slide_repo: TemplateSlideRepository):
        """初始化配置服务
        
        Args:
            template_info_repo: 模板信息仓储实例
            template_slide_repo: 模板幻灯片仓储实例
        """
        super().__init__()
        self.template_info_repo = template_info_repo
        self.template_slide_repo = template_slide_repo
    
    async def save_config(self, dto: ConfigSaveDto) -> str:
        """保存配置"""
        try:
            # 生成配置ID
            current_time = datetime.now().isoformat()
            
            # 创建TemplateInfo实体
            template_info = TemplateInfo(
                id=dto.id,
                template_name=dto.template_name,
                file_name=dto.file_name,
                file_size=dto.file_size,
                total_slides=dto.total_slides,
                file_path=dto.file_path,
                slide_width=dto.slide_width,
                slide_height=dto.slide_height,
                created_at=current_time,
                updated_at=current_time
            )
            
            # 保存模板信息
            await self.template_info_repo.add(template_info)
            
            # 保存每个幻灯片配置
            for slide_data in dto.slides:
                # 生成唯一ID
                slide_id = str(uuid.uuid4())
                
                # 创建TemplateSlide实体
                template_slide = TemplateSlide(
                    id=slide_id,
                    template_id=dto.id,
                    slide_index=slide_data.slide_index,
                    width=slide_data.width,
                    height=slide_data.height,
                    background=slide_data.background,
                    elements=[elem.model_dump() for elem in slide_data.elements],
                    data_source_config_info=[data_source_config.model_dump() for data_source_config in slide_data.data_source_config_info],
                    created_at=current_time,
                    updated_at=current_time
                )
                
                # 保存幻灯片配置
                await self.template_slide_repo.add(template_slide)
            
            return dto.id
        except Exception as e:
            # 删除模板目录及文件             
            import os
            import shutil
            template_dir = os.path.join(config.UPLOAD_FOLDER, template_id)
            if os.path.exists(template_dir):
                shutil.rmtree(template_dir, ignore_errors=True)
            self._log_error(f"保存配置失败: {str(e)}")
            raise Exception(f"保存配置失败: {str(e)}")
    
    async def update_config(self, template_id: str, slide_index: int, data_source_config_info: any) -> None:
        """更新配置"""
        try:
            await self.template_slide_repo.update_data_source_config_info(template_id, slide_index, data_source_config_info)
        except Exception as e:
            self._log_error(f"更新配置失败: {str(e)}")
            raise Exception(f"更新配置失败: {str(e)}")
    
    async def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载配置"""
        try:
            # 获取模板信息
            template_info = await self.template_info_repo.find_by_id(config_id)
            if not template_info:
                raise FileNotFoundError(f"配置不存在: {config_id}")
            
            # 获取幻灯片配置
            template_slides = await self.template_slide_repo.find_by_template_id(config_id)
            
            # 构建配置数据
            config_data = {
                'id': template_info.id,
                'templateName': template_info.template_name,
                'file_name': template_info.file_name,
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
                        'elements': slide.elements,
                        'data_source_config_info': slide.data_source_config_info,
                        'updated_at': slide.updated_at
                    }
                    for slide in template_slides
                ]                
            }
            
            return config_data
        except Exception as e:
            self._log_error(f"加载配置失败: {str(e)}")
            raise Exception(f"加载配置失败: {str(e)}")