<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" :class="{ 'maximized': isMaximized }" @click.stop>
      <div class="modal-header">
        <div class="header-left">
          <h3 class="modal-title">流程配置设计器</h3>
        </div>
        <div class="header-right">
          <button class="maximize-btn" @click="toggleMaximize">
            <el-icon v-if="!isMaximized"><FullScreen /></el-icon>
            <el-icon v-else><Refresh /></el-icon>
          </button>
          <button class="close-btn" @click="handleClose">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>
      
      <!-- 数据预览模态框 -->
      <DataPreviewModal
        :visible="showPreviewModal"
        :sheet-data="previewSheetData"
        :sheet-name="previewSheetName"
        :available-sheets="getAvailableSheets()"
        :current-sheet="previewSheetName"
        :loading="previewLoading"
        @confirm-selection="handleDataSelectionConfirm"
        @confirm-sheet="confirmSheetSelection"
        @sheet-change="handleSheetChange"
        @cancel="handleDataSelectionCancel"
        @close="showPreviewModal = false"
      />
      
      <!-- 指令执行结果模态框 -->
      <ExecutionResultModal
        :visible="showResultModal"
        :result-modal-data="resultModalData"
        :active-tab="activeTab"
        @update:visible="(visible) => { showResultModal = visible }"
        @update:active-tab="(tab) => { activeTab = tab }"
        @handle-result-modal-ok="handleResultModalOk"
      />
      
      <div class="modal-body">
        <!-- 数据处理工作区 -->
        <div class="data-process-workspace">
          <!-- 数据加载遮罩层 -->
          <div v-if="modalState.dataLoading" class="data-loading-overlay">
            <div class="loading-content">
              <div class="loading-spinner">
                <el-icon><Loading /></el-icon>
              </div>
              <div class="loading-text">
                <h4>正在加载流程数据...</h4>
                <p>请稍候，数据加载完成后即可开始设计流程</p>
              </div>
            </div>
          </div>
          
          <!-- 左侧指令面板 -->
          <div class="panel-wrapper instruction-panel-wrapper" :class="{ 'collapsed': isInstructionPanelCollapsed }">
            <InstructionPanel 
              :instruction-categories="displayInstructionCategories"
              :instruction-loading="instructionLoading"
              @instruction-drag-start="handleInstructionDragStart"
            />
            <!-- 折叠/展开按钮 -->
            <div class="panel-collapse-btn" @click="toggleInstructionPanel" :title="isInstructionPanelCollapsed ? '展开指令面板' : '折叠指令面板'">
              <el-icon>{{ isInstructionPanelCollapsed ? '>' : '<' }}</el-icon>
            </div>
          </div>
          
          <!-- 中间画布区域 -->
          <ProcessCanvas 
            :canvas-initialized="canvasInitialized"
            :selectedNode="canvasSelectedNode"
            :selectedEdge="canvasSelectedEdge"
            :params-panel="paramsPanelState"
            @node-selected="handleNodeSelected"
            @edge-selected="handleEdgeSelected"
          />
          
          <!-- 右侧参数面板 -->
          <div class="panel-wrapper parameter-panel-wrapper" :class="{ 'collapsed': isParameterPanelCollapsed }">
            <ParameterPanel 
              :paramsPanel="paramsPanelState"
              :instructionCategories="displayInstructionCategories"
              :canvas-graph="canvasGraph"
              @update-node="handleNodeUpdate"
              @update-edge="handleEdgeUpdate"
              @instruction-executed="handleInstructionExecuted"
              @show-data-preview="handleShowDataPreview"
            />
            <!-- 折叠/展开按钮 -->
            <div class="panel-collapse-btn" @click="toggleParameterPanel" :title="isParameterPanelCollapsed ? '展开参数面板' : '折叠参数面板'">
              <el-icon>{{ isParameterPanelCollapsed ? '<' : '>' }}</el-icon>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">

        <button 
          type="button" 
          class="btn btn-primary"
          :disabled="isExecuting"
          @click="executeProcess"
        >
          <i v-if="isExecuting" class="icon-loading"></i>
          <i v-else class="icon-play"></i>
          {{ isExecuting ? '执行中...' : '执行流程' }}
        </button>
        <button 
          type="button" 
          class="btn btn-success"
          @click="saveProcess"
        >
          <i class="icon-save"></i>
          保存流程
        </button>
        <button type="button" class="btn btn-secondary" @click="handleClose">
          <i class="icon-close"></i>
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useDataProcess } from '@/composables/useDataProcess';
import { useInstructionParams } from '@/composables/useInstructionParams';
import { httpClient } from '@/services/httpClient';
// ElementPlusIconsVue已移至InstructionPanel组件
// import { downloadFile } from '@/utils/fileUtils'; // 移除未使用的导入

import DataPreviewModal from '@/components/DataPreviewModal.vue';
  import ExecutionResultModal from '@/components/DataProcess/ExecutionResultModal.vue';
  import InstructionPanel from '@/components/DataProcess/InstructionPanel.vue';
  import ProcessCanvas from '@/components/DataProcess/ProcessCanvas.vue';
  import ParameterPanel from '@/components/DataProcess/ParameterPanel.vue';
  import type { SheetData, DataSelection } from '@/types/dataExtraction';
  import { ElIcon } from 'element-plus';
  import { Loading } from '@element-plus/icons-vue';
  import { downloadFile } from '@/utils/fileUtils';

