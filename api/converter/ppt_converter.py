#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT转HTML转换器 - 集成配置编辑功能
在生成的HTML页面中嵌入配置项显示和编辑功能
"""

import json
import os
import sys
from datetime import datetime
import time
from typing import List, Dict, Any, Optional, Union
import win32com.client

# 导入数据传输对象
from dto.ppt_dto import (
    ElementPosition, ElementStyle, ElementData, 
    PPTElement, SlideConfig, PPTConfig
)
from converter.base_converter import BaseConverter
from enum import IntEnum

class MsoShapeType(IntEnum):
    """
    MsoShapeType 枚举 (Office)
    指定形状的类型。
    """
    msoPlaceholder        = 14   # 占位符
    msoTextBox            = 17   # 文本框
    msoPicture            = 13   # 图片
    msoTable              = 19   # 表格
    msoEmbeddedOLEObject  = 7    # 嵌入式 OLE 对象
    msoChart              = 3    # 图表
    msoLine               = 9    # 折线图
    mso3DModel            = 30   # 3D 模型
    msoAutoShape          = 1    # 自选图形
    msoCallout            = 2    # 标注
    msoCanvas             = 20   # 画布
    msoComment            = 4    # 评论
    msoContentApp         = 27   # 内容 Office 加载项
    msoDiagram            = 21   # 图
    msoFormControl        = 8    # 网单控件
    msoFreeform           = 5    # 任意多边形
    msoGraphic            = 28   # 图形
    msoGroup              = 6    # 组
    msoIgxGraphic         = 24   # SmartArt 图形
    msoInk                = 22   # 墨迹
    msoInkComment         = 23   # 墨迹批注
    msoLinked3DModel      = 31   # 链接的 3D 模型
    msoLinkedGraphic      = 29   # 链接的图形
    msoLinkedOLEObject    = 10   # 链接 OLE 对象
    msoLinkedPicture      = 11   # 链接图片
    msoMedia              = 16   # 媒体
    msoOLEControlObject   = 12   # OLE 控件对象
    msoScriptAnchor       = 18   # 脚本定位标记
    msoShapeTypeMixed     = -2   # 混合形状类型
    msoSlicer             = 25   # 切片器
    msoTextEffect         = 15   # 文本效果
    msoWebVideo           = 26   # Web 视频
    msoUnknown            = 0    # 未知类型

class PPTConverterWithEditor(BaseConverter):
    """集成配置编辑功能的PPT转换器"""
    
    def __init__(self):
        self.ppt_app = None
        self.presentation = None
        self.config = None
    
    def convert_ppt_to_html_with_editor(self, ppt_path: str, output_html: str = None, config_file: str = None):
        """
        转换PPT为HTML并集成配置编辑功能
        
        Args:
            ppt_path: PPT文件路径
            output_html: 输出HTML文件路径
            config_file: 配置文件路径
        """
        try:
            print("🎯 开始PPT转换流程（集成配置编辑功能）...")
            
            # 阶段1: 解析PPT配置
            print("\n📋 阶段1: 解析PPT配置...")
            self.config = self._parse_ppt_config(ppt_path)            
            
            # 保存配置文件
            if config_file:
                self._save_config(config_file)
            
            # 阶段2: 关闭PPT文件
            print("\n🔒 阶段2: 关闭PPT文件...")
            self._close_ppt()
            
            # 阶段3: 生成带编辑器的HTML
            print("\n🎨 阶段3: 生成带配置编辑器的HTML...")
            if not output_html:
                output_html = ppt_path.replace('.pptx', '_with_editor.html').replace('.ppt', '_with_editor.html')
            
            self._generate_html_with_editor(output_html)
            
            print(f"\n✅ 转换完成!")
            print(f"📄 HTML文件: {output_html}")
            if config_file:
                print(f"⚙️ 配置文件: {config_file}")
            
            return output_html
            
        except Exception as e:
            print(f"❌ 转换失败: {str(e)}")
            self._close_ppt()
            raise
    
    def _parse_ppt_config(self, ppt_path: str) -> PPTConfig:
        """解析PPT配置"""
        try:
            # 检查文件是否存在
            if not os.path.exists(ppt_path):
                raise FileNotFoundError(f"PPT文件不存在: {ppt_path}")
            
            print(f"📂 正在打开PPT文件: {ppt_path}")
            
            # 打开PPT应用
            self.ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            # 不设置Visible属性，让PowerPoint保持默认状态
            self.ppt_app.Visible = True 
            self.ppt_app.DisplayAlerts = False  # 禁用警告对话框
            
            # 打开演示文稿
            abs_path = os.path.abspath(ppt_path)
            print(f"📖 正在读取演示文稿...")
            # self.presentation = self.ppt_app.Presentations.Open(abs_path, ReadOnly=True, Untitled=True, WithWindow=False)
            self.presentation = self.ppt_app.Presentations.Open(abs_path)
            
            # 获取基本信息
            print(f"📏 正在获取基本信息...")
            slide_width = float(self.presentation.PageSetup.SlideWidth)
            slide_height = float(self.presentation.PageSetup.SlideHeight)
            total_slides = int(self.presentation.Slides.Count)
            
            print(f"📊 PPT信息: {total_slides}张幻灯片, 尺寸: {slide_width:.1f}x{slide_height:.1f}")
            
            # 解析所有幻灯片
            slides = []
            for i in range(1, total_slides + 1):
                try:
                    print(f"🔍 正在解析第 {i}/{total_slides} 张幻灯片...")
                    slide = self.presentation.Slides(i)                    
                    self.ppt_app.ActiveWindow.View.GotoSlide(i)
                    slide_config = self._parse_slide_config(slide, i-1, slide_width, slide_height)
                    slides.append(slide_config)
                except Exception as e:
                    print(f"⚠️ 解析第 {i} 张幻灯片失败: {str(e)}")
                    # 创建一个空的幻灯片配置
                    slides.append(SlideConfig(
                        slide_index=i-1,
                        width=slide_width,
                        height=slide_height,
                        background="#ffffff",
                        elements=[]
                    ))
            
            return PPTConfig(
                file_path=ppt_path,
                total_slides=total_slides,
                slide_width=slide_width,
                slide_height=slide_height,
                created_time=datetime.now().isoformat(),
                slides=slides
            )
            
        except Exception as e:
            print(f"❌ 解析PPT配置失败: {str(e)}")
            # 确保清理资源
            self._close_ppt()
            raise
    
    def _parse_slide_config(self, slide, slide_index: int, width: float, height: float) -> SlideConfig:
        """解析单个幻灯片配置"""
        try:
            # 提取背景
            background_info = self._extract_slide_background(slide)
            
            # 处理背景信息，确保向后兼容
            if isinstance(background_info, dict):
                # 新格式：{"type": "color/image", "value": "..."}
                background = background_info
            else:
                # 旧格式：直接是颜色字符串，转换为新格式
                background = {"type": "color", "value": background_info}
            
            # 提取所有元素
            elements = []
            background_image_element = None
            
            try:
                shapes_count = slide.Shapes.Count
                print(f"  📦 发现 {shapes_count} 个元素")
                
                for j in range(1, shapes_count + 1):
                    try:
                        shape = slide.Shapes(j)
                        element = self._parse_element(shape, slide_index, j-1)
                        if element:
                            elements.append(element)
                    except Exception as e:
                        print(f"    ⚠️ 解析第 {j} 个元素失败: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"  ⚠️ 获取幻灯片元素失败: {str(e)}")
            
            # 如果检测到背景图片元素，更新背景信息
            if background_image_element and background_image_element.data.image_data:
                print(f"    ✅ 将图片元素设置为背景: {background_image_element.element_id}")
                background = {"type": "image", "value": background_image_element.data.image_data}
            
            # 确保background是字符串格式，符合SlideConfig的要求
            background_str = "#ffffff"  # 默认白色背景
            if isinstance(background, dict):
                if background.get("type") == "color":
                    background_str = background.get("value", "#ffffff")
                elif background.get("type") == "image":
                    # 对于图片背景，可以使用特殊格式或者默认颜色
                    background_str = f"url({background.get('value', '')})"
            elif isinstance(background, str):
                background_str = background
            
            return SlideConfig(
                slide_index=slide_index,
                width=width,
                height=height,
                background=background_str,
                elements=elements
            )
            
        except Exception as e:
            print(f"⚠️ 解析幻灯片配置失败: {str(e)}")
            return SlideConfig(
                slide_index=slide_index,
                width=width,
                height=height,
                background="#ffffff",
                elements=[]
            )
    
    def _parse_element(self, shape, slide_index: int, element_index: int) -> Optional[PPTElement]:
        """解析单个元素"""
        try:
            # 基本信息
            element_id = f"slide_{slide_index}_element_{element_index}_{shape.Type}"
            
            # 更准确的元素类型判断
            element_type:MsoShapeType = self._parse_element_type(shape)
            if element_type == MsoShapeType.msoUnknown:
                print(f"    ⚠️ 未识别的元素类型，请检查代码")
                return None

            # 位置信息 - 添加调试输出
            try:
                left = float(shape.Left)
                top = float(shape.Top)
                width = float(shape.Width)
                height = float(shape.Height)
                
                print(f"    📏 位置信息 - Left: {left}, Top: {top}, Width: {width}, Height: {height}")
                
                # 检查异常值
                if height == 0.0:
                    print(f"    ⚠️ 发现高度为0的元素!")
                    print(f"    元素名称: {shape.Name}")
                    print(f"    元素类型: {shape.Type}")
                    print(f"    是否有文本: {hasattr(shape, 'TextFrame') and shape.TextFrame.HasText}")
                    if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText:
                        print(f"    文本内容: {shape.TextFrame.TextRange.Text[:50]}...")
                
                if width == 0.0:
                    print(f"    ⚠️ 发现宽度为0的元素!")
                
                position = ElementPosition(
                    left=left,
                    top=top,
                    width=width,
                    height=height
                )
            except Exception as e:
                print(f"    ❌ 获取位置信息失败: {str(e)}")
                # 使用默认值
                position = ElementPosition(
                    left=0.0,
                    top=0.0,
                    width=100.0,
                    height=20.0
                )
            # 样式信息
            style = self._extract_element_style(shape,element_type)
            # 数据内容
            data = self._extract_element_data(shape,element_type)
            return PPTElement(
                element_id=element_id,
                element_name=shape.Name,
                element_type=element_type,
                element_type_name=element_type.name,
                position=position,
                style=style,
                data=data
            )
            
        except Exception as e:
            print(f"⚠️ 解析元素失败: {str(e)}")
            return None
    def _parse_element_type(self, shape) -> MsoShapeType:
        """更准确地确定元素类型，基于MsoShapeType枚举"""
        try:
            shape_type = getattr(shape, 'Type', 0)
            shape_name = getattr(shape, 'Name', '').lower()
            print(f"    🔍 判断元素类型 - 形状类型: {shape_type}, 名称: {shape_name}")
            
            element_type:MsoShapeType = MsoShapeType(shape_type) if shape_type in MsoShapeType._value2member_map_ else MsoShapeType.msoUnknown
            
            # 检查是否是OLE嵌入对象
            if element_type == MsoShapeType.msoEmbeddedOLEObject:  # 7 - msoEmbeddedOLEObject
                if self._safe_hasattr(shape, 'OLEFormat'):
                    ole_format = shape.OLEFormat
                    if hasattr(ole_format, 'ProgID'):
                        prog_id = str(ole_format.ProgID).lower()
                        print(f"    🔍 发现OLE对象: {prog_id}")
                        if 'excel' in prog_id and ('worksheet' in prog_id or 'sheet' in prog_id):
                            print(f"    ✅ 识别为Excel嵌入表格")                            
                else:
                    element_type= MsoShapeType.msoUnknown         
            
            # 检查是否是自由形状
            if element_type == MsoShapeType.msoFreeform:  # 5 - msoFreeform
                print(f"    🔍 Freeform形状，进行特殊检查...")                
                # # 检查是否包含表格相关属性
                # for attr_name in ['Table', 'table', 'TABLE']:
                #     if hasattr(shape, attr_name):
                #         try:
                #             table_obj = getattr(shape, attr_name)
                #             if table_obj is not None:
                #                 print(f"    ✅ Freeform中发现{attr_name}属性，识别为隐藏表格")
                #                 return "hidden_table"
                #         except Exception as e:
                #             print(f"    ⚠️ Freeform {attr_name}属性检查失败: {str(e)}")
                
                # # 根据名称判断是否为表格
                # table_keywords = ['table', 'excel', 'worksheet', '表格', '工作表', 'grid', 'data']
                # if any(keyword in shape_name for keyword in table_keywords):
                #     print(f"    ✅ Freeform根据名称识别为表格: {shape_name}")
                #     return "name_inferred_table"
                
                # print(f"    ✅ 识别为自由形状")
                # return "freeform"
                        
            return element_type
        except Exception as e:
            print(f"    ⚠️ 元素类型判断失败: {str(e)}")
            return MsoShapeType.msoUnknown
    
    def _safe_hasattr(self, obj, attr_name: str) -> bool:
        """安全地检查COM对象是否有指定属性，避免COM异常"""
        try:
            return hasattr(obj, attr_name)
        except Exception as e:
            print(f"    ⚠️ 检查属性 '{attr_name}' 时发生COM异常: {str(e)}")
            return False

    def _extract_element_style(self, shape,element_type) -> ElementStyle:
        """提取元素样式"""
        style = ElementStyle()
        
        try:
            # 字体样式
            if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText:
                text_range = shape.TextFrame.TextRange
                if hasattr(text_range, 'Font'):
                    font = text_range.Font
                    style.font_family = getattr(font, 'Name', 'Arial')
                    # 修复：使用px单位
                    if hasattr(font, 'Size'):
                        style.font_size = f"{float(font.Size)}px"
                    style.color = self._get_color_rgb(getattr(font, 'Color', None))
                    # 提取字体样式属性
                    style.font_style = 'italic' if hasattr(font, 'Italic') and font.Italic else 'normal'
                    style.font_weight = 'bold' if hasattr(font, 'Bold') and font.Bold else 'normal'
                    style.text_decoration = 'underline' if hasattr(font, 'Underline') and font.Underline else 'none'
                    # 提取文本对齐方式
                    if hasattr(text_range, 'ParagraphFormat'):
                        paragraph_format = text_range.ParagraphFormat
                        if hasattr(paragraph_format, 'Alignment'):
                            alignment = paragraph_format.Alignment
                            # PowerPoint中的对齐方式: 1=左对齐, 2=居中, 3=右对齐, 4=两端对齐
                            if alignment == 1:
                                style.text_align = 'left'
                            elif alignment == 2:
                                style.text_align = 'center'
                            elif alignment == 3:
                                style.text_align = 'right'
                            elif alignment == 4:
                                style.text_align = 'justify'
                            else:
                                style.text_align = 'left'
            
            # 背景色 - 修复透明背景处理
            if hasattr(shape, 'Fill'):
                fill = shape.Fill
                if hasattr(fill, 'Type'):
                    fill_type = fill.Type
                    if fill_type == 1:  # msoFillSolid - 纯色填充
                        if hasattr(fill, 'ForeColor'):
                            style.background_color = self._get_color_rgb(fill.ForeColor)
                        else:
                            style.background_color = "#ffffff"
                    elif fill_type == 0:  # msoFillMixed 或无填充 - 透明
                        style.background_color = "transparent"
                    elif fill_type == -2:  # msoFillBackground 或透明填充
                        style.background_color = "transparent"
                    else:
                        # 其他填充类型（渐变、图案等）暂时使用白色
                        style.background_color = "#ffffff"
                else:
                    # 如果无法获取填充类型，检查是否有可见性
                    if hasattr(fill, 'Visible') and not fill.Visible:
                        style.background_color = "transparent"
                    else:
                        style.background_color = "#ffffff"
            else:
                # 没有Fill属性，默认透明
                style.background_color = "transparent"
            
            # 边框
            if hasattr(shape, 'Line'):
                style.border = self._extract_border_style(shape.Line)
                
        except Exception as e:
            print(f"⚠️ 提取样式失败: {str(e)}")
        
        return style
    
    def _extract_element_data(self, shape,element_type) -> ElementData:
        """提取元素数据"""
        data = ElementData()
        
        try:
            # 文本框（msoTextBox=17）或  自动形状（msoAutoShape=1）
            if element_type == MsoShapeType.msoTextBox or element_type ==MsoShapeType.msoAutoShape:
                print(f"    📊 处理文本框...")                
                text_content = self._extract_text_content(shape)
                if text_content:
                    data.text_content = text_content
                    print(f"    📝 提取文本内容: {text_content[:50]}...")
                else:
                    print(f"    ⚠️ 提取文本内容失败")
                    data.text_content = ""
            # 图片（msoPicture=13）
            elif element_type == MsoShapeType.msoPicture:            
                print(f"    🖼️ 确认为图片元素，正在提取图片数据...")
                image_data = self._extract_image_data(shape)
                if image_data:
                    data.image_data = image_data
                    data.original_image_data = image_data
                    print(f"    ✅ 图片数据提取成功")
                else:
                    print(f"    ⚠️ 图片数据提取失败")  
            # 标准表格（msoTable=19）
            elif element_type == MsoShapeType.msoTable:
                print(f"    📊 处理标准表格...")
                if hasattr(shape, 'Table') and shape.Table is not None:
                    table_result = self._extract_table_data(shape.Table)
                    # 检查返回值是否为新的数据结构
                    if isinstance(table_result, dict) and 'data' in table_result:
                        table_data = table_result['data']
                        if table_data and len(table_data) > 0:
                            data.table_data = table_data
                            # 保存行高和列宽信息
                            data.table_row_heights = table_result.get('row_heights', [])
                            data.table_col_widths = table_result.get('col_widths', [])
                            print(f"    ✅ 标准表格数据提取完成，行数: {len(table_data)}")
                            print(f"    📋 表格数据预览: {table_data[:2] if len(table_data) > 0 else 'Empty'}")
                            print(f"    📏 提取到行高信息: {len(data.table_row_heights)}行")
                            print(f"    📏 提取到列宽信息: {len(data.table_col_widths)}列")
                        else:
                            print(f"    ⚠️ 标准表格数据为空")
                    # 兼容旧的数据结构
                    elif table_result and len(table_result) > 0:
                        data.table_data = table_result
                        print(f"    ✅ 标准表格数据提取完成，行数: {len(table_result)}")
                    # 静默处理表格数据
                # OLE嵌入表格（msoEmbeddedOLEObject=7）
            elif element_type == MsoShapeType.msoEmbeddedOLEObject:
                # 处理OLE嵌入表格...
                if hasattr(shape, 'OLEFormat'):
                    try:
                        ole_format = shape.OLEFormat
                        if hasattr(ole_format, 'Object'):                             
                            ole_object = ole_format.Object
                            # 获取当前活动单元格信息
                            # shape.Select() 
                            ole_format.Activate()  
                            time.sleep(1)
                            active_cell =ole_object.Application.ActiveCell
                            cell_address = active_cell.Address
                            cell_row = active_cell.Row
                            cell_column = active_cell.Column
                            
                            # 存储活动单元格信息
                            data.active_cell = {
                                'address': cell_address,
                                'row': cell_row,
                                'column': cell_column
                            }                            
                            # 提取OLE对象中的多工作表数据                            
                            ole_data = self._extract_ole_table_data(ole_object)
                            if ole_data:
                                # 检查是否有多个工作表
                                if isinstance(ole_data, dict) and 'sheets' in ole_data:
                                    data.ole_datas = ole_data
                                    # 对于单工作表情况，也保持向后兼容填充table_data
                                    if len(ole_data['sheets']) == 1:
                                        data.table_data = ole_data['sheets'][0]['data']
                                    print(f"    ✅ OLE嵌入表格多工作表数据提取成功，工作表数量: {len(ole_data['sheets'])}")
                                else:
                                    # 兼容旧格式，单工作表直接赋值给table_data
                                    data.table_data = ole_data
                                    print(f"    ✅ OLE嵌入表格数据提取成功，行数: {len(ole_data)}")
                            else:
                                print(f"    ⚠️ OLE嵌入表格数据为空")
                            
                    except Exception as ole_e:
                        print(f"    ⚠️ OLE嵌入表格数据提取失败: {str(ole_e)}")
                        import traceback
                        print(f"    📋 详细错误: {traceback.format_exc()}")           
            # 图表 (msoChart = 3)
            elif element_type == MsoShapeType.msoChart:
                print(f"    📊 发现图表类型，正在提取数据...")
                if hasattr(shape, 'Chart'):
                    data.chart_data = self._extract_chart_data_with_style(shape.Chart)
                    print(f"    ✅ 图表数据提取成功")
                else:
                    print(f"    ⚠️ 图表对象无Chart属性")
            else:
                print(f"    ℹ️ 不支持的元素类型，跳过数据提取")

                
        except Exception as e:
            print(f"⚠️ 提取元素数据失败: {str(e)}")
        
        return data

    def _extract_chart_data_with_style(self, chart):
        """提取图表数据和样式"""
        try:
            # 首先检查chart对象是否有效
            if not chart:
                print("    ⚠️ 图表对象为空，使用默认数据")
                return self._create_default_chart_data()
            
            # 创建基础图表数据结构
            chart_data = {
                "type": "bar",  # 默认类型，后续会根据实际图表类型更新
                "data": {
                    "labels": [],
                    "datasets": []
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "title": {
                            "display": False,
                            "text": ""
                        },
                        "legend": {
                            "display": True
                        }
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True
                        }
                    }
                }
            }
            
            # 尝试获取图表标题
            try:
                if hasattr(chart, 'HasTitle') and chart.HasTitle:
                    if hasattr(chart, 'ChartTitle'):
                        chart_title = chart.ChartTitle
                        if hasattr(chart_title, 'Text') and chart_title.Text:
                            title_text = str(chart_title.Text).strip()
                            if title_text:
                                chart_data["options"]["plugins"]["title"]["display"] = True
                                chart_data["options"]["plugins"]["title"]["text"] = title_text
                                print(f"    📊 图表标题: {title_text}")
                        else:
                            print("    📊 图表无标题文本")
                else:
                    print("    📊 图表无标题")
            except Exception as e:
                print(f"    ⚠️ 获取图表标题失败: {str(e)}")
            
            # 尝试获取图例设置
            try:
                if hasattr(chart, 'HasLegend') and chart.HasLegend:
                    if hasattr(chart, 'Legend'):
                        legend = chart.Legend
                        chart_data["options"]["plugins"]["legend"]["display"] = True
                        # 获取图例的位置和大小信息
                        if hasattr(legend, 'Left') and hasattr(legend, 'Top') and hasattr(legend, 'Width') and hasattr(legend, 'Height'):
                            try:
                                legend_left = float(legend.Left)
                                legend_top = float(legend.Top)
                                legend_width = float(legend.Width)
                                legend_height = float(legend.Height)
                                
                                # 将图例的位置和大小信息添加到chart_data中
                                if "legend" not in chart_data["options"]["plugins"]:
                                    chart_data["options"]["plugins"]["legend"] = {}
                                chart_data["options"]["plugins"]["legend"]["position_data"] = {
                                    "left": legend_left,
                                    "top": legend_top,
                                    "width": legend_width,
                                    "height": legend_height
                                }
                                print(f"    📊 图例位置和大小: left={legend_left}, top={legend_top}, width={legend_width}, height={legend_height}")
                            except Exception as size_e:
                                print(f"    ⚠️ 获取图例位置和大小失败: {str(size_e)}")
                else:
                    chart_data["options"]["plugins"]["legend"]["display"] = False
                    print("    📊 图表无图例")
            except Exception as e:
                print(f"    ⚠️ 获取图例设置失败: {str(e)}")
            
            # 尝试获取绘图区信息
            try:
                if hasattr(chart, 'PlotArea'):
                    plot_area = chart.PlotArea
                    if hasattr(plot_area, 'Left') and hasattr(plot_area, 'Top') and hasattr(plot_area, 'Width') and hasattr(plot_area, 'Height'):
                        try:
                            plot_left = float(plot_area.Left)
                            plot_top = float(plot_area.Top)
                            plot_width = float(plot_area.Width)
                            plot_height = float(plot_area.Height)
                            
                            # 将绘图区的位置和大小信息添加到chart_data中
                            if "legend" not in chart_data["options"]["plugins"]:
                                chart_data["options"]["plugins"]["legend"] = {}
                            chart_data["options"]["plugins"]["legend"]["plot_area_data"] = {
                                "left": plot_left,
                                "top": plot_top,
                                "width": plot_width,
                                "height": plot_height
                            }
                            print(f"    📊 绘图区位置和大小: left={plot_left}, top={plot_top}, width={plot_width}, height={plot_height}")
                        except Exception as size_e:
                            print(f"    ⚠️ 获取绘图区位置和大小失败: {str(size_e)}")
                else:
                    print("    📊 图表无绘图区信息")
            except Exception as e:
                print(f"    ⚠️ 获取绘图区信息失败: {str(e)}")
            
            # 尝试获取图表类型
            try:
                if hasattr(chart, 'ChartType'):
                    chart_type = chart.ChartType
                    print(f"    📊 图表类型代码: {chart_type}")
                    
                    # 根据PowerPoint图表类型映射到Chart.js类型
                    type_mapping = {
                        # 柱状图类型
                        51: "bar",      # xlColumnClustered - 簇状柱形图
                        52: "bar",      # xlColumnStacked - 堆积柱形图 (保持为bar，但需要特殊配置)
                        53: "bar",      # xlColumnStacked100 - 100%堆积柱形图
                        54: "bar",      # xl3DColumnClustered - 3D簇状柱形图
                        55: "bar",      # xl3DColumnStacked - 3D堆积柱形图
                        56: "bar",      # xl3DColumnStacked100 - 3D 100%堆积柱形图
                        -4100: "bar",   # xl3DColumn - 3D柱形图
                        
                        # 条形图类型
                        57: "bar",      # xlBarClustered - 簇状条形图
                        58: "bar",      # xlBarStacked - 堆积条形图
                        59: "bar",      # xlBarStacked100 - 100%堆积条形图
                        60: "bar",      # xl3DBarClustered - 3D簇状条形图
                        61: "bar",      # xl3DBarStacked - 3D堆积条形图
                        62: "bar",      # xl3DBarStacked100 - 3D 100%堆积条形图
                        
                        # 折线图类型
                        4: "line",      # xlLine - 折线图
                        63: "line",     # xlLineStacked - 堆积折线图
                        64: "line",     # xlLineStacked100 - 100%堆积折线图
                        65: "line",     # xlLineMarkers - 带数据标记的折线图
                        66: "line",     # xlLineMarkersStacked - 带数据标记的堆积折线图
                        67: "line",     # xlLineMarkersStacked100 - 带数据标记的100%堆积折线图
                        -4101: "line",  # xl3DLine - 3D折线图
                        
                        # 饼图类型
                        5: "pie",       # xlPie - 饼图
                        69: "pie",      # xlPieExploded - 分离型饼图
                        68: "pie",      # xlPieOfPie - 复合饼图
                        71: "pie",      # xlBarOfPie - 复合条饼图
                        -4102: "pie",   # xl3DPie - 3D饼图
                        70: "pie",      # xl3DPieExploded - 3D分离型饼图
                        
                        # 环形图类型
                        -4120: "doughnut", # xlDoughnut - 环形图
                        80: "doughnut",    # xlDoughnutExploded - 分离型环形图
                        
                        # 面积图类型
                        1: "line",      # xlArea - 面积图 (Chart.js中用line模拟)
                        76: "line",     # xlAreaStacked - 堆积面积图
                        77: "line",     # xlAreaStacked100 - 100%堆积面积图
                        -4098: "line",  # xl3DArea - 3D面积图
                        78: "line",     # xl3DAreaStacked - 3D堆积面积图
                        79: "line",     # xl3DAreaStacked100 - 3D 100%堆积面积图
                        
                        # 散点图类型
                        -4169: "scatter", # xlXYScatter - 散点图
                        72: "scatter",    # xlXYScatterSmooth - 平滑线散点图
                        73: "scatter",    # xlXYScatterSmoothNoMarkers - 无数据标记的平滑线散点图
                        74: "scatter",    # xlXYScatterLines - 直线散点图
                        75: "scatter",    # xlXYScatterLinesNoMarkers - 无数据标记的直线散点图
                        
                        # 气泡图类型
                        15: "bubble",   # xlBubble - 气泡图
                        87: "bubble",   # xlBubble3DEffect - 三维气泡图
                        
                        # 雷达图类型
                        -4151: "radar", # xlRadar - 雷达图
                        81: "radar",    # xlRadarMarkers - 带数据标记的雷达图
                        82: "radar",    # xlRadarFilled - 填充雷达图
                        
                        # 股价图类型
                        88: "line",     # xlStockHLC - 盘高-盘低-收盘图
                        89: "line",     # xlStockOHLC - 开盘-盘高-盘低-收盘图
                        90: "line",     # xlStockVHLC - 成交量-盘高-盘低-收盘图
                        91: "line",     # xlStockVOHLC - 成交量-开盘-盘高-盘低-收盘图
                        
                        # 曲面图类型
                        83: "line",     # xlSurface - 三维曲面图
                        84: "line",     # xlSurfaceWireframe - 三维曲面图(框架图)
                        85: "line",     # xlSurfaceTopView - 曲面图(俯视图)
                        86: "line",     # xlSurfaceTopViewWireframe - 曲面图(俯视框架图)
                        
                        # 新增图表类型 (Excel 2016+)
                        117: "bar",     # xlTreemap - 树状图 (用bar模拟)
                        118: "bar",     # xlHistogram - 直方图
                        119: "bar",     # xlWaterfall - 瀑布图
                        120: "pie",     # xlSunburst - 旭日图 (用pie模拟)
                        121: "bar",     # xlBoxWhisker - 箱形图
                        122: "bar",     # xlPareto - 帕累托图
                        123: "bar",     # xlFunnel - 漏斗图
                        140: "bar",     # xlRegionMap - 地图 (用bar模拟)
                        
                        # 圆锥、圆柱、棱锥图类型
                        99: "bar",      # xlConeColClustered - 簇状圆锥柱形图
                        100: "bar",     # xlConeColStacked - 堆积圆锥柱形图
                        101: "bar",     # xlConeColStacked100 - 100%堆积圆锥柱形图
                        102: "bar",     # xlConeBarClustered - 簇状圆锥条形图
                        103: "bar",     # xlConeBarStacked - 堆积圆锥条形图
                        104: "bar",     # xlConeBarStacked100 - 100%堆积圆锥条形图
                        105: "bar",     # xlConeCol - 三维圆锥柱形图
                        
                        92: "bar",      # xlCylinderColClustered - 簇状圆柱柱形图
                        93: "bar",      # xlCylinderColStacked - 堆积圆柱柱形图
                        94: "bar",      # xlCylinderColStacked100 - 100%堆积圆柱柱形图
                        95: "bar",      # xlCylinderBarClustered - 簇状圆柱条形图
                        96: "bar",      # xlCylinderBarStacked - 堆积圆柱条形图
                        97: "bar",      # xlCylinderBarStacked100 - 100%堆积圆柱条形图
                        98: "bar",      # xlCylinderCol - 三维圆柱柱形图
                        
                        106: "bar",     # xlPyramidColClustered - 簇状棱锥柱形图
                        107: "bar",     # xlPyramidColStacked - 堆积棱锥柱形图
                        108: "bar",     # xlPyramidColStacked100 - 100%堆积棱锥柱形图
                        109: "bar",     # xlPyramidBarClustered - 簇状棱锥条形图
                        110: "bar",     # xlPyramidBarStacked - 堆积棱锥条形图
                        111: "bar",     # xlPyramidBarStacked100 - 100%堆积棱锥条形图
                        112: "bar",     # xlPyramidCol - 三维棱锥柱形图
                    }
                    
                    if chart_type in type_mapping:
                        chart_data["type"] = type_mapping[chart_type]
                        
                        # 特殊处理堆叠图表
                        stacked_types = [52, 53, 55, 56, 58, 59, 61, 62, 63, 64, 66, 67, 76, 77, 78, 79, 
                                       93, 94, 96, 97, 100, 101, 103, 104, 107, 108, 110, 111]
                        
                        if chart_type in stacked_types:
                            print(f"    📊 检测到堆叠图表类型: {chart_type}")
                            # 为堆叠图表添加特殊配置
                            if chart_data["type"] == "bar":
                                chart_data["options"]["scales"]["x"] = {"stacked": True}
                                chart_data["options"]["scales"]["y"] = {"stacked": True}
                                chart_data["options"]["plugins"]["title"]["text"] = f"堆叠柱状图 (类型: {chart_type})"
                            elif chart_data["type"] == "line":
                                chart_data["options"]["elements"] = {"line": {"fill": True}}
                                chart_data["options"]["plugins"]["title"]["text"] = f"堆叠折线图 (类型: {chart_type})"
                        
                        # 为100%堆叠图表添加特殊配置
                        percent_stacked_types = [53, 56, 59, 62, 64, 67, 77, 79, 94, 97, 101, 104, 108, 111]
                        if chart_type in percent_stacked_types:
                            print(f"    📊 检测到100%堆叠图表类型: {chart_type}")
                            if chart_data["type"] == "bar":
                                chart_data["options"]["scales"]["y"]["max"] = 100
                                chart_data["options"]["plugins"]["title"]["text"] = f"100%堆叠柱状图 (类型: {chart_type})"
                        
                        print(f"    📊 映射图表类型: {chart_data['type']} (PowerPoint类型: {chart_type})")
                    else:
                        print(f"    ⚠️ 未知图表类型: {chart_type}，使用默认柱状图")
                        chart_data["type"] = "bar"
                        chart_data["options"]["plugins"]["title"]["text"] = f"未知图表类型 (类型: {chart_type})"
            except Exception as e:
                print(f"    ⚠️ 获取图表类型失败: {str(e)}")
            
            # 尝试提取图表数据
            try:
                if hasattr(chart, 'SeriesCollection'):
                    series_collection = chart.SeriesCollection()
                    series_count = series_collection.Count
                    print(f"    📊 发现 {series_count} 个数据系列")
                    
                    # 提取标签（类别）
                    if series_count > 0:
                        first_series = series_collection.Item(1)
                        if hasattr(first_series, 'XValues'):
                            try:
                                x_values = first_series.XValues
                                if x_values:
                                    chart_data["data"]["labels"] = [str(val) for val in x_values]
                                    print(f"    📊 提取到 {len(chart_data['data']['labels'])} 个标签")
                            except:
                                pass
                    
                    # 如果没有标签，尝试从图表的CategoryNames获取
                    if not chart_data["data"]["labels"]:
                        try:
                            if hasattr(chart, 'Axes'):
                                axes = chart.Axes()
                                if axes.Count > 0:
                                    x_axis = axes.Item(1)  # X轴
                                    if hasattr(x_axis, 'CategoryNames'):
                                        category_names = x_axis.CategoryNames
                                        if category_names:
                                            chart_data["data"]["labels"] = [str(name) for name in category_names]
                                            print(f"    📊 从轴标签提取到 {len(chart_data['data']['labels'])} 个标签")
                        except:
                            pass
                    
                    # 提取坐标轴刻度线和网格线显示状态
                    try:
                        if hasattr(chart, 'Axes'):
                            axes = chart.Axes()
                            # 初始化scales配置
                            if "scales" not in chart_data["options"]:
                                chart_data["options"]["scales"] = {}
                            
                            # 处理X轴
                            if axes.Count > 0:
                                x_axis = axes.Item(1)  # X轴
                                if "x" not in chart_data["options"]["scales"]:
                                    chart_data["options"]["scales"]["x"] = {}
                                
                                # 提取X轴网格线显示状态
                                if hasattr(x_axis, 'HasMajorGridlines'):
                                    try:
                                        chart_data["options"]["scales"]["x"]["grid"] = {
                                            "display": bool(x_axis.HasMajorGridlines)
                                        }
                                        print(f"    📊 X轴主要网格线显示状态: {x_axis.HasMajorGridlines}")
                                    except Exception as e:
                                        print(f"    ⚠️ 获取X轴网格线状态失败: {str(e)}")
                                
                                # 提取X轴刻度线显示状态
                                if hasattr(x_axis, 'TickLabelPosition'):
                                    try:
                                        # 如果刻度标签位置为0，表示不显示
                                        chart_data["options"]["scales"]["x"]["ticks"] = {
                                            "display": x_axis.TickLabelPosition != 0
                                        }
                                        print(f"    📊 X轴刻度线显示状态: {x_axis.TickLabelPosition != 0}")
                                    except Exception as e:
                                        pass
                            
                            # 处理Y轴（通常是第二个轴）
                            if axes.Count > 1:
                                y_axis = axes.Item(2)  # Y轴
                                if "y" not in chart_data["options"]["scales"]:
                                    chart_data["options"]["scales"]["y"] = {}
                                
                                # 提取Y轴网格线显示状态
                                if hasattr(y_axis, 'HasMajorGridlines'):
                                    try:
                                        chart_data["options"]["scales"]["y"]["grid"] = {
                                            "display": bool(y_axis.HasMajorGridlines)
                                        }
                                        # Y轴主要网格线显示状态已设置
                                    except Exception as e:
                                        pass
                                
                                # 提取Y轴刻度线显示状态
                                if hasattr(y_axis, 'TickLabelPosition'):
                                    try:
                                        # 如果刻度标签位置为0，表示不显示
                                        chart_data["options"]["scales"]["y"]["ticks"] = {
                                            "display": y_axis.TickLabelPosition != 0
                                        }
                                        print(f"    📊 Y轴刻度线显示状态: {y_axis.TickLabelPosition != 0}")
                                    except Exception as e:
                                        print(f"    ⚠️ 获取Y轴刻度线状态失败: {str(e)}")
                    except Exception as e:
                        print(f"    ⚠️ 提取坐标轴刻度线信息失败: {str(e)}")
                    
                    # 如果仍然没有标签，创建默认标签
                    if not chart_data["data"]["labels"]:
                        chart_data["data"]["labels"] = [f"类别 {i+1}" for i in range(4)]
                    
                    # 提取数据系列和颜色
                    for i in range(min(series_count, 6)):  # 最多处理6个系列
                        try:
                            series = series_collection.Item(i + 1)
                            series_name = getattr(series, 'Name', f'系列 {i+1}')
                            
                            # 提取数据值
                            values = []
                            if hasattr(series, 'Values'):
                                try:
                                    series_values = series.Values
                                    if series_values:
                                        values = [float(val) if val is not None else 0 for val in series_values]
                                except:
                                    pass
                            
                            # 如果没有数据，创建默认数据
                            if not values:
                                values = [12, 19, 3, 5][:len(chart_data["data"]["labels"])]
                            
                            # 尝试提取系列颜色
                            series_color = self._extract_series_color(series, i,chart_data["type"])
                            
                            dataset = {
                                "label": str(series_name),
                                "data": values,
                                "backgroundColor": series_color,
                                "borderColor": series_color,
                                "borderWidth": 1
                            }
                            
                            chart_data["data"]["datasets"].append(dataset)
                            print(f"    📊 添加数据系列: {series_name}, 数据点: {len(values)}, 颜色: {series_color}")
                            
                        except Exception as e:
                            print(f"    ⚠️ 处理第 {i+1} 个系列失败: {str(e)}")
                            continue
            except Exception as e:
                print(f"    ⚠️ 提取图表数据失败: {str(e)}")
            
            # 如果没有提取到任何数据系列，使用默认数据
            if not chart_data["data"]["datasets"]:
                print("    📊 未提取到数据系列，使用默认数据")
                return self._create_default_chart_data()
            
            print(f"    ✅ 图表数据提取完成: {len(chart_data['data']['datasets'])} 个系列")
            return chart_data
            
        except Exception as e:
            print(f"    ❌ 图表数据提取失败: {str(e)}")
            return self._create_default_chart_data()
    
    def _create_default_chart_data(self):
        """创建默认图表数据"""
        return {
            "type": "bar",
            "data": {
                "labels": ["类别 1", "类别 2", "类别 3", "类别 4"],
                "datasets": [{
                    "label": "数据系列",
                    "data": [12, 19, 3, 5],
                    "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"],
                    "borderColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "图表标题"
                    },
                    "legend": {
                        "display": True
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }

    def _extract_series_color(self, series, index,chart_data_type):
        """提取数据系列的颜色"""
        try:
            # 尝试从系列的Format.Fill获取颜色
            if hasattr(series, 'Format'):
                try:
                    color=''
                    if chart_data_type=='line':                        
                        color = self._get_color_rgb(series.Format.Line.ForeColor)
                    else:                        
                        color = self._get_color_rgb(series.Format.Fill.ForeColor)
                    if color and color != "#ffffff":  # 避免默认白色
                        return color                
                except:     
                    pass
            
            # 尝试从Points获取颜色（对于柱状图等）
            if hasattr(series, 'Points'):
                try:
                    points = series.Points()
                    if points.Count > 0:
                        first_point = points.Item(1)
                        if hasattr(first_point, 'Format'):
                            format_obj = first_point.Format
                            if hasattr(format_obj, 'Fill'):
                                fill = format_obj.Fill
                                if hasattr(fill, 'ForeColor'):
                                    color = self._get_color_rgb(fill.ForeColor)
                                    if color and color != "#ffffff":
                                        return color
                except:
                    pass
            
            # 如果无法提取颜色，使用默认颜色
            default_colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
            return default_colors[index % len(default_colors)]
            
        except Exception as e:
            print(f"    ⚠️ 提取系列颜色失败: {str(e)}")
            # 返回默认颜色
            default_colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
            return default_colors[index % len(default_colors)]
            
    def _extract_text_content(self, shape) -> str:
        """增强的文本内容提取方法"""
        text_content = ""
        
        try:
            # 方法1: 标准TextFrame方式
            if hasattr(shape, 'TextFrame'):
                text_frame = shape.TextFrame
                if hasattr(text_frame, 'HasText') and text_frame.HasText:
                    if hasattr(text_frame, 'TextRange') and hasattr(text_frame.TextRange, 'Text'):
                        text_content = str(text_frame.TextRange.Text).strip()
                        if text_content:
                            return text_content
            
            # 方法2: 直接访问Text属性（某些占位符可能需要）
            if hasattr(shape, 'Text'):
                text = str(shape.Text).strip()
                if text:
                    return text
            
            # 方法3: 通过PlaceholderFormat访问（标题占位符）
            if hasattr(shape, 'PlaceholderFormat'):
                try:
                    placeholder = shape.PlaceholderFormat
                    if hasattr(placeholder, 'ContainedType'):
                        # 如果是标题类型的占位符，尝试获取文本
                        if hasattr(shape, 'TextFrame') and shape.TextFrame:
                            text_frame = shape.TextFrame
                            if hasattr(text_frame, 'TextRange'):
                                text_range = text_frame.TextRange
                                if hasattr(text_range, 'Text'):
                                    text_content = str(text_range.Text).strip()
                                    if text_content:
                                        return text_content
                except Exception as e:
                    print(f"    ⚠️ 占位符文本提取失败: {str(e)}")
            
            # 方法4: 遍历TextFrame中的段落（处理复杂文本）
            if hasattr(shape, 'TextFrame') and shape.TextFrame:
                try:
                    text_frame = shape.TextFrame
                    if hasattr(text_frame, 'TextRange') and hasattr(text_frame.TextRange, 'Paragraphs'):
                        paragraphs = text_frame.TextRange.Paragraphs()
                        all_text = []
                        for i in range(1, paragraphs.Count + 1):
                            paragraph = paragraphs.Item(i)
                            if hasattr(paragraph, 'Text'):
                                para_text = str(paragraph.Text).strip()
                                if para_text:
                                    all_text.append(para_text)
                        if all_text:
                            return '\n'.join(all_text)
                except Exception as e:
                    print(f"    ⚠️ 段落文本提取失败: {str(e)}")
            
        except Exception as e:
            print(f"    ⚠️ 文本提取过程出错: {str(e)}")
        
        return text_content
    
    def _extract_ole_table_data(self, ole_object):
        """提取OLE嵌入的Excel表格数据，支持多个工作表"""
        try:
            print(f"    🔍 开始提取OLE Excel表格数据...")
            print(f"    📋 OLE对象类型: {type(ole_object)}")
            print(f"    📋 OLE对象属性: {[attr for attr in dir(ole_object) if not attr.startswith('_')][:10]}")
            
            result = {'sheets': []}
            
            # 尝试获取所有工作表
            worksheets = None
            if hasattr(ole_object, 'Worksheets'):
                worksheets = ole_object.Worksheets
                worksheets_count = worksheets.Count
                print(f"    📊 发现 {worksheets_count} 个工作表")
            else:
                print(f"    ⚠️ 无法访问工作表集合，尝试单个工作表")
                # 回退到原有逻辑
                if hasattr(ole_object, 'ActiveSheet'):
                    worksheet = ole_object.ActiveSheet
                    sheet_name = getattr(worksheet, 'Name', 'ActiveSheet')
                    print(f"    🔍 使用ActiveSheet: {sheet_name}")
                    sheet_data = self._extract_single_worksheet_data(worksheet, sheet_name)
                    if sheet_data and len(sheet_data['data']) > 0:
                        result['sheets'].append({
                            'name': sheet_name,
                            'data': sheet_data['data'],
                            'row_heights': sheet_data['row_heights'],
                            'col_widths': sheet_data['col_widths'],
                            'merged_cells': sheet_data['merged_cells']
                        })
                        print(f"    ✅ 成功提取单个工作表数据: {sheet_name}")
                        # 对于单个工作表，保持向后兼容，直接返回数据而不是对象
                        if worksheets_count is None or worksheets_count == 1:
                            return sheet_data
                        return result
                    else:
                        print(f"    ⚠️ 单个工作表无有效数据")
                        return None
                else:
                    print(f"    ❌ 既没有Worksheets也没有ActiveSheet属性")
                    # 尝试其他可能的属性
                    if hasattr(ole_object, 'Workbook'):
                        workbook = ole_object.Workbook
                        print(f"    🔍 尝试通过Workbook访问工作表")
                        if hasattr(workbook, 'Worksheets'):
                            worksheets = workbook.Worksheets
                            worksheets_count = worksheets.Count
                            print(f"    📊 通过Workbook发现 {worksheets_count} 个工作表")
                        else:
                            print(f"    ❌ Workbook也没有Worksheets属性")
                            return None
                    else:
                        print(f"    ❌ 也没有Workbook属性")
                        return None
            
            # 遍历所有工作表，查找包含数据的工作表
            for sheet_index in range(1, worksheets_count + 1):
                try:
                    worksheet = worksheets.Item(sheet_index)
                    sheet_name = getattr(worksheet, 'Name', f'Sheet{sheet_index}')
                    print(f"    🔍 检查工作表 {sheet_index}: {sheet_name}")
                    
                    # 检查工作表是否有数据
                    if hasattr(worksheet, 'UsedRange'):
                        used_range = worksheet.UsedRange
                        if used_range and hasattr(used_range, 'Rows') and hasattr(used_range, 'Columns'):
                            rows_count = used_range.Rows.Count
                            cols_count = used_range.Columns.Count
                            
                            # 只处理有实际数据的工作表（至少1行1列）
                            if rows_count > 0 and cols_count > 0:
                                print(f"    ✅ 工作表 '{sheet_name}' 包含数据: {rows_count}x{cols_count}")
                                
                                # 提取该工作表的数据
                                sheet_data = self._extract_single_worksheet_data(worksheet, sheet_name)
                                if sheet_data and len(sheet_data['data']) > 0:
                                    result['sheets'].append({
                                        'name': sheet_name,
                                        'data': sheet_data['data'],
                                        'row_heights': sheet_data['row_heights'],
                                        'col_widths': sheet_data['col_widths'],
                                        'merged_cells': sheet_data['merged_cells']
                                    })
                            else:
                                print(f"    ⚠️ 工作表 '{sheet_name}' 无有效数据: {rows_count}x{cols_count}")
                        else:
                            print(f"    ⚠️ 工作表 '{sheet_name}' 无UsedRange")
                    else:
                        print(f"    ⚠️ 工作表 '{sheet_name}' 无UsedRange属性")
                        
                except Exception as sheet_e:
                    print(f"    ⚠️ 处理工作表 {sheet_index} 失败: {str(sheet_e)}")
                    continue
            
            # 汇总结果
            if result['sheets']:
                print(f"    ✅ 成功提取多工作表数据，工作表数量: {len(result['sheets'])}")
                for sheet in result['sheets']:
                    print(f"      - {sheet['name']}: {len(sheet['data'])} 行数据")
                # 对于单个工作表，保持向后兼容，直接返回数据而不是对象
                if len(result['sheets']) == 1:
                    return result['sheets'][0]['data']
                return result
            else:
                return None
                
        except Exception as e:
            return None
    
    def _extract_single_worksheet_data(self, worksheet, sheet_name):
        """提取单个工作表的数据，包括行列宽高和合并单元格信息"""
        try: 
            # 获取UsedRange
            used_range = worksheet.UsedRange
            
            # 确保从A1开始读取
            start_row = 1
            start_col = 1
            end_row = used_range.Row + used_range.Rows.Count - 1
            end_col = used_range.Column + used_range.Columns.Count - 1
            
            # 计算实际行数和列数
            rows_count = end_row - start_row + 1
            cols_count = end_col - start_col + 1
            
            print(f"    📊 读取范围: A1:{chr(64+end_col)}{end_row}")
            
            table_data = []
            row_heights = []
            col_widths = []
            merged_cells = []            
            
            # 提取行高 - 从第1行开始
            for row in range(start_row, end_row + 1):
                try:
                    height = worksheet.Rows(row).Height
                    row_heights.append(height)
                except Exception as e:
                    print(f"    ⚠️ 提取行 {row} 高度失败: {str(e)}")
                    row_heights.append(15)  # 默认行高
            
            # 提取列宽 - 从第1列开始
            for col in range(start_col, end_col + 1):
                try:
                    width = worksheet.Columns(col).Width
                    col_widths.append(width)
                except Exception as e:
                    print(f"    ⚠️ 提取列 {col} 宽度失败: {str(e)}")
                    col_widths.append(8.43)  # 默认列宽
            
            # 提取合并单元格信息
            try:
                visited = set()
                for row in range(start_row, end_row + 1):
                    for col in range(start_col, end_col + 1):
                        cell = worksheet.Cells(row, col)
                        if cell.Address in visited:
                            continue

                        # 检查是否是合并区域的一部分
                        if cell.MergeCells:
                            merge_area = cell.MergeArea
                            start_row_merge = merge_area.Row
                            end_row_merge = merge_area.Row + merge_area.Rows.Count - 1
                            start_col_merge = merge_area.Column
                            end_col_merge = merge_area.Column + merge_area.Columns.Count - 1
                            
                            # 只记录合并区域的左上角单元格
                            merged_cells.append({
                                "row": start_row_merge - 1,  # 转换为0索引
                                "col": start_col_merge - 1,  # 转换为0索引
                                "rowspan": end_row_merge - start_row_merge + 1,
                                "colspan": end_col_merge - start_col_merge + 1
                            })
            except Exception as e:
                print(f"    ⚠️ 提取合并单元格信息失败: {str(e)}")
            
            # 提取实际数据 - 从A1开始
            for row in range(start_row, end_row + 1):
                row_data = []
                for col in range(start_col, end_col + 1):
                    try:
                        cell = worksheet.Cells(row, col)
                        cell_value = ""
                        
                        # 尝试获取单元格值
                        if hasattr(cell, 'Value') and cell.Value is not None:
                            cell_value = str(cell.Value).strip()
                        elif hasattr(cell, 'Text'):
                            cell_value = str(cell.Text).strip()
                        
                        # 获取单元格样式
                        background_color = "#ffffff"
                        text_color = "#000000"
                        border = "1px solid #ddd"
                        
                        # 尝试获取背景色
                        try:
                            if hasattr(cell, 'Interior') and hasattr(cell.Interior, 'Color'):
                                color_value = cell.Interior.Color
                                if color_value and color_value != -4142:  # -4142 表示无颜色
                                    # 转换颜色值为十六进制
                                    background_color = self._convert_excel_color_to_hex(color_value)
                        except:
                            pass
                        
                        # 尝试获取字体颜色
                        try:
                            if hasattr(cell, 'Font') and hasattr(cell.Font, 'Color'):
                                font_color = cell.Font.Color
                                if font_color and font_color != -4142:
                                    text_color = self._convert_excel_color_to_hex(font_color)
                        except:
                            pass
                         
                        # 尝试获取字体样式
                        font_name = "Arial"
                        font_size = 10
                        font_bold = False
                        font_italic = False
                         
                        try:
                            if hasattr(cell, 'Font'):
                                if hasattr(cell.Font, 'Name') and cell.Font.Name:
                                    font_name = cell.Font.Name
                                if hasattr(cell.Font, 'Size') and cell.Font.Size:
                                    font_size = cell.Font.Size
                                if hasattr(cell.Font, 'Bold') and cell.Font.Bold:
                                    font_bold = cell.Font.Bold
                                if hasattr(cell.Font, 'Italic') and cell.Font.Italic:
                                    font_italic = cell.Font.Italic
                        except:
                            pass
                        
                        # 尝试获取对齐方式
                        horizontal_align = "general"
                        vertical_align = "bottom"
                        
                        try:
                            if hasattr(cell, 'HorizontalAlignment'):
                                # Excel的水平对齐常量映射到CSS值
                                align_map = {
                                    -4108: "center",  # xlCenter
                                    -4131: "left",    # xlLeft
                                    -4152: "right",   # xlRight
                                    -4160: "justify", # xlJustify
                                    -4130: "fill",    # xlFill
                                    # 默认为general
                                }
                                horizontal_align = align_map.get(cell.HorizontalAlignment, "general")
                            
                            if hasattr(cell, 'VerticalAlignment'):
                                # Excel的垂直对齐常量映射到CSS值
                                valign_map = {
                                    -4108: "middle",  # xlCenter
                                    -4160: "justify", # xlJustify
                                    -4107: "top",     # xlTop
                                    # 默认为bottom
                                }
                                vertical_align = valign_map.get(cell.VerticalAlignment, "bottom")
                        except:
                            pass
                        
                        # 尝试获取数据格式
                        data_format = "general"
                        
                        try:
                            if hasattr(cell, 'NumberFormat') and cell.NumberFormat:
                                data_format = cell.NumberFormat
                        except:
                            pass
                        
                        # 检查是否为合并单元格的左上角单元格
                        is_merged = False
                        rowspan = 1
                        colspan = 1
                        for merged in merged_cells:
                            if merged['row'] == row - 1 and merged['col'] == col - 1:
                                is_merged = True
                                rowspan = merged['rowspan']
                                colspan = merged['colspan']
                                break
                        
                        row_data.append({
                            "text": cell_value,
                            "background_color": background_color,
                            "text_color": text_color,
                            "border": border,
                            "is_merged": is_merged,
                            "rowspan": rowspan,
                            "colspan": colspan,
                            "font_name": font_name,
                            "font_size": font_size,
                            "font_bold": font_bold,
                            "font_italic": font_italic,
                            "horizontal_align": horizontal_align,
                            "vertical_align": vertical_align,
                            "data_format": data_format
                        })
                        
                    except Exception as cell_e:
                        print(f"    ⚠️ 提取单元格 ({row},{col}) 失败: {str(cell_e)}")
                        row_data.append({
                            "text": "",
                            "background_color": "#ffffff",
                            "text_color": "#000000",
                            "border": "1px solid #ddd",
                            "is_merged": False,
                            "rowspan": 1,
                            "colspan": 1
                        })
                
                if row_data:
                    table_data.append(row_data)
            
            result = {
                "data": table_data,
                "row_heights": row_heights,
                "col_widths": col_widths,
                "merged_cells": merged_cells
            }
            
            print(f"    ✅ 工作表 '{sheet_name}' 数据提取完成: {len(table_data)} 行, {len(row_heights)} 行高, {len(col_widths)} 列宽, {len(merged_cells)} 个合并单元格")
            return result
            
        except Exception as e:
            print(f"    ⚠️ 提取工作表 '{sheet_name}' 数据失败: {str(e)}")
            return {
                "data": [],
                "row_heights": [],
                "col_widths": [],
                "merged_cells": []
            }
    def _generate_html_with_editor(self, convert_ppt_to_html: str):
        """生成带配置编辑器的HTML"""
        html_content = self._build_html_with_editor()
        
        with open(convert_ppt_to_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _build_html_with_editor(self) -> str:
        """构建带编辑器的HTML内容 - 使用外部模板"""
        import os
        
        # 获取模板文件路径
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'ppt_editor_template.html')
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            # 如果模板文件不存在，返回简单的错误页面
            return self._build_fallback_html()
        
        try:
            # 读取模板文件
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 准备配置数据
            config_json = json.dumps(self.config.model_dump(), ensure_ascii=False, indent=2)
            
            # 替换模板中的占位符
            html = template_content.replace('{{CONFIG_JSON_PLACEHOLDER}}', config_json)
            
            return html
            
        except Exception as e:
            print(f"⚠️ 读取模板文件失败: {str(e)}")
            return self._build_fallback_html()
    
    def _build_fallback_html(self) -> str:
        """构建备用的简单HTML页面"""
        config_json = json.dumps(self.config.model_dump(), ensure_ascii=False, indent=2)
        
        return f"""<!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>PPT转换结果</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .error {{ color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 4px; }}
                    .config {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; }}
                    pre {{ white-space: pre-wrap; word-wrap: break-word; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>PPT转换结果</h1>
                    <div class="error">
                        <h3>⚠️ 模板加载失败</h3>
                        <p>无法加载编辑器模板文件，显示基本配置信息：</p>
                    </div>
                    <div class="config">
                        <h3>📄 配置数据</h3>
                        <pre>{config_json}</pre>
                    </div>
                </div>
            </body>
            </html>"""
            
    def _extract_slide_background(self, slide):
        """提取幻灯片背景（支持颜色和图片）"""
        bg_info={"type": "color", "value": "#ffffff"}
        try:
            # 尝试多种方式获取背景
            if hasattr(slide, 'Background') and slide.Background:
                background = slide.Background
                
                # 方法1: 尝试获取填充
                if hasattr(background, 'Fill') and background.Fill:
                    fill = background.Fill
                    if hasattr(fill, 'Type'):
                        print(f"    🎨 背景填充类型: {fill.Type}")
                        
                        # 检查填充类型
                        if fill.Type == 1:  # msoFillSolid - 纯色填充
                            if hasattr(fill, 'ForeColor'):
                                color = self._get_color_rgb(fill.ForeColor)
                                if color and color != "#000000":  # 如果不是默认的黑色
                                    print(f"    🎨 提取到纯色背景: {color}")
                                    bg_info= {"type": "color", "value": color}
                        elif fill.Type == 5:  # msoFillPicture - 图片填充
                            print("    🖼️ 检测到背景图片")
                            # 尝试提取背景图片
                            background_image = self._extract_background_image(fill, slide)
                            if background_image:
                                bg_info= {"type": "image", "value": background_image}
                        elif fill.Type == 0:  # msoFillMixed - 混合填充，通常是白色
                            bg_info= {"type": "color", "value": "#ffffff"}
                        
                        # 渐变填充
                        elif fill.Type == 2:  # 渐变填充
                            bg_info= {"type": "gradient", "value": ""}                        
                        # 图片填充
                        elif fill.Type == 3:  # 图片填充
                            bg_info['type'] = 'picture'
                            # 尝试提取图片
                            try:
                                if hasattr(fill, 'UserPicture'):
                                    bg_info['image'] = "background_image"  # 占位符
                            except Exception as e:
                                print(f"    ⚠️ 提取背景图片失败: {str(e)}")
                        
                        # 检查透明度
                        if hasattr(fill, 'Transparency'):
                            bg_info['transparency'] = fill.Transparency
                
                # 方法2: 尝试获取颜色方案
                if hasattr(background, 'ColorScheme'):
                    bg_info= {"type": "color", "value": "#ffffff"}  # 使用默认白色
            
            # 如果都失败了，返回白色作为默认背景
            return bg_info
        except Exception as e:
            print(f"    ⚠️ 提取背景失败: {str(e)}")
            return bg_info
    
    def _extract_background_image(self, fill, slide):
        """提取背景图片"""
        try:
            import tempfile
            import base64
            import os
            
            # 方法1: 尝试通过TextureOffsetX等属性获取图片
            if hasattr(fill, 'TextureName'):
                print(f"    🖼️ 背景图片名称: {fill.TextureName}")
            
            # 方法2: 尝试导出整个幻灯片然后提取背景
            # 这是一个变通方法，因为PowerPoint COM API对背景图片的直接访问有限
            try:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # 导出幻灯片为图片
                slide.Export(temp_path, "PNG")
                
                # 读取并编码为base64
                with open(temp_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # 清理临时文件
                os.unlink(temp_path)
                
                print("    ✅ 成功提取背景图片")
                return f"data:image/png;base64,{image_data}"
                
            except Exception as e:
                print(f"    ⚠️ 导出幻灯片图片失败: {str(e)}")
            
            # 方法3: 尝试通过UserPicture属性
            if hasattr(fill, 'UserPicture'):
                try:
                    user_picture = fill.UserPicture
                    print(f"    🖼️ 找到UserPicture: {user_picture}")
                    # 这里可能需要进一步处理
                except Exception as e:
                    print(f"    ⚠️ 获取UserPicture失败: {str(e)}")
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ 提取背景图片失败: {str(e)}")
            return None

    def _get_color_rgb(self, color_obj):
        """获取颜色RGB值"""
        try:
            if hasattr(color_obj, 'RGB'):
                rgb = color_obj.RGB
                r = rgb & 255
                g = (rgb >> 8) & 255
                b = (rgb >> 16) & 255
                color_hex = f"#{r:02x}{g:02x}{b:02x}"
                print(f"    🎨 提取颜色成功: {color_hex}")
                return color_hex
            elif hasattr(color_obj, 'Value'):
                # 尝试从Value属性获取颜色
                value = color_obj.Value
                # 处理可能的颜色值格式
                if isinstance(value, int):
                    r = value & 255
                    g = (value >> 8) & 255
                    b = (value >> 16) & 255
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    print(f"    🎨 从Value提取颜色: {color_hex}")
                    return color_hex
            print(f"    ⚠️ 颜色对象没有RGB属性: {dir(color_obj)}")
        except Exception as e:
            print(f"    ⚠️ 提取颜色RGB失败: {str(e)}")
        # 默认返回透明色而不是白色，以便区分提取失败和真正的白色
        return "transparent"
    def _convert_excel_color_to_hex(self, color_value):
        """将Excel颜色值转换为十六进制颜色"""
        try:
            if isinstance(color_value, int|float):
                # Excel颜色是BGR格式，需要转换为RGB
                blue = (int(color_value) >> 16) & 0xFF
                green = (int(color_value) >> 8) & 0xFF
                red = int(color_value) & 0xFF
                return f"#{red:02x}{green:02x}{blue:02x}"
            return "#ffffff"
        except:
            return "#ffffff"

    def _extract_border_style(self, line):
        """提取边框样式"""
        try:
            if hasattr(line, 'Visible') and line.Visible:
                weight = getattr(line, 'Weight', 1)
                color = self._get_color_rgb(getattr(line, 'ForeColor', None))
                return f"{weight}px solid {color}"
        except:
            pass
        return ""
    
    def _extract_table_data(self, table):
        """提取表格数据，包含样式信息、合并单元格、行高和列宽处理"""
        try:
            # 首先检查table对象是否有效
            if not table:
                return []
            
            # 安全地获取行数和列数
            try:
                rows_count = int(table.Rows.Count)
                cols_count = int(table.Columns.Count)
                print(f"    🔍 表格尺寸: {rows_count}x{cols_count}")
            except Exception as e:
                print(f"    ⚠️ 无法获取表格尺寸: {str(e)}")
                return []
            
            # 提取行高信息
            row_heights = []
            try:
                for i in range(1, rows_count + 1):
                    try:
                        row = table.Rows(i)
                        # 获取行高（单位：磅）
                        row_height = getattr(row, 'Height', 15)
                        row_heights.append(float(row_height))
                    except Exception as e:
                        print(f"    ⚠️ 获取行高失败 (行 {i}): {str(e)}")
                        row_heights.append(15)  # 默认行高
                print(f"    ✅ 提取行高信息完成: {len(row_heights)}行")
            except Exception as e:
                print(f"    ⚠️ 提取行高信息失败: {str(e)}")
            
            # 提取列宽信息
            col_widths = []
            try:
                for i in range(1, cols_count + 1):
                    try:
                        column = table.Columns(i)
                        # 获取列宽（单位：磅）
                        col_width = getattr(column, 'Width', 72)
                        col_widths.append(float(col_width))
                    except Exception as e:
                        print(f"    ⚠️ 获取列宽失败 (列 {i}): {str(e)}")
                        col_widths.append(72)  # 默认列宽
                print(f"    ✅ 提取列宽信息完成: {len(col_widths)}列")
            except Exception as e:
                print(f"    ⚠️ 提取列宽信息失败: {str(e)}")
            
            # 创建一个矩阵来跟踪合并单元格
            merged_cells = {}  # 存储合并单元格信息 {(row, col): {'colspan': x, 'rowspan': y}}
            processed_cells = set()  # 已处理的单元格位置
            
            # 检测合并单元格的改进方法
            print(f"    🔍 开始检测合并单元格")
            
            for row_idx in range(1, rows_count + 1):
                for col_idx in range(1, cols_count + 1):
                    # 如果已经被处理过，跳过
                    if (row_idx, col_idx) in processed_cells:
                        continue
                    
                    try:
                        cell = table.Cell(row_idx, col_idx)
                        
                        # 检测合并单元格的改进方法
                        colspan = 1
                        rowspan = 1
                        
                        # 获取当前单元格的文本作为参考
                        current_text = ""
                        try:
                            if hasattr(cell, 'Shape') and cell.Shape:
                                shape = cell.Shape
                                if hasattr(shape, 'TextFrame') and shape.TextFrame:
                                    text_frame = shape.TextFrame
                                    if hasattr(text_frame, 'HasText') and text_frame.HasText:
                                        if hasattr(text_frame, 'TextRange') and text_frame.TextRange:
                                            text_range = text_frame.TextRange
                                            if hasattr(text_range, 'Text'):
                                                current_text = str(text_range.Text).strip()
                        except:
                            pass
                        
                        # 检查右侧单元格是否合并（通过比较文本内容）
                        for check_col in range(col_idx + 1, cols_count + 1):
                            try:
                                check_cell = table.Cell(row_idx, check_col)
                                check_text = ""
                                
                                # 获取检查单元格的文本
                                if hasattr(check_cell, 'Shape') and check_cell.Shape:
                                    shape = check_cell.Shape
                                    if hasattr(shape, 'TextFrame') and shape.TextFrame:
                                        text_frame = shape.TextFrame
                                        if hasattr(text_frame, 'HasText') and text_frame.HasText:
                                            if hasattr(text_frame, 'TextRange') and text_frame.TextRange:
                                                text_range = text_frame.TextRange
                                                if hasattr(text_range, 'Text'):
                                                    check_text = str(text_range.Text).strip()
                                
                                # 如果文本相同且不为空，可能是合并的单元格
                                if current_text and check_text == current_text:
                                    colspan += 1
                                    print(f"    🔍 检测到可能的水平合并: ({row_idx},{col_idx}) -> ({row_idx},{check_col})")
                                    processed_cells.add((row_idx, check_col))
                                else:
                                    break
                            except:
                                break
                            
                            # 检查下方单元格是否合并（通过比较文本内容）
                        for check_row in range(row_idx + 1, rows_count + 1):
                            try:
                                check_cell = table.Cell(check_row, col_idx)
                                check_text = ""
                                
                                # 获取检查单元格的文本
                                if hasattr(check_cell, 'Shape') and check_cell.Shape:
                                    shape = check_cell.Shape
                                    if hasattr(shape, 'TextFrame') and shape.TextFrame:
                                        text_frame = shape.TextFrame
                                        if hasattr(text_frame, 'HasText') and text_frame.HasText:
                                            if hasattr(text_frame, 'TextRange') and text_frame.TextRange:
                                                text_range = text_frame.TextRange
                                                if hasattr(text_range, 'Text'):
                                                    check_text = str(text_range.Text).strip()
                                
                                # 如果文本相同且不为空，可能是合并的单元格
                                if current_text and check_text == current_text:
                                    rowspan += 1
                                    print(f"    🔍 检测到可能的垂直合并: ({row_idx},{col_idx}) -> ({check_row},{col_idx})")
                                else:
                                    break
                            except:
                                # 如果访问失败，可能是合并的单元格
                                # 单元格访问失败，可能是合并单元格
                                rowspan += 1
                        
                        # 如果检测到合并单元格，记录信息
                        if colspan > 1 or rowspan > 1:
                            merged_cells[(row_idx, col_idx)] = {
                                'colspan': colspan,
                                'rowspan': rowspan
                            }
                            # 检测到合并单元格
                            
                            # 标记被合并的单元格
                            for r in range(row_idx, min(row_idx + rowspan, rows_count + 1)):
                                for c in range(col_idx, min(col_idx + colspan, cols_count + 1)):
                                    if r != row_idx or c != col_idx:
                                        processed_cells.add((r, c))
                    
                    except Exception as e:
                        pass
                        continue
            
            # 提取数据
            data = []
            for row_idx in range(1, rows_count + 1):
                row_data = []
                for col_idx in range(1, cols_count + 1):
                    # 如果这个单元格已经被合并到其他单元格中，跳过
                    if (row_idx, col_idx) in processed_cells:
                        continue
                        
                    try:
                        cell = table.Cell(row_idx, col_idx)
                        # 提取单元格数据，包含文本和样式
                        cell_data = {
                            "text": "",
                            "background_color": "#ffffff",
                            "text_color": "#000000",
                            "border": "1px solid #ccc"
                        }
                        
                        # 添加合并信息
                        if (row_idx, col_idx) in merged_cells:
                            merge_info = merged_cells[(row_idx, col_idx)]
                            cell_data["colspan"] = merge_info['colspan']
                            cell_data["rowspan"] = merge_info['rowspan']
                            print(f"    📋 添加合并单元格属性: ({row_idx},{col_idx}) colspan={merge_info['colspan']} rowspan={merge_info['rowspan']}")
                        
                        # 安全地提取单元格文本和样式
                        try:
                            if hasattr(cell, 'Shape') and cell.Shape:
                                shape = cell.Shape
                                
                                # 提取文本内容
                                if hasattr(shape, 'TextFrame') and shape.TextFrame:
                                    text_frame = shape.TextFrame
                                    if hasattr(text_frame, 'HasText') and text_frame.HasText:
                                        if hasattr(text_frame, 'TextRange') and text_frame.TextRange:
                                            text_range = text_frame.TextRange
                                            if hasattr(text_range, 'Text'):
                                                cell_data["text"] = str(text_range.Text).strip()
                                
                                # 提取背景色
                                if hasattr(shape, 'Fill') and shape.Fill:
                                    fill = shape.Fill
                                    if hasattr(fill, 'Visible') and fill.Visible:
                                        if hasattr(fill, 'Type') and fill.Type == 1:  # msoFillSolid
                                            if hasattr(fill, 'ForeColor'):
                                                color_rgb = self._get_color_rgb(fill.ForeColor)
                                                if color_rgb and color_rgb != "#000000":
                                                    cell_data["background_color"] = color_rgb
                                                    print(f"    🎨 单元格({row_idx},{col_idx})背景色: {color_rgb}")
                                
                                # 提取文本颜色和字体样式
                                if hasattr(shape, 'TextFrame') and shape.TextFrame:
                                    text_frame = shape.TextFrame
                                    
                                    # 提取文本对齐方式
                                    if hasattr(text_frame, 'HorizontalAnchor'):
                                        horizontal_anchor = getattr(text_frame, 'HorizontalAnchor', 0)
                                        # 映射PowerPoint的水平对齐常量到CSS值
                                        horizontal_align_map = {
                                            1: 'left',      # msoAnchorNone
                                            2: 'center',    # msoAnchorCenter
                                            3: 'right',     # msoAnchorBoth
                                        }
                                        cell_data["horizontal_align"] = horizontal_align_map.get(horizontal_anchor, 'left')
                                        print(f"    📐 单元格({row_idx},{col_idx})水平对齐: {cell_data['horizontal_align']}")
                                    
                                    if hasattr(text_frame, 'VerticalAnchor'):
                                        vertical_anchor = getattr(text_frame, 'VerticalAnchor', 0)
                                        # 映射PowerPoint的垂直对齐常量到CSS值
                                        vertical_align_map = {
                                            1: 'top',       # msoAnchorTop
                                            2: 'middle',    # msoAnchorMiddle
                                            3: 'bottom',    # msoAnchorBottom
                                        }
                                        cell_data["vertical_align"] = vertical_align_map.get(vertical_anchor, 'top')
                                        print(f"    📐 单元格({row_idx},{col_idx})垂直对齐: {cell_data['vertical_align']}")
                                    
                                    if hasattr(text_frame, 'TextRange') and text_frame.TextRange:
                                        text_range = text_frame.TextRange
                                        if hasattr(text_range, 'Font') and text_range.Font:
                                            font = text_range.Font
                                            
                                            # 提取文本颜色
                                            if hasattr(font, 'Color'):
                                                color_rgb = self._get_color_rgb(font.Color)
                                                if color_rgb:
                                                    cell_data["text_color"] = color_rgb
                                            
                                            # 提取字体名称
                                            if hasattr(font, 'Name'):
                                                cell_data["font_name"] = str(getattr(font, 'Name', 'Arial'))
                                            
                                            # 提取字体大小
                                            if hasattr(font, 'Size'):
                                                try:
                                                    cell_data["font_size"] = float(getattr(font, 'Size', 10))
                                                except:
                                                    cell_data["font_size"] = 10
                                            
                                            # 提取粗体设置
                                            if hasattr(font, 'Bold'):
                                                cell_data["font_bold"] = bool(getattr(font, 'Bold', False))
                                            
                                            # 提取斜体设置
                                            if hasattr(font, 'Italic'):
                                                cell_data["font_italic"] = bool(getattr(font, 'Italic', False))
                                            
                                            # 提取下划线设置
                                            if hasattr(font, 'Underline'):
                                                underline_val = getattr(font, 'Underline', 0)
                                                cell_data["font_underline"] = underline_val != 0
                                            
                                            # 字体样式已提取
                        except Exception as e:
                            pass
                        
                        row_data.append(cell_data)
                    
                    except Exception as e:
                        pass
                        # 添加空单元格数据
                        row_data.append({
                            "text": "",
                            "background_color": "#ffffff",
                            "text_color": "#000000",
                            "border": "1px solid #ccc"
                        })
                
                if row_data:  # 只有当行有数据时才添加
                    data.append(row_data)
            
            # 表格数据提取完成
            # 返回表格数据、行高和列宽信息
            return {
                "data": data,
                "row_heights": row_heights,
                "col_widths": col_widths
            }
            
        except Exception as e:
            return []

    def _extract_image_data(self, shape):
        """提取图片数据"""
        try:
            import tempfile
            import base64
            import os
            
            print(f"    🔄 开始导出图片...")
            print(f"    🔍 形状信息: Type={getattr(shape, 'Type', 'N/A')}, Name={getattr(shape, 'Name', 'N/A')}")
            
            # 检查形状是否有PictureFormat属性
            has_picture_format = hasattr(shape, 'PictureFormat') and shape.PictureFormat
            print(f"    📷 PictureFormat可用: {has_picture_format}")
            
            # 检查形状是否有OLEFormat属性
            has_ole_format = hasattr(shape, 'OLEFormat') and shape.OLEFormat
            print(f"    📋 OLEFormat可用: {has_ole_format}")
            
            # 方法1: 尝试直接导出图片
            print(f"    🔄 尝试方法1: 直接导出图片")
            image_data = self._try_export_image(shape)
            if image_data:
                print(f"    ✅ 方法1成功: 图片数据长度 {len(image_data)} 字符")
                return image_data
            
            # 方法2: 尝试从PictureFormat获取图片
            print(f"    🔄 尝试方法2: 从PictureFormat获取")
            image_data = self._try_extract_from_picture_format(shape)
            if image_data:
                print(f"    ✅ 方法2成功: 图片数据长度 {len(image_data)} 字符")
                return image_data
            
            # 方法3: 尝试从OLE对象获取图片
            print(f"    🔄 尝试方法3: 从OLE对象获取")
            image_data = self._try_extract_from_ole_object(shape)
            if image_data:
                print(f"    ✅ 方法3成功: 图片数据长度 {len(image_data)} 字符")
                return image_data
            
            print(f"    ❌ 所有图片提取方法都失败")
            print(f"    🔄 返回占位符图片（1x1透明像素）")
            # 返回占位符图片（1x1透明像素）
            placeholder = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            return placeholder
            
        except Exception as e:
            print(f"    ⚠️ 提取图片数据失败: {str(e)}")
            print(f"    🔄 返回占位符图片（异常情况）")
            # 返回占位符图片（1x1透明像素）
            placeholder = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            return placeholder

    def _try_export_image(self, shape):
        """尝试导出图片的第一种方法"""
        try:
            import tempfile
            import base64
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 尝试多种导出格式
            export_formats = [
                (2, 'PNG'),   # ppShapeFormatPNG
                (1, 'JPG'),   # ppShapeFormatJPG  
                (0, 'EMF'),   # ppShapeFormatEMF
                (3, 'GIF'),   # ppShapeFormatGIF
                (4, 'BMP'),   # ppShapeFormatBMP
            ]
            
            exported = False
            for format_code, format_name in export_formats:
                try:
                    print(f"    📤 尝试导出为 {format_name} 格式...")
                    shape.Export(temp_path, format_code)
                    
                    # 检查文件是否成功创建且有内容
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        print(f"    ✅ 成功导出为 {format_name} 格式")
                        exported = True
                        break
                    else:
                        print(f"    ⚠️ {format_name} 格式导出失败或文件为空")
                except Exception as e:
                    pass
                    continue
            
            if not exported:
                pass
                return None
            
            # 读取并编码
            with open(temp_path, 'rb') as f:
                image_bytes = f.read()
                if len(image_bytes) == 0:
                    pass
                    
        except Exception as e:
            pass
            return None

    def _try_extract_from_picture_format(self, shape):
        """尝试从PictureFormat获取图片数据"""
        try:
            if hasattr(shape, 'PictureFormat') and shape.PictureFormat:
                picture_format = shape.PictureFormat
                print(f"    🔍 尝试从PictureFormat获取图片...")
                
                # 尝试获取图片文件名
                if hasattr(picture_format, 'Filename'):
                    filename = picture_format.Filename
                    print(f"    📁 图片文件名: {filename}")
                
                # 尝试复制到剪贴板然后获取
                if hasattr(shape, 'Copy'):
                    try:
                        shape.Copy()
                        print(f"    📋 图片已复制到剪贴板")
                        
                        # 尝试从剪贴板获取图片数据
                        clipboard_data = self._try_get_from_clipboard()
                        if clipboard_data:
                            print(f"    ✅ 从剪贴板获取图片成功")
                            return clipboard_data
                            
                    except Exception as copy_e:
                        print(f"    ⚠️ 复制图片失败: {str(copy_e)}")
                
            return None
            
        except Exception as e:
            print(f"    ⚠️ 从PictureFormat提取图片失败: {str(e)}")
            return None

    def _try_get_from_clipboard(self):
        """尝试从剪贴板获取图片数据"""
        try:
            import win32clipboard
            from PIL import Image
            import io
            import base64
            
            print(f"    🔄 尝试从剪贴板获取图片...")
            
            # 打开剪贴板
            win32clipboard.OpenClipboard()
            
            try:
                # 检查剪贴板中是否有图片数据
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    print(f"    📋 剪贴板中发现DIB格式图片")
                    
                    # 获取DIB数据
                    dib_data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                    
                    # 将DIB数据转换为PIL Image
                    # DIB格式需要特殊处理
                    img_buffer = io.BytesIO(dib_data)
                    
                    # 尝试直接读取为图片
                    try:
                        img = Image.open(img_buffer)
                        
                        # 转换为PNG格式的base64
                        output_buffer = io.BytesIO()
                        img.save(output_buffer, format='PNG')
                        img_bytes = output_buffer.getvalue()
                        
                        image_data = base64.b64encode(img_bytes).decode('utf-8')
                        print(f"    ✅ 剪贴板图片转换成功，大小: {len(image_data)} 字符")
                        return f"data:image/png;base64,{image_data}"
                        
                    except Exception as img_e:
                        print(f"    ⚠️ DIB数据转换失败: {str(img_e)}")
                
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP):
                    print(f"    📋 剪贴板中发现BITMAP格式图片")
                    # 可以尝试处理BITMAP格式，但比较复杂
                    
                else:
                    print(f"    ❌ 剪贴板中没有图片数据")
                    
            finally:
                win32clipboard.CloseClipboard()
                
            return None
            
        except ImportError:
            print(f"    ⚠️ 缺少win32clipboard或PIL库，无法从剪贴板获取图片")
            return None
        except Exception as e:
            print(f"    ⚠️ 从剪贴板获取图片失败: {str(e)}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None

    def _try_extract_from_ole_object(self, shape):
        """尝试从OLE对象获取图片数据"""
        try:
            if hasattr(shape, 'OLEFormat') and shape.OLEFormat:
                ole_format = shape.OLEFormat
                print(f"    🔍 尝试从OLE对象获取图片...")
                
                if hasattr(ole_format, 'ProgID'):
                    prog_id = str(ole_format.ProgID).lower()
                    print(f"    📋 OLE程序ID: {prog_id}")
                    
                    # 检查是否是图片相关的OLE对象
                    if any(img_type in prog_id for img_type in ['paint', 'image', 'picture', 'photo']):
                        print(f"    🖼️ 发现图片类型的OLE对象")
                        # 尝试导出OLE对象
                        return self._try_export_image(shape)
                
            return None
            
        except Exception as e:
            print(f"    ⚠️ 从OLE对象提取图片失败: {str(e)}")
            return None

    
    def _save_config(self, config_file: str):
        """保存配置文件"""
        with open(config_file, 'w', encoding='utf-8') as f:
            # 使用Pydantic模型的model_dump方法而不是asdict
            json.dump(self.config.model_dump(), f, ensure_ascii=False, indent=2)
    
    def _close_ppt(self):
        """安全关闭PPT应用"""
        try:
            if self.presentation:
                print("🔒 正在关闭演示文稿...")
                try:
                    self.presentation.Close(SaveChanges=0)
                except Exception as e:
                    print(f"⚠️ 关闭演示文稿时出错: {str(e)}")
                finally:
                    self.presentation = None
            
            if self.ppt_app:
                print("🔒 正在关闭PowerPoint应用...")
                try:
                    # 尝试退出应用
                    self.ppt_app.Quit()
                except Exception as e:
                    print(f"⚠️ 退出PowerPoint时出错: {str(e)}")
                finally:
                    self.ppt_app = None
                    
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {str(e)}")
            self.presentation = None
            self.ppt_app = None