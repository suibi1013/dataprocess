#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作控制器
处理文件内容和样式的获取，支持网络路径和本地路径
"""

from sys import exception
from fastapi import APIRouter, Query, HTTPException, Depends
import os
from pathlib import Path
from typing import Optional

# 导入配置和服务
from config import config
from utils.excel_helper import ExcelHelper
from utils.common import CommonUtils

# 创建APIRouter实例
router = APIRouter(prefix="/api", tags=["文件操作"])

@router.get("/file/excel_data_and_style")
async def get_file_info(
    file_path: str = Query(..., description="Excel文件路径"),
    sheet_name: Optional[str] = Query(None, description="工作表名称")
):
    """
    获取Excel文件内容和样式信息
    
    - **file_path**: Excel文件路径，可以是本地路径（必须在允许的目录内）
    - **sheet_name**: 工作表名称，不指定则使用第一个工作表
    """
    try:
        # 安全设置：允许访问的本地目录白名单
        allowed_local_dirs = [
            config.UPLOAD_FOLDER,
            config.TEMPLATES_FOLDER,
            config.DATA_SOURCES_FOLDER
        ]
        
        # 检查路径安全性
        normalized_path = os.path.normpath(file_path)
        is_safe = False
        for allowed_dir in allowed_local_dirs:
            allowed_dir_norm = os.path.normpath(allowed_dir)
            if normalized_path.startswith(allowed_dir_norm):
                is_safe = True
                break
        
        if not is_safe:
            raise HTTPException(
                status_code=403,
                detail=f"访问路径 {file_path} 被拒绝：不在允许的目录范围内"
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在：{file_path}"
            )
        
        # 检查文件扩展名是否为Excel相关
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ExcelHelper.EXCEL_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式：{file_ext}，仅支持Excel文件（{', '.join(ExcelHelper.EXCEL_EXTENSIONS)}）"
            )
        
        # 使用ExcelHelper读取Excel范围数据和样式
        file_result = await ExcelHelper.read_excel_file(file_path, sheet_name)
        
        # 检查读取结果
        if not file_result or not file_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=file_result.get('message', '读取Excel文件失败')
            )
        
        result_data = {
            'files': [],
            'sheets': [],
            'data': {}
        }
        # 尝试文件名解码
        filename=Path(file_path).stem
        original_filename=''
        try:
            original_filename=CommonUtils.decode_code_to_text(filename)
        except Exception as e:
            original_filename=filename
        if file_result['success'] and file_result['data']:
            # 获取返回的数据
            file_data = file_result['data']
            
            # 处理文件信息，保留original_filename
            for file_info in file_data['files']:
                # 添加原始文件名信息
                file_info['filename'] = filename
                file_info['original_filename'] = original_filename
                result_data['files'].append(file_info)
            
            # 合并工作表名称（去重）
            for sheet in file_data['sheets']:
                if sheet not in result_data['sheets']:
                    result_data['sheets'].append(sheet)
            
            # 合并数据，修改键名以匹配原有格式
            for original_key, sheet_data in file_data['data'].items():
                # 使用唯一名称生成新的键
                new_key = f"{filename}_{sheet_data['sheet_name']}"
                # 复制数据并确保包含所有必要字段
                result_data['data'][new_key] = {
                    'filename': filename,
                    'sheet_name': sheet_data['sheet_name'],
                    'columns': sheet_data['columns'],
                    'rows': sheet_data['rows'],
                    'total_rows': sheet_data['total_rows'],
                    'displayed_rows': sheet_data['displayed_rows']
                }
                
        return {
            "success": True,
            "message":f'成功获取文件 {os.path.basename(file_path)} 中工作表 {sheet_name} 的数据',
            "data": result_data
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"获取Excel数据失败：{str(e)}"
        )

@router.get("/file/download_file")
async def download_file(filepath: str):
    """
    下载文件（URL 或本地路径），使用流式传输处理大文件，避免内存溢出。
    """
    import requests
    import os
    from urllib.parse import urlparse
    import mimetypes
    from fastapi.responses import StreamingResponse
    from fastapi import HTTPException
    
    try:
        parsed = urlparse(filepath)

        # 安全检查：本地文件路径验证
        if parsed.scheme not in ('http', 'https'):
            # 安全设置：允许访问的本地目录白名单
            allowed_local_dirs = [
                config.UPLOAD_FOLDER,
                config.TEMPLATES_FOLDER,
                config.DATA_SOURCES_FOLDER
            ]
            
            # 检查路径安全性
            normalized_path = os.path.normpath(filepath)
            is_safe = False
            for allowed_dir in allowed_local_dirs:
                allowed_dir_norm = os.path.normpath(allowed_dir)
                if normalized_path.startswith(allowed_dir_norm):
                    is_safe = True
                    break
            
            if not is_safe:
                raise HTTPException(
                    status_code=403,
                    detail=f"访问路径 {filepath} 被拒绝：不在允许的目录范围内"
                )

        # 推测文件名
        filename = os.path.basename(filepath)
        if not filename or '.' not in filename:
            # 从 URL path 尝试获取
            parsed_path = parsed.path
            if parsed_path and '/' in parsed_path:
                filename = os.path.basename(parsed_path)
            if not os.path.splitext(filename)[1]:
                # 仍然没有扩展名
                filename += '.bin'

        # 推测 MIME 类型
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'

        # 根据文件类型创建流式生成器
        if parsed.scheme in ('http', 'https'):
            # 网络文件流式读取函数
            def stream_network_file():
                with requests.get(filepath, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    # 分块读取，每块10MB
                    for chunk in r.iter_content(chunk_size=10 * 1024 * 1024):
                        if chunk:
                            yield chunk
        else:
            # 本地文件流式读取函数
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"本地文件不存在: {filepath}")
            if not os.path.isfile(filepath):
                raise IsADirectoryError(f"路径不是文件: {filepath}")
                
            def stream_local_file():
                # 分块读取，每块10MB
                with open(filepath, 'rb') as f:
                    chunk = f.read(10 * 1024 * 1024)
                    while chunk:
                        yield chunk
                        chunk = f.read(10 * 1024 * 1024)

        # 选择对应的流式生成器
        file_stream = stream_network_file() if parsed.scheme in ('http', 'https') else stream_local_file()

        # 返回StreamingResponse实现流式下载
        return StreamingResponse(
            content=file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"文件处理失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件下载失败: {str(e)}"
        )