import { ref, computed, watch } from 'vue';
import type { 
  DataExtractionParams, 
  NodeData, 
  DataSourceFile 
} from '@/types/dataExtraction';
import { dataSourceService } from '@/services/dataExtractionService';
import { dataSourceInfoCache } from '@/composables/useDataProcess';
import type {ExcelFilesInfo } from '@/types/dataSourceFile';

/**
 * 节点参数管理组合式函数
 */
export function useNodeParams() {
  // 当前编辑的节点
  const currentNode = ref<any>(null);
  
  // 节点参数
  const nodeParams = ref<DataExtractionParams>({
    sourceDataPath: '',
    startRow: 1,
    endRow: 10,
    startColumn: 'A',
    endColumn: 'C',
    resultVariableName: 'extractedData'
  } as DataExtractionParams);
  
  // 数据源文件列表
  const dataSourceFiles = ref<DataSourceFile[]>([]);
  
  // 加载状态
  const isLoading = ref(false);
  
  // 错误信息
  const error = ref<string>('');
  
  // 数据源选项列表
  const dataSourceOptions = computed(() => {
    // 直接返回已经格式化的选项数据
    return dataSourceFiles.value.map((item: any) => ({
      value: item.value || item.id,
      label: item.label || item.name
    }));
  });
  
  // 是否可以预览数据
  const canPreviewData = computed(() => {
    return !!nodeParams.value.sourceDataPath;
  });
  
  /**
   * 设置当前编辑的节点
   * @param node 节点实例
   */
  const setCurrentNode = (node: any) => {
    currentNode.value = node;
    
    if (node) {
      const nodeData: NodeData = node.getData();
      
      // 如果节点没有参数，初始化默认参数
      if (!nodeData.params) {
        nodeData.params = {
          sourceDataPath: '',
          startRow: 1,
          endRow: 10,
          startColumn: 'A',
          endColumn: 'C',
          resultVariableName: 'extractedData'
        };
        node.setData(nodeData);
      }
      
      // 更新本地参数状态
      nodeParams.value = { ...nodeData.params };
    }
  };
  
  /**
   * 更新节点参数
   * @param paramName 参数名
   * @param paramValue 参数值
   */
  const updateNodeParam = (paramName: string, paramValue: any) => {
    if (!currentNode.value) return;

    // 更新本地状态
    (nodeParams.value as any)[paramName] = paramValue;

    // 更新节点数据
    const nodeData: NodeData = currentNode.value.getData();
    if (!nodeData.params) {
      nodeData.params = { ...nodeParams.value };
    } else {
      (nodeData.params as any)[paramName] = paramValue;
    }
    currentNode.value.setData(nodeData);
  };
  
  /**
   * 批量更新节点参数
   * @param params 参数对象
   */
  const updateNodeParams = (params: Partial<DataExtractionParams>) => {
    if (!currentNode.value) return;
    
    // 更新本地状态
    Object.assign(nodeParams.value, params);
    
    // 更新节点数据
    const nodeData: NodeData = currentNode.value.getData();
    if (!nodeData.params) {
      nodeData.params = { ...nodeParams.value };
    } else {
      Object.assign(nodeData.params, params);
    }
    currentNode.value.setData(nodeData);
  };  

  /**
   * 加载指定数据源的详细信息和文件列表
   * @param dataSourceId 数据源ID
   */
  const loadDataSourceFiles = async (dataSourceId: string) => {
    if (!dataSourceId) {
      error.value = '数据源ID未设置';
      return;
    }
    
    isLoading.value = true;
    error.value = '';
    
    try {
      let dataResult = null;
      
      // 优先从缓存获取数据源数据
      if (dataSourceInfoCache.value.has(dataSourceId)) {
        const cachedData = dataSourceInfoCache.value.get(dataSourceId);
        
        // 将缓存数据转换为API响应格式
        if (cachedData) {
          dataResult = {
            success: true,
            data: cachedData
          };
        } 
      }
      // 如果缓存中没有数据，则调用API（兜底方案）
      if (!dataResult) {        
        // 调用/api/datasource/{data_source_id}/data接口获取数据源数据
        dataResult = await dataSourceService.getDataSourceData(dataSourceId);
        
        // 将API响应数据存入缓存
        if (dataResult.success) {
          dataSourceInfoCache.value.set(dataSourceId, dataResult.data);
        }
      }
      
      if (dataResult.success && dataResult.data) {
        const dataResult_files = dataResult.data.files;
        const sourceOptions: Array<{ value: string; label: string }> = [];
        
        // 遍历所有工作表，为每个工作表创建一个选项
        dataResult_files.forEach((f:ExcelFilesInfo) => {
          const sheets = f.sheets;
          sheets.forEach(sheetName => {
            const value = `${f.file_path}:${sheetName}`;
            const label = `${f.original_filename} - ${sheetName}`;
            sourceOptions.push({ value, label });
          });
        });
        
        // 将选项存储到dataSourceFiles中（符合DataSourceFile接口）
        dataSourceFiles.value = sourceOptions.map(option => ({
          id: option.value,
          name: option.label,
          path: option.value,
          filename: option.label.split(' - ')[0] || option.label, // 提取文件名部分
          original_filename: option.label.split(' - ')[0] || option.label,
          file_path: option.value,
          sheets: [option.label.split(' - ')[1] || ''] // 提取工作表名部分
        }));
      } else {
        error.value = dataResult.error || dataResult.message || '加载数据源文件失败';
        dataSourceFiles.value = [];
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载数据源文件失败';
      dataSourceFiles.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 获取节点参数（用于执行指令）
   * @returns 节点参数对象
   */
  const getNodeParams = (): Record<string, any> => {
    if (!currentNode.value) return {};
    
    const nodeData: NodeData = currentNode.value.getData();
    const params = nodeData.params || nodeParams.value;
    
    return {
      sourceDataPath: params.sourceDataPath,
      startRow: parseInt(String(params.startRow)),
      endRow: parseInt(String(params.endRow)),
      startColumn: params.startColumn,
      endColumn: params.endColumn,
      resultVariableName: params.resultVariableName
    };
  };
  
  /**
   * 重置参数到默认值
   */
  const resetParams = () => {
    const defaultParams: DataExtractionParams = {
      sourceDataPath: '',
      startRow: 1,
      endRow: 10,
      startColumn: 'A',
      endColumn: 'C',
      resultVariableName: 'extractedData'
    };
    
    nodeParams.value = { ...defaultParams };
    
    if (currentNode.value) {
      const nodeData: NodeData = currentNode.value.getData();
      nodeData.params = { ...defaultParams };
      currentNode.value.setData(nodeData);
    }
  };
  
  // 监听参数变化，自动保存到节点
  watch(
    () => nodeParams.value,
    (newParams) => {
      if (currentNode.value) {
        const nodeData: NodeData = currentNode.value.getData();
        nodeData.params = { ...newParams };
        currentNode.value.setData(nodeData);
      }
    },
    { deep: true }
  );
  
  return {
    // 状态
    currentNode,
    nodeParams,
    dataSourceFiles,
    isLoading,
    error,
    
    // 计算属性
    dataSourceOptions,
    canPreviewData,
    
    // 方法
    setCurrentNode,
    updateNodeParam,
    updateNodeParams,
    loadDataSourceFiles,
    getNodeParams,
    resetParams
  };
}