// Props
interface Props {
  visible: boolean;
}

const props = defineProps<Props>();

// Emits
interface Emits {
  close: [];
  success: [];
}

const emit = defineEmits<Emits>();



// 使用数据处理组合式函数（单例模式）
const {
  executeProcess: runProcess,
  saveDataProcess: saveProcessConfig,
  clearCanvas,
  instructionCategories,
  instructionLoading,
  selectedNode: canvasSelectedNode,
  selectedEdge: canvasSelectedEdge,
  showDataProcessModal,
  hideDataProcessModal,
  resetDataProcessModal,
  resetExecutionState,
  modalState,
  canvasGraph
} = useDataProcess();

// 使用单例实例中的计算属性，确保状态同步
const isExecuting = computed(() => modalState.executing);

// 使用指令参数组合式函数
// 使用ref包装函数引用，避免组件更新时引用丢失
const instructionParamsRef = ref(useInstructionParams());
const {
  paramsPanel: paramsPanelState,
  showParamsPanel: showNodeParams,
  hideParamsPanel,
  setAvailableColumns,
  setInstructionCategories,
  updateParamValue: updateInstructionParam
} = instructionParamsRef.value;

// 使用本地数据或API数据
const displayInstructionCategories = computed(() => {
  return instructionCategories.value;
});

// 状态
const processing = ref(false);
const availableColumns = ref<string[]>([]);
const canvasInitialized = ref(false);
const showPreviewModal = ref(false);
const previewSheetData = ref<SheetData | null>(null);
const previewSheetName = ref('');
const previewLoading = ref(false);
// 窗口最大化状态
const isMaximized = ref(false);
// 面板折叠状态
const isInstructionPanelCollapsed = ref(false);
const isParameterPanelCollapsed = ref(false);

// 监听showPreviewModal变化，优化数据加载策略
watch(
  () => showPreviewModal.value,
  async (newValue) => {
    // 当showPreviewModal变为true时，尝试获取实际数据
    if (newValue) {
      previewLoading.value = true;
      
      try {
        // 如果没有实际数据，设置为空状态，不使用测试数据
        if (!previewSheetData.value) {
          console.warn('No actual data available');
          previewSheetData.value = {
            columns: [],
            rows: []
          };
          previewSheetName.value = '无数据';
        }
      } catch (error) {
        console.error('Error loading preview data:', error);
        // 出错时设置为空状态
        if (!previewSheetData.value) {
          previewSheetData.value = {
            columns: [],
            rows: []
          };
          previewSheetName.value = '加载失败';
        }
      } finally {
        previewLoading.value = false;
      }
    }
  },
  { immediate: true }
);

// 结果模态框状态
const showResultModal = ref(false);
const activeTab = ref('finalResult'); // 默认选中最终结果标签页
const resultModalData = ref<{
  success: boolean;
  title: string;
  message: string;
  details?: string;
  finalResult?: string;
} | null>(null);


// 处理结果模态框确定按钮点击
const handleResultModalOk = () => {
  showResultModal.value = false;
  activeTab.value = 'finalResult'; // 重置选中的标签页，下次打开时默认显示最终结果
};
    
// 保存当前预览的参数名
const currentPreviewParamName = ref('');
// 保存当前预览的文件路径
const currentPreviewFilePath = ref('');

// 本地存储工作表列表的Map
const fileSheetsMap = ref(new Map());

// 获取可用工作表列表
const getAvailableSheets = () => {
  if (!currentPreviewFilePath.value) {
    return [];
  }
  
  const sheets = fileSheetsMap.value.get(currentPreviewFilePath.value) || [];
  
  // 确保返回的是基于sheet_name的工作表名称列表
  // 这个函数返回的列表将直接用于DataPreviewModal的标签显示
  return sheets;
};

// 设置文件的工作表列表
const setFileSheets = (filePath: string, sheets: string[]) => {
  fileSheetsMap.value.set(filePath, sheets);
};



// 生成缓存键的函数
const getCacheKey = (filePath) => `excel_data_${filePath}`;

// 从缓存中获取数据的函数
const getCachedData = (filePath) => {
  try {
    const cacheKey = getCacheKey(filePath);
    const cachedData = sessionStorage.getItem(cacheKey);
    if (cachedData) {
      return JSON.parse(cachedData);
    }
  } catch (error) {
    console.error('从缓存读取数据失败:', error);
  }
  return null;
};

// 将数据存入缓存的函数
const setCachedData = (filePath, data) => {
  try {
    const cacheKey = getCacheKey(filePath);
    sessionStorage.setItem(cacheKey, JSON.stringify(data));
  } catch (error) {
    console.error('写入缓存失败:', error);
  }
};

