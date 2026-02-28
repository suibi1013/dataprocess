// 模板编辑器服务
// 处理模板编辑页面的配置加载和保存

import { httpClient } from './httpClient';
import type { ApiResponse } from '@/types';

// 定义PPT配置类型
export interface PPTConfig {
  file_name?: string;
  file_path?: string;
  id?: string;
  slide_height?: number;
  slide_width?: number;
  slides?: Array<Slide>;
  templateName?: string;
  total_slides?: number;
}

export interface Slide {
  background?: string;
  data_source_config_info?: Record<string, any>;
  elements?: Array<Element>;
  height?: number;
  width?: number;
  updated_at?: string;
}

export interface Element {
  children?: Array<Element>;
  data?: {
    active_cell?: any;
    chart_data?: any;
    data_source_config?: {
      type: string;
      data_source_name: string;
      data_source_path: string;
      excel_sheet_name: string;
      excel_cell_range?: string;
    };
    ole_datas?: any;
    image_data?: string;
    original_image_data?: string;
    text_content?: string;
    table_data?: any;
    table_row_heights?: number[];
    table_col_widths?: number[];
  };
  element_id?: string;
  element_name?: string;
  element_type?: string;
  element_type_name?: string;
  id?: string;
  position?: {
    left?: number;
    top?: number;
    width?: number;
    height?: number;
  };
  style?: {
    background_color?: string;
    border?: string;
    color?: string;
    font_family?: string;
    font_size?: string;
    font_style?: string;
    font_weight?: string;
    text_align?: string;
    text_decoration?: string;
  };
}

/**
 * 模板编辑器服务类
 */
export class TemplateEditorService {
  private readonly basePath = '/template';

  /**
   * 加载模板配置
   * @param templateId 模板ID
   */
  async loadTemplateConfig(templateId: string): Promise<ApiResponse<PPTConfig>> {
    try {
      const response = await httpClient.get<PPTConfig>('/template/config/load', {
        config_id: templateId
      });
      return response;
    } catch (error) {
      console.error('加载模板配置失败:', error);
      throw error;
    }
  }

  /**
   * 保存模板配置
   * @param templateId 模板ID
   * @param config PPT配置
   */
  async saveTemplateConfig(templateId: string, slideIndex: number, data_source_config_info: any): Promise<ApiResponse<PPTConfig>> {
    try {
      // 调用 /api/template/config/update 接口来更新模板配置
      const response = await httpClient.post<PPTConfig>('/template/config/update', {
        template_id: templateId,
        slide_index: slideIndex,
        data_source_config_info: data_source_config_info
      });

      return response;
    } catch (error) {
      console.error('保存模板配置失败:', error);
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
}