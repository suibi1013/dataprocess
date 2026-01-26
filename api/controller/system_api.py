#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理控制器
处理系统级别的功能，如数据库备份还原等
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import os
from io import BytesIO

from service.system_service import SystemService
from di.container import inject

# 创建APIRouter实例
router = APIRouter(prefix="/api", tags=["System"])


# 数据库备份接口
@router.post("/system/backup")
async def backup_database(
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    数据库备份接口
    备份文件格式为JSON文件的zip压缩格式，不包含指定数据表
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    - data: 备份数据，包含备份文件路径和文件名
    """
    result = system_service.backup_database()
    return result


# 数据库还原接口
@router.post("/system/restore")
async def restore_database(
    backup_file_path: str,
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    数据库还原接口
    从JSON文件的zip压缩包中还原数据库
    
    输入参数：
    - backup_file_path: 备份文件路径
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    """
    result = system_service.restore_database(backup_file_path)
    return result


# 获取备份列表接口
@router.get("/system/backups")
async def get_backup_list(
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    获取备份文件列表接口
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    - data: 备份文件列表
    """
    result = system_service.get_backup_list()
    return result


# 删除备份接口
@router.delete("/system/backup/{backup_filename}")
async def delete_backup(
    backup_filename: str,
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    删除备份文件接口
    
    输入参数：
    - backup_filename: 备份文件名
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    """
    result = system_service.delete_backup(backup_filename)
    return result


# 下载备份文件接口
@router.get("/system/backup/download/{backup_filename}")
async def download_backup(
    backup_filename: str,
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    下载备份文件接口
    
    输入参数：
    - backup_filename: 备份文件名
    
    输出：
    - 备份文件流（JSON文件的zip压缩格式）
    """
    try:
        backup_dir = system_service.get_backup_dir()
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 读取文件并返回
        def file_generator():
            with open(backup_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk
        
        return StreamingResponse(
            file_generator(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={backup_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载备份文件失败: {str(e)}")


# 上传备份文件并还原接口
@router.post("/system/restore/upload")
async def upload_and_restore(
    file: bytes = File(...),
    filename: str = Form(...),
    system_service: SystemService = Depends(lambda: inject(SystemService))
):
    """
    上传备份文件并还原接口
    支持上传JSON文件的zip压缩包并还原数据库
    
    输入参数：
    - file: 备份文件流
    - filename: 备份文件名
    
    输出参数：
    - success: 是否成功
    - message: 提示信息
    """
    result = system_service.upload_and_restore(file, filename)
    return result
