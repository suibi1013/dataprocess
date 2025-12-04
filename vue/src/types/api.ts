// API相关类型定义

import { ApiResponse } from './common';
import { DataSource, CreateDataSourceRequest, DataSourcePreview } from './dataSource';
import { Instruction, InstructionCategory, InstructionExecutionResult } from './instruction';

// API端点配置
export interface ApiEndpoints {
  // 数据源相关
  dataSources: {
    list: string;
    create: string;
    get: (_id: string) => string;
    update: (_id: string) => string;
    delete: (_id: string) => string;
    preview: (_id: string) => string;
  };
  // 指令相关
  instructions: {
    categories: string;
    list: string;
    execute: string;
  };
}

// HTTP请求方法
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// 请求配置
export interface RequestConfig {
  method: HttpMethod;
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
}

// API服务接口定义
export interface DataSourceApiService {
  // 获取数据源列表
  getDataSources(): Promise<ApiResponse<DataSource[]>>;
  
  // 创建数据源
  createDataSource(_data: CreateDataSourceRequest): Promise<ApiResponse<DataSource>>;
  
  // 获取数据源详情
  getDataSource(_id: string): Promise<ApiResponse<DataSource>>;
  
  // 更新数据源
  updateDataSource(_id: string, _data: Partial<DataSource>): Promise<ApiResponse<DataSource>>;
  
  // 删除数据源
  deleteDataSource(_id: string): Promise<ApiResponse<void>>;
  
  // 预览数据源数据
  previewDataSource(_id: string): Promise<ApiResponse<DataSourcePreview>>;
}

export interface InstructionApiService {
  // 获取指令分类
  getInstructionCategories(): Promise<ApiResponse<InstructionCategory[]>>;
  
  // 获取指令列表
  getInstructions(): Promise<ApiResponse<Instruction[]>>;
  
  // 执行指令
  executeInstruction(_instructionId: string, _params: Record<string, any>): Promise<ApiResponse<InstructionExecutionResult>>;
}

// 错误响应
export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

// 请求拦截器类型
export type RequestInterceptor = (_config: RequestConfig) => RequestConfig | Promise<RequestConfig>;

// 响应拦截器类型
export type ResponseInterceptor = (_response: any) => any | Promise<any>;

// 错误拦截器类型
export type ErrorInterceptor = (_error: any) => any | Promise<any>;