// 处理参数面板发出的数据预览请求
const handleShowDataPreview = async (previewData) => {
  if (!previewData.filePath) {
    return;
  }
  try {
    // 设置当前参数名和文件路径
    currentPreviewParamName.value = previewData.paramName || '';
    currentPreviewFilePath.value = previewData.filePath || '';
    
    // 立即显示预览窗口，初始状态为加载中
    previewLoading.value = true;
    showPreviewModal.value = true;
    
    // 首先尝试从缓存中获取数据
    const cachedResult = getCachedData(currentPreviewFilePath.value);
    if (cachedResult) {
      // 处理缓存的数据
      const apiData = cachedResult.data;
      let sheetData = null;
      
      // 查找数据对象中的第一个有效表格数据
      if (apiData.data && typeof apiData.data === 'object') {
        // 获取所有工作表名称，优先使用sheet_name属性
        const sheetNames = Object.values(apiData.data).map(sheet => sheet.sheet_name || Object.keys(apiData.data)[Object.values(apiData.data).indexOf(sheet)]);
        
        // 使用本地Map存储工作表列表
        setFileSheets(currentPreviewFilePath.value, sheetNames);
        
        // 获取第一个表格数据（假设只有一个表格或默认使用第一个）
        const firstSheetKey = sheetNames[0];
        if (firstSheetKey) {
          // 遍历找到与第一个工作表名称匹配的数据
          let foundSheetData = null;
          for (const [key, sheet] of Object.entries(apiData.data)) {
            if (sheet.sheet_name === firstSheetKey || key === firstSheetKey) {
              foundSheetData = sheet;
              break;
            }
          }
          
          if (foundSheetData) {
            sheetData = foundSheetData;
            // 设置工作表名称为显示名称（即sheetNames[0]），确保与标签页名称一致
            previewSheetName.value = firstSheetKey;
          }
        }
      }
      
      // 如果找到了表格数据，则设置预览数据
      if (sheetData) {
        previewSheetData.value = sheetData;
      } else {
        // 如果没有找到表格数据，设置空数据
        previewSheetData.value = { columns: [], rows: [] };
        previewSheetName.value = previewData.sheetName || 'Sheet1';
        console.warn('未找到有效的表格数据');
      }
      previewLoading.value = false;
      return;
    }
    
    // 如果缓存中没有数据，调用/api/file/excel_data_and_style接口获取数据
    const result = await httpClient.get(`/file/excel_data_and_style?file_path=${encodeURIComponent(currentPreviewFilePath.value)}`);
    
    // 将API返回的结果存入缓存
    setCachedData(currentPreviewFilePath.value, result);
      
      if (result.success && result.data) {
        // 从API返回的数据中提取正确的表格数据
        const apiData = result.data;
        let sheetData = null;
        
        // 查找数据对象中的第一个有效表格数据
        if (apiData.data && typeof apiData.data === 'object') {
          // 获取所有工作表名称，优先使用sheet_name属性
          const sheetNames = Object.values(apiData.data).map(sheet => sheet.sheet_name || Object.keys(apiData.data)[Object.values(apiData.data).indexOf(sheet)]);
          
          // 使用本地Map存储工作表列表
          setFileSheets(currentPreviewFilePath.value, sheetNames);
          
          // 获取第一个表格数据（假设只有一个表格或默认使用第一个）
          const firstSheetKey = sheetNames[0];
          if (firstSheetKey) {
            // 遍历找到与第一个工作表名称匹配的数据
            let foundSheetData = null;
            for (const [key, sheet] of Object.entries(apiData.data)) {
              if (sheet.sheet_name === firstSheetKey || key === firstSheetKey) {
                foundSheetData = sheet;
                break;
              }
            }
            
            if (foundSheetData) {
              sheetData = foundSheetData;
              // 设置工作表名称为显示名称（即sheetNames[0]），确保与标签页名称一致
              previewSheetName.value = firstSheetKey;
            }
          }
        }
        
        // 如果找到了表格数据，则设置预览数据
        if (sheetData) {
          previewSheetData.value = sheetData;
        } else {
          // 如果没有找到表格数据，设置空数据
          previewSheetData.value = { columns: [], rows: [] };
          previewSheetName.value = previewData.sheetName || 'Sheet1';
          console.warn('未找到有效的表格数据');
        }
      } else {
        console.error('获取数据失败:', result.message || '未知错误');
      }
  } catch (error) {
    console.error('显示数据预览失败:', error);
  } finally {
    previewLoading.value = false;
  }
};
    // 监听节点选择变化，更新变量列表
    watch(canvasSelectedNode, () => {
      // 变量选择器显示时，变量列表将通过后端接口获取
    });

// 监听弹窗显示状态（优化生命周期管理）
watch(() => props.visible, async (visible) => {
  try {
    if (visible) {
      // 直接调用showDataProcessModal进行初始化
      await showDataProcessModal();
      
      // 将已加载的指令数据传递给useInstructionParams
      setInstructionCategories(instructionCategories.value);
      
      // 初始化可用列为空数组
      availableColumns.value = [];
      setAvailableColumns([]);
      
      // 标记画布已初始化
      canvasInitialized.value = true;
    } else {
      // 模态框隐藏时清理
      availableColumns.value = [];
      canvasInitialized.value = false;
      clearCanvas();
      hideParamsPanel();
      resetDataProcessModal();
    }
  } catch (error) {
    console.error('处理模态框可见性变化时出现错误:', error);
  }
});

