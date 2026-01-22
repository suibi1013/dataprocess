#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT处理服务层 - 依赖注入版本
负责PPT文件的上传、转换、配置管理等核心业务逻辑
"""

import os
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from config import config
from service.file_service import Fileservice
from service.ppt_conversion_service import PPTConversionservice
from utils.common import CommonUtils
class PPTservice:
    """PPT服务 - 依赖注入版本"""
    
    def __init__(self, file_service: Fileservice,conversion_service: PPTConversionservice):
        self.file_service = file_service
        self.conversion_service = conversion_service
        self.upload_folder = config.UPLOAD_FOLDER
        self.allowed_extensions = ['.ppt', '.pptx']
        self.max_file_size = 50 * 1024 * 1024
    
    async def upload_and_parse_ppt(self, file_name:str, file_data:bytes) -> Dict[str, Any]:
        """上传并解析PPT文件"""
        try:
            # 验证文件
            if not self.file_service.validate_file(file_name, self.allowed_extensions):
                return {
                    "success": False,
                    "message": "不支持的文件类型，请上传PPT或PPTX文件",
                    "file_info": None,
                    "conversion_result": None
                }
            # 创建文件目录
            template_unique_id=CommonUtils.generate_unique_id()
            output_dir = os.path.join(self.upload_folder, template_unique_id)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            # 保存文件
            file_name_noextension, file_ext = os.path.splitext(file_name)
            unique_file_name_noextension=CommonUtils.encode_text_to_code(file_name_noextension)
            file_path = os.path.join(output_dir, unique_file_name_noextension+file_ext)
            await self.file_service.save_uploaded_file(
                file_data, 
                file_path
            )
            # 解析转换PPT
            conversion_result = await self.conversion_service.convert_ppt_to_html(
                file_path, 
                output_dir
            )
            print(f"转换结果: {conversion_result}")
            
            return {
                    "template_unique_id":template_unique_id,
                    'file_name': file_name,
                    "file_path":file_path,
                    "file_size":len(file_data),
                    "output_html_path":conversion_result.get('convert_ppt_to_html'),
                    "total_slides":conversion_result.get('total_slides',0),
                    **conversion_result.get('config')
                }
            
        except Exception as e:
            raise Exception(f"上传解析失败: {str(e)}")