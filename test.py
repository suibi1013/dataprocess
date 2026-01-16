from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from typing import List, Dict, Any, Union, Callable, Optional
import re
import ast
from pypinyin import lazy_pinyin, Style
import os
def _col_to_index_1based(col: Union[str, int],max_col: int) -> int:
    """将列索引转换为 1-based 的列索引"""    
    if isinstance(col, int):
        if col < 1: raise ValueError("Column index must be >= 1")
        return col
    elif isinstance(col, str):        
        col = col.upper().strip()
        idx = 0
        for ch in col:
            if not ch.isalpha(): raise ValueError(f"Invalid column letter: {col}")
            idx = idx * 26 + (ord(ch) - ord('A') + 1)
        return idx  
def _col_to_index_0based(col: Union[str, int],max_col: int) -> int:
    """将列索引转换为 0-based 的列索引
    :param col: 列索引（1-based 或字母表示）
    :param max_col: 最大列索引（用于验证,1-based）
    :return: 0-based 的列索引
    """
    if isinstance(col, str):
        # 先尝试将字符串转换为整数
        if not col.isalpha(): 
            col = int(col)
    if isinstance(col, int):
        # 验证列索引是否在有效范围内
        if col > max_col: raise ValueError(f"Column index must be <= {max_col}")
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
# 索引颜色列表
COLOR_INDEX = [
    "00000000",  # 0: 黑色
    "00FFFFFF",  # 1: 白色
    "00FF0000",  # 2: 红色
    "0000FF00",  # 3: 绿色
    "000000FF",  # 4: 蓝色
    "00FFFF00",  # 5: 黄色
    "00FF00FF",  # 6: 洋红色
    "0000FFFF",  # 7: 青色
    "00800000",  # 8: 深灰色
    "00FF8080",  # 9: 浅红色
    "0080FF80",  # 10: 浅绿色
    "008080FF",  # 11: 浅蓝色
    "00FFFF80",  # 12: 浅黄色
    "00FF80FF",  # 13: 浅洋红色
    "0080FFFF",  # 14: 浅青色
    "00C0C0C0",  # 15: 浅灰色
    # 更多索引颜色...
]

# 获取主题RGB颜色的函数
def get_theme_rgb(theme, tint,workbook):
    """从主题索引获取RGB颜色"""
    #"""将 Excel 主题色 + 色调转换为 ARGB 字符串（如 'FF00FF00'）"""
    try:
        clr_scheme = workbook.theme.themeElements.clrScheme
        # 映射 theme 索引到 clrScheme 属性
        theme_colors = [
            clr_scheme.lt1.val,   # 0: Light 1 (usually white)
            clr_scheme.dk1.val,   # 1: Dark 1 (usually black)
            clr_scheme.lt2.val,   # 2: Light 2
            clr_scheme.dk2.val,   # 3: Dark 2
            clr_scheme.accent1.val,
            clr_scheme.accent2.val,
            clr_scheme.accent3.val,
            clr_scheme.accent4.val,
            clr_scheme.accent5.val,
            clr_scheme.accent6.val,
        ]
        if theme < len(theme_colors):
            base_rgb = theme_colors[theme]
        else:
            return None

        # 验证 base_rgb 是 6 位十六进制
        if not base_rgb or not re.match(r'^[0-9A-Fa-f]{6}$', base_rgb):
            return None

        # 应用 tint（色调调整）
        def apply_tint(rgb_hex, tint_value):
            r = int(rgb_hex[0:2], 16)
            g = int(rgb_hex[2:4], 16)
            b = int(rgb_hex[4:6], 16)

            if tint_value < 0:
                # Darken
                r = int(r * (1 + tint_value))
                g = int(g * (1 + tint_value))
                b = int(b * (1 + tint_value))
            else:
                # Lighten
                r = int(r * (1 - tint_value) + 255 * tint_value)
                g = int(g * (1 - tint_value) + 255 * tint_value)
                b = int(b * (1 - tint_value) + 255 * tint_value)

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            return f"{r:02X}{g:02X}{b:02X}"

        rgb = apply_tint(base_rgb, tint)
        return f"FF{rgb}".upper()  # Alpha=FF (不透明)
    except Exception:
        return None