// datapath类型参数现在作为普通参数处理，不再需要特殊的watch监听器

// 使用useInstructionParams中导出的updateParamValue方法来确保参数面板UI同步更新
const updateParamValue = (paramName: string, value: any) => {
  // 调用解构出来的updateInstructionParam方法
  updateInstructionParam(paramName, value);
  // 通知画布更新
  canvasGraph.value?.trigger('node:updated', { node: paramsPanelState.selectedNode });
};



// 指令面板相关功能已移至InstructionPanel组件

// 处理指令拖拽开始
const handleInstructionDragStart = (event: DragEvent, instruction: any) => {
  if (event.dataTransfer) {
    // 设置拖拽数据
    event.dataTransfer.setData('application/json', JSON.stringify(instruction));
    event.dataTransfer.effectAllowed = 'copy';
    
    // 设置拖拽效果
    const dragImage = event.target as HTMLElement;
    if (dragImage) {
      event.dataTransfer.setDragImage(dragImage, dragImage.offsetWidth / 2, dragImage.offsetHeight / 2);
    }
  }
};

// 处理边更新
const handleEdgeUpdate = (eventData: { edge: any; label: string; logic_express: string; paramsPanel: any }) => {
  const { edge, label, logic_express, paramsPanel } = eventData;
  
  if (edge) {
    try {
      // 更新边的数据
      const edgeData = edge.getData() || {};
      edgeData.label = label;
      edgeData.logic_express = logic_express;
      edge.setData(edgeData);
      
      // 使用X6的API直接更新边的标签显示
      edge.setLabels([
        {
          position: 0.5,
          attrs: {
            text: {
              text: label,
              fill: '#333',
              fontSize: 10,
              textAnchor: 'middle',
              textVerticalAnchor: 'middle'
            },
            rect: {
              fill: 'white',
              stroke: '#ddd',
              strokeWidth: 1,
              rx: 4,
              ry: 4,
              padding: [4, 8]
            }
          }
        }
      ]);      
      
      // 更新参数面板状态
      Object.assign(paramsPanelState, paramsPanel);
      
    } catch (error) {
      console.error('❌ 边标签更新失败:', error);
    }
  }
};

/**
 * 处理数据选择确认
 */
const handleDataSelectionConfirm = (selection: DataSelection) => {
  // 查找当前选中的节点
  if (paramsPanelState.selectedNode) {
    const nodeData = paramsPanelState.selectedNode.getData();
    const updatedNodeData = {
      ...nodeData,
      params: {
        ...nodeData.params,
        sheetName:selection.sheetName,
        startRow: selection.startRow,
        endRow: selection.endRow,
        startColumn: selection.startColumn,
        endColumn: selection.endColumn        
      }
    };
    paramsPanelState.selectedNode.setData(updatedNodeData);
    // 将选中区域信息回写到参数设置表单
    updateParamValue('sheetName', selection.sheetName);
    updateParamValue('startRow', selection.startRow);
    updateParamValue('endRow', selection.endRow);
    updateParamValue('startColumn', selection.startColumn);
    updateParamValue('endColumn', selection.endColumn);
  }
  
  showPreviewModal.value = false;
};

/**
   * 处理数据选择取消
   */
  const handleDataSelectionCancel = () => {
    showPreviewModal.value = false;
  };

  /**
   * 处理指令执行结果
   */
  const handleInstructionExecuted = (resultData) => {
    // 设置结果模态框数据
    resultModalData.value = resultData;
    // 显示结果模态框
    showResultModal.value = true;
  };

// 变量和函数已在前面定义，避免重复声明



// 处理边选中事件
const handleEdgeSelected = (edge: any) => {
  // 直接更新paramsPanelState以确保响应性
  const edgeData = edge.getData() || {};
  const currentLabel = edgeData.label || '';
  const currentLogicExpress = edgeData.logic_express || '';
  
  paramsPanelState.selectedNode = null;
  paramsPanelState.selectedEdge = edge;
  paramsPanelState.params = { label: currentLabel, logic_express: currentLogicExpress };
  paramsPanelState.visible = true;
};

// 处理节点更新事件（从ParameterPanel组件接收）
const handleNodeUpdate = (nodeData: any) => {
  if (!canvasSelectedNode.value) return;
  
  const node = canvasSelectedNode.value;
  
  // 更新节点数据
  node.setData({
    ...node.getData(),
    ...nodeData
  });
  
  // 同时更新paramsPanelState中的params，确保props.paramsPanel.params值正确更新
  if (nodeData.params && paramsPanelState) {
    paramsPanelState.params = { ...nodeData.params };
    
    // 同步更新paramFormItems中的对应项值
    Object.entries(nodeData.params).forEach(([paramName, value]) => {
      const formItem = paramsPanelState.paramFormItems.find(
        item => item.param?.name === paramName || item.name === paramName
      );
      if (formItem) {
        formItem.value = value;
      }
    });
  }
  
  // 触发节点更新
  canvasGraph.value?.trigger('node:updated', { node });
};

