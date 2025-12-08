import os
import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from werkzeug.utils import secure_filename

from config import config

class Fileservice:
    """文件处理服务 - 依赖注入版本"""
    
    def __init__(self):
        self.upload_folder = config.UPLOAD_FOLDER
        self.data_source_folder = config.DATA_SOURCES_FOLDER
        self.allowed_extensions = {'.ppt', '.pptx'}
        self.excel_extensions = {'.xlsx', '.xls'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        # 确保目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.data_source_folder, exist_ok=True)
    
    def validate_file(self, filename: str, allowed_extensions: List[str]) -> bool:
        """验证文件"""
        if not filename:
            return False
        
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return file_ext in allowed_extensions
    
    def validate_file_with_size(self, filename: str, file_size: int, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """验证文件和大小"""
        if not filename:
            return False, "文件名不能为空"
        
        if file_size <= 0:
            return False, "文件大小无效"
        
        if file_size > self.max_file_size:
            return False, f"文件大小超过限制（{self.max_file_size // (1024*1024)}MB）"
        
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext not in allowed_extensions:
            return False, "不支持的文件类型"
        
        return True, ""
    
    async def save_uploaded_file(self, file_data: bytes, filename: str, upload_folder: str) -> str:
        """保存上传文件"""
        file_path = os.path.join(upload_folder, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"❌ 删除文件失败: {str(e)}")
            return False
