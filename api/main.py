#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI + 依赖注入版本
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
from controller.template_api import api_router as template_api_router
from controller.data_source_api import router as datasource_router
from controller.instruction_api import router as instruction_router
from controller.data_process_api import router as data_process_router
from controller.file_api import router as file_router
from controller.system_api import router as system_router

# 创建FastAPI应用
app = FastAPI(
    title="数据流程",
    description="提供数据流程设计、管理和执行",
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
    expose_headers=["Content-Disposition"]  # 暴露 Content-Disposition请求头，用于获取文件名称
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
app.include_router(template_api_router)
app.include_router(datasource_router)
app.include_router(instruction_router)
app.include_router(data_process_router)
app.include_router(file_router)
app.include_router(system_router)

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
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动数据流程服务平台")
    parser.add_argument("--port", type=int, default=5001, help="服务器端口号，默认5001")
    args = parser.parse_args()
    
    # API服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=args.port,
        reload=False,  # 在生产环境中禁用reload，避免启动多个python进程
        log_level="info"
    )