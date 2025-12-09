// 指令相关类型定义

// 指令类别
export interface InstructionCategory {
  id: string;
  name: string;
  description: string;
  icon?: string;
  expanded?: boolean; // 是否展开
  sort_order?: number; // 排序顺序
  instructions: Instruction[]; // 该类别下的指令列表
}

// 指令参数定义
export interface InstructionParam {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'file' | 'range' | 'column' | 'textarea' | 'select_excelpath';
  label: string;
  required: boolean;
  defaultValue?: any;
  options?: Array<{ label: string; value: any }>;
  description?: string;
  placeholder?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  // 列选择相关
  multiple?: boolean; // 是否支持多选
  columns?: string[]; // 可选的列名列表
}

// 指令定义
export interface Instruction {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  params: InstructionParam[];
  inputPorts?: number;
  outputPorts?: number;
  color?: string;
  sort_order?: number; // 排序顺序
  is_active?: boolean; // 是否启用
  // Python脚本代码
  python_script?: string;
}

// 画布节点
export interface CanvasNode {
  id: string;
  instructionId: string;
  x: number;
  y: number;
  params: Record<string, any>;
  label?: string;
  description?: string; // 节点描述信息
  inputTypes?: Record<string, boolean>; // 输入类型配置，键为参数名，值为是否是表达式类型
  intput_types?: { t: string[]; e: string[] }; // 格式化后的输入类型配置，用于后端接口
}

// 画布连线
export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  sourcePort?: string;
  targetPort?: string;
}

// 数据处理流程
export interface DataProcessFlow {
  id?: string;
  name: string;
  description: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  createdAt?: string;
  updatedAt?: string;
}

// 指令执行参数
export interface InstructionExecutionParams {
  instructionId: string;
  params: Record<string, any>;
  inputData?: any;
}

// 指令执行结果
export interface InstructionExecutionResult {
  success: boolean;
  data?: any;
  message?: string;
  error?: string;
  executionTime?: number;
}

// 流程执行状态
export interface ProcessExecutionStatus {
  total: number;
  current: number;
  currentStep: string;
  isRunning: boolean;
  results: Record<string, InstructionExecutionResult>;
}

// ParamsPanelState 已移至 dataSource.ts 中定义，避免重复导出

// DataProcessModalState 已移至 dataSource.ts 中定义，避免重复导出

// 指令参数表单项
export interface ParamFormItem {
  param: InstructionParam;
  value: any;
  error?: string;
}

// 指令执行上下文
export interface InstructionExecutionContext {
  dataSourceId: string;
  availableColumns: string[];
  previousResults: Record<string, any>;
}

// 创建/更新指令请求接口
export interface CreateInstructionRequest {
  name: string;
  description: string;
  category: string;
  icon?: string;
  params: InstructionParam[];
  inputPorts?: number;
  outputPorts?: number;
  color?: string;
  sort_order?: number;
  is_active?: boolean;
  type?: 'data-extraction' | 'data-filter' | 'data-sort' | 'data-transform' | 'data-export' | 'custom';
}

// 更新指令请求接口
export interface UpdateInstructionRequest {
  name?: string;
  description?: string;
  category?: string;
  icon?: string;
  params?: InstructionParam[];
  inputPorts?: number;
  outputPorts?: number;
  color?: string;
  sort_order?: number;
  is_active?: boolean;
  type?: string;
}

// 创建/更新分类请求接口
export interface CreateCategoryRequest {
  name: string;
  description: string;
  icon?: string;
  sort_order?: number;
}

// 指令列表响应接口
export interface InstructionListResponse {
  success: boolean;
  message?: string;
  data?: {
    categories: InstructionCategory[];
    total: number;
  };
}

// 单条指令响应接口
export interface InstructionResponse {
  success: boolean;
  message?: string;
  data?: Instruction;
}

// 分类响应接口
export interface CategoryResponse {
  success: boolean;
  message?: string;
  data?: InstructionCategory;
}