def get_color_rgb(cell_color, workbook=None): 
    """ 
    Safely extract RGB hex string (without alpha) from openpyxl color object. 
    Returns None if no color. 
    """ 
    if not cell_color:
        return None 
 
    if cell_color.type == 'rgb' and cell_color.rgb:
        # Remove alpha channel (first 2 chars) 
        return cell_color.rgb[2:] if len(cell_color.rgb) == 8 else cell_color.rgb 
    elif cell_color.type == 'theme' and workbook is not None:
        return get_theme_rgb(workbook, cell_color.theme, getattr(cell_color, 'tint', 0.0)) 
    elif cell_color.type == 'indexed':
        idx = cell_color.indexed 
        if idx < len(COLOR_INDEX):
            indexed_rgb = COLOR_INDEX[idx] 
            if indexed_rgb and len(indexed_rgb) == 8:
                return indexed_rgb[2:] 
    return None

# ==================== 样式转换函数 ====================
def _convert_color_to_dict(color, workbook=None) -> Dict[str, Any]:
    """将Color对象转换为可序列化的字典，只保留关键颜色信息"""
    if not color:
        return None
    
    color_dict = {}
    
    # 使用安全的方式获取RGB值
    rgb_value = get_color_rgb(color,workbook)
    if rgb_value:
        color_dict['rgb'] = rgb_value
    
    # 仍然保留其他颜色属性
    try:
        if hasattr(color, 'theme'):
            # 只在theme是有效整数时添加
            theme_val = color.theme
            if isinstance(theme_val, int):
                color_dict['theme'] = theme_val
    except Exception:
        pass
    
    try:
        if hasattr(color, 'tint'):
            color_dict['tint'] = color.tint
    except Exception:
        pass
    
    try:
        if hasattr(color, 'type'):
            color_dict['type'] = color.type
    except Exception:
        pass
    
    # 如果没有获取到任何有效属性，返回None
    return color_dict if color_dict else None

def _convert_font_to_dict(font, workbook=None) -> Dict[str, Any]:
    """将Font对象转换为可序列化的字典"""
    return {
        'name': font.name,
        'size': font.size,
        'bold': font.bold,
        'italic': font.italic,
        'underline': font.underline,
        'strike': font.strike,
        'color': _convert_color_to_dict(font.color,workbook),
        'vertAlign': font.vertAlign,
        'scheme': font.scheme
    }

def _convert_fill_to_dict(fill,workbook=None) -> Dict[str, Any]:
    """将Fill对象转换为可序列化的字典"""
    if hasattr(fill, 'patternType'):
        return {
            'patternType': fill.patternType,
            'fgColor': _convert_color_to_dict(fill.fgColor,workbook),
            'bgColor': _convert_color_to_dict(fill.bgColor,workbook)
        }
    return {}

def _convert_side_to_dict(side,workbook=None) -> Dict[str, Any]:
    """将Side对象转换为可序列化的字典"""
    if not side:
        return {'style': None, 'color': None}
    return {
        'style': side.style,
        'color': _convert_color_to_dict(side.color,workbook)
    }

def _convert_border_to_dict(border,workbook=None) -> Dict[str, Any]:
    """将Border对象转换为可序列化的字典"""
    return {
        'left': _convert_side_to_dict(border.left,workbook),
        'right': _convert_side_to_dict(border.right,workbook),
        'top': _convert_side_to_dict(border.top,workbook),
        'bottom': _convert_side_to_dict(border.bottom,workbook),
        'diagonal': _convert_side_to_dict(border.diagonal,workbook),
        'diagonal_direction': border.diagonal_direction,
        'outline': border.outline,
        'vertical': border.vertical,
        'horizontal': border.horizontal
    }

def _convert_alignment_to_dict(alignment,workbook=None) -> Dict[str, Any]:
    """将Alignment对象转换为可序列化的字典"""
    return {
        'horizontal': alignment.horizontal,
        'vertical': alignment.vertical,
        'text_rotation': alignment.text_rotation,
        'wrap_text': alignment.wrap_text,
        'shrink_to_fit': alignment.shrink_to_fit,
        'indent': alignment.indent,
        'relativeIndent': alignment.relativeIndent,
        'justifyLastLine': alignment.justifyLastLine,
        'readingOrder': alignment.readingOrder
    }

def _convert_protection_to_dict(protection) -> Dict[str, Any]:
    """将Protection对象转换为可序列化的字典"""
    return {
        'locked': protection.locked,
        'hidden': protection.hidden
    }

