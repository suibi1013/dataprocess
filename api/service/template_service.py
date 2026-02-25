#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板服务层
负责模板相关的业务逻辑处理
遵循分层架构：服务层调用仓储层，仓储层继承基础仓储
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from pandas.core.internals.construction import dict_to_mgr

from repository.template_info_repository import TemplateInfoRepository
from repository.template_slide_repository import TemplateSlideRepository
from service.base_service import BaseService
from service.result import Result
from config import config
import os
from utils.excel_pyxl import read_excel_range_data_by_range
from utils.ppt_win32com import replace_data_win32com

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
    
    async def replace_template_data(self, template_id: str) -> Result:
        """模板数据替换
        
        Args:
            template_id: 模板ID
            
        Returns:
            Result: 数据替换结果的响应对象
        """
        try:
            # 导入必要的模块
            import os
            from utils.excel_helper import ExcelHelper
            import win32com.client
            import pythoncom
            
            # 获取模板信息
            template_info = await self.template_info_repo.find_by_id(template_id)
            if not template_info:
                return Result.fail("模板不存在")            

            template_file_path = template_info.file_path            
            if not os.path.exists(template_file_path):
                return Result.fail("模板文件不存在")
            
            # 获取模板目录
            template_dir = os.path.dirname(template_file_path)
            
            # 获取模板幻灯片配置
            template_slides = await self.template_slide_repo.find_by_template_id(template_id)
            if not template_slides:
                return Result.fail("模板幻灯片配置不存在")
            
            # 梳理要替换元素的数据来源信息，按页分组
            elements_to_replace = {}
            for slide_info in template_slides:
                # 确保 slide_index 对应的键存在
                if slide_info.slide_index not in elements_to_replace:
                    elements_to_replace[slide_info.slide_index] = {}
                
                for element in slide_info.elements:
                    if 'data' in element and 'data_source_config' in element['data']:
                            data_source_config = element['data']['data_source_config']
                            if not data_source_config:
                                continue
                            data_source_path = data_source_config.get('data_source_path')
                            excel_sheet_name = data_source_config.get('excel_sheet_name')
                            excel_cell_range = data_source_config.get('excel_cell_range')
                            elements_to_replace[slide_info.slide_index][element.get('element_name')]={
                                "element_type": element.get('element_type'),
                                "data_source_path": data_source_path,
                                "excel_sheet_name": excel_sheet_name,
                                "excel_cell_range": excel_cell_range
                            }
            # 初始化COM库
            pythoncom.CoInitialize()
            
            try:
                # 加载PPT文件
                ppt_app = win32com.client.Dispatch('PowerPoint.Application')
                # 不设置 Visible 属性，使用默认值
                prs = ppt_app.Presentations.Open(template_file_path)
                
                for slide_index in elements_to_replace:
                    # win32com中幻灯片索引从1开始
                    if 1 <= slide_index + 1 <= prs.Slides.Count:
                        slide = prs.Slides(slide_index + 1)
                        elements = elements_to_replace[slide_index]
                        element_names = elements.keys()
                        
                        # 遍历PPT中的所有形状，找到对应的元素
                        for shape in slide.Shapes:
                            if shape.Name in element_names:
                                element_info = elements[shape.Name]
                                element_type = element_info.get('element_type')
                                data_source_path = element_info.get('data_source_path')
                                excel_sheet_name = element_info.get('excel_sheet_name')
                                excel_cell_range = element_info.get('excel_cell_range')
                                # 读取Excel数据
                                excel_data=None
                                try:                                    
                                    # 使用ExcelHelper读取数据
                                    excel_data = read_excel_range_data_by_range(
                                        data_source_path, 
                                        excel_sheet_name, 
                                        excel_cell_range,
                                        include_styles=True
                                    )                            
                                except Exception as e:
                                    self._log_error(f"读取Excel数据失败: {str(e)}")
                                # 替换数据
                                replace_data_win32com(shape,element_type, excel_data)

                # 保存替换后的PPT文件
                # 使用template_info表中的template_name名称
                base_name = template_info.template_name
                ext = '.pptx'  # 确保使用PPTX扩展名
                output_file_name = f"{base_name}{ext}"
                output_file_path = os.path.join(template_dir, output_file_name)
                
                # 保存为新文件
                prs.SaveAs(output_file_path)
                
                # 安全关闭演示文稿和退出应用
                try:
                    if prs:
                        prs.Close()
                except Exception as e:
                    self._log_error(f"关闭演示文稿失败: {str(e)}")
                
                try:
                    if ppt_app:
                        ppt_app.Quit()
                except Exception as e:
                    self._log_error(f"退出PowerPoint应用失败: {str(e)}")
            finally:
                # 释放COM库
                pythoncom.CoUninitialize()
            
            return Result.success(data={
                'template_id': template_id,
                'output_file_path': output_file_path,
                'message': '数据替换成功'
            })
        except Exception as e:
            self._log_error(f"数据替换失败: {str(e)}")
            return Result.fail(f"数据替换失败: {str(e)}")    
    