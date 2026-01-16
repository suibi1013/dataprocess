import xlwings as xw
from typing import List, Dict, Any, Union, Tuple
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
def write_data_to_existing_excel(
    data: List[List[Dict[str, Any]]],
    file_path: str,
    sheet_name: str,
    start_row: int = 1,
    start_col: Union[str, int] = 1,
    write_style: bool = True,
) -> None:
    """
    将带样式数据写入已有的 Excel 文件的指定位置。

    :param data: 二维数据，每个元素为 {'value': ..., 'style': {...}}
    :param file_path: 目标 Excel 文件路径（将被修改！）
    :param sheet_name: 要写入的工作表名称
    :param start_row: 写入起始行（1-based，默认 1）
    :param start_col: 写入起始列（1-based，可为列字母如 'A' 或数字如 1，默认 1）
    :param write_style: 是否写入样式（默认 True）
    """
    if not data or not data[0]:
        return  # 空数据，直接返回
    n_rows = len(data)
    n_cols = len(data[0]) if n_rows > 0 else 1
    # 处理索引，改为以0为起始的索引，处理负数索引（-1 表示末尾）
    
    start_row = _col_to_index_0based(start_row,n_rows)
    start_col = _col_to_index_0based(start_col,n_cols)
    end_row = _col_to_index_0based(-1,n_rows)
    end_col = _col_to_index_0based(-1,n_cols)

    app = xw.App(visible=False)
    try:
        wb = app.books.open(file_path)
        ws = wb.sheets[sheet_name]

        # 遍历 data 并写入
        for i, row in enumerate(data):
            for j, cell_info in enumerate(row):
                target_row = start_row + i
                target_col = start_col + j
                cell = ws[target_row, target_col]

                # 检查是否为合并单元格，且不是左上角单元格，若是则跳过
                if cell.merge_cells:
                    merge_area = cell.merge_area
                    # 使用更安全的方式获取合并区域的左上角单元格
                    # 对于合并区域，左上角单元格是merge_area的第一个单元格
                    top_left_cell = merge_area[0, 0]  # 使用0-based索引更安全
                    if cell.address != top_left_cell.address:
                        continue

                # 写入值
                value = cell_info.get('value', "")
                cell.value = value

                # 不写入样式，直接跳过
                if not write_style:
                    continue
                # 应用样式
                style = cell_info.get('style', {})
                if not style:
                    continue

                # --- 字体 ---
                font = style.get('font', {})
                if font:
                    cell.font.name = font.get('name', 'Calibri')
                    cell.font.size = font.get('size', 11)
                    cell.font.bold = bool(font.get('bold', False))
                    cell.font.italic = bool(font.get('italic', False))
                    underline = font.get('underline')
                    cell.font.underline = underline is not None  # 简化：非 None 即下划线
                    cell.font.strikethrough = bool(font.get('strike', False))

                    # 字体颜色（仅处理 RGB）
                    color = font.get('color')
                    if color and color.get('type') == 'rgb':
                        rgb = color.get('rgb', '000000').lstrip('#').lstrip('0x')
                        if len(rgb) == 6:
                            bgr = int(rgb[4:6] + rgb[2:4] + rgb[0:2], 16)
                            cell.font.color = bgr

                # --- 填充背景色 ---
                fill = style.get('fill', {})
                fg_color = fill.get('fgColor')
                if fg_color and fg_color.get('type') == 'rgb':
                    rgb = fg_color.get('rgb', 'FFFFFF').lstrip('#').lstrip('0x')
                    if len(rgb) == 6:
                        bgr = int(rgb[4:6] + rgb[2:4] + rgb[0:2], 16)
                        cell.color = bgr  # 背景色

                # --- 对齐方式 ---
                alignment = style.get('alignment', {})
                if alignment:
                    vert = alignment.get('vertical')
                    if vert == 'center':
                        cell.api.VerticalAlignment = -4108  # xlCenter
                    elif vert == 'top':
                        cell.api.VerticalAlignment = -4160  # xlTop
                    elif vert == 'bottom':
                        cell.api.VerticalAlignment = -4107  # xlBottom

                    horz = alignment.get('horizontal')
                    if horz == 'center':
                        cell.api.HorizontalAlignment = -4108
                    elif horz == 'left':
                        cell.api.HorizontalAlignment = -4131
                    elif horz == 'right':
                        cell.api.HorizontalAlignment = -4152

                    wrap_text = alignment.get('wrap_text')
                    if wrap_text is not None:
                        cell.api.WrapText = bool(wrap_text)

                # --- 边框（简化：只设外边框为细实线） ---
                border = style.get('border', {})
                outline = border.get('outline', True)
                if outline:
                    # xlEdgeLeft=7, xlEdgeRight=10, xlEdgeTop=8, xlEdgeBottom=9
                    for edge in [7, 8, 9, 10]:
                        cell.api.Borders(edge).LineStyle = 1  # xlContinuous
                        cell.api.Borders(edge).Weight = 2     # xlThin

                # --- 数字格式 ---
                num_fmt = style.get('number_format', 'General')
                # cell.number_format = num_fmt
                if num_fmt is not None and isinstance(num_fmt, str):
                    try:
                        # 避免空字符串或纯空白
                        num_fmt = num_fmt.strip()
                        if num_fmt:
                            cell.number_format = num_fmt
                    except Exception:
                        # 忽略格式设置失败，不影响主流程
                        pass

        # 保存
        wb.save()
        wb.close()

    finally:
        app.quit()
    

