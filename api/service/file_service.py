import os
from typing import Optional, List, Tuple, Dict, Any

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
    
    def validate_file(self, file_name: str, allowed_extensions: List[str]) -> bool:
        """验证文件"""
        if not file_name:
            return False
        
        file_ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        return file_ext in allowed_extensions
    
    def validate_file_with_size(self, file_name: str, file_size: int, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """验证文件和大小"""
        if not file_name:
            return False, "文件名不能为空"
        
        if file_size <= 0:
            return False, "文件大小无效"
        
        if file_size > self.max_file_size:
            return False, f"文件大小超过限制（{self.max_file_size // (1024*1024)}MB）"
        
        file_ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        if file_ext not in allowed_extensions:
            return False, "不支持的文件类型"
        
        return True, ""
    
    async def save_uploaded_file(self, file_data: bytes, file_path: str) -> str:
        """保存上传文件"""        
        # 使用线程池异步执行文件写入操作
        import asyncio
        def write_file():
            with open(file_path, 'wb') as f:
                f.write(file_data)
            return file_path
        
        return await asyncio.to_thread(write_file)
    
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            import asyncio
            def remove_file():
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            
            return await asyncio.to_thread(remove_file)
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False
