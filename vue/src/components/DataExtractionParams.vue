<template>
  <div class="data-extraction-params">
    <div class="params-form active">
      <!-- 源数据路径选择 -->
      <div class="form-group">
        <label for="sourceDataPath">源数据路径:</label>
        <div class="source-data-path-container">
          <el-select
            v-model="nodeParams.sourceDataPath"
            placeholder="请选择源数据路径"
            :loading="isLoading"
            :disabled="isLoading"
            class="source-data-select"
            @change="handleSourceDataPathChange"
          >
            <el-option
              v-for="option in dataSourceOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          
          <el-button
            type="primary"
            size="small"
            :disabled="!canPreviewData"
            @click="handlePreviewData"
          >
            选择数据
          </el-button>
        </div>
      </div>
      <div class="help-section">
        <small class="help-text">
          选择数据源后，可通过"选择数据"按钮预览数据并选择区域自动填充范围参数
        </small>
      </div>
      
      <!-- 行范围选择 -->
      <div class="form-group">
        <label>选择行:</label>
        <div class="range-input-container">
          <el-input-number
            v-model="nodeParams.startRow"
            :min="1"
            size="small"
            @change="handleParamChange('startRow', $event)"
          />
          <span class="range-separator">-</span>
          <el-input-number
            v-model="nodeParams.endRow"
            :min="1"
            size="small"
            @change="handleParamChange('endRow', $event)"
          />
        </div>
      </div>
      
      <!-- 列范围选择 -->
      <div class="form-group">
        <label>选择列:</label>
        <div class="range-input-container">
          <el-input
            v-model="nodeParams.startColumn"
            size="small"
            placeholder="A"
            @input="handleParamChange('startColumn', $event)"
          />
          <span class="range-separator">-</span>
          <el-input
            v-model="nodeParams.endColumn"
            size="small"
            placeholder="C"
            @input="handleParamChange('endColumn', $event)"
          />
        </div>
      </div>
      
      <!-- 结果变量名 -->
      <div class="form-group">
        <label for="resultVariableName">结果变量名:</label>
        <el-input
          v-model="nodeParams.resultVariableName"
          size="small"
          placeholder="extractedData"
          @input="handleParamChange('resultVariableName', $event)"
        />
      </div>
      
      <!-- 运行指令按钮 -->
      <div class="params-actions">
        <el-button
          type="success"
          :loading="isExecuting"
          :disabled="!currentNode"
          @click="handleRunInstruction"
        >
          <el-icon><VideoPlay /></el-icon>
          运行指令
        </el-button>
      </div>
      
      <!-- 执行结果显示 -->
      <div v-if="executionResult" class="execution-result">
        <el-alert
          :title="executionResult.success ? '执行成功' : '执行失败'"
          :type="executionResult.success ? 'success' : 'error'"
          :description="executionResult.message"
          show-icon
          :closable="false"
        >
          <template v-if="executionResult.details" #default>
            <div class="result-details">
              <pre>{{ executionResult.details }}</pre>
            </div>
          </template>
        </el-alert>
      </div>
    </div>
    

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { ElSelect, ElOption, ElButton, ElInputNumber, ElInput, ElAlert, ElIcon } from 'element-plus';
import { VideoPlay } from '@element-plus/icons-vue';
import { useNodeParams } from '@/composables/useNodeParams';
import { useDataProcess } from '@/composables/useDataProcess';
import { dataSourceService } from '@/services/dataExtractionService';
import type { Node } from '@antv/x6';
import type { SheetData } from '@/types/dataExtraction';

// Props
interface Props {
  /** 当前数据源ID */
  dataSourceId?: string;
  /** 当前编辑的节点 */
  node?: Node | null;
  /** 参数更新回调函数 */
  onParamsUpdated?: (_params: Record<string, any>) => void;
}

const props = withDefaults(defineProps<Props>(), {
  dataSourceId: '',
  node: null,
  onParamsUpdated: () => {}
});

