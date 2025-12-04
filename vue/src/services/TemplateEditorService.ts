// 模板编辑器服务
// 处理模板编辑页面的配置加载和保存

import { httpClient } from './httpClient';
import type { ApiResponse } from '@/types';

// 定义PPT配置类型
export interface PPTConfig {
  file_path?: string;
  total_slides?: number;
  slide_width?: number;
  slide_height?: number;
  createTime?: string;
  slides?: Array<Slide>;
  theme?: string;
  settings?: Record<string, any>;
}

export interface Slide {
  width?: number;
  height?: number;
  background?: string | BackgroundConfig;
  elements?: Array<Element>;
}

export interface BackgroundConfig {
  type: 'color' | 'image';
  value: string;
}

export interface Element {
  id?: string;
  type: string;
  left?: number;
  top?: number;
  width?: number;
  height?: number;
  fontSize?: string;
  color?: string;
  bgColor?: string;
  content?: string;
  dataSourceId?: string;
  dataRange?: string;
  sheetName?: string;
  // 兼容HTML版本的数据结构
  element_type_name?: string;
  element_name?: string;
  position?: {
    left?: number;
    top?: number;
    width?: number;
    height?: number;
  };
  style?: {
    font_family?: string;
    font_size?: string;
    color?: string;
    background_color?: string;
    font_style?: string;
    font_weight?: string;
    text_decoration?: string;
    text_align?: string;
    border?: string;
  };
  data?: {
      active_cell?:any;
      text_content?: string;
      image_data?: string;
      table_data?: any;
      chart_data?: any;
      ole_datas?: any;
      table_row_heights?: number[];
      table_col_widths?: number[];
      data_source_config?: {
        type: string;
        data_source_name: string;
        excel_sheet_name: string;
        excel_cell_range?: string;
      };
    };
}

/**
 * 模板编辑器服务类
 */
export class TemplateEditorService {
  private readonly basePath = '/templates';
  
  /**
   * 加载模板配置
   * @param templateId 模板ID
   */
  async loadTemplateConfig(templateId: string): Promise<ApiResponse<PPTConfig>> {
    try {
      const response = await httpClient.get<PPTConfig>('/ppt/config/load', {
          config_id: templateId
      });      
      // 根据返回格式调整数据
      // 注意：API返回的格式是 { success: true, config_data: { config: {} } }WW
      const anyResponse = response as any;
      if (anyResponse.success && anyResponse.config_data && anyResponse.config_data.config) {
        // 对配置数据进行转换，确保元素ID和类型字段名匹配
        const config = anyResponse.config_data.config;
        
        // 转换每个幻灯片中的元素
        if (config.slides && Array.isArray(config.slides)) {
          config.slides = config.slides.map((slide: any) => {
            if (slide.elements && Array.isArray(slide.elements)) {
              slide.elements = slide.elements.map((element: any) => {
                // 转换element_id为id
                if (element.element_id && !element.id) {
                  element.id = element.element_id;
                }
                
                // 转换element_type为type（如果没有element_type_name）
                if (element.element_type && !element.type && !element.element_type_name) {
                  element.type = element.element_type;
                }
                
                return element;
              });
            }
            return slide;
          });
        }
        
        return {
          success: response.success,
          data: config
        };
      } else if (anyResponse.data && anyResponse.data.config_data && anyResponse.data.config_data.config) {
        // 兼容之前的格式：{ success: true, data: { config_data: { config: {} } } }
        return {
          success: response.success,
          data: anyResponse.data.config_data.config
        };
      } else if (anyResponse.data && anyResponse.data.config) {
        // 兼容格式：{ success: true, data: { config: {} } }
        return {
          success: response.success,
          data: anyResponse.data.config
        };
      }
      
      return response;
    } catch (error) {
      console.error('加载模板配置失败:', error);
      
      // 为了演示，返回默认配置
      return {
        success: true,
        data: this.getMockPptConfig(templateId)
      };
    }
  }
  
