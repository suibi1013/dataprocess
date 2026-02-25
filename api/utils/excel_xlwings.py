import xlwings as xw
from typing import List, Dict, Any, Union, Tuple
import os
import time

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
def _find_contiguous_regions(cells: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """查找单元格列表中的连续矩形区域
    
    优化：支持多行连续区域的合并，减少区域数量
    
    :param cells: 单元格列表，格式为 [(row, col), ...]（0-based）
    :return: 连续区域列表，每个区域为 ((start_row, start_col), (end_row, end_col))
    """
    if not cells:
        return []
    
    # 按行排序，然后按列排序
    sorted_cells = sorted(cells, key=lambda x: (x[0], x[1]))
    
    # 首先按行合并连续列区域
    row_regions = []
    current_row = None
    current_start_col = None
    current_end_col = None
    
    for row, col in sorted_cells:
        if current_row is None:
            # 开始新行
            current_row = row
            current_start_col = col
            current_end_col = col
        elif row == current_row:
            # 同一行
            if col == current_end_col + 1:
                # 连续列
                current_end_col = col
            else:
                # 不连续，结束当前区域并开始新区域
                row_regions.append((current_row, current_start_col, current_end_col))
                current_start_col = col
                current_end_col = col
        else:
            # 新行，结束当前区域
            row_regions.append((current_row, current_start_col, current_end_col))
            current_row = row
            current_start_col = col
            current_end_col = col
    
    # 添加最后一个区域
    if current_row is not None:
        row_regions.append((current_row, current_start_col, current_end_col))
    
    # 现在合并多行连续的相同列范围区域
    if not row_regions:
        return []
    
    merged_regions = []
    # 按行和列范围排序
    sorted_row_regions = sorted(row_regions, key=lambda x: (x[1], x[2], x[0]))
    
    current_start_row = None
    current_end_row = None
    current_start_col = None
    current_end_col = None
    
    for row, start_col, end_col in sorted_row_regions:
        if current_start_row is None:
            # 开始新区域
            current_start_row = row
            current_end_row = row
            current_start_col = start_col
            current_end_col = end_col
        else:
            # 检查是否可以合并到当前区域
            # 条件：相同的列范围，并且行是连续的
            if (start_col == current_start_col and end_col == current_end_col and 
                row == current_end_row + 1):
                # 合并到当前区域
                current_end_row = row
            else:
                # 无法合并，结束当前区域并开始新区域
                merged_regions.append(((current_start_row, current_start_col), (current_end_row, current_end_col)))
                current_start_row = row
                current_end_row = row
                current_start_col = start_col
                current_end_col = end_col
    
    # 添加最后一个区域
    if current_start_row is not None:
        merged_regions.append(((current_start_row, current_start_col), (current_end_row, current_end_col)))
    
    return merged_regions


def _apply_style_to_cells(ws, style: Dict[str, Any], regions: List[Tuple[Tuple[int, int], Tuple[int, int]]]):
    """批量应用样式到一组连续区域（0-based 行列坐标）
    
    :param ws: 工作表对象
    :param style: 样式字典
    :param regions: 连续区域列表，每个区域为 ((start_row, start_col), (end_row, end_col))
    """
    if not regions:
        return
    
    # 对每个连续区域应用样式
    for (start_row, start_col), (end_row, end_col) in regions:
        # 创建连续区域的 Range 对象（1-based）
        rng = ws.range((start_row + 1, start_col + 1), (end_row + 1, end_col + 1))

        # === 字体 ===
        font_style = style.get('font', {})
        if font_style:
            if 'name' in font_style:
                rng.font.name = font_style['name']
            if 'size' in font_style:
                rng.font.size = font_style['size']
            if 'bold' in font_style:
                rng.font.bold = bool(font_style['bold'])
            if 'italic' in font_style:
                rng.font.italic = bool(font_style.get('italic', False))
            if 'underline' in font_style:
                rng.font.underline = font_style.get('underline') is not None
            if 'strike' in font_style:
                rng.font.strikethrough = bool(font_style.get('strike', False))
            color = font_style.get('color')
            if color and color.get('type') == 'rgb':
                rgb_str = color.get('rgb', '000000').lstrip('#').ljust(6, '0')[:6]
                try:
                    r = int(rgb_str[0:2], 16)
                    g = int(rgb_str[2:4], 16)
                    b = int(rgb_str[4:6], 16)
                    rng.font.color = (r, g, b)
                except Exception:
                    pass  # 忽略无效颜色

        # === 背景色 ===
        fill = style.get('fill', {})
        fg_color = fill.get('fgColor')
        if fg_color and fg_color.get('type') == 'rgb':
            rgb_str = fg_color.get('rgb', 'FFFFFF').lstrip('#').ljust(6, '0')[:6]
            try:
                r = int(rgb_str[0:2], 16)
                g = int(rgb_str[2:4], 16)
                b = int(rgb_str[4:6], 16)
                rng.color = (r, g, b)
            except Exception:
                pass

        # === 对齐 ===
        alignment = style.get('alignment', {})
        if alignment:
            vert_map = {'center': -4108, 'top': -4160, 'bottom': -4107}
            horz_map = {'center': -4108, 'left': -4131, 'right': -4152}

            api_rng = ws.api.Range(rng.address)
            if 'vertical' in alignment:
                v_align = alignment['vertical']
                api_rng.VerticalAlignment = vert_map.get(v_align, -4108)
            if 'horizontal' in alignment:
                h_align = alignment['horizontal']
                api_rng.HorizontalAlignment = horz_map.get(h_align, -4131)
            if 'wrap_text' in alignment:
                api_rng.WrapText = bool(alignment['wrap_text'])

        # === 边框（详细处理）===
        border = style.get('border', {})
        if border:
            api_rng = ws.api.Range(rng.address)
            
            # 定义边框边缘对应的常量
            edge_map = {
                'left': 7,      # xlEdgeLeft
                'right': 10,    # xlEdgeRight
                'top': 8,       # xlEdgeTop
                'bottom': 9     # xlEdgeBottom
            }
            
            # 处理每条边框
            for side_name, edge in edge_map.items():
                side_data = border.get(side_name, {})
                border_style = side_data.get('style')
                color = side_data.get('color')
                
                # 只有当样式或颜色存在时才设置边框
                if border_style or color:
                    try:
                        # 获取当前边缘的Border对象，减少重复调用
                        border_edge = api_rng.Borders(edge)
                        # 一次性设置边框属性
                        if border_style:
                            # 映射样式名称到Excel常量
                            line_style_map = {
                                'none':         -4142,   # xlLineStyleNone
                                'continuous':   1,       # 实线（默认）
                                'thin':         1,       # 通常等同于 continuous
                                'medium':       1,
                                'thick':        1,
                                'dashed':       2,       # 虚线
                                'dotted':       3,       # 点线
                                'dash_dot':     4,       # 点划线（短划+点）
                                'dash_dot_dot': 5,       # 双点划线（短划+两点）
                                'slant_dash_dot': 13,    # 斜点划线（Excel 特有）
                                'double':       6,       # 双线
                            }
                            border_edge.LineStyle = line_style_map.get(border_style, 1)
                            
                            if border_style == 'medium':
                                border_edge.Weight = 3  # xlMedium
                            elif border_style == 'thick':
                                border_edge.Weight = 4  # xlThick
                            else:
                                border_edge.Weight = 2  # xlThin
                        else:
                            border_edge.LineStyle = 1  # 默认实线 (xlContinuous)
                            border_edge.Weight = 2  # 默认细线
                        
                        # 设置边框颜色
                        if color and color.get('type') == 'rgb':
                            rgb_str = color.get('rgb', '000000').lstrip('#').ljust(6, '0')[:6]
                            try:
                                # Excel VBA使用BGR格式的长整型颜色值
                                r = int(rgb_str[0:2], 16)
                                g = int(rgb_str[2:4], 16)
                                b = int(rgb_str[4:6], 16)
                                bgr_color = b + (g << 8) + (r << 16)
                                border_edge.Color = bgr_color
                            except Exception as e:
                                print(f"警告: 设置边框颜色时出错: {e}")
                    except Exception as e:
                        print(f"警告: 设置边框时出错: {e}")


def write_data_to_existing_excel(
    data: Dict[str, Any],
    file_path: str,
    sheet_name: str,
    start_row: int = 1,
    start_col: Union[str, int] = 1,
    write_style: bool = True,
    chunk_size: int = 10000
) -> None:
    """
    高效分块写入带样式的结构化数据到现有 Excel 文件（同步分块处理）

    :param data: 字典，包含 'data'（二维列表，每个元素为 {"value":"xx","abs_pos":[],"style_id":0}）和 'style_map'（样式ID到样式字典的映射）
    :param file_path: 目标 Excel 文件路径（必须存在）
    :param sheet_name: 工作表名
    :param start_row: 起始行（1-based，默认第1行）
    :param start_col: 起始列（1-based 整数 或 字母，如 1 或 'A'）
    :param write_style: 是否写入样式
    :param chunk_size: 分块大小，默认10000行
    """
    # 分块处理逻辑
    if not data or not data.get('data') or not data['data'][0]:
        return

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    total_start_time = time.time()
    # 获取数据和样式映射
    excel_data = data['data']
    style_map = data.get('style_map', {})
    total_rows = len(excel_data)
    n_cols = len(excel_data[0])

    # 转换起始位置为 0-based
    start_row_0 = _col_to_index_0based(start_row, total_rows)
    start_col_0 = _col_to_index_0based(start_col, n_cols)

    # 数据分块
    def chunk_data_local(data, chunk_size):
        if not data:
            return []
        chunks = []
        total_rows = len(data)
        for i in range(0, total_rows, chunk_size):
            end = min(i + chunk_size, total_rows)
            chunk = {
                'data': data[i:end],
                'start_row': i,
                'end_row': end - 1
            }
            chunks.append(chunk)
        return chunks
    
    chunks = chunk_data_local(excel_data, chunk_size)
    total_chunks = len(chunks)
    print(f"数据分块完成，共 {total_chunks} 个块，每个块最多 {chunk_size} 行")

    # 分块处理
    app = None
    wb = None
    ws = None
    processed_rows = 0
    style_groups_applied = 0

    try:
        # 初始化 Excel 应用
        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False

        # 打开工作簿
        wb = app.books.open(file_path)

        # 确保工作表存在
        if sheet_name not in wb.sheet_names:
            ws = wb.sheets.add(name=sheet_name)
        else:
            ws = wb.sheets[sheet_name]

        # 处理每个数据块
        for chunk_idx, chunk in enumerate(chunks):
            chunk_data = chunk['data']
            chunk_start = chunk['start_row']
            chunk_end = chunk['end_row']
            chunk_rows = chunk_end - chunk_start + 1
            
            print(f"处理第 {chunk_idx + 1}/{total_chunks} 块，行范围: {chunk_start + 1}-{chunk_end + 1}，共 {chunk_rows} 行")

            # 构建当前块的值矩阵和样式映射
            value_matrix = []
            # 使用样式ID作为键的样式映射
            cell_style_map: Dict[int, List[Tuple[int, int]]] = {}

            for i, row in enumerate(chunk_data):
                value_row = []
                for j, cell in enumerate(row):
                    if cell is None:
                        value_row.append("")
                        continue

                    value = cell.get('value', "")
                    value_row.append(value)

                    # 使用 style_id 从 style_map 获取样式
                    if write_style:
                        style_id = cell.get('style_id')
                        if style_id is not None and style_id in style_map:
                            target_row = start_row_0 + chunk_start + i
                            target_col = start_col_0 + j
                            if style_id not in cell_style_map:
                                cell_style_map[style_id] = []
                            cell_style_map[style_id].append((target_row, target_col))
                value_matrix.append(value_row)

            # 写入当前块的值
            if value_matrix:
                current_block_start_row = start_row_0 + chunk_start + 1  # 转换为 1-based
                current_block_start_col = start_col_0 + 1  # 转换为 1-based
                ws.range((current_block_start_row, current_block_start_col)).value = value_matrix
                print(f"  写入值完成")

            # 应用当前块的样式
            if write_style and cell_style_map:
                # 预处理样式映射，查找连续矩形区域
                style_regions_map: Dict[int, List[Tuple[Tuple[int, int], Tuple[int, int]]]] = {}
                for style_id, cells in cell_style_map.items():
                    regions = _find_contiguous_regions(cells)
                    style_regions_map[style_id] = regions

                # 应用样式
                for style_id, regions in style_regions_map.items():
                    try:
                        style = style_map.get(style_id, {})
                        if style:
                            _apply_style_to_cells(ws, style, regions)
                    except Exception as e:
                        print(f"  应用样式时出错: {e}")
                
                style_groups_applied += len(cell_style_map)
                print(f"  应用样式完成，共 {len(cell_style_map)} 个样式组")

            # 每个块写完后保存
            wb.save()
            print(f"  保存完成")
            processed_rows += chunk_rows

    except Exception as e:
        raise RuntimeError(f"写入 Excel 失败: {e}") from e
    finally:
        try:
            if wb:
                wb.close()
            if app:
                app.quit()
        except Exception:
            pass  # 忽略清理错误

    total_time = time.time() - total_start_time
    print(f"写入完成，共处理 {total_rows} 行数据，耗时 {round(total_time, 2)} 秒")
    return