# ==================== excel数据提取：读取区域 → 转为 A1 起点的局部矩阵 ====================
def read_excel_range_data(file_path: str,sheet_name: str,start_row: Optional[int] = 1,end_row: Optional[int] = -1,start_col: Optional[Union[str, int]] = 1,end_col: Optional[Union[str, int]] = -1,include_styles: bool = False,) -> List[List[Dict[str, Any]]]:    
    """
    读取 Excel 指定区域的数据（含样式和值）。
    
    如果未指定行列范围，则自动读取整个工作表的有效区域。
    
    :param file_path: Excel 文件路径
    :param sheet_name: 工作表名称
    :param start_row: 起始行（1-based），默认1，第一行
    :param end_row: 结束行（1-based），默认-1，最后一行
    :param start_col: 起始列（如 "A" 或 1），默认1，第一列
    :param end_col: 结束列（如 "Z" 或 26），默认-1，最后一列
    :param include_styles: 是否包含样式信息（如字体、填充、边框等），默认 False
    :return: 二维列表，每个单元格为 {'value', 'style', 'abs_pos'}
    """
    # 先加载 value-only 版本以获取最大行列（更快）
    workbook = load_workbook(file_path, data_only=True)
    ws_value = workbook[sheet_name]
    
    max_row = ws_value.max_row or 1
    max_col = ws_value.max_column or 1

    # 转换列为 1-based 索引
    start_row = _col_to_index_0based(start_row,max_row)+1
    end_row = _col_to_index_0based(end_row,max_row)+1
    start_col_idx = _col_to_index_0based(start_col,max_col)+1
    end_col_idx = _col_to_index_0based(end_col,max_col)+1

    # 校验范围
    if start_row > end_row or start_col_idx > end_col_idx:
        workbook.close()
        raise ValueError(f"Start must be <= End.start_row({start_row}), end_row({end_row}), start_col({start_col}), end_col({end_col})")

    # 获取样式
    wb_style=None
    ws_style=None
    if include_styles:
        # 加载带样式的 workbook
        wb_style = load_workbook(file_path, data_only=False)
        ws_style = wb_style[sheet_name]

    result = []
    for r in range(start_row, end_row + 1):
        row = []
        for c in range(start_col_idx, end_col_idx + 1):
            value_cell: Cell = ws_value.cell(row=r, column=c)
            cell_data = {
                'value': value_cell.value,
                'style': {},
                'abs_pos': [r,c],
            }
            #读取单元格样式
            if include_styles:
                style_cell: Cell = ws_style.cell(row=r, column=c)
                cell_data['style']={
                    'font': _convert_font_to_dict(style_cell.font,workbook),
                    'fill': _convert_fill_to_dict(style_cell.fill,workbook),
                    'border': _convert_border_to_dict(style_cell.border,workbook),
                    'alignment': _convert_alignment_to_dict(style_cell.alignment,workbook),
                    'number_format': style_cell.number_format,
                    'protection': _convert_protection_to_dict(style_cell.protection),
                }
            row.append(cell_data)
        result.append(row)

    if include_styles:
        wb_style.close()
    workbook.close()

    return result

# ==================== 筛选行：按操作符和值对指定列进行筛选 ====================
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
def filter_excel_data_by_column(data: Union[List[List[Dict[str, Any]]], str],filter_col: Union[str, int],operator: str,value: Any = None,has_header: bool = False) -> List[List[Dict[str, Any]]]:
    """
    按操作符和值对指定列进行筛选。
    
    :param data: 数据
    :param filter_col: 列（如 "B" 或 1）
    :param operator: 操作符，如 "like", "!=", "is not None" 等
    :param value: 比较值（对 is None 类可省略）
    :param has_header: 是否保留首行为标题
    """
    if not data:
        return []
    data = ast.literal_eval(str(data))
    max_col = len(data[0])
    col_index = _col_to_index_0based(filter_col,max_col)
    if col_index < 0 or col_index >= len(data[0]):
        raise IndexError(f"列 {filter_col} 超出范围")

    condition = _build_condition(operator, value)

    if has_header:
        header = [data[0]]
        rows_to_filter = data[1:]
    else:
        header = []
        rows_to_filter = data

    filtered_rows = [
        row for row in rows_to_filter
        if condition(row[col_index]['value'])
    ]

    return header + filtered_rows

