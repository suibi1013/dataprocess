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
        file_name = os.path.basename(filepath)
        if not file_name or '.' not in file_name:
            # 从 URL path 尝试获取
            parsed_path = parsed.path
            if parsed_path and '/' in parsed_path:
                file_name = os.path.basename(parsed_path)
            if not os.path.splitext(file_name)[1]:
                # 仍然没有扩展名
                file_name += '.bin'

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
                "Content-Disposition": f"attachment; file_name={file_name}"
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