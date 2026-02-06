from typing import List, Dict, Any, Union, Callable, Optional
import re
import ast

def _col_to_index_0based(col: Union[str, int],max_col: int) -> int:
    """将列索引转换为 0-based 的列索引
    :param col: 列索引（1-based 或字母表示）
    :param max_col: 最大列索引（用于验证,1-based）
    :return: 0-based 的列索引
    """
    if isinstance(col, str):
        if col.strip()=="": col=max_col
        else:
            # 先尝试将字符串转换为整数
            if not col.isalpha(): 
                col = int(col)
    if isinstance(col, int):
        # 验证列索引是否在有效范围内,写入时，允许超出最大索引
        # if col > max_col: raise ValueError(f"Column index must be <= {max_col}")
        if col==0: raise ValueError(f"Column index can't be 0")
        # 转换为 0-based 索引
        if col < 0:col=max_col+col
        else:col-=1
        return col
    elif isinstance(col, str):        
        col = col.upper().strip()
        idx = 0
        for ch in col:
            if not ch.isalpha(): raise ValueError(f"Invalid column letter: {col}")
            idx = idx * 26 + (ord(ch) - ord('A') + 1)
        return idx-1   
def _build_condition(operator: str, value: Any) -> Callable[[Any], bool]:
    """
    根据操作符和值构建过滤条件函数。
    
    :param operator: 操作符，如 "==", "!=", "like", "is not None" 等
    :param value: 比较值（对 is None 类操作可忽略）
    :return: 接收 cell_value 并返回 bool 的函数
    """
    operator = operator.strip().lower()

    if operator == "is none":
        return lambda x: x is None and str(x).strip() == "" and str(x).strip().lower() == "none"

    if operator == "is not none":
        return lambda x: x is not None and str(x).strip() != "" and str(x).strip().lower() != "none"

    if operator == "==":
        return lambda x: x == value

    if operator == "!=":
        return lambda x: x != value

    if operator == ">":        
        # return lambda x: isinstance(x, (int, float)) and x > value
        return lambda x:float(x) > float(value)

    if operator == ">=":
        # return lambda x: isinstance(x, (int, float)) and x >= value
        return lambda x:float(x) >= float(value)

    if operator == "<":
        # return lambda x: isinstance(x, (int, float)) and x < value
        return lambda x:float(x) < float(value)

    if operator == "<=":
        # return lambda x: isinstance(x, (int, float)) and x <= value
        return lambda x:float(x) <= float(value)

    if operator == "in":
        value = ast.literal_eval(str(value))
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("操作符 'in' 要求 value 是列表、元组或集合")
        val_set = set(value)
        return lambda x: x in val_set

    if operator == "not in":
        value = ast.literal_eval(str(value))
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("操作符 'not in' 要求 value 是列表、元组或集合")
        val_set = set(value)
        return lambda x: x not in val_set

    if operator == "like":
        # 模糊匹配：转为字符串并检查是否包含（忽略大小写）
        pattern = str(value).lower() if value is not None else ""
        return lambda x: x is not None and pattern in str(x).lower()

    if operator == "startswith":
        prefix = str(value).lower() if value is not None else ""
        return lambda x: x is not None and str(x).lower().startswith(prefix)

    if operator == "endswith":
        suffix = str(value).lower() if value is not None else ""
        return lambda x: x is not None and str(x).lower().endswith(suffix)

    # 支持正则（可选扩展）
    if operator == "regex":
        try:
            compiled = re.compile(str(value), re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {value}") from e
        return lambda x: x is not None and compiled.search(str(x)) is not None

    raise ValueError(f"不支持的操作符: '{operator}'")
def filter_excel_data_by_column(
    data: Dict[str, Any],
    filter_col: Union[str, int],
    operator: str,
    value: Any = None,
    has_header: bool = False
) -> List[List[Dict[str, Any]]]:
    """
    按操作符和值对指定列进行筛选。
    
    :param data:表格数据，包含 'data'（二维列表，每个元素为 {"value":"xx","abs_pos":[],"style_id":0}）和 'style_map'（样式ID到样式字典的映射）
    :param filter_col: 列（如 "B" 或 1）
    :param operator: 操作符，如 "like", "!=", "is not None" 等
    :param value: 比较值（对 is None 类可省略）
    :param has_header: 是否保留首行为标题
    """    
    if not data or not data.get('data') or not data['data'][0]:
        return data
    # 获取数据和样式映射
    excel_data = data['data']
    n_cols = len(excel_data[0])

    # 转换起始位置为 0-based
    col_index = _col_to_index_0based(filter_col, n_cols)    
    if col_index < 0 or col_index >= len(excel_data[0]):
        raise IndexError(f"列 {filter_col} 超出范围")

    condition = _build_condition(operator, value)

    if has_header:
        header = [excel_data[0]]
        rows_to_filter = excel_data[1:]
    else:
        header = []
        rows_to_filter = excel_data

    filtered_rows = [
        row for row in rows_to_filter
        if condition(row[col_index]['value'])
    ]
    data['data'] = header + filtered_rows
    return data
