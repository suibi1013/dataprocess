// 边框样式
interface BorderStyle {
  style: 'none' | 'solid' | 'dashed' | 'dotted'; // 可根据实际扩展
  color: string; // 如 "#000000"
  width: number;
}

// 单元格定义
export interface Cell {
  text: string;
  formulas: string;
  font_name: string;
  font_size: number;
  font_color: string;
  font_bold: boolean;
  font_italic: boolean;
  font_underline: boolean;
  background_color: string;
  horizontal_align: 'left' | 'center' | 'right';
  vertical_align: 'top' | 'middle' | 'bottom';
  border_top: BorderStyle;
  border_bottom: BorderStyle;
  border_left: BorderStyle;
  border_right: BorderStyle;
  width: number;
  height: number;
  is_merged: boolean;
  merge_range: string | null; // 如 "A1:B2"，或 null
}
// 一行数据：键为列字母（A, B, C...），值为 Cell
export interface Row {
  [column: string]: Cell; // key 是列名，如 "A", "B"
}
// =================== 工作表数据结构 ===================
export interface ExcelSheetData {
  filename: string;           // 所属文件名
  sheet_name: string;         // 工作表名称
  columns: string[];          // 列名数组，如 ["A", "B", "C"]
  rows:Row[]; // 行数据，每一行是一个对象（键为列名）
  total_rows: number;         // 总行数
  displayed_rows: number;     // 当前显示的行数（可能分页）
}
// =================== 单个文件信息 ===================
export interface ExcelFilesInfo {
  filename: string;           // 系统生成的文件名（含时间戳）
  file_path: string;          // 文件在服务器上的路径
  original_filename: string;  // 用户上传时的原始文件名
  sheets: string[];           // 该文件包含的工作表名称列表
}


// =================== 主响应结构 ===================
export interface ExcelImportResponse {
  files: ExcelFilesInfo[];     // 所有上传/解析的文件信息
  sheets: string[];           // 所有文件中提取出的唯一工作表名称列表（扁平化）
  data: {
    [key: string]: ExcelSheetData; // 键格式：`${filename}_${sheetName}`
  };
}