// 处理工作表切换
const handleSheetChange = async (displaySheetName: string): Promise<void> => {
  if (!currentPreviewFilePath.value) return;
  
  // 设置loading状态
  previewLoading.value = true;
  
  try {
    // 从缓存中获取该文件的数据
    const cachedResult = getCachedData(currentPreviewFilePath.value);
    
    if (cachedResult && cachedResult.data && cachedResult.data.data) {
      // 尝试根据显示名称找到对应的工作表数据
      const allSheets = cachedResult.data.data;
      
      // 查找对应的工作表对象
      let targetSheetData = null;
      
      // 遍历所有工作表，查找匹配的sheet_name或键名
      for (const [key, sheet] of Object.entries(allSheets)) {
        if (sheet.sheet_name === displaySheetName || key === displaySheetName) {
          targetSheetData = sheet;
          break;
        }
      }
      
      if (targetSheetData) {
        // 找到工作表数据，直接使用
        previewSheetData.value = targetSheetData;
        previewSheetName.value = displaySheetName;
        return;
      }
    }
    
    // 如果缓存中没有找到对应的数据，需要重新请求API获取指定工作表的数据
    const result = await httpClient.get(
      `/file/excel_data_and_style?file_path=${encodeURIComponent(currentPreviewFilePath.value)}&sheet_name=${encodeURIComponent(displaySheetName)}`
    );
    
    if (result.success && result.data && result.data.data) {
      // 尝试直接获取指定名称的工作表
      let foundSheet = null;
      
      // 首先尝试精确匹配sheet_name
      for (const [key, sheet] of Object.entries(result.data.data)) {
        if (sheet.sheet_name === displaySheetName || key === displaySheetName) {
          foundSheet = sheet;
          break;
        }
      }
      
      // 如果找到工作表数据
      if (foundSheet) {
        previewSheetData.value = foundSheet;
        previewSheetName.value = displaySheetName;
      } else {
        // 降级处理：尝试使用第一个可用的工作表
        const firstSheetEntry = Object.entries(result.data.data)[0];
        if (firstSheetEntry && firstSheetEntry[1]) {
          previewSheetData.value = firstSheetEntry[1];
          previewSheetName.value = displaySheetName;
          console.warn(`未找到指定工作表"${displaySheetName}"，使用第一个可用工作表`);
        } else {
          // 设置空数据作为兜底
          previewSheetData.value = { columns: [], rows: [] };
          previewSheetName.value = displaySheetName;
          console.warn(`未找到任何工作表数据`);
        }
      }
    } else {
      // API返回失败或数据格式不正确
      console.error('获取数据失败:', result.message || '未知错误');
      // 设置空数据作为兜底
      previewSheetData.value = { columns: [], rows: [] };
      previewSheetName.value = displaySheetName;
    }
  } catch (error) {
    console.error('获取指定工作表数据失败:', error);
    // 发生错误时，设置空数据作为兜底
    previewSheetData.value = { columns: [], rows: [] };
    previewSheetName.value = displaySheetName;
  } finally {
    // 无论成功失败，都重置loading状态
    previewLoading.value = false;
  }
};

// 确认选择工作表并回写sheetName - 被DataPreviewModal组件的confirm-sheet事件调用
function confirmSheetSelection(displaySheetName) {
  // 保存当前预览的工作表名称
  if (displaySheetName) {
    previewSheetName.value = displaySheetName;
  }
  showPreviewModal.value = false;
}

// 切换指令分类功能已移至InstructionPanel组件

// 执行流程
const executeProcess = async () => {
  processing.value = true;
  isExecuting.value = true; // 设置执行中状态，禁用按钮并显示执行中效果
  
  try {
    // 执行流程并保存返回结果
    const result = await runProcess(); 
    
    if (result) {
      let finalResult;      
      // 处理结果数据
      if (result.data) {
        // 判断是否为文件流结果
        const resultData = result.data.result?.final_result || result.data;
        
        // 判断是否为文件流：检查是否包含特定的文件流标识字段
        if (resultData && typeof resultData === 'object' && 
            ('file_data' in resultData || 'file_content' in resultData) && 
            ('file_name' in resultData || resultData.filename)) {
          
          // 自动下载文件
          const filename = resultData.file_name || resultData.filename || 'download.dat';
          const fileData = resultData.file_data || resultData.file_content;
          
          // 根据数据类型进行适当的转换和下载
          try {
            // 如果是base64编码的数据，需要先解码
            if (typeof fileData === 'string' && fileData.startsWith('data:')) {
              // 已经是data URL格式
              const link = document.createElement('a');
              link.href = fileData;
              link.download = filename;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            } else if (typeof fileData === 'string') {
              // 假设是base64编码的字符串
              const binaryString = atob(fileData);
              const len = binaryString.length;
              const bytes = new Uint8Array(len);
              for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              downloadFile(bytes.buffer, filename);
            } else {
              // 直接下载
              downloadFile(fileData, filename);
            }
            
            // 不显示文件流数据，而是显示下载提示
            finalResult = `文件已自动下载: ${filename}`;
          } catch (error) {
            console.error('文件下载失败:', error);
            // 下载失败时显示原始数据
            finalResult = JSON.stringify(resultData, null, 2);
          }
        } else {
          // 非文件流，正常显示
          finalResult = JSON.stringify(resultData, null, 2);
        }
      }
      
      // 设置结果模态框数据 - 使用返回的执行结果
      resultModalData.value = {
        success: result.success,
        title: result.success ? '执行成功' : '执行失败',
        message: result.message || (result.success ? '流程执行完成！' : '流程执行失败'),
        details: result.data ? JSON.stringify(result.data, null, 2) : (result.message || undefined),
        finalResult: finalResult
      };
      if (!result.success) {
        resultModalData.value.finalResult = result.message;
      }

    } else {
      // 如果没有返回结果，使用默认的成功信息
      resultModalData.value = {
        success: true,
        title: '执行成功',
        message: '流程执行完成！',
        details: undefined,
        finalResult: undefined
      };
    }
    
    showResultModal.value = true;
    emit('success');
  } catch (error) {
    console.error('流程执行失败:', error);
    
    // 设置错误模态框数据
    resultModalData.value = {
      success: false,
      title: '执行失败',
      message: '流程执行失败',
      details: error instanceof Error ? error.message : '未知错误',
      finalResult: undefined
    };
    showResultModal.value = true;
  } finally {
    processing.value = false;
    isExecuting.value = false; // 重置执行状态，启用按钮
  }
};

