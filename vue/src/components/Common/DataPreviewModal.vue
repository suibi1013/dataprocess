<template>
  <el-dialog v-model="dialogVisible" title="数据预览与区域选择" :width="'95%'" :top="'5vh'" :close-on-click-modal="false"
    :close-on-press-escape="false" class="data-preview-modal">
    <template #header>
      <div class="modal-header">
        <h3>数据预览与区域选择</h3>
      </div>
    </template>

    <div v-loading="isLoading" element-loading-text="正在加载数据，请稍候..."
      element-loading-background="rgba(255, 255, 255, 0.8)" class="modal-body">
      <!-- 工作表选择下拉列表 -->
      <div class="sheet-selection">
        <div class="flex items-center gap-2">
          <el-select v-model="selectedSheet" placeholder="请选择工作表" style="width: 240px">
            <el-option v-for="sheet in sheetsList" :key="sheet" :label="sheet" :value="sheet" />
          </el-select>
          <el-button type="primary" @click="handleSheetChange" :loading="isLoading" style="margin: 0px 10px">
            加载数据
          </el-button>
        </div>
      </div>
      <!-- 数据表格容器 -->
      <div class="table-container">
        <div v-if="sheetData && sheetData.columns && sheetData.rows" class="table-wrapper">
          <table id="selectableTable" class="selectable-data-table" @mousedown="handleMouseDown"
            @mousemove="handleMouseMove" @mouseup="handleMouseUp" @selectstart.prevent>
            <thead>
              <tr>
                <th class="row-number-header">行号</th>
                <th v-for="(col, index) in sheetData.columns" :key="index" :data-col-index="index" :data-col-name="col">
                  {{ col }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in sheetData.rows" :key="rowIndex" :data-row-index="rowIndex">
                <td class="row-number">{{ rowIndex + 1 }}</td>
                <td v-for="(col, colIndex) in sheetData.columns" :key="colIndex" class="selectable-cell"
                  :data-row="rowIndex" :data-col="colIndex" :data-col-name="col"
                  :style="getCellBackgroundStyle(row[col])">
                  <!-- 处理单元格数据，如果是包含样式的对象则提取文本内容并应用样式 -->
                  <span :style="getCellTextStyle(row[col])">
                    {{ getCellContent(row[col]) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-data">
            <el-empty>
              请点击加载数据按钮加载数据
            </el-empty>
          </div>
        </div>
        <!-- 分页控件 -->
        <div v-if="sheetData" class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100, 200]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalRows"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

    <template #footer>
      <div class="selection-actions">
        <div class="bottom-selection-status" :class="{ 'has-selection': hasValidSelection }">
          已选择区域：{{ selectionStatusText }}
        </div>
        <el-button @click="handleClearSelection">清除选择</el-button>
        <el-button type="primary" @click="handleConfirm">
          确认选择
        </el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { ElDialog, ElButton, ElEmpty, ElSelect, ElOption } from 'element-plus';
import type { SheetData, DataSelection, SelectionState, CellData } from '@/types/dataExtraction';
import { dataSourceService } from '@/services/dataExtractionService';

// Props
interface Props {
  /** 模态框显示状态 */
  visible: boolean;
  /** 文件路径 */
  filePath: string;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  filePath: ''
});

// Emits
interface Emits {
  /** 更新显示状态 */
  (_e: 'update:visible', _visible: boolean): void;
  /** 确认选择数据区域 */
  (_e: 'confirm-selection', _selection: DataSelection): void;
  /** 确认选择工作表 */
  (_e: 'confirm-sheet', _sheetName: string): void;
  /** 取消 */
  (_e: 'cancel'): void;
  /** 更新工作表数据 */
  (_e: 'update-sheet-data', _sheetData: SheetData | null): void;
}

const emit = defineEmits<Emits>();

// 处理确认选择（同时确认工作表和数据区域）
  const handleConfirm = () => {
    // 首先确认工作表选择
    emit('confirm-sheet', selectedSheet.value);
    // 如果有数据区域选择，也确认数据区域
    if (hasValidSelection.value && selectionState.value.currentSelection) {
      // 确保传递的选择对象包含sheetName属性
      const selectionWithSheetName: DataSelection = {
        ...selectionState.value.currentSelection,
        sheetName: selectedSheet.value // 添加sheetName属性，值为当前选中的工作表名称
      };
      emit('confirm-selection', selectionWithSheetName);
    }
  };

// 本地状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
});