// Emits
interface Emits {
  /** 参数变化 */
  (_e: 'param-change', _paramName: string, _paramValue: any): void;
  /** 批量参数更新 */
  (_e: 'params-updated', _params: Record<string, any>): void;
  /** 指令执行 */
  (_e: 'instruction-execute', _result: any): void;
  /** 显示数据预览 */
  (_e: 'show-data-preview', _sheetData: SheetData, _sheetName: string): void;
}

const emit = defineEmits<Emits>();

// 监听参数更新事件
watch(() => props.onParamsUpdated, (_callback) => {
  // 这个监听器实际上不需要，因为onParamsUpdated是一个回调函数，不是响应式数据
}, { immediate: true });

// 从父组件接收参数更新
defineExpose({
  handleParamsUpdatedFromParent: (params: Record<string, any>) => {
    // 更新本地参数状态
    Object.assign(nodeParams.value, params);
  }
});

// 使用组合式函数
const {
  currentNode,
  nodeParams,
  isLoading,
  dataSourceOptions,
  canPreviewData,
  setCurrentNode,
  updateNodeParam,
  loadDataSourceFiles, 
  getNodeParams
} = useNodeParams();

// 使用数据处理组合式函数获取缓存
const { dataSourceInfoCache } = useDataProcess();

// 本地状态
const previewLoading = ref(false);
const isExecuting = ref(false);
const executionResult = ref<{
  success: boolean;
  message: string;
  details?: string;
} | null>(null);

/**
 * 处理源数据路径变化
 */
const handleSourceDataPathChange = (value: string) => {
  updateNodeParam('sourceDataPath', value);
  emit('param-change', 'sourceDataPath', value);
};

/**
 * 处理参数变化
 */
const handleParamChange = (_paramName: string, _paramValue: any) => {
  updateNodeParam(_paramName as any, _paramValue);
  emit('param-change', _paramName, _paramValue);
};

/**
   * 处理预览数据
   * 根据文件路径+工作表名，获取单个工作表的内容
   */
  const handlePreviewData = async () => {    
    if (!nodeParams.value.sourceDataPath) {
      return;
    }
    
    try {
      previewLoading.value = true;
      
      // 立即显示预览窗口，初始状态为加载中
      emit('show-data-preview', null, '');
      
      // 解析数据源路径 - 格式为"数据源文件路径:工作表名"
      
      // 手动解析，因为dataSourceService.parseDataSourcePath返回的是dataSourceId和sheetName
      const parts = nodeParams.value.sourceDataPath.split(':');
      const dataSourceFilePath = parts[0] || '';
      const sheetName = parts[1] || '';
      
      if (!dataSourceFilePath || !sheetName) {
        console.error('无效的数据源路径格式，应为"数据源文件路径:工作表名"');
        return;
      }
      
      // 优先从缓存获取数据源详情，避免重复API调用
      let dataSourceDetails = null;
      const cacheKey = `${dataSourceFilePath}:${sheetName}`;
      
      if (dataSourceInfoCache.value.has(cacheKey)) {
        dataSourceDetails = dataSourceInfoCache.value.get(cacheKey);
      } else {
        // 使用新的API通过文件路径和工作表名获取数据
        const response = await dataSourceService.getDataSourceDataByFilePath(
          dataSourceFilePath, 
          sheetName, 
          100 // 限制获取100行数据用于预览
        );
        
        if (response.success && response.data) {
          dataSourceDetails = response.data;
          // 将结果存入缓存
          dataSourceInfoCache.value.set(cacheKey, dataSourceDetails);
        } else {
          console.error('获取数据源详情失败:', response.error || '未知错误');
          return;
        }
      }
      
      if (!dataSourceDetails) {
        console.error('未找到数据源详情');
        return;
      }
      
      // 获取目标sheet的数据
      let targetSheetData = null;
      
      // 处理返回的数据结构，确保能正确获取工作表数据
      if (dataSourceDetails.data) {
        // 查找指定名称的工作表
        const key=Object.keys(dataSourceDetails.data)[0]
        targetSheetData = dataSourceDetails.data[key]
      } 
      
      // 确保获取到有效的工作表数据
      if (!targetSheetData || !targetSheetData.columns || !targetSheetData.rows) {
        console.error(`未找到有效的工作表数据: ${sheetName}`);
        return;
      }
      
      // 更新预览窗口的数据
      emit('show-data-preview', targetSheetData, sheetName);
      
    } catch (error) {
      console.error('显示数据预览失败:', error);
    } finally {
      previewLoading.value = false;
    }
  };



