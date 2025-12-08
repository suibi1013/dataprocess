"""
PPT控制器 - FastAPI + 依赖注入版本
处理PPT相关的HTTP请求
"""

from fastapi import APIRouter, UploadFile, File, Form, Query, Depends, HTTPException
from typing import Dict, Any
import os
from dataclasses import dataclass
import json
from datetime import datetime

# 导入配置和服务
from config import config
from service.ppt_service import PPTservice
from service.config_service import Configservice
from di.container import inject
from dto.ppt_dto import ConfigUpdateDto

# 错误处理函数
async def handle_internal_error(e: Exception) -> None:
    """处理内部错误"""
    raise HTTPException(status_code=500, detail=f'内部服务器错误: {str(e)}')


async def handle_file_too_large() -> None:
    """处理文件过大错误"""
    raise HTTPException(status_code=413, detail='文件大小超过限制')


# 创建APIRouter实例
api_router = APIRouter(prefix="/api", tags=["PPT"])
static_router = APIRouter(prefix="/api", tags=["Static"])


# PPT相关路由定义
@api_router.post("/ppt/upload")
async def upload_ppt(
    ppt_file: UploadFile = File(...),
    templateName: str = Form(...),
    ppt_service: PPTservice = Depends(lambda: inject(PPTservice))
):
    """上传PPT文件"""
    try:
        # 读取文件内容
        file_content = await ppt_file.read()
        
        # 直接创建请求字典
        request = {
            "filename": ppt_file.filename,
            "file_data": file_content,
            "template_name": templateName
        }
        
        # 调用服务层
        response = await ppt_service.upload_ppt(request)
        
        # 如果转换成功，返回包含配置信息的响应
        if response.get('success', False):
            conversion_result = response.get('conversion_result', {})
            file_info = response.get('file_info', {})
            return {
                'success': True,
                'message': '文件上传并解析成功',
                'filename': ppt_file.filename,
                'file_unique': file_info.get('file_unique',''),
                'file_size': len(file_content),
                'config': conversion_result.get('config'),
                'slides_count': conversion_result.get('slides_count', 0),
                'output_html_path': conversion_result.get('convert_ppt_to_html')
            }
        else:
            return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@api_router.post("/ppt/config/save")
async def save_config(
    config_data: dict,
    config_service: Configservice = Depends(lambda: inject(Configservice))
):
    """保存配置"""
    try:
        # 直接使用配置数据
        config_id = await config_service.save_config(config_data)
        return {
            "success": True,
            "message": "配置保存成功",
            "config_id": config_id
        }            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

@api_router.post("/ppt/config/update")
async def update_config(
    request: ConfigUpdateDto,
    config_service: Configservice = Depends(lambda: inject(Configservice))
):
    """更新配置"""
    try:
        # 调用服务层方法更新配置
        config_data=await config_service.update_config(request.template_id, request.config_data)
        return {'success': True, 'message': '配置更新成功',"config_data": config_data}
    except HTTPException:
        raise
    except Exception as e:
        await handle_internal_error(e)


@api_router.get("/ppt/config/load")
async def load_config(
    config_id: str = Query(..., description="配置ID"),
    config_service: Configservice = Depends(lambda: inject(Configservice))
):
    """加载配置"""
    try:
        # 调用服务层方法加载配置
        config_data = await config_service.load_config(config_id)
        return {'success': True, "message": "配置加载成功",'config_data': config_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}")

@api_router.get("/info")
async def get_server_info(
    ppt_service: PPTservice = Depends(lambda: inject(PPTservice))
):
    """获取服务器信息"""
    return {
            "service_name": "PPT转HTML转换服务",
            "version": "2.0.0 (FastAPI + DI)",
            "supported_formats": ["ppt", "pptx"],
            "max_file_size": "50MB",
            "status": "running"
        }


@api_router.get("/templates")
async def get_templates(
    config_service: Configservice = Depends(lambda: inject(Configservice))
):
    """获取模板列表"""
    try:
        from repository.base_repository import SQLiteConnectionPool
        from repository.template_info_repository import TemplateInfoRepository
        
        # 创建连接池
        db_path = config.DB_PATH
        db_pool = SQLiteConnectionPool(db_path)
        
        # 创建模板信息仓储实例
        template_info_repo = TemplateInfoRepository(db_pool)
        
        # 获取所有模板信息
        template_infos = template_info_repo.find_all()
        
        # 构建响应数据
        templates = []
        for template_info in template_infos:
            template = {
                'id': template_info.id,
                'name': template_info.template_name,
                'filename': template_info.filename,
                'createTime': template_info.created_at,
                'status': 'ready'
            }
            templates.append(template)
        
        return {
            'success': True,
            'templates': templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'服务器错误: {str(e)}')


@api_router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str
):
    """删除指定模板"""
    try:
        from repository.base_repository import SQLiteConnectionPool
        from repository.template_info_repository import TemplateInfoRepository
        from repository.template_slide_repository import TemplateSlideRepository
        
        # 创建连接池
        db_path = config.DB_PATH
        db_pool = SQLiteConnectionPool(db_path)
        
        # 创建仓储实例
        template_info_repo = TemplateInfoRepository(db_pool)
        template_slide_repo = TemplateSlideRepository(db_pool)
        
        # 检查模板是否存在
        template_info = template_info_repo.find_by_id(template_id)
        if not template_info:
            raise HTTPException(status_code=404, detail='模板不存在')
        
        # 删除模板幻灯片配置
        template_slide_repo.delete_by_template_id(template_id)
        
        # 删除模板信息
        template_info_repo.delete(template_id)
        
        return {
            'success': True,
            'message': '模板删除成功'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'服务器错误: {str(e)}')


@api_router.get("/check_config_update")
async def check_config_update(
    filename: str = Query(..., description="文件名")
):
    """检查配置更新"""
    try:
        from repository.base_repository import SQLiteConnectionPool
        from repository.template_info_repository import TemplateInfoRepository
        
        # 创建连接池
        db_path = config.DB_PATH
        db_pool = SQLiteConnectionPool(db_path)
        
        # 创建模板信息仓储实例
        template_info_repo = TemplateInfoRepository(db_pool)
        
        # 获取所有模板信息
        template_infos = template_info_repo.find_all()
        
        # 查找匹配的模板
        for template_info in template_infos:
            if filename in template_info.filename:
                # 获取最后更新时间戳
                import time
                updated_time = datetime.fromisoformat(template_info.updated_at)
                mtime = time.mktime(updated_time.timetuple())
                
                return {
                    'success': True,
                    'hasUpdate': True,
                    'configFile': template_info.id + '.json',  # 保持与原接口兼容
                    'lastModified': mtime,
                    'message': '找到匹配的配置文件'
                }
        
        return {
            'success': True,
            'hasUpdate': False,
            'message': '未找到匹配的配置文件'
        }
    except Exception as e:
        return {
            'success': False,
            'hasUpdate': False,
            'message': f'检查配置更新失败: {str(e)}'
        }


# 静态文件服务路由
@static_router.get("/static")
async def index():
    """根路径重定向到编辑器"""
    static_dir = config.STATIC_FOLDER
    index_path = os.path.join(static_dir, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail='静态文件未找到')


@static_router.get("/static/{filename:path}")
async def serve_static(
    filename: str
):
    """提供静态文件服务 - 排除API路径"""
    # 如果路径以api开头，返回404
    if filename.startswith('api'):
        raise HTTPException(status_code=404, detail="Not Found")
    
    static_dir = config.STATIC_FOLDER
    file_path = os.path.join(static_dir, filename)
    
    # 安全检查：确保请求的文件在静态目录内
    if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail='文件未找到')