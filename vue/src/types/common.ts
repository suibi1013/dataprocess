// 通用类型定义

// API响应基础结构
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 分页参数
export interface PaginationParams {
  page: number;
  pageSize: number;
}

// 分页响应
export interface PaginationResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 文件上传响应
export interface FileUploadResponse {
  filename: string;
  originalName: string;
  size: number;
  path: string;
}

// 表格单元格样式
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

// 表格数据结构
export interface TableData {
  columns: string[];
  rows: (string | number)[][];
  styles?: { [key: string]: CellStyle };
}

// 选择区域
export interface SelectionRange {
  startRow: number;
  endRow: number;
  startCol: number;
  endCol: number;
}

// 模态框状态
export interface ModalState {
  visible: boolean;
  loading?: boolean;
}

// 状态消息
export interface StatusMessage {
  text: string;
  type: 'success' | 'error' | 'warning' | 'info';
  visible: boolean;
}