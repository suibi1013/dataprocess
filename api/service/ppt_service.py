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
    
    async def upload_ppt(self, request) -> Dict[str, Any]:
        """上传PPT文件"""
        try:
            # 验证文件
            if not self.file_service.validate_file(request["filename"], self.allowed_extensions):
                return {
                    "success": False,
                    "message": "不支持的文件类型，请上传PPT或PPTX文件",
                    "file_info": None,
                    "conversion_result": None
                }
            # 生成唯一文件名
            unique_filename=CommonUtils.encode_text_to_code(request["filename"])
            unique_filename_noextension=os.path.splitext(unique_filename)[0]
            output_dir = os.path.join(self.upload_folder, unique_filename_noextension)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 保存文件
            file_path = await self.file_service.save_uploaded_file(
                request["file_data"], 
                unique_filename, 
                output_dir
            )
            # 转换PPT
            conversion_result = await self.conversion_service.convert_ppt_to_html(
                file_path, 
                output_dir
            )
            print(f"转换结果: {conversion_result}")
            
            return {
                "success": True,
                "message": "文件上传并转换成功",
                "file_info": {
                    'filename': request["filename"],
                    'file_unique': unique_filename_noextension,
                    'file_path': file_path,
                    'file_size': len(request["file_data"])
                },
                "conversion_result": conversion_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"上传失败: {str(e)}",
                "file_info": None,
                "conversion_result": None
            }    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "message": "PPT转HTML服务运行正常",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "service_name": "PPT转HTML转换服务",
            "version": "2.0.0 (FastAPI + DI)",
            "supported_formats": ["ppt", "pptx"],
            "max_file_size": "50MB",
            "upload_folder": self.file_service.upload_folder,
            "status": "running"
        }