// 工作表列表
const sheetsList = ref<string[]>([]);

// 当前选中的工作表
const selectedSheet = ref('');

// 工作表数据
const sheetData = ref<SheetData | null>(null);

// 加载状态
const isLoading = ref(false);

// 分页相关状态
const currentPage = ref(1);
const pageSize = ref(50);
const totalPages = ref(1);
const totalRows = ref(0);

// 选择状态
const selectionState = ref<SelectionState>({
  isSelecting: false,
  startCell: null,
  endCell: null,
  currentSelection: null
});

// 鼠标状态
const isMouseDown = ref(false);

// 选择状态文本
const selectionStatusText = computed(() => {
  const selection = selectionState.value.currentSelection;
  if (!selection) {
    return '--暂无选择区域--';
  }

  return ` ${selection.start_column}${selection.start_row}:${selection.end_column}${selection.end_row}`;
});

// 是否有有效选择
const hasValidSelection = computed(() => {
  return !!selectionState.value.currentSelection;
});

/**
 * 处理鼠标按下事件
 */
const handleMouseDown = (event: MouseEvent) => {
  const cell = (event.target as HTMLElement).closest('.selectable-cell') as HTMLElement;
  if (!cell) return;

  event.preventDefault();
  isMouseDown.value = true;

  const row = parseInt(cell.dataset.row || '0');
  const col = parseInt(cell.dataset.col || '0');

  selectionState.value.isSelecting = true;
  selectionState.value.startCell = { row, col };
  selectionState.value.endCell = { row, col };

  updateSelection();
};

/**
 * 处理鼠标移动事件
 */
const handleMouseMove = (event: MouseEvent) => {
  if (!isMouseDown.value || !selectionState.value.isSelecting) return;

  const cell = (event.target as HTMLElement).closest('.selectable-cell') as HTMLElement;
  if (!cell) return;

  const row = parseInt(cell.dataset.row || '0');
  const col = parseInt(cell.dataset.col || '0');

  selectionState.value.endCell = { row, col };
  updateSelection();
};

/**
 * 处理鼠标释放事件
 */
const handleMouseUp = () => {
  isMouseDown.value = false;
  selectionState.value.isSelecting = false;
};

/**
 * 更新选择区域
 */
const updateSelection = () => {
  const { startCell, endCell } = selectionState.value;
  if (!startCell || !endCell || !sheetData.value) return;

  // 计算选择区域
  const minRow = Math.min(startCell.row, endCell.row);
  const maxRow = Math.max(startCell.row, endCell.row);
  const minCol = Math.min(startCell.col, endCell.col);
  const maxCol = Math.max(startCell.col, endCell.col);

  // 获取列名
  const columns = sheetData.value.columns;
  const start_column = columns[minCol] || 'A';
  const end_column = columns[maxCol] || 'A';

  // 更新选择状态
  selectionState.value.currentSelection = {
    start_row: minRow + 1, // 转换为1基索引
    end_row: maxRow + 1,
    start_column,
    end_column,
    startColIndex: minCol,
    endColIndex: maxCol
  };

  // 更新表格样式
  updateTableSelection(minRow, maxRow, minCol, maxCol);
};

/**
 * 更新表格选择样式
 */
const updateTableSelection = (minRow: number, maxRow: number, minCol: number, maxCol: number) => {
  // 清除之前的选择样式
  const allCells = document.querySelectorAll('.selectable-cell');
  allCells.forEach(cell => {
    cell.classList.remove('selected', 'selection-start', 'selection-end');
  });

  // 添加新的选择样式
  for (let row = minRow; row <= maxRow; row++) {
    for (let col = minCol; col <= maxCol; col++) {
      const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
      if (cell) {
        cell.classList.add('selected');

        if (row === minRow && col === minCol) {
          cell.classList.add('selection-start');
        }
        if (row === maxRow && col === maxCol) {
          cell.classList.add('selection-end');
        }
      }
    }
  }
};

/**
 * 清除选择
 */
const handleClearSelection = () => {
  resetSelection();

  // 清除表格样式
  const allCells = document.querySelectorAll('.selectable-cell');
  allCells.forEach(cell => {
    cell.classList.remove('selected', 'selection-start', 'selection-end');
  });
};

