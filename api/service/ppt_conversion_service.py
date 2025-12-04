
import os
import json
from typing import Optional, List, Tuple, Dict, Any
class PPTConversionservice:
    """PPT转换服务 - 依赖注入版本"""
    
    def __init__(self):
        pass
    
    async def convert_ppt_to_html(self, ppt_path: str, output_dir: str) -> Dict[str, Any]:
        """将PPT转换为HTML"""
        try:
            from converter.ppt_converter import PPTConverterWithEditor
            
            # 创建转换器实例
            converter = PPTConverterWithEditor()
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成输出HTML文件路径
            output_html = os.path.join(output_dir, 'ppt_editor.html')
            
            # 生成配置文件路径
            config_file = os.path.join(output_dir, 'config.json')
            
            print(f"开始转换PPT: {ppt_path}")
            # 调用转换器进行PPT解析和转换，传递config_file参数
            result_html = converter.convert_ppt_to_html_with_editor(
                ppt_path=ppt_path,
                output_html=output_html,
                config_file=config_file
            )
            print(f"转换结果HTML路径: {result_html}")
            
            # 检查转换是否成功（如果返回了HTML路径且文件存在）
            if result_html and os.path.exists(result_html):
                # 尝试读取配置文件获取slides_count
                slides_count = 0
                config_data = None
                try:
                    if os.path.exists(config_file):
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            slides_count = config_data.get('total_slides', 0)
                    else:
                        print(f"配置文件不存在: {config_file}")
                except Exception as e:
                    print(f"读取配置文件失败: {e}")
                
                return {
                    'success': True,
                    'convert_ppt_to_html': result_html,
                    'slides_count': slides_count,
                    'message': 'PPT解析和转换成功',
                    'config': config_data
                }
            else:
                return {
                    'success': False,
                    'error': '转换失败，未生成HTML文件',
                    'message': 'PPT解析和转换失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'PPT转换失败: {str(e)}'
            }