/**
 * 处理运行指令
 */
const handleRunInstruction = async () => {
    if (!currentNode.value) {
      return;
    }
    
    const nodeData = currentNode.value.getData();
    if (!nodeData || !nodeData.instructionId) {
      executionResult.value = {
        success: false,
        message: '节点数据无效，缺少指令ID'
      };
      return;
    }
    
    isExecuting.value = true;
    executionResult.value = null;
    
    try {
      const params = getNodeParams();
      // 转换参数名称：驼峰命名法 -> 蛇形命名法
      const convertedParams = {
        source_path: params.sourceDataPath,
        start_row: params.startRow,
        end_row: params.endRow,
        start_column: params.startColumn,
        end_column: params.endColumn,
        result_variable_name: params.resultVariableName
      };
      const result = await dataSourceService.executeInstruction(nodeData.instructionId, convertedParams);
    
    let details = '';
    if (result.data_shape) details += `数据形状: ${result.data_shape}\n`;
    if (result.execution_time) details += `执行时间: ${result.execution_time}秒\n`;
    if (result.output_path) details += `输出路径: ${result.output_path}\n`;
    
    executionResult.value = {
      success: true,
      message: result.message || '指令执行成功！',
      details: details || undefined
    };
    
    emit('instruction-execute', result);
  } catch (error) {
    executionResult.value = {
      success: false,
      message: '指令执行失败',
      details: error instanceof Error ? error.message : '未知错误'
    };
  } finally {
    isExecuting.value = false;
  }
};

// 监听节点参数变化，自动保存到节点数据并触发更新事件
watch(
  () => nodeParams.value,
  (newParams) => {
    if (currentNode.value) {
      const nodeData = currentNode.value.getData()
      nodeData.params = { ...newParams }
      currentNode.value.setData(nodeData)
      // 触发参数更新事件
      emit('params-updated', { ...newParams })
    }
  },
  { deep: true }
)

// 监听props变化
watch(
  () => props.node,
  (newNode) => {
    if (newNode) {
      setCurrentNode(newNode);
    }
  },
  { immediate: true }
);

watch(
  () => props.dataSourceId,
  (newDataSourceId) => {
    if (newDataSourceId) {
      // 加载数据源文件列表
      loadDataSourceFiles(newDataSourceId);
    }
  },
  { immediate: true }
);

// 组件挂载时初始化
onMounted(async () => {
  if (props.node) {
    setCurrentNode(props.node);
  }
  // 加载数据源列表，为下拉选择提供数据
  await loadDataSourceFiles(props.dataSourceId);
});
</script>

<style scoped>
.data-extraction-params {
  padding: 0;
}

.params-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.params-form h5 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
}

.source-data-path-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.source-data-select {
  flex: 1;
}

.help-section {
  margin-top: 5px;
}

.help-text {
  display: block;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.range-input-container {
  display: flex;
  align-items: center;
  gap: 5px;
}

.range-input-container .el-input-number,
.range-input-container .el-input {
  flex: 1;
}

.range-separator {
  color: #666;
  font-weight: 500;
  padding: 0 2px;
}

.params-actions {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #dee2e6;
}

.params-actions .el-button {
  width: 100%;
  padding: 10px;
  font-weight: 500;
}

.execution-result {
  margin-top: 15px;
}

.result-details {
  margin-top: 8px;
}

.result-details pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>