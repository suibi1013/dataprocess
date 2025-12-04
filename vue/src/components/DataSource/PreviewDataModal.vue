<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h2>Excel数据预览</h2>
        <button type="button" class="close-btn" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div class="preview-section">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
            <div class="loading-spinner">
              <i class="el-icon-loading"></i>
            </div>
            <p class="loading-text">正在加载数据...</p>
          </div>
          
          <!-- 错误状态 -->
          <div v-else-if="error" class="error-container">
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
          
          <!-- Excel风格工作表标签 -->
          <div v-else-if="allSheetsData && Object.keys(allSheetsData).length > 0" class="sheet-tabs-container">
            <div class="sheet-tabs">
              <div 
                v-for="sheetName in Object.keys(allSheetsData)" 
                :key="sheetName"
                class="sheet-tab"
                :class="{ active: currentSelectedSheet === sheetName }"
                @click="selectSheetTab(sheetName)"
              >
                {{ sheetName }}
              </div>
            </div>
            <div class="add-sheet-tab">+</div>
          </div>
          
          <!-- 数据预览容器 -->
          <div v-if="excelPreviewData.length > 0" class="data-preview-container">
            <div class="table-preview-wrapper">
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
          </div>
          <!-- 无数据状态 -->
          <div  v-if="excelPreviewData.length == 0 && !loading && !error" class="empty-data">
            <div class="empty-icon">
              <i class="el-icon-document-empty"></i>
            </div>
            <h4 class="empty-title">暂无数据</h4>
            <p class="empty-message">该数据源中没有找到任何数据</p>
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

// 单元格选择相关状态（暂时注释，后续实现时启用）
// const isSelecting = ref(false);
// const startCell = ref<{row: number, col: number} | null>(null);
// const lastCell = ref<{row: number, col: number} | null>(null);

// 监听弹窗显示状态和数据源变化
watch([() => props.visible, () => props.dataSource], ([visible, dataSource]) => {
  if (visible && dataSource) {
    openDataPreviewModal(dataSource.id);
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

// 打开数据预览模态框 - 优化为优先使用缓存
const openDataPreviewModal = async (dataSourceId: string) => {
  loading.value = true;
  error.value = '';
  
  // 清空选择状态
  selectedCellRange.value = '';
  
  try {
    let data = null;
    
    // 优先从缓存获取数据
    if (dataSourceInfoCache.value.has(dataSourceId)) {
      const cachedData = dataSourceInfoCache.value.get(dataSourceId);
      
      // 将缓存数据转换为预览模态框需要的格式
      if (cachedData) {
        data = {
          success: true,
          data: cachedData
        };
      } 
    }
    
    // 如果缓存中没有数据，则调用API（兜底方案）
    if (!data) {      
      data = await httpClient.get(`/datasource/${encodeURIComponent(dataSourceId)}/data`);
      
      // 将API响应数据存入缓存
      if (data.success) {
        dataSourceInfoCache.value.set(dataSourceId, data.data);
      }
    }
    
    if (data.success && data.data && data.data.data && Object.keys(data.data.data).length > 0) {
      // 存储所有工作表数据
      allSheetsData.value = data.data.data;
      
      // 默认选择第一个工作表
      const sheetNames = Object.keys(data.data.data);
      if (sheetNames.length > 0) {
        const firstSheet = sheetNames[0];
        currentSelectedSheet.value = firstSheet;
        
        // 直接使用返回的数据渲染表格
        const sheetData = data.data.data[firstSheet] || {};
        
        // 直接使用原始行数据
        excelPreviewData.value = mergeRowsWithStyles(sheetData.rows || []);
        excelPreviewColumns.value = sheetData.columns || [];
      }
    } else {
      throw new Error('未找到工作表或工作表为空');
    }
  } catch (err) {
    console.error('加载工作表失败:', err);
    error.value = err instanceof Error ? err.message : '加载工作表失败';
  } finally {
    loading.value = false;
  }
};

// 选择工作表标签 - 按照HTML版本逻辑
const selectSheetTab = (sheetName: string) => {
  if (!sheetName || !allSheetsData.value[sheetName]) {
    return;
  }
  
  // 更新当前选中的工作表
  currentSelectedSheet.value = sheetName;
  selectedCellRange.value = '';
  
  // 从缓存数据中加载选中工作表的数据
  const sheetData = allSheetsData.value[sheetName];
  
  // 直接使用原始行数据
  excelPreviewData.value = mergeRowsWithStyles(sheetData.rows || []);
  excelPreviewColumns.value = sheetData.columns || [];
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

// // 确认数据源选择
// const confirmDataSourceSelection = () => {
//   if (!selectedCellRange.value) {
//     return;
//   }
  
//   // 这里可以添加确认选择的逻辑
//   handleClose();
// };

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

/* 加载和错误状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  margin-bottom: 16px;
}

.loading-spinner i {
  font-size: 32px;
  color: #1890ff;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin: 0;
  font-size: 16px;
  color: #595959;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.error-icon {
  margin-bottom: 16px;
}

.error-icon i {
  font-size: 48px;
  color: #ff4d4f;
}

.error-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.error-message {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #8c8c8c;
  max-width: 400px;
}

/* Excel风格工作表标签样式 */
.sheet-tabs-container {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ddd;
  margin-bottom: 2px;
  background-color: #f8f9fa;
  padding: 0 5px;
  position: relative;
  height: 32px;
}

.sheet-tabs {
  display: flex;
  overflow-x: auto;
  flex: 1;
  white-space: nowrap;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.sheet-tabs::-webkit-scrollbar {
  display: none;
}

.sheet-tab {
  padding: 5px 15px;
  margin-right: 2px;
  background-color: #e0e0e0;
  border: 1px solid #ccc;
  border-bottom: none;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-family: Arial, sans-serif;
  height: 25px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.sheet-tab:hover {
  background-color: #f0f0f0;
}

.sheet-tab.active {
  background-color: white;
  border-bottom: 1px solid white;
  z-index: 1;
  position: relative;
}

.add-sheet-tab {
  width: 25px;
  height: 25px;
  background-color: #e0e0e0;
  border: 1px solid #ccc;
  border-bottom: none;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  margin-left: 5px;
  transition: background-color 0.2s;
}

.add-sheet-tab:hover {
  background-color: #f0f0f0;
}

/* 数据预览容器样式 */
.data-preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
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