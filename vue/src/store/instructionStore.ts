// 指令管理状态管理

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  Instruction,
  InstructionCategory,
  CanvasNode,
  CanvasEdge,
  DataProcessFlow,
  InstructionExecutionParams,
  InstructionExecutionResult,
  ProcessExecutionStatus
} from '@/types';
import { instructionService } from '@/services';
import type { ApiResponse } from '@/types/common';

export const useInstructionStore = defineStore('instruction', () => {
  // 状态定义
  const instructions = ref<Instruction[]>([]);
  const categories = ref<InstructionCategory[]>([]);
  const currentInstruction = ref<Instruction | null>(null);
  const executionResult = ref<InstructionExecutionResult | null>(null);
  const executionHistory = ref<InstructionExecutionResult[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 画布相关状态
  const canvasNodes = ref<CanvasNode[]>([]);
  const canvasEdges = ref<CanvasEdge[]>([]);
  const selectedNodes = ref<string[]>([]);
  const selectedEdges = ref<string[]>([]);
  const canvasLoading = ref(false);

  // 执行状态
  const executionStatus = ref<ProcessExecutionStatus>({
    total: 0,
    current: 0,
    currentStep: '空闲',
    isRunning: false,
    results: {}
  });
  const executionProgress = ref(0);
  const executionLogs = ref<string[]>([]);

  // 参数面板状态
  const showParametersPanel = ref(false);
  const parametersData = ref<Record<string, any>>({});

  // 计算属性
  const hasInstructions = computed(() => instructions.value.length > 0);
  const hasCategories = computed(() => categories.value.length > 0);
  const isExecuting = computed(() => executionStatus.value.isRunning);
  const canExecute = computed(() => {
    return canvasNodes.value.length > 0 && !executionStatus.value.isRunning;
  });

  // 统一获取分类和指令数据（避免重复API调用）
  const fetchAllData = async () => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<InstructionCategory[]> = await instructionService.getInstructionCategoriesWithInstructions();
      
      if (response.success && response.data) {
        // 提取分类数据
        categories.value = response.data;
        // 提取所有指令数据
        instructions.value = categories.value.flatMap(category => category.instructions || []);
      } else {
        throw new Error(response.message || '获取指令数据失败');
      }
    } catch (err: any) {
      error.value = err.message || '获取指令数据失败';
      console.error('获取指令数据失败:', err);
    } finally {
      loading.value = false;
    }
  };

  // 为了兼容现有代码保留fetchCategories方法，但内部调用统一的数据获取方法
  const fetchCategories = async () => {
    await fetchAllData();
  };

  // 为了兼容现有代码保留fetchInstructions方法，但内部调用统一的数据获取方法
  const fetchInstructions = async (_categoryId?: string) => {
    await fetchAllData();
  };

  // 获取指令详情
  const fetchInstructionDetail = async (id: string) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<Instruction> = await instructionService.getInstruction(id);
      
      if (response.success && response.data) {
        currentInstruction.value = response.data;
        return response.data;
      } else {
        throw new Error(response.message || '获取指令详情失败');
      }
    } catch (err: any) {
      error.value = err.message || '获取指令详情失败';
      console.error('获取指令详情失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 执行单个指令
  const executeInstruction = async (instructionId: string, params: InstructionExecutionParams) => {
    try {
      executionStatus.value = {
        total: 1,
        current: 0,
        currentStep: '执行中...',
        isRunning: true,
        results: {}
      };
      error.value = null;

      const response: ApiResponse<InstructionExecutionResult> = await instructionService.executeInstruction(instructionId, params);
      
      if (response.success && response.data) {
        executionResult.value = response.data;
        executionHistory.value.unshift(response.data);
        executionStatus.value = {
          total: 1,
          current: 1,
          currentStep: response.data.success ? '执行完成' : '执行失败',
          isRunning: false,
          results: { [instructionId]: response.data }
        };
        return response.data;
      } else {
        executionStatus.value = {
          total: 0,
          current: 0,
          currentStep: '执行失败',
          isRunning: false,
          results: {}
        };
        throw new Error(response.message || '指令执行失败');
      }
    } catch (err: any) {
      executionStatus.value = {
        total: 0,
        current: 0,
        currentStep: '执行失败',
        isRunning: false,
        results: {}
      };
      error.value = err.message || '指令执行失败';
      console.error('指令执行失败:', err);
      throw err;
    }
  };

  // 执行指令流
  const executeFlow = async (flow: DataProcessFlow) => {
    try {
      executionStatus.value = {
        total: flow.nodes.length,
        current: 0,
        currentStep: '开始执行流程...',
        isRunning: true,
        results: {}
      };
      executionProgress.value = 0;
      executionLogs.value = [];
      error.value = null;

      const response: ApiResponse<InstructionExecutionResult[]> = await instructionService.executeInstructionFlow(flow.id||'', flow.nodes.map(node => ({
        instructionId: node.instructionId,
        params: node.params
      })));
      
      if (response.success && response.data) {
        executionResult.value = response.data[0] || null;
        executionHistory.value.unshift(...response.data);
        executionStatus.value = {
          total: flow.nodes.length,
          current: flow.nodes.length,
          currentStep: '流程执行完成',
          isRunning: false,
          results: { flow: response.data as any }
        };
        executionProgress.value = 100;
        return response.data;
      } else {
        executionStatus.value = {
          total: 0,
          current: 0,
          currentStep: '执行失败',
          isRunning: false,
          results: {}
        };
        throw new Error(response.message || '流程执行失败');
      }
    } catch (err: any) {
      executionStatus.value = {
        total: 0,
        current: 0,
        currentStep: '执行失败',
        isRunning: false,
        results: {}
      };
      error.value = err.message || '流程执行失败';
      console.error('流程执行失败:', err);
      throw err;
    }
  };

  // 验证指令参数
  const validateParameters = async (instructionId: string, params: Record<string, any>) => {
    try {
      const response: ApiResponse<{ valid: boolean; errors?: string[] }> = await instructionService.validateInstructionParams(instructionId, params);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.message || '参数验证失败');
      }
    } catch (err: any) {
      console.error('参数验证失败:', err);
      throw err;
    }
  };

  // 获取执行历史
  const fetchExecutionHistory = async (limit?: number) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<InstructionExecutionResult[]> = await instructionService.getInstructionHistory(undefined, limit);
      
      if (response.success && response.data) {
        executionHistory.value = response.data;
      } else {
        throw new Error(response.message || '获取执行历史失败');
      }
    } catch (err: any) {
      error.value = err.message || '获取执行历史失败';
      console.error('获取执行历史失败:', err);
    } finally {
      loading.value = false;
    }
  };

  // 画布操作方法
  const addCanvasNode = (node: CanvasNode) => {
    canvasNodes.value.push(node);
  };

  const removeCanvasNode = (nodeId: string) => {
    canvasNodes.value = canvasNodes.value.filter(node => node.id !== nodeId);
    canvasEdges.value = canvasEdges.value.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    );
  };

  const updateCanvasNode = (nodeId: string, updates: Partial<CanvasNode>) => {
    const index = canvasNodes.value.findIndex(node => node.id === nodeId);
    if (index !== -1) {
      canvasNodes.value[index] = { ...canvasNodes.value[index], ...updates };
    }
  };

  const addCanvasEdge = (edge: CanvasEdge) => {
    canvasEdges.value.push(edge);
  };

  const removeCanvasEdge = (edgeId: string) => {
    canvasEdges.value = canvasEdges.value.filter(edge => edge.id !== edgeId);
  };

  const clearCanvas = () => {
    canvasNodes.value = [];
    canvasEdges.value = [];
    selectedNodes.value = [];
    selectedEdges.value = [];
  };

  const selectNode = (nodeId: string, multiple = false) => {
    if (multiple) {
      if (selectedNodes.value.includes(nodeId)) {
        selectedNodes.value = selectedNodes.value.filter(id => id !== nodeId);
      } else {
        selectedNodes.value.push(nodeId);
      }
    } else {
      selectedNodes.value = [nodeId];
    }
  };

  const selectEdge = (edgeId: string, multiple = false) => {
    if (multiple) {
      if (selectedEdges.value.includes(edgeId)) {
        selectedEdges.value = selectedEdges.value.filter(id => id !== edgeId);
      } else {
        selectedEdges.value.push(edgeId);
      }
    } else {
      selectedEdges.value = [edgeId];
    }
  };

  const clearSelection = () => {
    selectedNodes.value = [];
    selectedEdges.value = [];
  };

  // 参数面板操作
  const openParametersPanel = (nodeId: string) => {
    const node = canvasNodes.value.find(n => n.id === nodeId);
    if (node) {
      parametersData.value = { ...node.params };
      showParametersPanel.value = true;
    }
  };

  const closeParametersPanel = () => {
    showParametersPanel.value = false;
    parametersData.value = {};
  };

  const updateParameters = (nodeId: string, params: Record<string, any>) => {
    updateCanvasNode(nodeId, { params });
    parametersData.value = { ...params };
  };

  // 重置执行状态
  const resetExecutionState = () => {
    executionStatus.value = {
      total: 0,
      current: 0,
      currentStep: '',
      isRunning: false,
      results: {}
    };
    executionProgress.value = 0;
    executionLogs.value = [];
    executionResult.value = null;
  };

  // 添加执行日志
  const addExecutionLog = (log: string) => {
    executionLogs.value.push(`[${new Date().toLocaleTimeString()}] ${log}`);
  };

  // 更新执行进度
  const updateExecutionProgress = (progress: number) => {
    executionProgress.value = Math.max(0, Math.min(100, progress));
  };

  // 清除错误
  const clearError = () => {
    error.value = null;
  };

  return {
    // 状态
    instructions,
    categories,
    currentInstruction,
    executionResult,
    executionHistory,
    loading,
    error,
    canvasNodes,
    canvasEdges,
    selectedNodes,
    selectedEdges,
    canvasLoading,
    executionStatus,
    executionProgress,
    executionLogs,
    showParametersPanel,
    parametersData,

    // 计算属性
    hasInstructions,
    hasCategories,
    isExecuting,
    canExecute,

    // 方法
    fetchCategories,
    fetchInstructions,
    fetchAllData,
    fetchInstructionDetail,
    executeInstruction,
    executeFlow,
    validateParameters,
    fetchExecutionHistory,
    addCanvasNode,
    removeCanvasNode,
    updateCanvasNode,
    addCanvasEdge,
    removeCanvasEdge,
    clearCanvas,
    selectNode,
    selectEdge,
    clearSelection,
    openParametersPanel,
    closeParametersPanel,
    updateParameters,
    resetExecutionState,
    addExecutionLog,
    updateExecutionProgress,
    clearError
  };
});