/**
 * 重置选择状态
 */
const resetSelection = () => {
  selectionState.value = {
    isSelecting: false,
    startCell: null,
    endCell: null,
    currentSelection: null
  };
};

/**
 * 取消
 */
const handleCancel = () => {
  emit('cancel');
};

// 监听模态框显示状态变化
watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      // 重置选择状态
      resetSelection();

      // 重置工作表列表和选中状态
      sheetsList.value = [];
      selectedSheet.value = '';

      // 等待DOM更新后初始化
      await nextTick();

      // 如果文件路径存在，获取工作表列表
      if (props.filePath) {
        await loadSheetsList();
      }
    }
  }
);

// 监听工作表选择变化，清空数据表格
watch(
  () => selectedSheet.value,
  () => {
    // 当工作表变化时，清空数据表格
    sheetData.value = null;
    // 同时重置选择状态
    resetSelection();
    // 重置分页状态
    currentPage.value = 1;
    totalRows.value = 0;
    totalPages.value = 1;
  }
);

/**
 * 加载工作表列表
 */
const loadSheetsList = async () => {
  if (!props.filePath) return;

  isLoading.value = true;
  try {
    // 调用API获取工作表列表
    const response = await dataSourceService.getFileSheets(props.filePath);
    if (response.success) {
      sheetsList.value = response.data.sheets || [];
      // 如果有工作表，默认选择第一个
      if (sheetsList.value.length > 0 && !selectedSheet.value) {
        selectedSheet.value = sheetsList.value[0];
        // 不再自动加载数据，等待用户点击加载数据按钮
      }
    } else {
      console.error('获取工作表列表失败:', response.error);
      sheetsList.value = [];
    }
  } catch (error) {
    console.error('获取工作表列表异常:', error);
    sheetsList.value = [];
  } finally {
    isLoading.value = false;
  }
};

/**
 * 处理工作表切换
 */
const handleSheetChange = async () => {
  // 重置页码
  currentPage.value = 1;
  // 加载数据
  await loadSheetData();
};

/**
 * 加载工作表数据
 */
const loadSheetData = async () => {
  const sheetName = selectedSheet.value;
  if (sheetName && props.filePath) {
    isLoading.value = true;
    try {
      // 调用API获取工作表数据
      const response = await dataSourceService.getDataSourceDataByFilePath(props.filePath, sheetName, currentPage.value, pageSize.value);
      if (response.success) {
        // 更新工作表数据
        sheetData.value = response.data;
        // 更新分页信息
        if (response.data) {
          totalRows.value = response.data.total_rows || 0;
          totalPages.value = response.data.total_pages || 1;
        }
      } else {
        console.error('获取工作表数据失败:', response.error);
        sheetData.value = null;
        totalRows.value = 0;
        totalPages.value = 1;
      }
    } catch (error) {
      console.error('获取工作表数据异常:', error);
      sheetData.value = null;
      totalRows.value = 0;
      totalPages.value = 1;
    } finally {
      isLoading.value = false;
    }
  }
};

/**
 * 处理页码变化
 */
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadSheetData();
};

/**
 * 处理每页行数变化
 */
const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadSheetData();
};

/**
 * 获取单元格内容
 * 如果是包含样式信息的对象，则返回text属性
 * 否则直接返回值
 */
const getCellContent = (cellData: any): string => {
  if (typeof cellData === 'object' && cellData !== null && 'text' in cellData) {
    return cellData.text || '';
  }
  return cellData || '';
};

/**
 * 获取单元格文本样式对象
 * 提取字体相关的样式属性
 */
const getCellTextStyle = (cellData: any): Record<string, string> => {
  const style: Record<string, string> = {};

  if (typeof cellData === 'object' && cellData !== null && 'text' in cellData) {
    const cellObj = cellData as CellData;

    // 应用字体样式
    if (cellObj.font_name) style.fontFamily = cellObj.font_name;
    if (cellObj.font_size) style.fontSize = `${cellObj.font_size}px`;
    if (cellObj.font_color) style.color = cellObj.font_color;
    if (cellObj.font_bold) style.fontWeight = 'bold';
    if (cellObj.font_italic) style.fontStyle = 'italic';
    if (cellObj.font_underline) style.textDecoration = 'underline';
  }

  return style;
};

