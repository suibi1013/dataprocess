// 数据源状态管理

import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import { httpClient } from '@/services/httpClient';
import type {
  DataSource,
  CreateDataSourceRequest,
  DataSourceListParams,
  DataSourcePreview,
  ExcelFileInfo,
  ExcelConfig,
  ApiConfig,
  DatabaseConfig,
  DataSourceType,
  DataSourceConfig,
  FormErrors,
  AddDataSourceModalState,
  DataSourceCreationState
} from '@/types';
import { dataSourceService } from '@/services';
import type { ApiResponse } from '@/types/common';

export const useDataSourceStore = defineStore('dataSource', () => {
  // 状态定义
  const dataSources = ref<DataSource[]>([]);
  const currentDataSource = ref<DataSource | null>(null);
  const dataSourcePreview = ref<DataSourcePreview | null>(null);
  const excelFileInfo = ref<ExcelFileInfo | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const pagination = ref({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 模态框状态
  const showAddModal = ref(false);
  const showEditModal = ref(false);
  const showPreviewModal = ref(false);
  const showProcessModal = ref(false);

  // 表单状态
  const formState = reactive<{
    name: string;
    description: string;
    type: '' | DataSourceType;
    config: any;
    loading: boolean;
    errors: Record<string, string>;
  }>({
    type: 'excel',
    name: '',
    description: '',
    config: {
      files: []
    },
    loading: false,
    errors: {}
  });

  // 新增数据源模态框状态
  const addDataSourceModalState = ref<AddDataSourceModalState>({
    visible: false,
    currentStep: 1,
    selectedType: 'excel',
    formData: {
      name: '',
      type: 'excel',
      config: {
        files: []
      }
    },
    formErrors: {},
    isSubmitting: false
  });

  // 步骤控制状态
  const currentStep = ref(1);

  // 数据源创建状态
  const creationState = ref<DataSourceCreationState>({
    loading: false,
    success: false,
    error: null,
    isCreating: false,
    progress: 0,
    currentStep: ''
  });

  // 计算属性
  const hasDataSources = computed(() => dataSources.value.length > 0);
  
  const isConfigValid = computed(() => {
    const config = formState.config;
    const type = formState.type;
    
    switch (type) {
      case 'excel': {
        const excelConfig = config as Partial<ExcelConfig>;
        return !!(excelConfig.files && excelConfig.files.length > 0);
      }
      case 'api': {
        const apiConfig = config as Partial<ApiConfig>;
        return !!(apiConfig.url && apiConfig.url.trim());
      }
      case 'database': {
        const dbConfig = config as Partial<DatabaseConfig>;
        return !!(dbConfig.host && dbConfig.database && dbConfig.username);
      }
      default:
        return false;
    }
  });
  
  const isFormValid = computed(() => {
     const { type, name } = formState;
     return !!(name.trim() && type && isConfigValid.value);
   });
  
  // 表单验证 - 编辑模态框
  const isEditModalFormValid = computed(() => {
    // 基本验证逻辑
    if (!formState.name || !formState.type || !currentDataSource.value?.id) {
      return false;
    }
    
    // 根据不同类型进行验证
    if (formState.type === 'excel') {
      return Array.isArray(formState.config.files) && formState.config.files.length > 0;
    }
    
    if (formState.type === 'api') {
      const config = formState.config || {};
      return !!config['url'] && !!config['method'];
    }
    
    if (formState.type === 'database') {
        return true; // 暂时简化验证，后续可以根据实际情况完善
      }
    
    return true;
  });

  // 新增数据源模态框相关计算属性
  const isAddModalFormValid = computed(() => {
    const { formData } = addDataSourceModalState.value;
    const { type, name, config } = formData;
    
    if (!name.trim()) return false;
    
    switch (type) {
      case 'excel': {
        return (config as ExcelConfig).files && (config as ExcelConfig).files.length > 0;
      }
      case 'api': {
        const apiConfig = config as ApiConfig;
        return apiConfig.url && apiConfig.method;
      }
      case 'database': {
        const dbConfig = config as DatabaseConfig;
        return dbConfig.host && dbConfig.port && dbConfig.database && dbConfig.username;
      }
      default:
        return false;
    }
  });

  const canProceedToNextStep = computed(() => {
    const { currentStep, selectedType, formData } = addDataSourceModalState.value;
    
    if (currentStep === 1) {
      return selectedType !== null;
    }
    
    if (currentStep === 2) {
      return formData.name.trim() !== '';
    }
    
    return true;
  });

  // 获取数据源列表
  const fetchDataSources = async (params?: DataSourceListParams) => {
    try {
      loading.value = true;
      error.value = null;

      const queryParams = {
        page: pagination.value.current,
        page_size: pagination.value.pageSize,
        ...params
      };

      const response: any = await dataSourceService.getDataSources(queryParams);
      
      if (response.success) {
        // 处理API返回的data_sources字段
        const dataSourcesList = response.data_sources || response.data || [];
        
        // 转换API字段到Vue组件期望的格式
        const transformedDataSources = dataSourcesList.map((item: any) => ({
          ...item,
          status: item.is_active ? 'active' : 'inactive', // 映射is_active到status
          createdAt: item.created_time, // 映射created_time到createdAt
          updatedAt: item.updated_time  // 映射updated_time到updatedAt
        }));
        
        dataSources.value = transformedDataSources;
        
        // 使用API返回的total字段更新分页信息
        pagination.value = {
          current: queryParams.page || 1,
          pageSize: queryParams.page_size || 10,
          total: response.total || dataSourcesList.length
        };
      } else {
        throw new Error(response.message || '获取数据源列表失败');
      }
    } catch (err: any) {
      error.value = err.message || '获取数据源列表失败';
      console.error('获取数据源列表失败:', err);
    } finally {
      loading.value = false;
    }
  };

  // 创建数据源
  const createDataSource = async (data: CreateDataSourceRequest) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<DataSource> = await dataSourceService.createDataSource(data);
      if (response.success && response.data) {
        dataSources.value.unshift(response.data);
        pagination.value.total += 1;
        return response.data;
      } else {
        throw new Error(response.message || '创建数据源失败');
      }
    } catch (err: any) {
      error.value = err.message || '创建数据源失败';
      console.error('创建数据源失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 更新数据源
  const updateDataSource = async (id: string, data: Partial<CreateDataSourceRequest>) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<DataSource> = await dataSourceService.updateDataSource(id, data);
      
      if (response.success && response.data) {
        const index = dataSources.value.findIndex(ds => ds.id === id);
        if (index !== -1) {
          dataSources.value[index] = response.data;
        }
        if (currentDataSource.value?.id === id) {
          currentDataSource.value = response.data;
        }
        return response.data;
      } else {
        throw new Error(response.message || '更新数据源失败');
      }
    } catch (err: any) {
      error.value = err.message || '更新数据源失败';
      console.error('更新数据源失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 删除数据源
  const deleteDataSource = async (id: string) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<void> = await dataSourceService.deleteDataSource(id);
      
      if (response.success) {
        dataSources.value = dataSources.value.filter(ds => ds.id !== id);
        pagination.value.total -= 1;
        if (currentDataSource.value?.id === id) {
          currentDataSource.value = null;
        }
      } else {
        throw new Error(response.message || '删除数据源失败');
      }
    } catch (err: any) {
      error.value = err.message || '删除数据源失败';
      console.error('删除数据源失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 获取数据源详情
  const fetchDataSourceDetail = async (id: string) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<DataSource> = await dataSourceService.getDataSource(id);
      
      if (response.success && response.data) {
        currentDataSource.value = response.data;
        return response.data;
      } else {
        throw new Error(response.message || '获取数据源详情失败');
      }
    } catch (err: any) {
      error.value = err.message || '获取数据源详情失败';
      console.error('获取数据源详情失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 预览数据源数据
  const previewDataSource = async (id: string, _params?: any) => {
    try {
      loading.value = true;
      error.value = null;      
      const response: ApiResponse<DataSourcePreview> = await dataSourceService.previewDataSource(id);
      
      if (response.success && response.data) {
        dataSourcePreview.value = response.data;
        return response.data;
      } else {
        throw new Error(response.message || '预览数据失败');
      }
    } catch (err: any) {
      error.value = err.message || '预览数据失败';
      console.error('预览数据失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 测试数据源连接
  const testConnection = async (config: any) => {
    try {
      loading.value = true;
      error.value = null;

      const response: ApiResponse<{ success: boolean; message: string }> = await dataSourceService.testDataSourceConnection(config);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.message || '连接测试失败');
      }
    } catch (err: any) {
      error.value = err.message || '连接测试失败';
      console.error('连接测试失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  // 重置表单状态
  const resetFormState = () => {
    Object.assign(formState, {
      type: 'excel',
      name: '',
      description: '',
      config: {
        files: []
      },
      loading: false,
      errors: {}
    });
  };

  // 设置表单数据（用于编辑）
  const setFormData = (dataSource: DataSource) => {
    // 深拷贝数据源对象，避免直接修改原数据
    const clonedDataSource = JSON.parse(JSON.stringify(dataSource));
    
    // 确保config对象存在
    if (!clonedDataSource.config) {
      clonedDataSource.config = {};
    }
    
    // 为Excel类型特殊处理文件信息
    if (clonedDataSource.type === 'excel') {
      // 处理旧格式（config是数组）
      if (Array.isArray(clonedDataSource.config)) {
        clonedDataSource.config = {
          files: clonedDataSource.config.map((file: any) => ({
            // 保留所有原始字段
            ...file,
            // 确保必要的字段存在
            name: file.fileName || file.name || file.file_name,
            original_name: file.fileName || file.name || file.file_name,
            size: file.fileSize || file.size || file.file_size || 0,
            // 确保file_name字段也存在，用于前端显示
            file_name: file.file_name || file.fileName || file.name
          }))
        };
      } 
      // 处理新格式（config对象包含files数组）
      else if (clonedDataSource.config.files) {
        // 确保files是数组格式，保留所有原始字段
        clonedDataSource.config.files = clonedDataSource.config.files.map((file: any) => ({
          // 保留所有原始字段
          ...file,
          // 确保必要的字段存在
          name: file.fileName || file.name || file.file_name,
          original_name: file.fileName || file.name || file.file_name,
          size: file.fileSize || file.size || file.file_size || 0,
          // 确保file_name字段也存在，用于前端显示
          file_name: file.file_name || file.fileName || file.name
        }));
      }
    }
    
    Object.assign(formState, {
      type: clonedDataSource.type,
      name: clonedDataSource.name,
      description: clonedDataSource.description || '',
      config: clonedDataSource.config,
      loading: false,
      errors: {}
    });
  };

  // 模态框控制
  const openAddModal = () => {
    resetFormState();
    showAddModal.value = true;
  };

  const closeAddModal = () => {
    showAddModal.value = false;
    resetFormState();
  };

  const openEditModal = (dataSource: DataSource) => {
    setFormData(dataSource);
    currentDataSource.value = dataSource;
    showEditModal.value = true;
  };

  const closeEditModal = () => {
    showEditModal.value = false;
    resetFormState();
    currentDataSource.value = null;
  };
  
  // 编辑数据源
  const editDataSource = (dataSource: DataSource) => {
    try {
      // 深拷贝数据源对象，避免直接修改原数据
      const clonedDataSource = JSON.parse(JSON.stringify(dataSource));
      
      // 确保config对象存在
      if (!clonedDataSource.config) {
        clonedDataSource.config = {};
      }
      
      // 为Excel类型特殊处理文件信息
      if (clonedDataSource.type === 'excel') {
        // 处理旧格式（config是数组）
        if (Array.isArray(clonedDataSource.config)) {
          clonedDataSource.config = {
            files: clonedDataSource.config.map((file: any) => ({
              // 保留所有原始字段
              ...file,
              // 确保必要的字段存在
              name: file.fileName || file.name || file.file_name,
              original_name: file.fileName || file.name || file.file_name,
              size: file.fileSize || file.size || file.file_size || 0,
              // 确保file_name字段也存在，用于前端显示
              file_name: file.file_name || file.fileName || file.name
            }))
          };
        } 
        // 处理新格式（config对象包含files数组）
        else if (clonedDataSource.config.files) {
          // 确保files是数组格式，保留所有原始字段
          clonedDataSource.config.files = clonedDataSource.config.files.map((file: any) => ({
            // 保留所有原始字段
            ...file,
            // 确保必要的字段存在
            name: file.fileName || file.name || file.file_name,
            original_name: file.fileName || file.name || file.file_name,
            size: file.fileSize || file.size || file.file_size || 0,
            // 确保file_name字段也存在，用于前端显示
            file_name: file.file_name || file.fileName || file.name
          }));
        }
      }
      
      // 设置原始数据源引用（用于提交时获取ID）
      currentDataSource.value = dataSource;
      
      // 打开编辑模态框（openEditModal内部会调用setFormData）
      openEditModal(clonedDataSource);      
    } catch (error) {
      console.error('打开编辑模态框失败:', error);
    }
  };
  
  // 提交编辑数据源
  const submitEditDataSource = async () => {
      try {
        formState.loading = true;
        formState.errors = {};
        
        // 验证表单
        if (!isEditModalFormValid.value) {
          formState.errors.general = '请完善表单信息';
          return;
        }
        
        // 确保currentDataSource存在
        if (!currentDataSource.value) {
          throw new Error('未找到要编辑的数据源');
        }
        
        // 准备提交数据，只包含需要更新的字段
        const submitData = {
          name: formState.name,
          description: formState.description || '',
          config: formState.config,
          is_active: true // 保持激活状态
        };
        
        // 直接调用API更新数据源
        await httpClient.put(`/datasource/${currentDataSource.value.id}`, submitData);
        
        // 重新获取数据源列表以更新界面
        await fetchDataSources();
        
        // 关闭编辑模态框
        closeEditModal();        
      } catch (error: any) {
        formState.errors.general = error.message || '更新数据源时发生错误';
        console.error('更新数据源失败:', error);
        throw error;
      } finally {
        formState.loading = false;
      }
    };

  const openPreviewModal = (dataSource: DataSource) => {
    currentDataSource.value = dataSource;
    showPreviewModal.value = true;
  };

  const closePreviewModal = () => {
    showPreviewModal.value = false;
    dataSourcePreview.value = null;
  };

  const openProcessModal = (dataSource: DataSource) => {
    currentDataSource.value = dataSource;
    showProcessModal.value = true;
  };

  const closeProcessModal = () => {
    showProcessModal.value = false;
  };

  // 清除错误
  const clearError = () => {
    error.value = null;
  };

  // 设置分页
  const setPagination = (page: number, pageSize?: number) => {
    pagination.value.current = page;
    if (pageSize) {
      pagination.value.pageSize = pageSize;
    }
  };

  // 新增数据源模态框相关方法
  const showAddDataSourceModal = () => {
    addDataSourceModalState.value = {
      visible: true,
      currentStep: 1,
      selectedType: 'excel',
      formData: {
        name: '',
        type: 'excel',
        config: {
          files: []
        }
      },
      formErrors: {},
      isSubmitting: false
    };
  };

  const hideAddDataSourceModal = () => {
    addDataSourceModalState.value.visible = false;
    // 重置状态
    setTimeout(() => {
      addDataSourceModalState.value = {
        visible: false,
        currentStep: 1,
        selectedType: 'excel',
        formData: {
          name: '',
          type: 'excel',
          config: {
            files: []
          }
        },
        formErrors: {},
        isSubmitting: false
      };
    }, 300); // 等待动画完成
  };

  const setDataSourceType = (type: DataSourceType) => {
    addDataSourceModalState.value.selectedType = type;
    addDataSourceModalState.value.formData.type = type;
    
    // 重置配置
    switch (type) {
      case 'excel':
        addDataSourceModalState.value.formData.config = { files: [] };
        break;
      case 'api':
        addDataSourceModalState.value.formData.config = {
          url: '',
          method: 'GET',
          headers: {}
        };
        break;
      case 'database':
        addDataSourceModalState.value.formData.config = {
          type: 'mysql',
          host: '',
          port: 3306,
          database: '',
          username: '',
          password: ''
        };
        break;
    }
  };

  const updateFormData = (field: string, value: any) => {
    if (field.includes('.')) {
      const keys = field.split('.');
      let target: any = addDataSourceModalState.value.formData;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!target[keys[i]]) {
          target[keys[i]] = {};
        }
        target = target[keys[i]];
      }
      
      target[keys[keys.length - 1]] = value;
    } else {
      (addDataSourceModalState.value.formData as any)[field] = value;
    }
    
    // 清除相关错误
    if (addDataSourceModalState.value.formErrors[field]) {
      delete addDataSourceModalState.value.formErrors[field];
    }
  };

  const validateAddModalForm = (): boolean => {
    const errors: FormErrors = {};
    const { formData } = addDataSourceModalState.value;
    
    // 验证名称
    if (!formData.name.trim()) {
      errors.name = '请输入数据源名称';
    }
    
    // 根据类型验证配置
    // 简化验证逻辑，避免调用私有方法
    switch (formData.type) {
      case 'excel': {
        const excelConfig = formData.config as ExcelConfig;
        if (!excelConfig.files || excelConfig.files.length === 0) {
          errors.config = '请选择Excel文件';
        }
        break;
      }
      case 'api': {
        const apiConfig = formData.config as ApiConfig;
        if (!apiConfig.url) {
          errors.config = '请输入API地址';
        }
        break;
      }
      case 'database': {
        const dbConfig = formData.config as DatabaseConfig;
        if (!dbConfig.host) errors.config = '请输入数据库主机地址';
        else if (!dbConfig.database) errors.config = '请输入数据库名称';
        else if (!dbConfig.username) errors.config = '请输入用户名';
        break;
      }
    }

    // 转换FormErrors为Record<string, string>
    const stringErrors: Record<string, string> = {};
    Object.keys(errors).forEach(key => {
      const value = errors[key];
      if (value) stringErrors[key] = value;
    });
    
    addDataSourceModalState.value.formErrors = stringErrors;
    return Object.keys(errors).length === 0;
  };

  const submitAddDataSource = async () => {
    if (!validateAddModalForm()) {
      return;
    }
    
    try {  
      addDataSourceModalState.value.isSubmitting = true;
      creationState.value.isCreating = true;
      creationState.value.currentStep = '正在创建数据源...';
      creationState.value.progress = 0;
      
      const { formData } = addDataSourceModalState.value;
      const createRequest: CreateDataSourceRequest = {
        name: formData.name,
        type: formData.type,
        config: formData.config as DataSourceConfig
      };
      
      creationState.value.progress = 50;
      creationState.value.currentStep = '正在保存配置...';
      
      const newDataSource = await createDataSource(createRequest);
      
      creationState.value.progress = 80;
      creationState.value.currentStep = '正在刷新列表...';
      
      // 创建成功后刷新数据源列表，确保显示最新数据
      await fetchDataSources();
      
      creationState.value.progress = 100;
      creationState.value.currentStep = '创建完成';
      
      // 成功后关闭模态框
      hideAddDataSourceModal();     
      return newDataSource;
    } catch (err: any) {
      creationState.value.error = err.message || '创建数据源失败';
      throw err;
    } finally {
      addDataSourceModalState.value.isSubmitting = false;
      setTimeout(() => {
        creationState.value.isCreating = false;
        creationState.value.progress = 0;
        creationState.value.currentStep = '';
        creationState.value.error = null;
      }, 2000);
    }
  };

  const nextStep = () => {
    if (canProceedToNextStep.value && currentStep.value < 3) {
      currentStep.value++;
    }
  };

  const prevStep = () => {
    if (currentStep.value > 1) {
      currentStep.value--;
    }
  };

  return {
    // 状态
    dataSources,
    currentDataSource,
    dataSourcePreview,
    excelFileInfo,
    loading,
    error,
    pagination,
    showAddModal,
    showEditModal,
    showPreviewModal,
    showProcessModal,
    formState,
    addDataSourceModalState,
    creationState,
    currentStep,

    // 计算属性
    hasDataSources,
    isFormValid,
    isAddModalFormValid,
    canProceedToNextStep,
    isEditModalFormValid,

    // 方法
    fetchDataSources,
    createDataSource,
    updateDataSource,
    deleteDataSource,
    fetchDataSourceDetail,
    previewDataSource,
    testConnection,
    resetFormState,
    setFormData,
    openAddModal,
    closeAddModal,
    openEditModal,
    closeEditModal,
    editDataSource,
    submitEditDataSource,
    openPreviewModal,
    closePreviewModal,
    openProcessModal,
    closeProcessModal,
    clearError,
    setPagination,
    
    // 新增数据源模态框相关方法
    showAddDataSourceModal,
    hideAddDataSourceModal,
    setDataSourceType,
    updateFormData,
    validateAddModalForm,
    submitAddDataSource,
    nextStep,
    prevStep
  };
});