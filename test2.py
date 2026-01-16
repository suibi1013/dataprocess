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
    # === 新增：重置 xlwings 引擎 ===
    try:
        # 如果已有活跃引擎，先清理（避免状态污染）
        if hasattr(xw, '_xl_app') and xw._xl_app is not None:
            try:
                xw._xl_app.quit()
            except:
                pass
        # 清除内部缓存
        xw.apps.clear()
    except Exception:
        pass  # 忽略清理失败
    try:
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

            # 清空目标区域        
            clear_range_str = f"{xw.utils.col_name(start_col+1)}{start_row+1}:{xw.utils.col_name(end_col+1)}{end_row+1}"
            ws.range(clear_range_str).clear()

            # 遍历 data 并写入
            for i, row in enumerate(data):
                for j, cell_info in enumerate(row):
                    target_row = start_row + i
                    target_col = start_col + j
                    cell = ws[target_row, target_col]

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

                    # --- 边框（简化：只设外边框为细实线）---
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
    except Exception as e:
        import threading
        # print("当前线程:", threading.current_thread().name)
        # 获取完整错误信息（含文件、行号、函数、堆栈）
        import traceback
        error_msg = traceback.format_exc()
        raise Exception(f"写入 Excel 时出错: {e}\n{error_msg},当前线程: {threading.current_thread().name}")

