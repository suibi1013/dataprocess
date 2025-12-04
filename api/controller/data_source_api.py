#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源控制器 - FastAPI + 依赖注入版本
处理数据源相关的HTTP请求
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path as PathParam, File, UploadFile, Form, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
from werkzeug.utils import secure_filename

from config import config
from service.data_source_service import DataSourceservice
from di.container import inject
from dto.datasource_dto import (ExcelDataSourceConfig,ExcelDataSourceFilesConfig)
from utils.common import CommonUtils

class CreateDataSourceRequest(BaseModel):
    """创建数据源请求模型"""
    name: str
    description: Optional[str] = None
    type: str  # excel, api, database
    config: Dict[str, Any]  # 保持Dict类型用于接收前端数据，内部转换为DTO
    user_id: Optional[str] = "default"
    
    def to_data_source_dict(self) -> Dict[str, Any]:
        """转换为数据源字典，用于创建DTO"""
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'config': self.config,
            'user_id': self.user_id
        }

class UpdateDataSourceRequest(BaseModel):
    """更新数据源请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None  # 保持Dict类型用于接收前端数据
    is_active: Optional[bool] = None
    
    def to_update_dict(self) -> Dict[str, Any]:
        """转换为更新字典"""
        update_data = {}
        if self.name is not None:
            update_data['name'] = self.name
        if self.description is not None:
            update_data['description'] = self.description
        if self.config is not None:
            update_data['config'] = self.config
        if self.is_active is not None:
            update_data['is_active'] = self.is_active
        return update_data

# 处理内部服务器错误
async def handle_internal_error(exc: Exception) -> Dict[str, Any]:
    """处理内部服务器错误"""
    return {
        "success": False,
        "error": f"Internal server error: {str(exc)}",
        "message": "服务器内部错误，请稍后重试"
    }

# 创建APIRouter实例
router = APIRouter(prefix="/api",tags=["DataSource"])

# 数据源路由
@router.post("/datasource")
async def create_data_source(
    request: CreateDataSourceRequest,
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """创建数据源"""
    try:
        # 验证请求数据
        if not request.name or not request.type:
            raise HTTPException(status_code=400, detail="数据源名称和类型不能为空")
        
        # 调用服务层，使用转换方法
        result = await data_source_service.create_data_source(request.to_data_source_dict())
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data.to_dict() if result.data else None
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据源失败: {str(e)}")

@router.get("/datasource/file-data")
async def get_data_source_by_file_path(
    file_path: str = Query(..., description="Excel文件路径"), 
    sheet_name: str = Query(..., description="工作表名称"), 
    limit: int = Query(100, description="返回数据的最大行数"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """通过文件路径和工作表名获取数据源数据"""
    try:
        result = await data_source_service.get_data_source_by_file_path(file_path, sheet_name, limit)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"通过文件路径获取数据源数据失败: {str(e)}")

@router.get("/datasource/details/{data_source_id}")
async def get_data_source(
    data_source_id: str = PathParam(..., description="数据源ID"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """获取数据源详情"""
    try:
        result = await data_source_service.get_data_source(data_source_id)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源失败: {str(e)}")

@router.get("/datasources")
async def get_user_data_sources(
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """获取用户数据源列表"""
    try:
        result = await data_source_service.get_user_data_sources()
        
        if result.success:
            data_sources = result.data.get('data_sources', []) if result.data else []
            total = result.data.get('total', 0) if result.data else 0
            return {
                "success": True,
                "message": result.message,
                "data": data_sources,
                "total": total
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户数据源列表失败: {str(e)}")

@router.put("/datasource/{data_source_id}")
async def update_data_source(
    request: UpdateDataSourceRequest,
    data_source_id: str = PathParam(..., description="数据源ID"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """更新数据源"""
    try:
        # 过滤掉None值
        update_data = {k: v for k, v in request.dict().items() if v is not None}        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供有效的更新数据")        
        result = await data_source_service.update_data_source(data_source_id, update_data)        
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新数据源失败: {str(e)}")

@router.delete("/datasource/{data_source_id}")
async def delete_data_source(
    data_source_id: str = PathParam(..., description="数据源ID"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """删除数据源"""
    try:
        result = await data_source_service.delete_data_source(data_source_id)
        
        if result.success:
            return {
                "success": True,
                "message": result.message
            }
        else:
            raise HTTPException(status_code=404, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据源失败: {str(e)}")

@router.post("/datasource/upload_excel")
async def upload_excel(
    file: UploadFile = File(...),
    name: str = Form(...),
    type: str = Form(...),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """上传Excel文件并创建数据源"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        
        # 验证文件大小 (50MB限制)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
        
        # 保存文件
        filename = secure_filename(file.filename)
        excel_files_folder = f'{config.DATA_SOURCES_FOLDER}/excel_files'
        os.makedirs(excel_files_folder, exist_ok=True)
        
        # 生成唯一文件名
        unique_filename = CommonUtils.encode_text_to_code(filename)
        file_path = os.path.join(excel_files_folder, unique_filename)
        
        # 保存文件到磁盘
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        # 创建数据源配置
        datasource_config:ExcelDataSourceConfig=ExcelDataSourceConfig(
            file_name=filename,
            file_path=file_path,
            unique_name=unique_filename,
        )
        
        # 创建数据源请求
        request_data = {
            'name': name,
            'type': type,
            'config': [datasource_config.__dict__],
            'user_id': 'default'
        }
        
        # 调用服务层创建数据源
        result = await data_source_service.create_data_source(request_data)
        
        if result.success:
            return {
                "success": True,
                "message": f"Excel数据源 '{name}' 创建成功",
                "data": result.data
            }
        else:
            # 如果创建失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return result
            
    except HTTPException:
        raise
    except Exception as exc:
        return await handle_internal_error(exc)