params={"data":[[{"value":"基于全国，液奶驱动指标，低温牛奶和低温酸奶拆分到具体品牌（频次/价格/渗透率/单次量），截止至24P9","style":{},"abs_pos":[23,1]},{"value":None,"style":{},"abs_pos":[23,2]},{"value":None,"style":{},"abs_pos":[23,3]},{"value":None,"style":{},"abs_pos":[23,4]},{"value":None,"style":{},"abs_pos":[23,5]},{"value":None,"style":{},"abs_pos":[23,6]},{"value":None,"style":{},"abs_pos":[23,7]}],[{"value":None,"style":{},"abs_pos":[24,1]},{"value":None,"style":{},"abs_pos":[24,2]},{"value":None,"style":{},"abs_pos":[24,3]},{"value":None,"style":{},"abs_pos":[24,4]},{"value":None,"style":{},"abs_pos":[24,5]},{"value":None,"style":{},"abs_pos":[24,6]},{"value":None,"style":{},"abs_pos":[24,7]}],[{"value":"全国-低温酸奶","style":{},"abs_pos":[25,1]},{"value":None,"style":{},"abs_pos":[25,2]},{"value":None,"style":{},"abs_pos":[25,3]},{"value":None,"style":{},"abs_pos":[25,4]},{"value":None,"style":{},"abs_pos":[25,5]},{"value":None,"style":{},"abs_pos":[25,6]},{"value":None,"style":{},"abs_pos":[25,7]}],[{"value":None,"style":{},"abs_pos":[26,1]},{"value":"YTD22P9","style":{},"abs_pos":[26,2]},{"value":"YTD23P9","style":{},"abs_pos":[26,3]},{"value":"YTD24P9","style":{},"abs_pos":[26,4]},{"value":"MAT22P9","style":{},"abs_pos":[26,5]},{"value":"MAT23P9","style":{},"abs_pos":[26,6]},{"value":"MAT24P9","style":{},"abs_pos":[26,7]}],[{"value":"销额（百万元）","style":{},"abs_pos":[27,1]},{"value":14249.03,"style":{},"abs_pos":[27,2]},{"value":12982.1,"style":{},"abs_pos":[27,3]},{"value":12888.84,"style":{},"abs_pos":[27,4]},{"value":20115.48,"style":{},"abs_pos":[27,5]},{"value":18443.94,"style":{},"abs_pos":[27,6]},{"value":18068.27,"style":{},"abs_pos":[27,7]}],[{"value":"购买均价 元/KG","style":{},"abs_pos":[28,1]},{"value":18.8911,"style":{},"abs_pos":[28,2]},{"value":19.3331,"style":{},"abs_pos":[28,3]},{"value":19.5677,"style":{},"abs_pos":[28,4]},{"value":18.797,"style":{},"abs_pos":[28,5]},{"value":19.2503,"style":{},"abs_pos":[28,6]},{"value":19.5859,"style":{},"abs_pos":[28,7]}],[{"value":"渗透率%","style":{},"abs_pos":[29,1]},{"value":71.5278,"style":{},"abs_pos":[29,2]},{"value":68.2067,"style":{},"abs_pos":[29,3]},{"value":68.673,"style":{},"abs_pos":[29,4]},{"value":78.3943,"style":{},"abs_pos":[29,5]},{"value":74.9383,"style":{},"abs_pos":[29,6]},{"value":75.1334,"style":{},"abs_pos":[29,7]}],[{"value":"购买频次","style":{},"abs_pos":[30,1]},{"value":4.5794,"style":{},"abs_pos":[30,2]},{"value":4.2128,"style":{},"abs_pos":[30,3]},{"value":4.2009,"style":{},"abs_pos":[30,4]},{"value":6.0515,"style":{},"abs_pos":[30,5]},{"value":5.5009,"style":{},"abs_pos":[30,6]},{"value":5.4005,"style":{},"abs_pos":[30,7]}],[{"value":"每次购买量 KG","style":{},"abs_pos":[31,1]},{"value":1.1598,"style":{},"abs_pos":[31,2]},{"value":1.1475,"style":{},"abs_pos":[31,3]},{"value":1.1119,"style":{},"abs_pos":[31,4]},{"value":1.1451,"style":{},"abs_pos":[31,5]},{"value":1.1502,"style":{},"abs_pos":[31,6]},{"value":1.1101,"style":{},"abs_pos":[31,7]}]],"file_path":"E:\\projectcode\\dataprocess\\api\\config_infos/data_sources/excel_files/5oql5ZGK57uT5p6c.xlsx","sheet_name":"液奶&鲜奶驱动指标","start_row":"1","start_col":"A","write_style":True}

write_data_to_existing_excel(**params)