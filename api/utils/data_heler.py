from typing import Any
import io
from json import loads
class data_helper:
    def __init__(self):
        pass
    @staticmethod
    def convert_value(value: Any, param_type: str) -> Any:
        """
        根据参数类型转换值
        字符串string、整数int、小数float、布尔boolean、文件file、字典dict、列表list、表格数据tabledata（包含value、style属性）、任意类型any
        """
        try:
            match param_type:
                case "string":
                    if not value:
                        value=None
                    else:
                        if not isinstance(value, str):
                            value=str(value)
                case "int":
                    if not value:
                        value=None
                    else:
                        if not isinstance(value, int):
                            value=int(value)
                case "float":
                    if not value:
                        value=None
                    else:
                        if not isinstance(value, float):
                            value=float(value)
                case "boolean":                                       
                    if not value:
                        value=None
                    else:
                        if not isinstance(value, bool):
                            value=bool(value)
                case "file":                    
                    if not value:
                        value=None
                    else:
                        if not isinstance(value, io.IOBase):
                            raise ValueError("参数类型 'file' 要求 value 是文件对象")
                case "dict":
                    if not value:
                        value=dict()
                    else:
                        if not isinstance(value, dict):                         
                            value=dict(loads(value))    
                case "list":
                    if not value:
                        value=dict()
                    else:
                        if not isinstance(value, list):
                            value=list(loads(value))
                case "tabledata":
                    if not value:
                        value=dict()
                    else:
                        if not isinstance(value, dict):
                            value=dict(loads(value))
                case "any":
                    pass
                case _:
                    pass
        except ValueError as e:
            # raise ValueError(f"参数类型 {param_type} 转换值失败: {str(e)}")
            print(f"参数类型 {param_type} 转换值失败: {str(e)}")
        return value