# ==================== 筛选行：按操作符和值对指定列进行筛选 ====================
def filter_columns_by_header(data: Union[List[List[Dict[str, Any]]], str],include_headers: Optional[Union[List[str], str]] = None,exclude_headers: Optional[Union[List[str], str]] = None,) -> List[List[Dict[str, Any]]]:
    """
    根据首行（标题行）的值筛选列。
    
    - 如果提供 include_headers，则只保留这些标题对应的列；
    - 如果提供 exclude_headers，则排除这些标题对应的列；
    - 两者可同时使用（先 include，再 exclude）；
    - 至少提供其中一个，否则返回原数据。
    
    :param data: 来自 read_excel_range_to_local 的结果
    :param include_headers: 要保留的列标题列表（精确匹配）
    :param exclude_headers: 要排除的列标题列表（精确匹配）
    :return: 筛选后的数据（新列表，不修改原数据）
    """
    if not data:
        return data
    data = ast.literal_eval(str(data))
    include_headers= ast.literal_eval(str(include_headers)) if include_headers and str(include_headers) !='[]' else None
    exclude_headers= ast.literal_eval(str(exclude_headers)) if exclude_headers and str(exclude_headers) !='[]' else None

    # 提取首行所有标题（转为字符串以便比较）
    header_row = data[0]
    all_headers = [str(cell['value']) if cell['value'] is not None else '' for cell in header_row]

    # 初始化列索引集合
    if include_headers is not None:
        include_headers_set = set(include_headers)
        selected_cols = [
            i for i, h in enumerate(all_headers)
            if h in include_headers_set
        ]
    else:
        selected_cols = list(range(len(all_headers)))

    # 排除指定列
    if exclude_headers is not None:
        exclude_headers_set = set(exclude_headers)
        selected_cols = [
            i for i in selected_cols
            if all_headers[i] not in exclude_headers_set
        ]

    # 如果没有列被选中，返回空结构（保留行数，但无列）
    if not selected_cols:
        return [[] for _ in range(len(data))]

    # 构建新数据：只保留 selected_cols 中的列
    filtered_data = []
    for row in data:
        new_row = [row[col_idx] for col_idx in selected_cols]
        filtered_data.append(new_row)

    return filtered_data

# ==================== 筛选列：根据首行（标题行）的值筛选列 ====================
def sort_excel_data_by_column(data: Union[List[List[Dict[str, Any]]], str],sort_col: Union[str, int],reverse: bool = False,has_header: bool = False) -> List[List[Dict[str, Any]]]:
    """
    对数据按指定列排序。
    
    :param data: 二维列表，每个元素是包含 'value', 'style', 'abs_pos' 的字典
    :param start_col: 要排序的列索引（从0开始）
    :param reverse: 是否降序
    :param has_header: 是否包含标题行（若为 True，则第0行不参与排序，保持在最前）
    :return: 排序后的新数据（不修改原数据）
    """    
    if not data:
        return data
    data = ast.literal_eval(str(data))
    max_col = len(data[0])
    # 转换列标识为索引
    sort_col = _col_to_index_0based(sort_col,max_col)
    if sort_col < -1 or sort_col >= len(data[0]):
        raise IndexError(f"sort_col_index:{str(sort_col)}-{str(max_col)} 超出列范围")
    # 分离标题行和数据行
    header = []
    rows_to_sort = data
    if has_header:
        header = [data[0]]          # 保留标题（作为列表的列表，便于后续拼接）
        rows_to_sort = data[1:]
    if not rows_to_sort:
        return data  # 无数据可排序，直接返回
    def get_sort_key(row: List[Dict[str, Any]]) -> List[str]:
        cell_value = row[sort_col]['value']
        
        # 处理 None 或非字符串类型
        if cell_value is None:
            return ['']  # 排在最前或最后取决于排序方向，这里统一转为空字符串
        
        if isinstance(cell_value, str):
            # 中文转拼音（带声调），用于准确排序
            return lazy_pinyin(cell_value, style=Style.TONE3)
        else:
            # 非字符串（如数字、日期）直接排序
            return [cell_value]

    # 使用 sorted 创建新列表，保持原始数据不变
    sorted_rows = sorted(rows_to_sort, key=get_sort_key, reverse=reverse)
    # 合并标题 + 排序后的数据
    return header + sorted_rows

# ==================== 范围数据提取：根据指定范围提取数据 ====================
def slice_data_by_range(data: Union[List[List[Dict[str, Any]]], str],start_row: int = 1,end_row: int = -1,start_col: Union[str, int] = 1,end_col: Union[str, int] = -1) -> List[List[Dict[str, Any]]]:
    """
    对数据按 1 起始的行列索引范围切片。
    
    参数说明（均为 1 起始索引）：
    - start_row: 起始行索引（包含）
    - end_row:   结束行索引（包含），-1 表示最后一行
    - start_col: 起始列索引（包含）
    - end_col:   结束列索引（包含），-1 表示最后一列
    
    :return: 切片后的新数据（深拷贝结构，但 cell 内容为引用，因样式对象不可变）
    """
    if not data:
        return []
    if isinstance(data, str):
        data = ast.literal_eval(data)

    n_rows = len(data)
    n_cols = len(data[0]) if n_rows > 0 else 0

    # 处理索引，改为以0为起始的索引
    start_row=_col_to_index_0based(start_row,n_rows)
    end_row=_col_to_index_0based(end_row,n_rows)
    start_col=_col_to_index_0based(start_col,n_cols)
    end_col=_col_to_index_0based(end_col,n_cols)

    # 边界校验
    if not (0 <= start_row <= end_row < n_rows):
        raise IndexError(f"行范围 [{start_row}, {end_row}] 超出数据行数范围 [0, {n_rows - 1}]")
    if not (0 <= start_col <= end_col < n_cols):
        raise IndexError(f"列范围 [{start_col}, {end_col}] 超出数据列数范围 [0, {n_cols - 1}]")

    # 切片：逐行提取指定列
    sliced = []
    for r in range(start_row, end_row + 1):
        new_row = data[r][start_col:end_col + 1]
        sliced.append(new_row)

    return sliced

