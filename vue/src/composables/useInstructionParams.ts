// 指令参数处理相关的组合式函数
// 管理指令参数面板的显示、验证、保存等逻辑

import { ref, reactive, computed, watch } from 'vue';
import { instructionService } from '@/services/instructionService';
import type {
  Instruction,
  ParamFormItem,
  InstructionCategory
} from '@/types/instruction';
import type { ParamsPanelState } from '@/types/dataSource';
import type { Node } from '@antv/x6';

/**
 * 指令参数管理组合式函数
 */
export function useInstructionParams() {
  // ==================== 响应式状态 ====================
  
  // 参数面板状态
  const paramsPanel = reactive<ParamsPanelState>({
    visible: false,
    collapsed: false,
    selectedNode: null,
    selectedEdge: null,
    params: {},
    nodeData: null,
    paramFormItems: []
  });

  // 当前指令信息
  const currentInstruction = ref<Instruction | null>(null);
  const instructionLoading = ref(false);

  // 参数表单项
  const paramFormItems = ref<ParamFormItem[]>([]);
  const paramErrors = ref<Record<string, string>>({});
  const isValidating = ref(false);

  // 可用列名（用于列选择参数）
  const availableColumns = ref<string[]>([]);

  // 已加载的指令分类数据（用于避免重复API调用）
  const instructionCategories = ref<InstructionCategory[]>([]);

  // ==================== 计算属性 ====================
  
  const isParamsPanelVisible = computed(() => paramsPanel.visible && !paramsPanel.collapsed);
  const hasSelectedNode = computed(() => !!paramsPanel.selectedNode);
  const hasParamErrors = computed(() => Object.keys(paramErrors.value).length > 0);
  const canApplyParams = computed(() => {
    return hasSelectedNode.value && !hasParamErrors.value && !isValidating.value;
  });

  // ==================== 参数面板控制 ====================
  
  /**
   * 显示参数面板
   * @param node 选中的节点
   * @param instruction 可选的指令对象，如果提供则直接使用，不重新加载
   */
  const showParamsPanel = async (node: Node, instruction?: any) => {
    try {
      paramsPanel.selectedNode = node;
      // 修复节点数据获取方式
      if (typeof (node as any).getData === 'function') {
        paramsPanel.nodeData = (node as any).getData();
      }
      
      // 确保参数面板的参数对象存在
      if (!paramsPanel.params) {
        paramsPanel.params = {};
      }
      
      // 如果节点数据存在且有参数，加载到参数面板
      if (paramsPanel.nodeData && paramsPanel.nodeData.params) {
        paramsPanel.params = { ...paramsPanel.nodeData.params };
      }
    
      
      paramsPanel.visible = true;
      paramsPanel.collapsed = false;

      // 获取指令信息
      if (instruction) {
        // 如果直接提供了instruction对象，直接使用
        currentInstruction.value = instruction;
        initializeParamFormItems();
      } else if (paramsPanel.nodeData?.instructionId) {
        // 否则通过API加载
        await loadInstructionDetail(paramsPanel.nodeData.instructionId);
        initializeParamFormItems();
      }
      // 自动保存参数到节点 - 确保默认参数被保存
      if (typeof (node as any).setData === 'function' && paramsPanel.nodeData) {
        (node as any).setData(paramsPanel.nodeData);
      } else {
        // 节点不存在或无法设置数据
        console.warn('无法更新节点数据: 节点不存在或缺少setData方法');
      }
    } catch (error) {
      console.error('显示参数面板失败:', error);
    }
  };

  /**
   * 隐藏参数面板
   */
  const hideParamsPanel = () => {
    paramsPanel.visible = false;
    paramsPanel.selectedNode = null;
    paramsPanel.nodeData = null;
    paramsPanel.params = {};
    paramsPanel.paramFormItems = [];
    currentInstruction.value = null;
    paramFormItems.value = [];
    paramErrors.value = {};
  };

  /**
   * 切换参数面板折叠状态
   */
  const toggleParamsPanel = () => {
    paramsPanel.collapsed = !paramsPanel.collapsed;
  };

  // ==================== 指令信息管理 ====================
  
  /**
   * 设置已加载的指令分类数据
   * 用于避免重复调用API获取指令详情
   */
  const setInstructionCategories = (categories: InstructionCategory[]) => {
    instructionCategories.value = categories;
  };

  /**
   * 从已加载的指令数据中查找指令详情
   */
  const findInstructionById = (instructionId: string): Instruction | null => {
    for (const category of instructionCategories.value) {
      const instruction = category.instructions.find(inst => inst.id === instructionId);
      if (instruction) {
        return instruction;
      }
    }
    return null;
  };

  /**
   * 加载指令详情
   * 优化：优先从已加载的指令数据中查找，避免重复API调用
   */
  const loadInstructionDetail = async (instructionId: string) => {
    if (instructionLoading.value) return;

    instructionLoading.value = true;
    try {
      // 优先从已加载的指令数据中查找
      const cachedInstruction = findInstructionById(instructionId);
      if (cachedInstruction) {
        currentInstruction.value = cachedInstruction;
        return;
      }

      // 如果缓存中没有找到，则调用API（向后兼容）
      const response = await instructionService.getInstruction(instructionId);
      if (response.success && response.data) {
        currentInstruction.value = response.data;
      } else {
        throw new Error(response.message || '获取指令详情失败');
      }
    } catch (error) {
      console.error('加载指令详情失败:', error);
      currentInstruction.value = null;
    } finally {
      instructionLoading.value = false;
    }
  };

  // ==================== 参数表单管理 ====================
  
  /**
   * 初始化参数表单项
   */
  const initializeParamFormItems = () => {
    if (!currentInstruction.value || !paramsPanel.nodeData) return;

    // 清空现有表单项
    paramsPanel.paramFormItems = [];
    paramsPanel.params = {};

    // 获取指令的参数配置
    const instructionParams = currentInstruction.value.params || [];
    
    // 获取节点数据
    const nodeData = paramsPanel.nodeData;
    const nodeParams = nodeData.params || {};

    // 处理指令定义的参数配置信息
    instructionParams.forEach(param => {
      // 对于datapath类型参数，需要特殊处理其值的来源
      let paramValue;
      if (param.type === 'select_excelpath') {
        // 优先使用节点参数中的对应名称值，如果不存在则使用sourceDataPath或sheetPath作为回退
        paramValue = nodeParams[param.name] ?? nodeParams.sourceDataPath ?? nodeParams.sheetPath ?? param.defaultValue ?? getDefaultValueByType(param.type);
      } else {
        paramValue = nodeParams[param.name] ?? param.defaultValue ?? getDefaultValueByType(param.type);
      }
      
      const formItem = {
        param,
        value: paramValue,
        error: undefined
      };
      paramsPanel.paramFormItems.push(formItem);
      paramsPanel.params[param.name] = formItem.value;
    });
  };
  
  // setupDefaultParams函数已被移除，相关功能已在updateParamValue和showParamsPanel中实现

  /**
   * 根据参数类型获取默认值
   */
  const getDefaultValueByType = (type: string): any => {
    switch (type) {
      case 'string':
      case 'textarea':
      case 'select_excelpath':
        return '';
      case 'number':
        return 0;
      case 'boolean':
        return false;
      case 'select':
      case 'column':
        return null;
      case 'file':
        return null;
      case 'range':
        return [0, 100];
      default:
        return null;
    }
  };

  /**
   * 更新参数值并自动保存到节点
   */
  const updateParamValue = (paramName: string, value: any) => {
    paramsPanel.params[paramName] = value;

    // 同时更新paramFormItems中的对应项
    const formItem = paramsPanel.paramFormItems.find(item => item.param?.name === paramName);
    if (formItem) {
      formItem.value = value;
    }

    // 清除该参数的错误信息
    if (paramErrors.value[paramName]) {
      delete paramErrors.value[paramName];
    }
    
    // 自动保存参数到节点 - 实现无需保存按钮的自动保存
    if (paramsPanel.selectedNode && typeof (paramsPanel.selectedNode as any).getData === 'function' && typeof (paramsPanel.selectedNode as any).setData === 'function') {
      const node = paramsPanel.selectedNode as any;
      const nodeData = node.getData();
      if (!nodeData.params) {
        nodeData.params = {};
      }
      nodeData.params[paramName] = value;
      node.setData(nodeData);
    
    }
  };

  /**
   * 验证参数
   */
  const validateParams = async (): Promise<boolean> => {
    if (!currentInstruction.value || !paramsPanel.selectedNode) return false;

    isValidating.value = true;
    paramErrors.value = {};

    try {
      // 客户端验证
      const clientErrors = validateParamsOnClient();
      if (Object.keys(clientErrors).length > 0) {
        paramErrors.value = clientErrors;
        return false;
      }

      // 服务端验证
      const response = await instructionService.validateInstructionParams(
        currentInstruction.value.id,
        paramsPanel.params
      );

      if (response.success && response.data) {
        if (!response.data.valid && response.data.errors) {
          // 处理服务端返回的错误信息
          response.data.errors.forEach((error: string, index: number) => {
            paramErrors.value[`error_${index}`] = error;
          });
          return false;
        }
        return true;
      } else {
        paramErrors.value.general = response.message || '参数验证失败';
        return false;
      }
    } catch (error: any) {
      paramErrors.value.general = error.message || '参数验证时发生错误';
      return false;
    } finally {
      isValidating.value = false;
    }
  };

  /**
   * 客户端参数验证
   */
  const validateParamsOnClient = (): Record<string, string> => {
    const errors: Record<string, string> = {};

    paramsPanel.paramFormItems.forEach(item => {
      if (!item.param) return;
      
      const { param, value } = item;
      const paramName = param.name;

      // 必填验证
      if (param.required && (value === null || value === undefined || value === '')) {
        errors[paramName] = `${param.label}是必填项`;
        return;
      }

      // 类型验证
      if (value !== null && value !== undefined && value !== '') {
        switch (param.type) {
          case 'number':
            if (isNaN(Number(value))) {
              errors[paramName] = `${param.label}必须是数字`;
            } else if (param.validation) {
              const numValue = Number(value);
              if (param.validation.min !== undefined && numValue < param.validation.min) {
                errors[paramName] = `${param.label}不能小于${param.validation.min}`;
              }
              if (param.validation.max !== undefined && numValue > param.validation.max) {
                errors[paramName] = `${param.label}不能大于${param.validation.max}`;
              }
            }
            break;
          case 'string':
          case 'textarea':
            if (param.validation?.pattern) {
              const regex = new RegExp(param.validation.pattern);
              if (!regex.test(String(value))) {
                errors[paramName] = param.validation.message || `${param.label}格式不正确`;
              }
            }
            break;
        }
      }
    });

    return errors;
  };
  // ==================== 列数据管理 ====================
  
  /**
   * 设置可用列名
   */
  const setAvailableColumns = (columns: string[]) => {
    availableColumns.value = columns;
  };

  /**
   * 获取列选择选项
   */
  const getColumnOptions = () => {
    return availableColumns.value.map(column => ({
      label: column,
      value: column
    }));
  };

  // ==================== 监听器 ====================
  
  // 监听参数变化，实时验证
  watch(
    () => paramsPanel.params,
    () => {
      // 清除之前的错误信息
      paramErrors.value = {};
    },
    { deep: true }
  );

  // ==================== 返回接口 ====================
  
  return {
    // 状态
    paramsPanel,
    currentInstruction,
    instructionLoading,
    paramFormItems,
    paramErrors,
    isValidating,
    availableColumns,
    
    // 计算属性
    isParamsPanelVisible,
    hasSelectedNode,
    hasParamErrors,
    canApplyParams,
    
    // 参数面板控制
    showParamsPanel,
    hideParamsPanel,
    toggleParamsPanel,
    
    // 指令信息管理
    loadInstructionDetail,
    setInstructionCategories,
    findInstructionById,
    
    // 参数表单管理
    initializeParamFormItems,
    updateParamValue,
    validateParams,    
    // 列数据管理
    setAvailableColumns,
    getColumnOptions
  };
}