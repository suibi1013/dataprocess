// 模板相关类型定义

import { ApiResponse } from './common';

// 模板状态枚举
export enum TemplateStatus {
  // eslint-disable-next-line no-unused-vars
  READY = 'ready',
  // eslint-disable-next-line no-unused-vars
  PROCESSING = 'processing',
  // eslint-disable-next-line no-unused-vars
  ERROR = 'error'
}

// 模板对象接口
export interface Template {
  id: string;
  name: string;
  filename?: string;
  status: TemplateStatus;
  createTime: string;
  description?: string;
  type?: string;
}

// 创建模板请求接口
export interface CreateTemplateRequest {
  name: string;
  description?: string;
  file?: File;
}

// 更新模板请求接口
export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  file?: File;
}

// 模板API服务接口
export interface TemplateApiService {
  // 获取模板列表
  getTemplates(): Promise<ApiResponse<Template[]>>;
  
  // 创建模板
  createTemplate(_data: CreateTemplateRequest): Promise<ApiResponse<Template>>;
  
  // 获取模板详情
  getTemplate(_id: string): Promise<ApiResponse<Template>>;
  
  // 更新模板
  updateTemplate(_id: string, _data: UpdateTemplateRequest): Promise<ApiResponse<Template>>;
  
  // 删除模板
  deleteTemplate(_id: string): Promise<ApiResponse<void>>;
  
  // 上传模板文件
  uploadTemplateFile(_templateId: string, _file: File): Promise<ApiResponse<any>>;
}