@router.post("/upload_multiple_excel_data_sources")
async def upload_multiple_excel(
    files: List[UploadFile] = File(...),
    name: str = Form(None),
    description: Optional[str] = Form(None),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """上传多个Excel文件并创建单个数据源"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        # 创建数据源配置
        datasource_config_list:list[ExcelDataSourceConfig] = []
        failed_files = []
        
        # 处理所有文件
        for file in files:
            try:
                # 验证文件类型
                if not file.filename.lower().endswith(('.xlsx', '.xls')):
                    failed_files.append({
                        "filename": file.filename,
                        "error": "只支持Excel文件(.xlsx, .xls)"
                    })
                    continue
                
                # 验证文件大小 (50MB限制)
                if file.size and file.size > 50 * 1024 * 1024:
                    failed_files.append({
                        "filename": file.filename,
                        "error": "文件大小不能超过50MB"
                    })
                    continue
                
                # 保存文件
                filename = file.filename
                excel_files_folder = os.path.join(config.DATA_SOURCES_FOLDER, 'excel_files')
                os.makedirs(excel_files_folder, exist_ok=True)
                
                # 生成唯一文件名
                unique_filename = CommonUtils.encode_text_to_code(filename)
                file_path = os.path.join(excel_files_folder, unique_filename)
                
                try:
                    # 保存文件到磁盘
                    with open(file_path, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)
                except Exception as e:
                    return {"success": False, "message": f"文件保存失败:{str(e)}"}
                
                # 收集文件信息
                datasource_config:ExcelDataSourceConfig=ExcelDataSourceConfig(
                    file_name=filename,
                    file_path=file_path,
                    unique_name=unique_filename,
                )
                datasource_config_list.append(datasource_config)
                    
            except Exception as file_exc:
                failed_files.append({
                    "filename": file.filename,
                    "error": f"处理文件时出错: {str(file_exc)}"
                })
        
        # 生成数据源名称
        if not name:
            if len(datasource_config_list) == 1:
                data_source_name = os.path.splitext(datasource_config_list[0].file_name)[0]
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                data_source_name = f"多文件数据源_{timestamp}"
        else:
            data_source_name = name
        
        excel_config:ExcelDataSourceFilesConfig=ExcelDataSourceFilesConfig(files=datasource_config_list)
        # 创建数据源请求
        request_data = {
            'name': data_source_name,
            'type': 'excel',  # 默认为excel类型
            'config':excel_config.model_dump(),
            'user_id': 'default',
            'description': description
        }
        
        # 调用服务层创建数据源
        result = await data_source_service.create_data_source(request_data)
        
        if result.success:
            return {
                "success": True,
                "message": f"Excel数据源 '{data_source_name}' 创建成功，包含 {len(datasource_config_list)} 个文件",
                "data_source_name": data_source_name,
                "file_count": len(datasource_config_list),
                "failed_files": failed_files
            }
        else:
            # 如果创建失败，删除已上传的文件
            for datasource_config in datasource_config_list:
                if os.path.exists(datasource_config.file_path):
                    os.remove(datasource_config.file_path)  # 修复：使用正确的变量名
            return {
                "success": False,
                "message": "创建数据源失败",
                "error": result.get('error', '未知错误'),
                "failed_files": failed_files
            }
            
    except HTTPException:
        raise
    except Exception as exc:
        return await handle_internal_error(exc)

@router.get("/datasource/{data_source_id}/data")
async def get_data_source_data(
    data_source_id: str = PathParam(..., description="数据源ID"),
    sheet_name: Optional[str] = Query(None, description="工作表名称"),
    limit: int = Query(100, description="返回数据行数限制"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """获取数据源数据"""
    try:
        result = await data_source_service.get_data_source_data(data_source_id, sheet_name, limit)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源数据失败: {str(e)}")

@router.post("/datasource/{data_source_id}/range")
async def get_data_source_range(
    data_source_id: str = PathParam(..., description="数据源ID"),
    request: dict = Body(...),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """获取数据源指定范围的数据"""
    try:
        sheet_name = request.get('sheet_name')
        cell_range = request.get('cell_range')
        
        result = await data_source_service.get_data_source_range(data_source_id, sheet_name, cell_range)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data
            }
        else:
            raise HTTPException(status_code=404, detail=result.message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源范围数据失败: {str(e)}")


@router.post("/datasource/upload-file")
async def upload_data_source_file(
    file: UploadFile = File(...),
    unique_filename: Optional[str] = Form(None, description="文件标识id,可为空"),
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """上传数据源文件
    
    输入参数：
    - file: 文件流
    - unique_filename: 文件标识id,可为空
    
    输出参数：
    - file_name: 文件名称
    - unique_name: 文件标识id
    - file_path: 文件保存路径
    - file_size: 文件大小
    """
    try:
        # 获取原始文件名
        original_filename = file.filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 保存文件
        excel_files_folder = f'{config.DATA_SOURCES_FOLDER}/excel_files'
        os.makedirs(excel_files_folder, exist_ok=True)
        
        # 注意：只分割最后一个 . 后缀
        original_filename, ext = os.path.splitext(file.filename)
        # 生成唯一文件名
        if not unique_filename:
            # 如果没有提供unique_filename，使用FileHelper生成
            unique_filename = CommonUtils.encode_text_to_code(original_filename)+ext
        
        # 构建文件路径
        file_path = f'{excel_files_folder}/{unique_filename}'
        
        # 保存文件到磁盘
        content = await file.read()
        file_size = len(content)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
                
        # 返回文件信息
        return ExcelDataSourceConfig(
            file_name=original_filename,
            unique_name=unique_filename,
            file_path=file_path,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/datasource/all-options")
async def get_all_data_source_options(
    data_source_service: DataSourceservice = Depends(lambda: inject(DataSourceservice))
):
    """获取所有数据源信息，用于下拉选择
    
    返回结构：
    [{
        value: '数据源id',
        label: '数据源名称',
        children: [{
            value: '文件地址1',
            label: '文件名称1'
        }, {
            value: '文件地址2',
            label: '文件名称2'
        }]
    }]
    """
    try:
        # 获取所有数据源
        result = await data_source_service.get_user_data_sources()
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        data_sources = result.data.get('data_sources', []) if result.data else []
        options = []
        
        # 转换数据格式
        for ds in data_sources:
            if ds.type == 'excel':
                option = {
                    'value': ds.id,
                    'label': ds.name,
                    'children': []
                }
                
                # 处理配置中的文件信息
                files = ds.config.files
                
                # 处理多文件配置格式
                if isinstance(files, list):
                    for file_config in files:                    
                        option['children'].append({
                            'value': file_config.file_path,
                            'label': file_config.file_name
                        })
                
                # 只有当有子项时才添加到结果中
                if option['children']:
                    options.append(option)
        
        return options
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源选项失败: {str(e)}")