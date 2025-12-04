// 数据源相关类型定义

import { TableData } from './common';
import type { InstructionCategory, CanvasNode, ParamFormItem } from './instruction';

// 数据源类型枚举
export type DataSourceType = 'excel' | 'api' | 'database';

// Excel配置
export interface ExcelConfig {
  files: ExcelFile[];
}

// Excel文件信息
export interface ExcelFile {
  file_name?: string;
  unique_name?: string;
  file_path?: string;
  file_size?: number;
  size?: number; // 兼容原生File对象
  name?: string; // 兼容原生File对象
}

// API配置
export interface ApiConfig {
  url: string;
  method: 'GET' | 'POST';
  headers?: Record<string, string>;
}

// 数据库配置
export interface DatabaseConfig {
  type: 'mysql' | 'postgresql' | 'sqlite';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

// 模态框状态类型
export type ModalState = 'hidden' | 'visible';

// 表单验证错误类型
export interface FormErrors {
  name?: string;
  type?: string;
  config?: string;
  [key: string]: string | undefined;
}

// 数据源创建状态
export interface DataSourceCreationState {
  loading: boolean;
  success: boolean;
  error: string | null;
  isCreating: boolean;
  progress: number;
  currentStep: string;
}

// 新增数据源模态框状态
export interface AddDataSourceModalState {
  visible: boolean;
  currentStep: number;
  selectedType: DataSourceType;
  formData: {
    name: string;
    type: DataSourceType;
    config: Partial<DataSourceConfig>;
  };
  formErrors: Record<string, string>;
  isSubmitting: boolean;
}

// 数据源配置联合类型
export type DataSourceConfig = ExcelConfig | ApiConfig | DatabaseConfig;

// 数据源基础信息
export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  config: DataSourceConfig;
  status: 'active' | 'inactive' | 'error';
  createdAt: string;
  updatedAt: string;
  description?: string;
}

// 创建数据源请求
export interface CreateDataSourceRequest {
  name: string;
  type: DataSourceType;
  config: DataSourceConfig;
  description?: string;
}

// 数据源数据预览
export interface DataSourcePreview {
  dataSourceId: string;
  data: TableData | Record<string, TableData>; // 单文件或多文件
  isMultiFile: boolean;
}

// Excel工作表信息
export interface SheetInfo {
  name: string;
  data: TableData;
}

// Excel文件信息
export interface ExcelFileInfo {
  filename: string;
  sheets: SheetInfo[];
}

// 数据源表单状态
export interface DataSourceFormState {
  name: string;
  type: DataSourceType | '';
  config: Partial<DataSourceConfig>;
  loading: boolean;
  errors: Record<string, string>;
}

// 数据源列表查询参数
export interface DataSourceListParams {
  page?: number;
  pageSize?: number;
  type?: DataSourceType;
  status?: string;
  keyword?: string;
}

// 数据处理相关类型定义

// 数据处理模态框状态
export interface DataProcessModalState {
  visible: boolean;
  loading: boolean;
  saving: boolean;
  executing: boolean;
  dataLoading: boolean; // 新增：数据源数据加载状态
  instructions: InstructionCategory[];
  selectedNodes: string[];
  executionProgress: {
    visible: boolean;
    current: number;
    total: number;
    stepName: string;
  };
}

// 参数面板状态接口
export interface ParamsPanelState {
  visible: boolean;
  collapsed: boolean;
  selectedNode: any;
  selectedEdge: any;
  params: Record<string, any>;
  nodeData: CanvasNode | null;
  paramFormItems: ParamFormItem[];
}

// 单元格样式接口
export interface CellStyle {
  font_size?: number;
  font_color?: string;
  font_bold?: boolean;
  font_italic?: boolean;
  font_underline?: boolean;
  font_name?: string;
  horizontal_align?: 'left' | 'center' | 'right' | 'justify';
  vertical_align?: 'top' | 'center' | 'bottom';
  background_color?: string;
  border_top?: string;
  border_bottom?: string;
  border_left?: string;
  border_right?: string;
  width?: number;
  height?: number;
}