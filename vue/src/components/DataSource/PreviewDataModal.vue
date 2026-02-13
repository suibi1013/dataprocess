<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h2>Excel数据预览</h2>
        <button type="button" class="close-btn" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div class="preview-section">
          <!-- 文件选择和sheet选择 -->
          <div class="data-source-controls">
            <div v-if="props.dataSource?.type === 'excel'" class="selectors-container">
              <!-- 文件选择框 -->
              <div v-if="fileList.length > 0" class="file-selector inline">
                <label class="control-label">选择文件：</label>
                <select 
                  v-model="currentSelectedFile" 
                  @change="handleFileChange()"
                  class="file-select"
                >
                  <option 
                    v-for="file in fileList" 
                    :key="file.file_name"
                    :value="file.file_path"
                  >
                    {{ file.file_name}}
                  </option>
                </select>
              </div>
              
              <!-- 工作表下拉选择框 -->
              <div class="sheet-selector inline">
                <label class="control-label">选择工作表：</label>
                <select 
                  v-model="currentSelectedSheet" 
                  class="sheet-select"
                  :disabled="Object.keys(allSheetsData).length === 0"
                >
                  <option value="" disabled>
                    {{ Object.keys(allSheetsData).length === 0 ? '请先选择文件' : '请选择工作表' }}
                  </option>
                  <option 
                    v-for="sheetName in Object.keys(allSheetsData)" 
                    :key="sheetName"
                    :value="sheetName"
                  >
                    {{ sheetName }}
                  </option>
                </select>
                <button 
                  type="button" 
                  class="btn btn-primary ml-2"
                  @click="selectSheetTab(currentSelectedSheet)"
                  :disabled="!currentSelectedSheet || loading"
                >
                  {{ loading ? '加载中...' : '加载数据' }}
                </button>
                <span v-if="loading && currentSelectedSheet" class="sheet-loading-indicator">
                  <i class="el-icon-loading"></i>
                </span>
              </div>
            </div>
          </div>
          
          <!-- 数据预览容器 -->
          <div class="data-preview-container">
            <!-- 数据加载状态 -->
            <div v-if="loading" class="data-loading-container">
              <div class="loading-spinner">
                <i class="el-icon-loading"></i>
              </div>
              <p class="loading-text">正在加载数据...</p>
            </div>
            
            <!-- 数据加载错误 -->
            <div v-else-if="error" class="data-error-container">
              <div class="error-icon">
                <i class="el-icon-error"></i>
              </div>
              <h4 class="error-title">数据加载失败</h4>
              <p class="error-message">{{ error }}</p>
              <button class="btn btn-primary" @click="handleRetry">
                <i class="el-icon-refresh"></i>
                重试
              </button>
            </div>
            
            <!-- 数据显示 -->
            <div v-else-if="excelPreviewData.length > 0" class="table-preview-wrapper">
              <table id="data-preview-table" class="preview-table">
                <thead>
                  <tr>
                    <th class="row-number-header">#</th>
                    <th 
                      v-for="(column, index) in excelPreviewColumns" 
                      :key="index"
                      class="column-header-cell"
                    >
                      {{ column }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(row, rowIndex) in excelPreviewData" 
                    :key="rowIndex"
                    class="data-row"
                  >
                    <td class="row-number-cell">{{ rowIndex + 1 }}</td>
                    <td 
                      v-for="(column, colIndex) in excelPreviewColumns" 
                      :key="colIndex"
                      class="data-cell clickable-cell"
                      :style="getCellStyle(getCellData(row, column, colIndex))"
                      :title="formatCellValue(getCellData(row, column, colIndex))"
                      @click="handleCellClick($event, rowIndex, colIndex)"
                    >
                      <div class="cell-content">
                        {{ formatCellValue(getCellData(row, column, colIndex)) }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- 无数据状态 -->
            <div v-else class="empty-data">
              <div class="empty-icon">
                <i class="el-icon-document-empty"></i>
              </div>
              <h4 class="empty-title">暂无数据</h4>
              <p class="empty-message">该数据源中没有找到任何数据</p>
            </div>
          </div>
        </div>
          <!-- 选择信息 -->
          <div class="selection-info">
            <!-- <p>已选择: <span id="selected-range">{{ selectedCellRange || '无' }}</span></p> -->
            <p><span id="selected-range"></span></p>
            <button 
              type="button" 
              id="confirmDataSourceSelection" 
              class="btn btn-success" 
              @click="handleClose"
            >
              关闭
            </button>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { DataSource } from '@/types/dataSource';
import { dataSourceInfoCache } from '@/composables/useDataProcess';
import { httpClient } from '@/services/httpClient';
// import { useDataSourceStore } from '@/store/dataSourceStore';

// Props
interface Props {
  visible: boolean;
  dataSource: DataSource | null;
}

const props = defineProps<Props>();

// Emits
interface Emits {
  close: [];
}

const emit = defineEmits<Emits>();

// Store
// const dataSourceStore = useDataSourceStore();

// 状态变量 - 按照HTML版本的逻辑
const loading = ref(false);
const error = ref<string>('');
const currentSelectedSheet = ref<string>('');
const selectedCellRange = ref<string>('');
const excelPreviewData = ref<any[]>([]);
const excelPreviewColumns = ref<string[]>([]);
const allSheetsData = ref<Record<string, any>>({});
// 文件选择相关状态
const currentSelectedFile = ref<string>('');
const fileList = ref<any[]>([]);

// 单元格选择相关状态（暂时注释，后续实现时启用）
// const isSelecting = ref(false);
// const startCell = ref<{row: number, col: number} | null>(null);
// const lastCell = ref<{row: number, col: number} | null>(null);

// 监听弹窗显示状态和数据源变化
watch([() => props.visible, () => props.dataSource], ([visible, dataSource]) => {
  if (visible && dataSource) {
    openDataPreviewModal();
  } else if (!visible) {
    // 清理状态
    clearPreviewData();
  }
});

// 清理预览数据
const clearPreviewData = () => {
  currentSelectedSheet.value = '';
  selectedCellRange.value = '';
  excelPreviewData.value = [];
  excelPreviewColumns.value = [];
  allSheetsData.value = {};
  error.value = '';
};

const mergeRowsWithStyles = (rows: any[]) => {
  // 直接返回原始行数据，保持后端返回的数据结构不变
  return rows || [];
};

// 打开数据预览模态框 - 取消调用API，仅初始化UI
const openDataPreviewModal = async () => {
  loading.value = true;
  error.value = '';
  
  // 清空选择状态
  selectedCellRange.value = '';
  currentSelectedFile.value = '';
  currentSelectedSheet.value = '';
  excelPreviewData.value = [];
  excelPreviewColumns.value = [];
  allSheetsData.value = {};
  
  try {
    // 1. 首先初始化文件选择下拉框
    if (props.dataSource?.type === 'excel' && props.dataSource.config?.files) {
      fileList.value = props.dataSource.config.files;
    } else {
      fileList.value = [];
      currentSelectedFile.value = '';
    }
    
    // 2. 初始化sheet选择，设置为空结构
    allSheetsData.value = {};
    currentSelectedSheet.value = '';
    
    // 3. 清空预览数据
    excelPreviewData.value = [];
    excelPreviewColumns.value = [];
    
  } catch (err) {
    console.error('初始化预览窗口失败:', err);
    error.value = err instanceof Error ? err.message : '初始化预览窗口失败';
  } finally {
    loading.value = false;
  }
};

// 处理文件选择变化
const handleFileChange = async () => {
  // 使用参数或currentSelectedFile.value
  const fileValue = currentSelectedFile.value;
  
  // 清空当前数据
  currentSelectedSheet.value = '';
  excelPreviewData.value = [];
  excelPreviewColumns.value = [];
  allSheetsData.value = {};
  
  // 如果选择了文件且数据源存在，则调用API获取该文件的sheet名称
  if (fileValue && props.dataSource) {
    loading.value = true;
    error.value = '';
    
    try {      
      // 调用更新后的API接口，传递file_path参数
      const response = await httpClient.get('/datasource/file-sheets', {
        file_path: currentSelectedFile.value
      });
      if (response.success && response.data) {
        // 获取sheets数组
        let sheets = response.data.sheets;
        
        // 更新sheet数据
        allSheetsData.value = {};
        sheets.forEach((sheetName: string) => {
          allSheetsData.value[sheetName] = {};
        });
        // 默认选择第一个sheet
        if (sheets.length > 0) {
          currentSelectedSheet.value = sheets[0];
          // 不再自动加载数据，等待用户点击加载数据按钮
        }
      } else {
        console.error('API响应失败:', response);
        throw new Error('API响应失败');
      }
    } catch (err) {
      console.error('获取文件sheet名称失败:', err);
      error.value = err instanceof Error ? err.message : '获取文件sheet名称失败';
    } finally {
      loading.value = false;
    }
  } 
};

// 选择工作表标签 - 按照HTML版本逻辑
const selectSheetTab = async (sheetName: string) => {
  if (!sheetName) {
    return;
  }
  
  // 更新当前选中的工作表
  currentSelectedSheet.value = sheetName;
  selectedCellRange.value = '';
  
  // 清空当前数据，显示加载状态
  excelPreviewData.value = [];
  excelPreviewColumns.value = [];
  loading.value = true;
  
  try {
    // 从缓存或API中获取完整的sheet数据
    let sheetData = null;
    
    // 首先检查缓存
    if (currentSelectedFile.value && dataSourceInfoCache.value.has(currentSelectedFile.value+sheetName)) {
      const cachedData = dataSourceInfoCache.value.get(currentSelectedFile.value+sheetName);
      if (cachedData) {
        // 缓存中直接存储工作表数据
        sheetData = cachedData;
      }
    }
    
    // 如果缓存中没有数据，则重新获取完整数据
    if (!sheetData && currentSelectedFile.value) {
      try {
        // 调用更新后的API接口，传递file_path参数
        const data = await httpClient.get('/datasource/file-data', {
          file_path: currentSelectedFile.value,
          sheet_name: sheetName,
          limit: 20
        });
        if (data.success && data.data) {
          // API现在直接返回工作表数据
          sheetData = data.data;
          // 更新缓存
          dataSourceInfoCache.value.set(currentSelectedFile.value+sheetName, sheetData);
        }
      } catch (err) {
        console.error('调用Excel文件数据API失败:', err);
      }
    }
    
    // 加载选中工作表的数据
    if (sheetData) {
      // 直接使用原始行数据
      excelPreviewData.value = mergeRowsWithStyles(sheetData.rows || []);
      excelPreviewColumns.value = sheetData.columns || [];
    } else {
      throw new Error('未找到工作表数据');
    }
  } catch (err) {
    console.error('加载工作表数据失败:', err);
    error.value = err instanceof Error ? err.message : '加载工作表数据失败';
  } finally {
    loading.value = false;
  }
};

// 获取单元格数据 - 按照HTML版本逻辑
const getCellData = (row: any, column: string, colIndex: number): any => {
  // 如果excelPreviewData中的数据是二维数组，则直接按索引访问
  // 如果是对象数组，则按列名访问
  return Array.isArray(row) ? (row[colIndex] !== undefined ? row[colIndex] : '') : (row[column] !== undefined ? row[column] : '');
};

// 格式化单元格值显示 - 按照HTML版本逻辑
const formatCellValue = (cellData: any): string => {
  if (cellData === null || cellData === undefined) {
    return '';
  }
  
  // 处理新的单元格数据格式：包含样式信息的对象
  if (typeof cellData === 'object' && cellData !== null && Object.prototype.hasOwnProperty.call(cellData, 'text')) {
    return String(cellData.text || '');
  }
  
  // 处理旧格式：直接显示文本
  return String(cellData || '');
};

// 获取单元格样式 - 按照HTML版本逻辑
const getCellStyle = (cellData: any) => {
  // 如果不是包含样式信息的对象，返回空样式
  if (typeof cellData !== 'object' || cellData === null || !Object.prototype.hasOwnProperty.call(cellData, 'text')) {
    return {};
  }
  
  const styles: any = {};
  
  // 应用样式 - 完全按照HTML版本的逻辑
  if (cellData.background_color) {
    styles.backgroundColor = cellData.background_color;
  }
  if (cellData.text_color) {
    styles.color = cellData.text_color;
  }
  if (cellData.font_name) {
    styles.fontFamily = cellData.font_name;
  }
  if (cellData.font_size) {
    styles.fontSize = cellData.font_size + 'px';
  }
  if (cellData.font_bold) {
    styles.fontWeight = 'bold';
  }
  if (cellData.font_italic) {
    styles.fontStyle = 'italic';
  }
  if (cellData.font_underline) {
    styles.textDecoration = 'underline';
  }
  if (cellData.horizontal_align) {
    styles.textAlign = cellData.horizontal_align;
  }
  if (cellData.vertical_align) {
    styles.verticalAlign = cellData.vertical_align;
  }
  
  return styles;
};

// 处理单元格点击 - 按照HTML版本逻辑
const handleCellClick = (event: Event, rowIndex: number, colIndex: number) => {
  // 简化的单元格选择逻辑
  const cellAddress = `${String.fromCharCode(65 + colIndex)}${rowIndex + 1}`;
  selectedCellRange.value = cellAddress;
};

// 处理重试
const handleRetry = () => {
  if (props.dataSource) {
    openDataPreviewModal(props.dataSource.id);
  }
};

// 处理关闭
const handleClose = () => {
  emit('close');
};

// 处理遮罩层点击
const handleOverlayClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    handleClose();
  }
};
</script>

