// 数据提取相关的类型定义

/**
 * 数据提取参数接口
 */
export interface DataExtractionParams {
  /** 源数据路径 */
  sourceDataPath: string;
  /** 开始行 */
  startRow: number;
  /** 结束行 */
  endRow: number;
  /** 开始列 */
  startColumn: string;
  /** 结束列 */
  endColumn: string;
  /** 结果变量名 */
  resultVariableName: string;
}

/**
 * 节点数据接口
 */
export interface NodeData {
  /** 节点ID */
  id: string;
  /** 节点类型 */
  type: string;
  /** 节点名称 */
  name: string;
  /** 节点参数 */
  params?: DataExtractionParams;
}

/**
 * 数据源文件接口
 */
export interface DataSourceFile {
  /** 数据源ID */
  id: string;
  /** 显示名称 */
  name: string;
  /** 数据路径 (格式: "数据源ID:工作表名") */
  path: string;
  /** 文件名 (可选) */
  filename?: string;
  /** 原始文件名 (可选) */
  original_filename?: string;
  /** 文件路径 (可选) */
  file_path?: string;
  /** 工作表列表 (可选) */
  sheets?: string[];
}

/**
 * 数据源详情接口
 */
export interface DataSourceDetails {
  /** 文件列表 */
  files: DataSourceFile[];
  /** 数据内容 */
  data?: Record<string, SheetData>;
  /** 工作表列表 */
  sheets?: string[];
}

/**
 * 工作表数据接口
 */
export interface SheetData {
  /** 列名数组 */
  columns: string[];
  /** 行数据数组 */
  rows: Record<string, any>[];
}

/**
 * 数据选择区域接口
 */
export interface DataSelection {
  sheetName:string
  /** 开始行 */
  startRow: number;
  /** 结束行 */
  endRow: number;
  /** 开始列 */
  startColumn: string;
  /** 结束列 */
  endColumn: string;
  /** 开始列索引 */
  startColIndex: number;
  /** 结束列索引 */
  endColIndex: number;
}

/**
 * 指令执行结果接口
 */
export interface InstructionResult {
  /** 执行是否成功 */
  success: boolean;
  /** 结果消息 */
  message?: string;
  /** 数据形状 */
  data_shape?: string;
  /** 执行时间 */
  execution_time?: number;
  /** 输出路径 */
  output_path?: string;
  /** 原始结果数据 */
  data?: any;
}

/**
 * API响应接口
 */
export interface ApiResponse<T = any> {
  /** 请求是否成功 */
  success: boolean;
  /** 响应数据 */
  data?: T;
  /** 错误消息 */
  error?: string;
  /** 响应消息 */
  message?: string;
}

/**
 * 数据预览选择状态接口
 */
export interface SelectionState {
  /** 是否正在选择 */
  isSelecting: boolean;
  /** 选择开始的单元格 */
  startCell: { row: number; col: number } | null;
  /** 选择结束的单元格 */
  endCell: { row: number; col: number } | null;
  /** 当前选择区域 */
  currentSelection: DataSelection | null;
}

/**
 * 表格单元格接口
 */
export interface TableCell {
  /** 行索引 */
  row: number;
  /** 列索引 */
  col: number;
  /** 列名 */
  colName: string;
  /** 单元格值 */
  value: any;
}

/**
 * 单元格数据接口（包含样式信息）
 */
export interface CellData {
  /** 单元格文本内容 */
  text: string;
  /** 公式 */
  formulas?: string;
  /** 字体名称 */
  font_name?: string;
  /** 字体大小 */
  font_size?: number;
  /** 字体颜色 */
  font_color?: string;
  /** 是否粗体 */
  font_bold?: boolean;
  /** 是否斜体 */
  font_italic?: boolean;
  /** 是否下划线 */
  font_underline?: boolean;
  /** 背景颜色 */
  background_color?: string;
  /** 水平对齐方式 */
  horizontal_align?: string;
  /** 垂直对齐方式 */
  vertical_align?: string;
  /** 上边框样式 */
  border_top?: {
    style: string;
    color: string;
    width: number;
  };
  /** 下边框样式 */
  border_bottom?: {
    style: string;
    color: string;
    width: number;
  };
  /** 左边框样式 */
  border_left?: {
    style: string;
    color: string;
    width: number;
  };
  /** 右边框样式 */
  border_right?: {
    style: string;
    color: string;
    width: number;
  };
  /** 单元格宽度 */
  width?: number;
  /** 单元格高度 */
  height?: number;
  /** 是否是合并单元格 */
  is_merged?: boolean;
  /** 合并区域 */
  merge_range?: string;
}

/**
 * 数据预览模态框配置接口
 */
export interface PreviewModalConfig {
  /** 工作表数据 */
  sheetData: SheetData;
  /** 工作表名称 */
  sheetName: string;
  /** 是否显示选择功能 */
  showSelection?: boolean;
  /** 确认选择回调 */
  onConfirmSelection?: (_selection: DataSelection) => void;
  /** 取消回调 */
  onCancel?: () => void;
}