params={"data":[[{"value":"n182r3 - table - 2024/11/21 14:55:26","style":{},"abs_pos":[3,1]},{"value":"YTD22P9","style":{},"abs_pos":[3,3]},{"value":"YTD23P9","style":{},"abs_pos":[3,4]},{"value":"YTD24P9","style":{},"abs_pos":[3,5]},{"value":"MAT22P9","style":{},"abs_pos":[3,6]},{"value":"MAT23P9","style":{},"abs_pos":[3,7]},{"value":"MAT24P9","style":{},"abs_pos":[3,8]},{"value":"自定义列","style":"","abs_pos":[1,8]}],[{"value":"SHENGCHANSHANG  ","style":{},"abs_pos":[5,1]},{"value":100,"style":{},"abs_pos":[5,3]},{"value":100,"style":{},"abs_pos":[5,4]},{"value":100,"style":{},"abs_pos":[5,5]},{"value":100,"style":{},"abs_pos":[5,6]},{"value":100,"style":{},"abs_pos":[5,7]},{"value":100,"style":{},"abs_pos":[5,8]},{"value":"常温牛奶","style":"","abs_pos":[2,8]}],[{"value":" MEMBER’S MARK  ","style":{},"abs_pos":[91,1]},{"value":0.7003,"style":{},"abs_pos":[91,3]},{"value":0.6586,"style":{},"abs_pos":[91,4]},{"value":0.7322,"style":{},"abs_pos":[91,5]},{"value":0.6966,"style":{},"abs_pos":[91,6]},{"value":0.6124,"style":{},"abs_pos":[91,7]},{"value":0.7061,"style":{},"abs_pos":[91,8]},{"value":"常温牛奶","style":"","abs_pos":[3,8]}],[{"value":" 长富  ","style":{},"abs_pos":[28,1]},{"value":0.3288,"style":{},"abs_pos":[28,3]},{"value":0.3246,"style":{},"abs_pos":[28,4]},{"value":0.3426,"style":{},"abs_pos":[28,5]},{"value":0.3323,"style":{},"abs_pos":[28,6]},{"value":0.3365,"style":{},"abs_pos":[28,7]},{"value":0.3478,"style":{},"abs_pos":[28,8]},{"value":"常温牛奶","style":"","abs_pos":[4,8]}],[{"value":" 友芝友  ","style":{},"abs_pos":[45,1]},{"value":0.0038,"style":{},"abs_pos":[45,3]},{"value":0.0002,"style":{},"abs_pos":[45,4]},{"value":0.0019,"style":{},"abs_pos":[45,5]},{"value":0.0029,"style":{},"abs_pos":[45,6]},{"value":0.0001,"style":{},"abs_pos":[45,7]},{"value":0.0015,"style":{},"abs_pos":[45,8]},{"value":"常温牛奶","style":"","abs_pos":[5,8]}],[{"value":" 优诺  ","style":{},"abs_pos":[53,1]},{"value":0,"style":{},"abs_pos":[53,3]},{"value":0,"style":{},"abs_pos":[53,4]},{"value":0,"style":{},"abs_pos":[53,5]},{"value":0,"style":{},"abs_pos":[53,6]},{"value":0,"style":{},"abs_pos":[53,7]},{"value":0,"style":{},"abs_pos":[53,8]},{"value":"常温牛奶","style":"","abs_pos":[6,8]}],[{"value":" 涌优  ","style":{},"abs_pos":[86,1]},{"value":0.0011,"style":{},"abs_pos":[86,3]},{"value":0.0001,"style":{},"abs_pos":[86,4]},{"value":0.0023,"style":{},"abs_pos":[86,5]},{"value":0.0013,"style":{},"abs_pos":[86,6]},{"value":0.0028,"style":{},"abs_pos":[86,7]},{"value":0.002,"style":{},"abs_pos":[86,8]},{"value":"常温牛奶","style":"","abs_pos":[7,8]}],[{"value":" 迎春乐  ","style":{},"abs_pos":[63,1]},{"value":0.0361,"style":{},"abs_pos":[63,3]},{"value":0.043,"style":{},"abs_pos":[63,4]},{"value":0.0252,"style":{},"abs_pos":[63,5]},{"value":0.0394,"style":{},"abs_pos":[63,6]},{"value":0.0386,"style":{},"abs_pos":[63,7]},{"value":0.0275,"style":{},"abs_pos":[63,8]},{"value":"常温牛奶","style":"","abs_pos":[8,8]}],[{"value":" 银桥  ","style":{},"abs_pos":[35,1]},{"value":0.2522,"style":{},"abs_pos":[35,3]},{"value":0.2301,"style":{},"abs_pos":[35,4]},{"value":0.1964,"style":{},"abs_pos":[35,5]},{"value":0.2746,"style":{},"abs_pos":[35,6]},{"value":0.2322,"style":{},"abs_pos":[35,7]},{"value":0.1988,"style":{},"abs_pos":[35,8]},{"value":"常温牛奶","style":"","abs_pos":[9,8]}],[{"value":" 银鹭  ","style":{},"abs_pos":[23,1]},{"value":0.123,"style":{},"abs_pos":[23,3]},{"value":0.1598,"style":{},"abs_pos":[23,4]},{"value":0.1925,"style":{},"abs_pos":[23,5]},{"value":0.1262,"style":{},"abs_pos":[23,6]},{"value":0.1519,"style":{},"abs_pos":[23,7]},{"value":0.1821,"style":{},"abs_pos":[23,8]},{"value":"常温牛奶","style":"","abs_pos":[10,8]}],[{"value":" 一鸣  ","style":{},"abs_pos":[87,1]},{"value":0.0547,"style":{},"abs_pos":[87,3]},{"value":0.0633,"style":{},"abs_pos":[87,4]},{"value":0.0907,"style":{},"abs_pos":[87,5]},{"value":0.0452,"style":{},"abs_pos":[87,6]},{"value":0.0603,"style":{},"abs_pos":[87,7]},{"value":0.0893,"style":{},"abs_pos":[87,8]},{"value":"常温牛奶","style":"","abs_pos":[11,8]}],[{"value":" 伊利  ","style":{},"abs_pos":[7,1]},{"value":31.5295,"style":{},"abs_pos":[7,3]},{"value":31.9782,"style":{},"abs_pos":[7,4]},{"value":32.5379,"style":{},"abs_pos":[7,5]},{"value":31.5635,"style":{},"abs_pos":[7,6]},{"value":31.5791,"style":{},"abs_pos":[7,7]},{"value":32.3974,"style":{},"abs_pos":[7,8]},{"value":"常温牛奶","style":"","abs_pos":[12,8]}]],"file_path":"E:\\projectcode\\dataprocess\\api\\config_infos/data_sources/excel_files/6K6h566X5YWs5byP5ray5aW2.xlsx","sheet_name":"四品类品牌份额%","start_row":"4","start_col":"A","write_style":True}

print(write_data_to_existing_excel(**params))