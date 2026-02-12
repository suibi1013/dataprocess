import hashlib
import os
import traceback
from typing import Dict, Any, List, Optional, Tuple

import xlwings as xw
from dto.common_dto import ApiResponse

class ExcelHelper:
    # Excel文件扩展名
    EXCEL_EXTENSIONS = {'.xlsx', '.xls'}
    
    @staticmethod
    def _number_to_column_letter(col_num):
        """将数字转换为Excel列字母（1 -> A, 2 -> B, 27 -> AA）"""
        result = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            result = chr(65 + remainder) + result
        return result
    
    @staticmethod
    def _parse_border_style(border):
        """解析边框样式信息"""
        border_info = {
            'style': 'none',
            'color': '#000000',
            'width': 0
        }
        
        try:
            # 获取边框样式
            if hasattr(border, 'LineStyle'):
                line_style = border.LineStyle
                # 映射xlwings边框样式到CSS样式
                if line_style == 1:  # xlContinuous
                    border_info['style'] = 'solid'
                elif line_style == -4115:  # xlDash
                    border_info['style'] = 'dashed'
                elif line_style == -4118:  # xlDot
                    border_info['style'] = 'dotted'
                elif line_style == 5:  # xlDashDot
                    border_info['style'] = 'dashdot'
                elif line_style == 6:  # xlDashDotDot
                    border_info['style'] = 'dashdotdot'
            
            # 获取边框颜色
            if hasattr(border, 'Color'):
                color = border.Color
                if color:
                    if isinstance(color, tuple):
                        # RGB元组转换为十六进制
                        border_info['color'] = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                    elif isinstance(color, int):
                        # 整数颜色值转换为十六进制
                        border_info['color'] = f'#{color:06x}'
            
            # 获取边框粗细
            if hasattr(border, 'Weight'):
                weight = border.Weight
                # 映射xlwings边框粗细到宽度值
                if weight == 1:  # xlHairline
                    border_info['width'] = 1
                elif weight == 2:  # xlThin
                    border_info['width'] = 2
                elif weight == -4138:  # xlMedium
                    border_info['width'] = 3
                elif weight == 4:  # xlThick
                    border_info['width'] = 5
        except Exception as e:
            print(f"解析边框样式时出错: {str(e)}")
        
        return border_info
    
    @staticmethod
    def _get_merged_cells_in_range(worksheet, range_obj):
        """获取指定范围内的合并单元格信息"""
        merged_cells = []
        
        try:
            if hasattr(worksheet, 'api'):
                ws_api = worksheet.api
                if hasattr(ws_api, 'UsedRange') and hasattr(ws_api.UsedRange, 'MergedCells'):
                    # 遍历工作表中的所有合并单元格
                    for merged_area in ws_api.UsedRange.MergedCells:
                        if hasattr(merged_area, 'Address'):
                            merged_cells.append({
                                'range': merged_area.Address,
                                'row_start': merged_area.Row,
                                'col_start': merged_area.Column,
                                'row_count': merged_area.Rows.Count,
                                'col_count': merged_area.Columns.Count
                            })
        except Exception as e:
            print(f"获取合并单元格信息时出错: {str(e)}")
        
        return merged_cells
    
    @staticmethod
    def _get_cell_style_info(cell):
        """获取单元格样式信息"""
        style_info = {
            'font_name': 'Arial',
            'font_size': 11,
            'font_color': '#000000',
            'font_bold': False,
            'font_italic': False,
            'font_underline': False,
            'background_color': '#FFFFFF',
            'horizontal_align': 'left',
            'vertical_align': 'top',
            'border_top': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_bottom': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_left': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_right': {'style': 'none', 'color': '#000000', 'width': 0}
        }
        
        try:
            # 获取字体信息
            if hasattr(cell, 'font'):
                font = cell.font
                if hasattr(font, 'name'):
                    style_info['font_name'] = font.name
                if hasattr(font, 'size'):
                    style_info['font_size'] = font.size
                if hasattr(font, 'color'):
                    # 处理ARGB格式的颜色值
                    color = font.color
                    if isinstance(color, int) and color > 0:
                        # 去除Alpha通道，保留RGB值
                        rgb = color & 0xFFFFFF
                        style_info['font_color'] = f'#{rgb:06x}'
                if hasattr(font, 'bold'):
                    style_info['font_bold'] = font.bold
                if hasattr(font, 'italic'):
                    style_info['font_italic'] = font.italic
                if hasattr(font, 'underline'):
                    style_info['font_underline'] = font.underline
            
            # 获取背景色
            if hasattr(cell, 'fill') and hasattr(cell.fill, 'color'):
                fill_color = cell.fill.color
                if fill_color:
                    # 处理ARGB格式的颜色值
                    if isinstance(fill_color, int) and fill_color > 0:
                        # 去除Alpha通道，保留RGB值
                        rgb = fill_color & 0xFFFFFF
                        style_info['background_color'] = f'#{rgb:06x}'
            
            # 获取对齐方式
            if hasattr(cell, 'horizontal_alignment'):
                style_info['horizontal_align'] = cell.horizontal_alignment
            if hasattr(cell, 'vertical_alignment'):
                style_info['vertical_align'] = cell.vertical_alignment
            
            # 获取边框信息
            if hasattr(cell, 'top_border'):
                border = cell.top_border
                style_info['border_top'] = {
                    'style': border.style if hasattr(border, 'style') else 'none',
                    'color': border.color if hasattr(border, 'color') else '#000000',
                    'width': border.width if hasattr(border, 'width') else 0
                }
            if hasattr(cell, 'bottom_border'):
                border = cell.bottom_border
                style_info['border_bottom'] = {
                    'style': border.style if hasattr(border, 'style') else 'none',
                    'color': border.color if hasattr(border, 'color') else '#000000',
                    'width': border.width if hasattr(border, 'width') else 0
                }
            if hasattr(cell, 'left_border'):
                border = cell.left_border
                style_info['border_left'] = {
                    'style': border.style if hasattr(border, 'style') else 'none',
                    'color': border.color if hasattr(border, 'color') else '#000000',
                    'width': border.width if hasattr(border, 'width') else 0
                }
            if hasattr(cell, 'right_border'):
                border = cell.right_border
                style_info['border_right'] = {
                    'style': border.style if hasattr(border, 'style') else 'none',
                    'color': border.color if hasattr(border, 'color') else '#000000',
                    'width': border.width if hasattr(border, 'width') else 0
                }
        except Exception as e:
            print(f"获取单元格样式信息时出错: {str(e)}")
        
        return style_info
    
    @staticmethod
    def _get_cell_style_info_xlwings(cell):
        """获取xlwings单元格样式信息，包括字体、对齐、边框、背景等"""
        style_info = {
            'font_name': 'Arial',
            'font_size': 11,
            'font_color': '#000000',
            'font_bold': False,
            'font_italic': False,
            'font_underline': False,
            'background_color': '#FFFFFF',
            'horizontal_align': 'left',
            'vertical_align': 'top',
            'border_top': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_bottom': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_left': {'style': 'none', 'color': '#000000', 'width': 0},
            'border_right': {'style': 'none', 'color': '#000000', 'width': 0},
            'width': None,
            'height': None,
            'is_merged': False,
            'merge_range': None
        }
        
        try:
            # 获取字体信息
            if hasattr(cell, 'font'):
                font = cell.font
                if hasattr(font, 'name') and font.name:
                    style_info['font_name'] = font.name
                if hasattr(font, 'size') and font.size:
                    style_info['font_size'] = font.size
                if hasattr(font, 'color') and font.color:
                    # xlwings颜色格式处理
                    color = font.color
                    if isinstance(color, tuple):
                        # RGB元组转换为十六进制
                        style_info['font_color'] = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                    elif isinstance(color, int):
                        # 整数颜色值转换为十六进制
                        style_info['font_color'] = f'#{color:06x}'
                if hasattr(font, 'bold'):
                    style_info['font_bold'] = font.bold
                if hasattr(font, 'italic'):
                    style_info['font_italic'] = font.italic
                if hasattr(font, 'underline'):
                    style_info['font_underline'] = font.underline
            
            # 获取背景色
            if hasattr(cell, 'color') and cell.color:
                color = cell.color
                if isinstance(color, tuple):
                    # RGB元组转换为十六进制
                    style_info['background_color'] = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                elif isinstance(color, int):
                    # 整数颜色值转换为十六进制
                    style_info['background_color'] = f'#{color:06x}'
            
            # 获取单元格尺寸
            if hasattr(cell, 'column_width') and cell.column_width:
                style_info['width'] = cell.column_width
            if hasattr(cell, 'row_height') and cell.row_height:
                style_info['height'] = cell.row_height
            
            try:
                api_cell = cell.api
                
                # 获取对齐方式
                if hasattr(api_cell, 'HorizontalAlignment'):
                    h_align = api_cell.HorizontalAlignment
                    if h_align == -4108:  # xlCenter
                        style_info['horizontal_align'] = 'center'
                    elif h_align == -4152:  # xlRight
                        style_info['horizontal_align'] = 'right'
                    elif h_align == -4131:  # xlLeft
                        style_info['horizontal_align'] = 'left'
                    elif h_align == -4130:  # xlJustify
                        style_info['horizontal_align'] = 'justify'
                
                if hasattr(api_cell, 'VerticalAlignment'):
                    v_align = api_cell.VerticalAlignment
                    if v_align == -4108:  # xlCenter
                        style_info['vertical_align'] = 'middle'
                    elif v_align == -4160:  # xlTop
                        style_info['vertical_align'] = 'top'
                    elif v_align == -4107:  # xlBottom
                        style_info['vertical_align'] = 'bottom'
                
                # 获取边框信息
                if hasattr(api_cell, 'Borders'):
                    borders = api_cell.Borders
                    
                    # 上边框
                    if hasattr(borders, 'Item'):
                        try:
                            top_border = borders.Item(8)  # xlEdgeTop
                            style_info['border_top'] = ExcelHelper._parse_border_style(top_border)
                        except:
                            pass
                        
                        try:
                            bottom_border = borders.Item(9)  # xlEdgeBottom
                            style_info['border_bottom'] = ExcelHelper._parse_border_style(bottom_border)
                        except:
                            pass
                        
                        try:
                            left_border = borders.Item(7)  # xlEdgeLeft
                            style_info['border_left'] = ExcelHelper._parse_border_style(left_border)
                        except:
                            pass
                        
                        try:
                            right_border = borders.Item(10)  # xlEdgeRight
                            style_info['border_right'] = ExcelHelper._parse_border_style(right_border)
                        except:
                            pass
                
                # 检查是否为合并单元格
                if hasattr(api_cell, 'MergeArea'):
                    merge_area = api_cell.MergeArea
                    if merge_area.Cells.Count > 1:
                        style_info['is_merged'] = True
                        style_info['merge_range'] = merge_area.Address
            except Exception as e:
                print(f"获取单元格详细信息时出错: {str(e)}")
        except Exception as e:
            print(f"获取单元格样式信息时出错: {str(e)}")
        
        return style_info
    
    @staticmethod
    def _extract_sheet_data_with_styles(worksheet, limit: int = 100):
        """从worksheet中提取数据、样式和公式信息"""
        # 获取工作表的实际数据范围
        used_range = worksheet.used_range
        if used_range is None:
            return {
                'columns': [],
                'rows': [],
                'total_rows': 0
            }
        
        max_row = used_range.last_cell.row
        max_col = used_range.last_cell.column
        
        # 生成Excel列名 (A, B, C, ...)
        excel_columns = []
        for i in range(max_col):
            col_name = ExcelHelper._number_to_column_letter(i + 1)
            excel_columns.append(col_name)
        
        # 提取数据、样式和公式
        rows_data = []
        
        # 限制读取的行数
        actual_limit = min(limit, max_row) if max_row > 0 else 0
        
        for row_idx in range(1, actual_limit + 1):
            row_data = {}
            
            for col_idx in range(1, max_col + 1):
                cell_obj={}
                cell = worksheet.range((row_idx, col_idx))
                col_name = ExcelHelper._number_to_column_letter(col_idx)
                
                # 获取单元格显示值
                cell_value = cell.value if cell.value is not None else ''                
                cell_obj['text']=cell_value
                
                # 获取单元格公式
                cell_formula = ''
                try:
                    formula = cell.formula
                    if formula and formula.startswith('='):
                        cell_formula = formula
                except Exception:
                    # 如果获取公式失败，保持为空字符串
                    cell_formula = ''
                cell_obj['formulas'] = cell_formula
                
                # 获取单元格样式
                cell_style = ExcelHelper._get_cell_style_info_xlwings(cell)
                cell_obj.update(cell_style)            

                row_data[col_name] = cell_obj
            
            rows_data.append(row_data)
        
        return {
            'columns': excel_columns,
            'rows': rows_data,
            'total_rows': max_row
        }
    
    @staticmethod
    def _read_excel_range_with_xlwings(file_path: str, sheet_name: str = None, cell_range: str = None):
        """使用xlwings读取Excel文件的指定范围数据，包含样式信息"""
        app = None
        workbook = None
        try:
            print(f"启动Excel应用程序读取范围数据...")
            app = xw.App(visible=False, add_book=False)
            print(f"打开Excel文件: {file_path}")
            workbook = app.books.open(file_path)
            
            # 获取指定的工作表
            if sheet_name:
                if sheet_name not in [sheet.name for sheet in workbook.sheets]:
                    raise ValueError(f'工作表 {sheet_name} 不存在')
                worksheet = workbook.sheets[sheet_name]
            else:
                # 使用第一个工作表
                worksheet = workbook.sheets[0]
                sheet_name = worksheet.name
            
            print(f"读取工作表: {sheet_name}")
            
            # 如果没有指定范围，读取整个工作表的数据
            if not cell_range:
                used_range = worksheet.used_range
                if used_range is None:
                    return {'data': [], 'styles': [], 'merged_cells': []}
                range_obj = used_range
            else:
                # 解析单元格范围，支持 A1:C3 或 A1 格式
                try:
                    range_obj = worksheet.range(cell_range)
                except Exception as e:
                    raise ValueError(f'无效的单元格范围: {cell_range}, 错误: {str(e)}')
            
            # 获取范围的起始位置
            start_row = range_obj.row
            start_col = range_obj.column
            # 获取数据和样式
            table_data = []            
            table_row_heights = []
            table_col_widths = []
            
            # 遍历范围内的每个单元格
            for row_idx in range(range_obj.shape[0]):
                row_data = []
                row_height=20.4  # 默认行高                
                col_width = 55.08  # 默认列宽
                
                for col_idx in range(range_obj.shape[1]):
                    # 获取单元格对象
                    cell = worksheet.cells(start_row + row_idx, start_col + col_idx)
                    
                    # 获取单元格值
                    cell_value = cell.value
                    if cell_value is None:
                        cell_value = ''
                    else:
                        cell_value = str(cell_value)
                    
                    # 获取单元格样式
                    cell_style = ExcelHelper._get_cell_style_info_xlwings(cell)
                    
                    cell_obj = {
                        'text': cell_value,
                        'style': cell_style
                    }
                    row_data.append(cell_obj)
                
                table_data.append(row_data)
                table_row_heights.append(row_height)
                table_col_widths.append(col_width)
            
            # 获取合并单元格信息
            merged_cells = ExcelHelper._get_merged_cells_in_range(worksheet, range_obj)
            
            result = {
                "data": table_data,
                "merged_cells": merged_cells,
                "table_row_heights": table_row_heights,
                "table_col_widths": table_col_widths
            }
            return result
            
        except Exception as e:
            print(f"读取Excel范围数据失败: {str(e)}")
            raise e
        finally:
            # 确保Excel应用程序正确关闭
            try:
                if workbook is not None:
                    workbook.close()
                if app is not None:
                    app.quit()
            except Exception as cleanup_error:
                print(f"清理Excel应用程序时出错: {str(cleanup_error)}")
    
    @staticmethod
    def get_excel_sheet_names(file_path: str) -> List[str]:
        """
        获取Excel文件中所有工作表的名称
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            List[str]: 工作表名称列表
        """
        app = None
        workbook = None
        
        try:
            # 验证文件存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'文件不存在: {file_path}')
            
            # 验证文件类型
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ExcelHelper.EXCEL_EXTENSIONS:
                raise ValueError(f'不支持的文件类型: {file_ext}')
            
            # 使用xlwings读取Excel文件
            app = xw.App(visible=False, add_book=False)
            workbook = app.books.open(file_path)
            
            # 获取所有工作表的名称
            sheet_names = [sheet.name for sheet in workbook.sheets]
            
            return sheet_names
            
        except Exception as e:
            print(f"获取Excel工作表名称失败: {str(e)}")
            raise
        finally:
            # 确保关闭Excel应用程序
            if workbook:
                try:
                    workbook.close()
                except Exception as close_error:
                    print(f"关闭工作簿时出错: {str(close_error)}")
            
            if app:
                try:
                    app.quit()
                except Exception as quit_error:
                    print(f"退出Excel应用程序时出错: {str(quit_error)}")
    
    @staticmethod
    async def read_excel_file(file_path: str, sheet_name: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        读取Excel文件数据和格式信息
        
        Args:
            file_path: Excel文件路径
            sheet_name: 指定工作表名称，默认为None（读取所有工作表）
            limit: 每个工作表读取的最大行数
            
        Returns:
            Dict: 包含文件信息、工作表信息和数据的字典
        """
        app = None
        workbook = None
        
        try:
            # 验证文件存在
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f'文件不存在: {file_path}',
                    'data': None
                }
            
            # 验证文件类型
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ExcelHelper.EXCEL_EXTENSIONS:
                return {
                    'success': False,
                    'message': f'不支持的文件类型: {file_ext}',
                    'data': None
                }
            
            result_data = {
                'files': [],
                'sheets': [],
                'data': {}
            }
            
            # 使用xlwings读取Excel文件
            app = xw.App(visible=False, add_book=False)
            workbook = app.books.open(file_path)
            sheet_names = [sheet.name for sheet in workbook.sheets]
            
            # 记录文件信息
            file_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'sheets': sheet_names
            }
            result_data['files'].append(file_info)
            
            # 合并所有sheet名称（去重）
            for sheet in sheet_names:
                if sheet not in result_data['sheets']:
                    result_data['sheets'].append(sheet)
            
            # 如果指定了sheet名称，只读取该sheet
            if sheet_name:
                if sheet_name in sheet_names:
                    worksheet = workbook.sheets[sheet_name]
                    sheet_data = ExcelHelper._extract_sheet_data_with_styles(worksheet, limit)
                    
                    # 使用文件名+sheet名作为key，避免重复
                    key = f"{os.path.basename(file_path)}_{sheet_name}"
                    
                    result_data['data'][key] = {
                        'file_name': os.path.basename(file_path),
                        'sheet_name': sheet_name,
                        'columns': sheet_data['columns'],
                        'rows': sheet_data['rows'],
                        'total_rows': sheet_data['total_rows'],
                        'displayed_rows': len(sheet_data['rows'])
                    }
            else:
                # 读取所有sheet的数据（每个sheet限制行数）
                for sheet in sheet_names:
                    worksheet = workbook.sheets[sheet]
                    sheet_data = ExcelHelper._extract_sheet_data_with_styles(worksheet, limit)
                    
                    # 使用文件名+sheet名作为key，避免重复
                    key = f"{os.path.basename(file_path)}_{sheet}"
                    result_data['data'][key] = {
                        'file_name': os.path.basename(file_path),
                        'sheet_name': sheet,
                        'columns': sheet_data['columns'],
                        'rows': sheet_data['rows'],
                        'total_rows': sheet_data['total_rows'],
                        'displayed_rows': len(sheet_data['rows'])
                    }
            
            return {
                'success': True,
                    'message': f'Excel文件读取成功，共处理 {len(result_data["sheets"])} 个工作表',
                    'data': result_data
                }
                
            
        except Exception as e:
            return {
                'success': False,
                'message': f'读取Excel文件时发生异常: {str(e)}',
                'data': None
            }
        finally:
            # 确保关闭Excel应用程序
            if workbook:
                try:
                    workbook.close()
                except Exception as close_error:
                    print(f"关闭工作簿时出错: {str(close_error)}")
            
            if app:
                try:
                    app.quit()
                except Exception as quit_error:
                    print(f"退出Excel应用程序时出错: {str(quit_error)}")
        
        