# ==================== excel数据提取-整合:excel数据提取、筛选行、筛选列、安列排序、范围数据提取 ====================
def extract_excel_data(file_path: str,sheet_name: str,start_row: int = 1,end_row: int = -1,start_col: Union[str, int] = 1,end_col: Union[str, int] = -1,include_styles: bool = False,has_header: bool = True,filter_col: Union[str, int]='A',filter_operator: str="==",filter_values: Optional[List[Any]] = None,keep_headers: Optional[List[str]] = None,exclude_headers: Optional[List[str]] = None,sort_col: Union[str, int] = 1,reverse: bool = False,slice_start_row: int = 1,slice_end_row: int = -1,slice_start_col: Union[str, int] = 1,slice_end_col: Union[str, int] = -1,) -> List[List[Dict[str, Any]]]:
    """
    从 Excel 文件中提取数据，并返回一个二维列表。

    :param file_path: Excel文件
    :param sheet_name: sheet名称
    :param start_row: 起始行索引（包含）,1-based,-1 表示最后一行
    :param end_row: 结束行索引（包含）,1-based,-1 表示最后一行
    :param start_col: 起始列索引（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :param end_col: 结束列索引（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :param include_styles: 是否返回样式（若为 True,则每个单元格包含样式信息）
    :param has_header: 是否包含标题行（若为 True,则第0行不参与筛选、排序,若为False,则不处理筛选列逻辑）
    :param filter_col: 筛选索引列（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :param filter_operator: 筛选操作符（[{"value":"==","label":"等于"},{"value":"!=","label":"不等于"},{"value":">","label":"大于"},{"value":">=","label":"大于等于"},{"value":"<","label":"小于"},{"value":"<=","label":"小于等于"},{"value":"like","label":"包含（模糊匹配）"},{"value":"startswith","label":"以...开头"},{"value":"endswith","label":"以...结尾"},{"value":"in","label":"在列表中"},{"value":"not in","label":"不在列表中"},{"value":"regex","label":"正则匹配"},{"value":"is none","label":"为空（NULL）"},{"value":"is not none","label":"不为空（非 NULL)"}])
    :param filter_values: 筛选值列表，示例格式：["a","b","c"]
    :param keep_headers: 保留的标题集合,若为空，则保留所有标题列,示例格式：["a","b","c"]
    :param exclude_headers: 排除的标题集合,若为空，则不排除任何标题,示例格式：["a","b","c"]
    :param sort_col: 排序列索引（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :param reverse: 是否按降序排序,False升序,True为降序,默认为 False
    :param slice_start_row: 行提取范围起始行索引（包含）,1-based,-1 表示最后一行
    :param slice_end_row: 行提取范围结束行索引（包含）,1-based,-1 表示最后一行
    :param slice_start_col: 行提取范围起始列索引（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :param slice_end_col: 行提取范围结束列索引（包含）,1-based(-1 表示最后一列) 或字母表示（如 'A' 表示第1列)
    :return: 提取后的二维列表（每个元素为一个单元格信息,包括value、style、abs_pos信息)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    excel_data=read_excel_range_data(file_path,sheet_name,start_row,end_row,start_col,end_col,include_styles)
    excel_data=filter_excel_data_by_column(excel_data,filter_col,filter_operator,filter_values,has_header)    
    if has_header and filter_col:
        # 若包含标题行，则根据第0行标题名称，选择或排除标题列
        excel_data=filter_columns_by_header(excel_data,keep_headers,exclude_headers)  
    if sort_col:
        excel_data=sort_excel_data_by_column(excel_data,sort_col,reverse,has_header)
    excel_data=slice_data_by_range(excel_data,slice_start_row,slice_end_row,slice_start_col,slice_end_col)
    return excel_data