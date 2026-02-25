"""
模板管理接口
"""

from fastapi import APIRouter, UploadFile, File, Form, Query, Depends, HTTPException
from fastapi.responses import FileResponse
import os
from urllib.parse import quote
# 导入配置和服务
from config import config
from utils.common import CommonUtils
from service.ppt_service import PPTservice
from service.config_service import Configservice
from service.template_service import TemplateService
from di.container import inject
from dto.template_dto import ConfigUpdateDto,ConfigSaveDto

# 创建APIRouter实例
api_router = APIRouter(prefix="/api", tags=["template"])
# PPT相关路由定义
@api_router.post("/template/upload_and_parse_ppt")
async def upload_and_parse_ppt(
    ppt_file: UploadFile = File(...),
    templateName: str = Form(...),
    ppt_service: PPTservice = Depends(lambda: inject(PPTservice))
):
    """上传并解析PPT文件"""
    try:
        # 读取文件内容
        file_content = await ppt_file.read()
        
        # 调用服务层
        response = await ppt_service.upload_and_parse_ppt(ppt_file.filename,file_content)        
        return {
            'success': True,
            'message': '文件上传并解析成功',
             'data':response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@api_router.post("/template/config/save")
async def save_config(
    config_data: ConfigSaveDto,
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

@api_router.post("/template/config/update")
async def update_config(
    request: ConfigUpdateDto,
    config_service: Configservice = Depends(lambda: inject(Configservice))
):
    """更新配置"""
    try:
        # 调用服务层方法更新配置
        config_data=await config_service.update_config(request.template_id, request.config_data)
        return {'success': True, 'message': '配置更新成功',"config_data": config_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'内部服务器错误: {str(e)}')


@api_router.get("/template/config/load")
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
        
@api_router.get("/template/list")
async def get_templates(
    template_service: TemplateService = Depends(lambda: inject(TemplateService))
):
    """获取模板列表"""
    try:
        # 调用服务层获取模板列表
        result = await template_service.get_templates()
        
        # 根据结果返回相应的响应
        if result.success:
            return {
                'success': True,
                'templates': result.data.get('templates', [])
            }
        else:
            raise HTTPException(status_code=500, detail=result.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取模板列表失败: {str(e)}')


@api_router.delete("/template/{template_id}")
async def delete_template(
    template_id: str,
    template_service: TemplateService = Depends(lambda: inject(TemplateService))
):
    """删除指定模板"""
    try:
        # 调用服务层删除模板
        result = await template_service.delete_template(template_id)
        
        # 根据结果返回相应的响应
        if result.success:
            return {
                'success': True,
                'message': result.message
            }
        else:
            raise Exception(result.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'删除模板失败: {str(e)}')


@api_router.get("/template/check_config_update")
async def check_config_update(
    file_name: str = Query(..., description="文件名"),
    template_service: TemplateService = Depends(lambda: inject(TemplateService))
):
    """检查配置更新"""
    try:
        # 调用服务层检查配置更新
        result = await template_service.check_config_update(file_name)
        
        # 根据结果返回相应的响应
        if result.success:
            return {
                'success': True,
                'hasUpdate': result.data.get('hasUpdate', False),
                'configFile': result.data.get('configFile', ''),
                'lastModified': result.data.get('lastModified', 0),
                'message': result.data.get('message', '')
            }
        else:
            return {
                'success': False,
                'hasUpdate': False,
                'message': result.message
            }
    except Exception as e:
        return {
            'success': False,
            'hasUpdate': False,
            'message': f'检查配置更新失败: {str(e)}'
        }


# 静态文件服务路由
@api_router.get("/static")
async def index():
    """根路径重定向到编辑器"""
    static_dir = config.STATIC_FOLDER
    index_path = os.path.join(static_dir, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail='静态文件未找到')


@api_router.get("/static/{file_name:path}")
async def serve_static(
    file_name: str
):
    """提供静态文件服务 - 排除API路径"""
    # 如果路径以api开头，返回404
    if file_name.startswith('api'):
        raise HTTPException(status_code=404, detail="Not Found")
    
    static_dir = config.STATIC_FOLDER
    file_path = os.path.join(static_dir, file_name)
    
    # 安全检查：确保请求的文件在静态目录内
    if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail='文件未找到')


@api_router.post("/template/replace_data")
async def replace_template_data(
    template_id: str = Query(..., description="模板ID"),
    template_service: TemplateService = Depends(lambda: inject(TemplateService))
):
    """模板数据替换接口
    根据模板id，读取模板页配置信息，获取数据源文件数据，替换PPT内元素数据
    返回替换后的PPT文件流
    """
    try:
        # 调用服务层进行数据替换
        result = await template_service.replace_template_data(template_id)
        
        # 根据结果返回相应的响应
        if result.success:
            output_file_path = result.data.get('output_file_path')
            if output_file_path:
                # 返回文件流
                # 从文件路径中提取文件名
                output_file_name = os.path.basename(output_file_path)
                # 【关键】清理并编码文件名
                safe_name = CommonUtils.safe_filename(output_file_name)
                encoded_filename = quote(safe_name, safe='')  # safe='' 表示对所有非字母数字字符编码

                # 构造只包含 filename* 的 Content-Disposition（符合 RFC 5987）
                content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"

                return FileResponse(
                    output_file_path,
                    media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    headers={'Content-Disposition': content_disposition}
                )
            else:
                raise HTTPException(status_code=500, detail='文件生成失败')
        else:
            raise HTTPException(status_code=500, detail=result.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'数据替换失败: {str(e)}')