<style scoped>
/* 模态框基础样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  color: #8c8c8c;
  transition: all 0.2s ease;
  font-size: 24px;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #595959;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.preview-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 数据加载和错误状态样式已移至 .data-loading-container 和 .data-error-container */

/* 数据源控制区域样式 */
.data-source-controls {
  margin-bottom: 16px;
}

/* 选择器容器样式 */
.selectors-container {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

/* 文件选择器样式 */
.file-selector {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-selector.inline {
  margin-bottom: 0;
}

/* 工作表选择器样式 */
.sheet-selector {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sheet-selector.inline {
  margin-bottom: 0;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.file-select,
.sheet-select {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  min-width: 200px;
  outline: none;
}

.file-select:hover,
.sheet-select:hover {
  border-color: #40a9ff;
}

.file-select:focus,
.sheet-select:focus {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.file-select:disabled,
.sheet-select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  color: #999;
}

.sheet-loading-indicator {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  font-size: 12px;
  color: #1890ff;
}

.sheet-loading-indicator i {
  animation: spin 1s linear infinite;
  font-size: 12px;
}

/* 数据预览容器样式 */
.data-preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

/* 数据加载状态样式 */
.data-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  min-height: 300px;
}

.data-loading-container .loading-spinner {
  margin-bottom: 16px;
}

.data-loading-container .loading-spinner i {
  font-size: 32px;
  color: #1890ff;
  animation: spin 1s linear infinite;
}

.data-loading-container .loading-text {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 500;
}

/* 数据错误状态样式 */
.data-error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  min-height: 300px;
}

.data-error-container .error-icon {
  margin-bottom: 16px;
}

.data-error-container .error-icon i {
  font-size: 48px;
  color: #ff4d4f;
}

.data-error-container .error-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.data-error-container .error-message {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #8c8c8c;
  max-width: 400px;
}

.data-error-container .btn {
  margin-top: 8px;
}

.table-preview-wrapper {
  overflow: auto;
  max-height: 400px;
  border: 1px solid #ddd;
}

/* 数据表格样式 - 按照HTML版本 */
.preview-table {
  border-collapse: collapse;
  min-width: 100%;
  background-color: white;
}

.preview-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 2px solid #dee2e6;
  min-width: 80px;
}

.preview-table td, .preview-table th {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  font-size: 13px;
}

.preview-table .data-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
}

