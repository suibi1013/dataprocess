import json
import orjson
import os
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
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 格式无效 ({filepath}): {e}")
def read_json_file1(filepath: str) -> dict:
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
        # with open(filepath, 'r', encoding='utf-8') as f:
        #     return json.load(f)
        with open(filepath, 'rb') as f:
            return orjson.loads(f.read())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 格式无效 ({filepath}): {e}")

import orjson

def write_json_file_fast(filepath: str, data: dict) -> None:
    """
    快速将 Python 对象写入 JSON 文件（使用 orjson）
    """
    # orjson.dumps 返回 bytes，且默认不支持 ensure_ascii=False（它总是输出 UTF-8）
    json_bytes = orjson.dumps(
        data,
        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS  # 可选：美化+排序
    )
    
    with open(filepath, 'wb') as f:  # 必须用 wb 模式
        f.write(json_bytes)
        
import time
time_begin=time.time()
print("方法2读取json文件",time_begin)
read_json_file1(r'E:\projectcode\dataprocess\api\config_infos\data_processes\process_flows\58bcae6f-02a5-4e7c-a934-b61d82d3689e\debug\node_1770278866993_dwcwa9wld.json')
time_end=time.time()
print(f"方法2读取json文件耗时: {time_end-time_begin} 秒")

time_begin=time.time()
print("方法1读取json文件",time_begin)
read_json_file(r'E:\projectcode\dataprocess\api\config_infos\data_processes\process_flows\58bcae6f-02a5-4e7c-a934-b61d82d3689e\debug\node_1770278866993_dwcwa9wld.json')
time_end=time.time()
print(f"方法1读取json文件耗时: {time_end-time_begin} 秒")