// 保存数据处理流程
const saveDataProcess = async () => {
  try {
    // 使用已经从useDataProcess解构出的saveProcessConfig函数
    await saveProcessConfig();
    
    // 直接使用alert显示成功消息
    alert('数据处理流程保存成功！');
    
  } catch (error: any) {
    console.error('流程保存失败:', error);
    // 直接使用alert显示错误消息
    const errorMessage = error instanceof Error ? error.message : String(error);
    alert(`流程保存失败: ${errorMessage}`);
  }
};

// 查找指令信息函数已在上方定义

// 处理节点选中事件
const handleNodeSelected = (node: any) => {
  try {
    if (showNodeParams && node) {
      const nodeData = node.getData();
      if (nodeData && nodeData.instructionId) {
        const instruction = findInstructionById(nodeData.instructionId);
        if (instruction) {
          // 先调用showNodeParams方法来设置参数表单
          showNodeParams(node, instruction);
          
          // 然后直接更新paramsPanelState以确保响应性，特别是清除selectedEdge
          paramsPanelState.selectedNode = node;
          paramsPanelState.selectedEdge = null;
          paramsPanelState.visible = true;
        }
      }
    }
  } catch (error) {
    console.error('处理节点选中事件失败:', error);
  }
};

// 保存流程（底部按钮）
const saveProcess = async () => {
  await saveDataProcess();
};

// 参数现在已实现自动保存功能，无需手动保存函数

// 处理关闭
const handleClose = () => {
  try {
    // 在关闭前清理参数面板避免 vnode 错误
    hideParamsPanel();
    // 重置执行状态
    resetExecutionState();
    // 调用hideDataProcessModal函数正确关闭模态框
    hideDataProcessModal();
  } catch (error) {
    console.error('关闭模态框清理失败:', error);
  } finally {
    emit('close');
  }
};

// 处理遮罩层点击
const handleOverlayClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    handleClose();
  }
};

// 切换窗口最大化状态
const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value;
};

// 切换指令面板折叠状态
const toggleInstructionPanel = () => {
  isInstructionPanelCollapsed.value = !isInstructionPanelCollapsed.value;
};

// 切换参数面板折叠状态
const toggleParameterPanel = () => {
  isParameterPanelCollapsed.value = !isParameterPanelCollapsed.value;
};

// 查找指令信息
const findInstructionById = (instructionId: string) => {
  for (const category of displayInstructionCategories.value) {
    const instruction = category.instructions.find(inst => inst.id === instructionId);
    if (instruction) return instruction;
  }
  return null;
};

// 监听画布中选中的节点，显示参数面板
watch(canvasSelectedNode, (newNode) => {
  try {
    if (newNode && showNodeParams) {
      const nodeData = newNode.getData();
      if (nodeData && nodeData.instructionId) {
        const instruction = findInstructionById(nodeData.instructionId);
        if (instruction) {
          showNodeParams(newNode, instruction);
        }
      }
    }
  } catch (error) {
    console.error('监听选中节点失败:', error);
  }
}, { immediate: true });

// 创建一个引用对象用于全局访问
defineExpose({
  showPreviewModal,
  handleShowDataPreview
});

// 生命周期
onMounted(() => {
  // 移除重复的初始化逻辑，因为watch监听器已经处理了
  // 如果组件挂载时模态框已经显示，watch监听器会自动处理初始化
  
  // 添加全局引用，使ParameterPanel可以直接访问
  // @ts-ignore
  window.parentDataProcessModal = {
    showPreviewModal,
    handleShowDataPreview
  };  
});