.preview-table tr:hover {
  background-color: #f8f9fa;
}

.preview-table .data-cell:hover {
  overflow: visible !important;
  white-space: pre-wrap !important;
  word-wrap: break-word;
  background-color: #fff3cd !important;
  border: 2px solid #ffc107 !important;
  z-index: 100;
  position: relative;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  padding: 8px 12px;
  min-width: max-content;
}

.preview-table .clickable-cell {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.preview-table .clickable-cell:hover {
  background-color: #e3f2fd !important;
}

.row-number-header,
.row-number-cell {
  width: 60px;
  text-align: center;
  background: #f8f9fa;
  font-weight: 600;
  color: #8c8c8c;
}

.column-header-cell {
  min-width: 120px;
  max-width: 200px;
}

.cell-content {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 选择信息样式 */
.selection-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid #dee2e6;
  margin-top: 10px;
}

.selection-info p {
  margin: 0;
  font-size: 14px;
}

.empty-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-icon i {
  font-size: 48px;
  color: #d9d9d9;
}

.empty-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.empty-message {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  min-width: 80px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
  border-color: #40a9ff;
}

.btn-outline {
  background: white;
  border-color: #1890ff;
  color: #1890ff;
}

.btn-outline:hover:not(:disabled) {
  background: #f0f8ff;
}

.btn-secondary {
  background: white;
  border-color: #d9d9d9;
  color: #595959;
}

.btn-secondary:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #40a9ff;
  color: #1890ff;
}

.btn-success {
  background: #52c41a;
  border-color: #52c41a;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #73d13d;
  border-color: #73d13d;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-container {
    margin: 10px;
    max-width: none;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .data-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .columns-list {
    grid-template-columns: 1fr;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
  
  .btn {
    width: 100%;
  }
}
</style>