  /**
   * 保存模板配置
   * @param templateId 模板ID
   * @param config PPT配置
   */
  async saveTemplateConfig(templateId: string, config: PPTConfig): Promise<ApiResponse<PPTConfig>> {
    try {
      // 调用 /api/ppt/config/update 接口来更新模板配置
      const response = await httpClient.post<PPTConfig>('/ppt/config/update', {
        template_id: templateId,
        config_data: config
      });
      
      // 保存到本地存储，以便快速访问
      sessionStorage.setItem('pptConfig', JSON.stringify(config));
      
      return response;
    } catch (error) {
      console.error('保存模板配置失败:', error);
      
      // 即使API调用失败，也尝试保存到本地存储
      sessionStorage.setItem('pptConfig', JSON.stringify(config));
      
      throw error;
    }
  }
  
  /**
   * 导出模板为HTML
   * @param templateId 模板ID
   * @param config PPT配置
   */
  async exportTemplateToHtml(templateId: string, config: PPTConfig): Promise<ApiResponse<string>> {
    try {
      const response = await httpClient.post<string>(`${this.basePath}/${templateId}/export/html`, config);
      return response;
    } catch (error) {
      console.error('导出模板为HTML失败:', error);
      throw error;
    }
  }
  
  /**
   * 导出模板为PDF
   * @param templateId 模板ID
   * @param config PPT配置
   */
  async exportTemplateToPdf(templateId: string, config: PPTConfig): Promise<ApiResponse<string>> {
    try {
      const response = await httpClient.post<string>(`${this.basePath}/${templateId}/export/pdf`, config);
      return response;
    } catch (error) {
      console.error('导出模板为PDF失败:', error);
      throw error;
    }
  }
  
  /**
   * 生成模板预览图
   * @param templateId 模板ID
   * @param config PPT配置
   */
  async generateTemplatePreview(templateId: string, config: PPTConfig): Promise<ApiResponse<string>> {
    try {
      const response = await httpClient.post<string>(`${this.basePath}/${templateId}/preview`, config);
      return response;
    } catch (error) {
      console.error('生成模板预览图失败:', error);
      throw error;
    }
  }
  
  /**
   * 获取模拟PPT配置数据
   * @param templateId 模板ID
   */
  private getMockPptConfig(templateId: string): PPTConfig {
    return {
      file_path: `${templateId}.pptx`,
      total_slides: 2,
      slide_width: 800,
      slide_height: 600,
      createTime: new Date().toISOString(),
      slides: [
        {
          width: 800,
          height: 600,
          background: '#f0f0f0',
          elements: [
            {
              id: 'title-1',
              type: 'text',
              left: 100,
              top: 50,
              width: 600,
              height: 100,
              fontSize: '24px',
              color: '#333333',
              content: '数据可视化标题'
            },
            {
              id: 'subtitle-1',
              type: 'text',
              left: 100,
              top: 150,
              width: 600,
              height: 50,
              fontSize: '16px',
              color: '#666666',
              content: '这是一个副标题'
            },
            {
              id: 'chart-1',
              type: 'chart',
              left: 100,
              top: 220,
              width: 600,
              height: 300,
              content: 'chart-data-1'
            }
          ]
        },
        {
          width: 800,
          height: 600,
          background: {
            type: 'color',
            value: '#ffffff'
          },
          elements: [
            {
              id: 'title-2',
              type: 'text',
              left: 100,
              top: 50,
              width: 600,
              height: 100,
              fontSize: '24px',
              color: '#333333',
              content: '第二页内容'
            },
            {
              id: 'image-1',
              type: 'image',
              left: 100,
              top: 180,
              width: 300,
              height: 200,
              content: 'https://via.placeholder.com/300x200'
            },
            {
              id: 'text-1',
              type: 'text',
              left: 450,
              top: 180,
              width: 250,
              height: 200,
              fontSize: '14px',
              color: '#333333',
              content: '这里是一些说明文字，用于解释图表或图片的内容。\n\n可以有多行文本。'
            }
          ]
        }
      ]
    };
  }
}