onUnmounted(() => {
  // 组件卸载时清理
  try {
    // 先隐藏参数面板避免 vnode 错误
    hideParamsPanel();
    // 清理画布资源
    clearCanvas();
    // 重置整个数据处理模态框状态
    resetDataProcessModal();
    // 清理全局引用
    // @ts-ignore
    window.parentDataProcessModal = null;
  } catch (error) {
    console.error('清理资源失败:', error);
  }
});
</script>

<style scoped>
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
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.modal-container.maximized {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  max-height: 100vh;
  border-radius: 0;
  z-index: 1001;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.maximize-btn {
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
}

.maximize-btn:hover {
  background: #f5f5f5;
  color: #595959;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.data-source-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #f0f8ff;
  border: 1px solid #d6e4ff;
  border-radius: 16px;
  font-size: 14px;
  color: #1890ff;
}

.data-source-info i {
  font-size: 16px;
}

.data-source-name {
  font-weight: 500;
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
}

.close-btn:hover {
  background: #f5f5f5;
  color: #595959;
}

.modal-body {
  flex: 1;
  overflow: hidden; /* 恢复为hidden，防止整个模态框滚动 */
  padding: 0;
}

/* 数据加载遮罩层样式 */
.data-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
  min-width: 300px;
}

.loading-spinner {
  font-size: 32px;
  color: #1890ff;
}

.loading-text h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.loading-text p {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

/* 数据处理工作区布局 */
.data-process-workspace {
  display: flex;
  height: 100%;
  min-height: 600px;
  position: relative;
  overflow: hidden;
  flex-shrink: 1; /* 确保可以适当缩小以适应父容器 */
}

/* 面板容器 */
.panel-wrapper {
  position: relative;
  transition: width 0.3s ease;
  overflow: hidden;
}

/* 指令面板容器 */
.instruction-panel-wrapper {
  width: 280px;
  flex-shrink: 0;
  background: #fafafa;
}

/* 指令面板折叠状态 */
.instruction-panel-wrapper.collapsed {
  width: 32px;
}

/* 参数面板容器 */
.parameter-panel-wrapper {
  width: 320px;
  flex-shrink: 0;
  background: #fafafa;
}

/* 参数面板折叠状态 */
.parameter-panel-wrapper.collapsed {
  width: 32px;
}

/* 画布容器样式 */
.canvas-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 确保ProcessCanvas组件能够占据整个容器空间 */
.canvas-wrapper > * {
  flex: 1;
  width: 100%;
  height: 100%;
}

/* 折叠/展开按钮 */
.panel-collapse-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 48px;
  background: #e8e8e8;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0 4px 4px 0;
  color: #595959;
  transition: all 0.2s ease;
  z-index: 10;
}

/* 指令面板的折叠按钮 */
.instruction-panel-wrapper .panel-collapse-btn {
  right: 0;
}

/* 参数面板的折叠按钮 */
.parameter-panel-wrapper .panel-collapse-btn {
  left: 0;
  border-radius: 4px 0 0 4px;
}

/* 折叠按钮悬停效果 */
.panel-collapse-btn:hover {
  background: #d9d9d9;
  color: #1890ff;
}

/* 折叠状态下的面板内容隐藏 */
.panel-wrapper.collapsed > *:not(.panel-collapse-btn) {
  display: none;
}

/* 指令面板样式已移至InstructionPanel组件 */

/* 画布相关样式已移至ProcessCanvas组件 */

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #8c8c8c;
  pointer-events: none;
}

.canvas-placeholder i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.canvas-placeholder p {
  margin: 0;
  font-size: 14px;
}

/* 右侧参数面板 */
/* 参数面板样式已移至ParameterPanel组件 */
.params-panel {
  /* 保留基础样式以确保布局兼容性 */
  width: 300px;
  flex-shrink: 0;
}

