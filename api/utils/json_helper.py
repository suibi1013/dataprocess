import json
# import orjson
import os

class json_helper:
    def __init__(self):
        pass

    @staticmethod
    def read_json_file(filepath: str) -> dict:
        """
        读取json文件信息，并转换为json对象        
        Args:
            filepath: json文件路径            
        Returns:
            dict: json对象
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
            # with open(filepath, 'rb') as f:
            #     return orjson.loads(f.read())
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 格式无效 ({filepath}): {e}")

    @staticmethod
    def set_nested_value(data: dict, path: str, value):
        """
        在嵌套字典中按点分路径设置值（会修改原字典）
        
        Args:
            data: 目标字典（会被修改）
            path: 点分路径，如 "a.b.c"
            value: 要设置的值
        """
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}  # 自动创建缺失的嵌套字典
            current = current[key]
        current[keys[-1]] = value

    @staticmethod
    def update_json_file(filepath: str, path: str, value):
        """
        修改 JSON 文件中指定路径的值，并保存回文件
        
        Args:
            filepath: JSON 文件路径
            path: 点分路径（如 "param_in.a"）
            value: 新值
        """
        # 1. 读取原文件
        data = json_helper.read_json_file(filepath)
        
        # 2. 设置新值
        json_helper.set_nested_value(data, path, value)
        
        # 3. 写回文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise IOError(f"写入 JSON 文件失败 ({filepath}): {e}")