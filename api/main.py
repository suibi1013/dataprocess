#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT上传处理服务器 - FastAPI + 依赖注入版本
提供PPT文件上传、转换和管理功能
"""

import os
import sys
from pathlib import Path

# 获取当前文件所在目录，并添加到Python搜索路径
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# 导入依赖注入相关模块
from di.config import configure_dependencies
from controller.ppt_api import api_router as ppt_api_router, static_router as ppt_static_router
from controller.data_source_api import router as datasource_router
from controller.instruction_api import router as instruction_router
from controller.data_process_api import router as data_process_router
from controller.file_api import router as file_router

# 创建FastAPI应用
app = FastAPI(
    title="PPT转HTML转换服务",
    description="提供PPT文件上传、转换为HTML格式的API服务 - 依赖注入版本",
    version="2.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "file://*"  # 允许Electron应用（file协议）访问
    ],  # 允许的具体域名和协议
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置依赖注入
container = configure_dependencies()

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"收到请求: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"请求处理完成: {request.method} {request.url} - 状态码: {response.status_code} - 耗时: {process_time:.4f}s")
    return response

# 注册路由
app.include_router(ppt_api_router)
app.include_router(ppt_static_router)
app.include_router(datasource_router)
app.include_router(instruction_router)
app.include_router(data_process_router)
app.include_router(file_router)

# 全局异常处理
@app.exception_handler(413)
async def request_entity_too_large_handler(request, exc):
    """文件过大错误处理"""
    return JSONResponse(status_code=413, content={
        "success": False,
        "error": "文件大小超过限制（50MB）",
        "message": "上传的文件过大，请选择小于50MB的文件"
    })

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """内部服务器错误处理"""
    return JSONResponse(status_code=500, content={
        "success": False,
        "error": f"Internal server error: {str(exc)}",
        "message": "服务器内部错误，请稍后重试"
    })

if __name__ == '__main__':
    import uvicorn
    # 启动PPT转HTML后端API服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5001,
        reload=False,  # 在生产环境中禁用reload，避免启动多个python进程
        log_level="info"
    )