/* 保留一些必要的容器样式以确保布局正常 */

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-label .required {
  color: #ff4d4f;
  margin-left: 2px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 变量选择器样式 */
.input-with-variable {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-with-variable .form-input {
  flex: 1;
}

.variable-select-btn {
  width: 32px;
  height: 32px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.variable-select-btn:hover {
  background: #40a9ff;
}

.variable-selector {
  position: relative;
  margin-top: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.variable-search {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.variable-search-input {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.variable-tree {
  max-height: 200px;
  overflow-y: auto;
}

.variable-node-group {
  margin-bottom: 4px;
}

.variable-node-title {
  padding: 8px 12px;
  background: #f5f5f5;
  font-weight: 500;
  font-size: 13px;
  color: #333;
  border-bottom: 1px solid #e8e8e8;
}

/* 树形结构样式 */
.tree-node-header {
  display: flex;
  align-items: center;
  user-select: none;
}

.tree-expand-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  text-align: center;
  line-height: 16px;
  font-size: 10px;
  transition: transform 0.2s;
  color: #606266;
}

.tree-expand-icon.expanded {
  color: #1890ff;
}

.tree-node-children {
  transition: all 0.3s ease;
}

.variable-item {
  padding: 6px 12px 6px 24px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.2s;
}

.variable-item:hover {
  background: #f0f8ff;
  color: #1890ff;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.column-selector {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 8px;
}

.multi-column-selector {
  max-height: 120px;
  overflow-y: auto;
}

.column-option {
  margin-bottom: 6px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  font-size: 13px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
  width: auto;
}

.form-help {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.form-error {
    margin-top: 4px;
    font-size: 12px;
    color: #ff4d4f;
    line-height: 1.4;
  }
  
  /* 开关样式 */
  .switch-container {
    display: flex;
    align-items: center;
    margin-top: 4px;
  }
  
  .switch-label {
    display: inline-block;
    position: relative;
    width: 48px;
    height: 24px;
  }
  
  .switch-input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .switch-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
    border-radius: 24px;
  }
  
  .switch-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
  }
  
  .switch-input:checked + .switch-slider {
    background-color: #1890ff;
  }
  
  .switch-input:checked + .switch-slider:before {
    transform: translateX(24px);
  }
  
  /* 文件上传样式 */
  .upload-container {
    margin-top: 4px;
  }
  
  .upload-input {
    display: none;
  }
  
  .upload-button {
    display: inline-block;
    padding: 6px 12px;
    background-color: #f0f0f0;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
  }
  
  .upload-button:hover {
    background-color: #e6f7ff;
    border-color: #91d5ff;
  }
  
  .upload-file-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    background-color: #f0f8ff;
    border: 1px solid #91d5ff;
    border-radius: 4px;
    margin-top: 4px;
    font-size: 14px;
  }
  
  .remove-file-btn {
    padding: 2px 8px;
    background-color: #f5222d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }
  
  .remove-file-btn:hover {
    background-color: #ff4d4f;
  }

  /* 结果模态框样式 */
  /* 动画效果 */
  @keyframes successPulse {
    0% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    50% {
      transform: scale(1.1);
      opacity: 1;
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  /* 滚动条美化 */
  .details-content::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  
  .details-content::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .details-content::-webkit-scrollbar-thumb {
    background: #c0c4cc;
    border-radius: 3px;
  }
  
  .details-content::-webkit-scrollbar-thumb:hover {
    background: #909399;
  }
.params-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
  font-size: 13px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f0f0f0;
  border-top: 2px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

.no-params {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 13px;
}

.params-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 16px;
  text-align: center;
  color: #8c8c8c;
}

.params-placeholder i {
  font-size: 32px;
  opacity: 0.5;
}

.params-placeholder p {
  margin: 0;
  font-size: 14px;
}

.params-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
  
  .params-actions {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #e4e7ed;
  }
  
  .params-actions .el-button {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .execution-result {
    margin-top: 16px;
  }
  
  .result-details {
    margin-top: 8px;
    padding: 12px;
    background-color: #f5f7fa;
    border: 1px solid #ebeef5;
    border-radius: 4px;
  }
  
  .result-details pre {
    margin: 0;
    font-size: 12px;
    line-height: 1.5;
    color: #606266;
    overflow-x: auto;
  }

.node-info h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.params-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-card {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: white;
  transition: all 0.2s ease;
  cursor: pointer;
}

.step-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.step-card.active {
  border-color: #1890ff;
  background: #f0f8ff;
}

.step-header {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.step-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #f5f5f5;
  border-radius: 50%;
  color: #595959;
}

.step-card.active .step-icon {
  background: #1890ff;
  color: white;
}

.step-info {
  flex: 1;
}

.step-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.step-description {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.step-checkbox input {
  width: 18px;
  height: 18px;
}

.step-config {
  padding: 0 16px 16px 16px;
  border-top: 1px solid #f0f0f0;
}

.config-section {
  margin-top: 16px;
}

.config-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.filter-rules,
.transform-rules {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-rule,
.transform-rule {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.rule-select,
.config-select {
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  background: white;
}

.rule-input {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.remove-rule-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: #ff4d4f;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-rule-btn:hover {
  background: #ff7875;
}

.add-rule-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px dashed #d9d9d9;
  background: white;
  color: #595959;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-rule-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.sort-config,
.group-config {
  display: flex;
  gap: 12px;
}

.config-select {
  flex: 1;
}

.process-preview {
  margin-top: 32px;
}

.preview-container {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: white;
}

.preview-loading,
.preview-error,
.preview-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  text-align: center;
  color: #8c8c8c;
}

.preview-loading i {
  animation: spin 1s linear infinite;
}

.preview-error {
  color: #ff4d4f;
}

.preview-data {
  padding: 16px;
}

.preview-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
}

.stat-item {
  font-size: 14px;
  color: #595959;
}

.preview-table {
  overflow: auto;
  max-height: 300px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  border-right: 1px solid #f0f0f0;
}

.data-table th {
  background: #fafafa;
  font-weight: 600;
  color: #262626;
  position: sticky;
  top: 0;
}

.preview-more {
  padding: 12px;
  text-align: center;
  color: #8c8c8c;
  font-size: 14px;
  background: #f9f9f9;
  border-top: 1px solid #f0f0f0;
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

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
  min-width: 60px;
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
  
  .step-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .filter-rule,
  .transform-rule {
    flex-direction: column;
    align-items: stretch;
  }
  
  .sort-config,
  .group-config {
    flex-direction: column;
  }
  
  .preview-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
  
  .btn {
    width: 100%;
  }
}
</style>