/**
 * 获取单元格背景样式对象
 * 提取背景、对齐和边框相关的样式属性
 */
const getCellBackgroundStyle = (cellData: any): Record<string, string> => {
  const style: Record<string, string> = {};

  if (typeof cellData === 'object' && cellData !== null && 'text' in cellData) {
    const cellObj = cellData as CellData;

    // 应用背景颜色
    if (cellObj.background_color) style.backgroundColor = cellObj.background_color;

    // 应用对齐方式
    if (cellObj.horizontal_align) style.textAlign = cellObj.horizontal_align;
    if (cellObj.vertical_align) style.verticalAlign = cellObj.vertical_align;

    // 应用边框样式
    if (cellObj.border_top?.style !== 'none') {
      style.borderTop = `${cellObj.border_top?.width}px ${cellObj.border_top?.style} ${cellObj.border_top?.color}`;
    }
    if (cellObj.border_bottom?.style !== 'none') {
      style.borderBottom = `${cellObj.border_bottom?.width}px ${cellObj.border_bottom?.style} ${cellObj.border_bottom?.color}`;
    }
    if (cellObj.border_left?.style !== 'none') {
      style.borderLeft = `${cellObj.border_left?.width}px ${cellObj.border_left?.style} ${cellObj.border_left?.color}`;
    }
    if (cellObj.border_right?.style !== 'none') {
      style.borderRight = `${cellObj.border_right?.width}px ${cellObj.border_right?.style} ${cellObj.border_right?.color}`;
    }
  }

  return style;
};
</script>

<style scoped>
.data-preview-modal :deep(.el-dialog) {
  height: 90vh;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.data-preview-modal :deep(.el-dialog__body) {
  flex: 1;
  padding: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.modal-body {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 1px;
}

.sheet-selection {
  padding: 0px 10px;
  margin-bottom: 10px;
}

.sheet-selection .el-select {
  font-size: 12px;
}

.sheet-tabs {
  display: flex;
  gap: 6px;
  padding: 0px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  overflow-x: auto;
}

.sheet-tab {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  color: #606266;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.sheet-tab:hover {
  color: #409eff;
  border-color: #c6e2ff;
}

.sheet-tab.active {
  color: #409eff;
  border-color: #409eff;
  background: #ecf5ff;
}

.selection-info {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.selection-tip {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.selection-status {
  font-weight: 600;
  font-size: 14px;
  color: #909399;
  transition: color 0.3s;
}

.selection-status.has-selection {
  color: #409eff;
}

.table-container {
  overflow: auto;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fff;
}

.table-wrapper {
  min-width: 100%;
  height: 100%;
}

.selectable-data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  user-select: none;
}

.selectable-data-table th,
.selectable-data-table td {
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.selectable-data-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #606266;
  position: sticky;
  top: 0;
  z-index: 10;
}

.row-number-header,
.row-number {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #909399;
  text-align: center;
  min-width: 60px;
  position: sticky;
  left: 0;
  z-index: 5;
}

.row-number-header {
  z-index: 15;
}

.selectable-cell {
  cursor: crosshair;
  transition: background-color 0.2s;
}

.selectable-cell:hover {
  background-color: #f0f9ff;
}

.selectable-cell.selected {
  background-color: #e1f5fe !important;
  border-color: #409eff !important;
}

.selectable-cell.selection-start {
  background-color: #bbdefb !important;
  border: 2px solid #409eff !important;
}

.selectable-cell.selection-end {
  background-color: #bbdefb !important;
  border: 2px solid #409eff !important;
}

.empty-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.selection-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 选择状态提示样式 - 位于清除选择按钮左侧 */
.bottom-selection-status {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  margin-right: 12px;
  align-self: center;
  white-space: nowrap;
}

.bottom-selection-status.has-selection {
  color: #409eff;
  border-color: #409eff;
  background: rgba(236, 245, 255, 0.95);
}

/* 数据表格容器样式 - 设置高度为屏幕区域高度的60% */
.table-container {
  height: 60vh;
  overflow: auto;
}

/* 滚动条样式 */
.table-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 分页容器样式 */
.pagination-container {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 10px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
  border-radius: 0 0 6px 6px;
}

.pagination-container :deep(.el-pagination) {
  margin: 0;
}
</style>