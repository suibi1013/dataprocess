
import os
import json
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from config import config
class Configservice:
    """配置服务 - 依赖注入版本"""
    
    def __init__(self):
        self.config_folder = config.TEMPLATES_FOLDER
        os.makedirs(self.config_folder, exist_ok=True)
    
    async def save_config(self, config_data: Dict[str, Any]) -> str:
        """保存配置"""
        try:
            file_path = config_data.get('config', {}).get('file_path', '')
            config_id = os.path.splitext(os.path.basename(file_path))[0]
            config_filename = f"{config_id}.json"
            config_path = os.path.join(self.config_folder, config_filename)
            
            # 添加元数据
            config_with_meta = {
                'id': config_id,
                'created_at': datetime.now().isoformat(),
                'data': config_data
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_with_meta, f, ensure_ascii=False, indent=2)
            
            return config_id
        except Exception as e:
            raise Exception(f"保存配置失败: {str(e)}")
    
    async def update_config(self,config_id:str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置"""
        try:
            config_filename = f"{config_id}.json"
            config_path = os.path.join(self.config_folder, config_filename)
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_id}")
            config_data_old={}
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data_old = json.load(f)
            
            config_data_old['updated_time']=datetime.now().isoformat()
            config_data_old['data']=config_data
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data_old, f, ensure_ascii=False, indent=2)
            
            return config_data
        except Exception as e:
            raise Exception(f"更新配置失败: {str(e)}")
    
    async def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载配置"""
        try:
            config_filename = f"{config_id}.json"
            config_path = os.path.join(self.config_folder, config_filename)
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_id}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return config_data.get('data', {})
        except Exception as e:
            raise Exception(f"加载配置失败: {str(e)}")