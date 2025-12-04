<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">{{ mode === 'add' ? '添加数据源' : '编辑数据源' }}</h3>
        <button class="close-btn" @click="handleClose">
          <i class="el-icon-close"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <!-- 基本信息 -->
          <div class="form-section">
            <h4 class="section-title">基本信息</h4>
            
            <div class="form-group">
              <label class="form-label required">数据源名称</label>
              <input 
                v-model="formData.name"
                type="text"
                class="form-input"
                :class="{ error: errors.name }"
                placeholder="请输入数据源名称"
                maxlength="50"
              >
              <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">描述</label>
              <textarea 
                v-model="formData.description"
                class="form-textarea"
                placeholder="请输入数据源描述（可选）"
                rows="3"
                maxlength="200"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label required">数据源类型</label>
              <!-- 添加模式下显示选择框，编辑模式下显示只读信息 -->
              <template v-if="mode === 'add'">
                <select 
                  v-model="formData.type"
                  class="form-select"
                  :class="{ error: errors.type }"
                  @change="handleTypeChange"
                >
                  <option value="">请选择数据源类型</option>
                  <option value="excel">Excel文件</option>
                  <option value="api">API接口</option>
                  <option value="database">数据库</option>
                </select>
                <span v-if="errors.type" class="error-message">{{ errors.type }}</span>
              </template>
              <template v-else>
                <div class="type-display">
                  <i :class="getTypeIcon(formData.type)"></i>
                  <span>{{ getTypeLabel(formData.type) }}</span>
                  <span class="type-note">（类型不可修改）</span>
                </div>
              </template>
            </div>
          </div>
          
          <!-- Excel配置 -->
          <div v-if="formData.type === 'excel'" class="form-section">
            <h4 class="section-title">Excel配置</h4>
            
            <div class="form-group">
              <label class="form-label required">Excel文件</label>
              
              <!-- 已上传文件列表 -->
              <div v-if="hasUploadedFiles" class="uploaded-files-list">
                <div class="files-grid">
                  <!-- 添加模式下显示多文件 -->
                  <template v-if="mode === 'add'">
                    <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                    <i class="el-icon-document"></i>
                    <div class="file-details">
                      <p class="file-name">{{ file.name }}</p>
                      <p class="file-size">{{ formatFileSize(file.size) }}</p>
                    </div>
                    <button type="button" class="remove-file-btn" @click="removeFileByIndex(index)">
                      <i class="el-icon-close"></i>
                    </button>
                    </div>
                  </template>
                  <!-- 编辑模式下显示文件 -->
                  <template v-else>
                    <!-- 显示合并后的文件列表 -->
                    <div v-if="mergedFileList.length > 0">
                      <div v-for="file in mergedFileList" :key="file.key" class="file-item">
                        <i class="el-icon-document"></i>
                        <div class="file-details">
                          <p class="file-name">
                            {{ file.file_name || file.name || '未知文件名' }}
                            <span v-if="file.isNew" class="new-file-tag">new</span>
                          </p>
                          <p class="file-size">{{ file.file_size || file.size ? formatFileSize(file.file_size || file.size) : '未知大小' }}</p>
                        </div>
                        <button 
                          type="button" 
                          class="remove-file-btn" 
                          @click="handleRemoveNewFile(file)"
                        >
                          <i class="el-icon-close"></i>
                        </button>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
              
              <!-- 文件上传区域 -->
              <div class="file-upload-area" :style="{ marginTop: hasUploadedFiles ? '12px' : '0' }">
                <input 
                  ref="fileInput"
                  type="file"
                  accept=".xlsx,.xls"
                  multiple
                  class="file-input"
                  @change="handleFileChange"
                >
                <div class="upload-content">
                  <div class="upload-placeholder">
                    <i class="el-icon-upload"></i>
                    <p>{{ mode === 'add' ? '点击添加更多Excel文件' : '点击添加更多Excel文件' }}</p>
                    <p class="upload-hint">支持 .xlsx, .xls 格式，可多选文件</p>
                  </div>
                </div>
              </div>
              
              <span v-if="errors.file" class="error-message">{{ errors.file }}</span>
            </div>
          </div>
          
          <!-- API配置 -->
          <div v-if="formData.type === 'api'" class="form-section">
            <h4 class="section-title">API配置</h4>
            
            <div class="form-group">
              <label class="form-label required">API地址</label>
              <input 
                v-model="formData.config.url"
                type="url"
                class="form-input"
                :class="{ error: errors.url }"
                placeholder="https://api.example.com/data"
              >
              <span v-if="errors.url" class="error-message">{{ errors.url }}</span>
            </div>
            
            <div class="form-group">
              <label class="form-label">请求方法</label>
              <select v-model="formData.config.method" class="form-select">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">请求头</label>
              <textarea 
                v-model="formData.config.headers"
                class="form-textarea"
                placeholder='{ "Authorization": "Bearer token" }'
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">请求参数</label>
              <textarea 
                v-model="formData.config.params"
                class="form-textarea"
                placeholder='{ "page": 1, "size": 100 }'
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">数据路径</label>
              <input 
                v-model="formData.config.dataPath"
                type="text"
                class="form-input"
                placeholder="data.list（用于提取嵌套数据）"
              >
            </div>
            
            <div class="form-actions">
              <button 
                type="button" 
                class="btn btn-outline"
                :disabled="!canTest || loading"
                @click="handleTest"
              >
                <i v-if="testing" class="el-icon-loading"></i>
                {{ testing ? '测试中...' : '测试连接' }}
              </button>
            </div>
          </div>
          
          <!-- 数据库配置 -->
          <div v-if="formData.type === 'database'" class="form-section">
            <h4 class="section-title">数据库配置</h4>
            
            <div class="form-group">
              <label class="form-label">数据库类型</label>
              <!-- 编辑模式下显示只读信息 -->
              <template v-if="mode === 'edit'">
                <div class="type-display">
                  <i :class="getDbTypeIcon(formData.config.dbType)"></i>
                  <span>{{ getDbTypeLabel(formData.config.dbType) }}</span>
                  <span class="type-note">（类型不可修改）</span>
                </div>
              </template>
              <!-- 添加模式下显示选择框 -->
              <template v-else>
                <select 
                  v-model="formData.config.dbType"
                  class="form-select"
                  :class="{ error: errors.dbType }"
                >
                  <option value="">请选择数据库类型</option>
                  <option value="mysql">MySQL</option>
                  <option value="postgresql">PostgreSQL</option>
                  <option value="sqlite">SQLite</option>
                  <option value="oracle">Oracle</option>
                  <option value="sqlserver">SQL Server</option>
                </select>
                <span v-if="errors.dbType" class="error-message">{{ errors.dbType }}</span>
              </template>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label required">主机地址</label>
                <input 
                  v-model="formData.config.host"
                  type="text"
                  class="form-input"
                  :class="{ error: errors.host }"
                  placeholder="localhost"
                >
                <span v-if="errors.host" class="error-message">{{ errors.host }}</span>
              </div>
              <div class="form-group">
                <label class="form-label required">端口</label>
                <input 
                  v-model.number="formData.config.port"
                  type="number"
                  class="form-input"
                  :class="{ error: errors.port }"
                  placeholder="3306"
                  min="1"
                  max="65535"
                >
                <span v-if="errors.port" class="error-message">{{ errors.port }}</span>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label required">数据库名</label>
              <input 
                v-model="formData.config.database"
                type="text"
                class="form-input"
                :class="{ error: errors.database }"
                placeholder="database_name"
              >
              <span v-if="errors.database" class="error-message">{{ errors.database }}</span>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label required">用户名</label>
                <input 
                  v-model="formData.config.username"
                  type="text"
                  class="form-input"
                  :class="{ error: errors.username }"
                  placeholder="username"
                >
                <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
              </div>
              <div class="form-group">
                <label class="form-label required">密码</label>
                <input 
                  v-model="formData.config.password"
                  type="password"
                  class="form-input"
                  :class="{ error: errors.password }"
                  placeholder="password"
                >
                <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">查询语句</label>
              <textarea 
                v-model="formData.config.query"
                class="form-textarea"
                placeholder="SELECT * FROM table_name LIMIT 100"
                rows="4"
              ></textarea>
            </div>
            
            <div class="form-actions">
              <button 
                type="button" 
                class="btn btn-outline"
                :disabled="!canTest || loading"
                @click="handleTest"
              >
                <i v-if="testing" class="el-icon-loading"></i>
                {{ testing ? '测试中...' : '测试连接' }}
              </button>
            </div>
          </div>
        </form>
      </div>
      
      <!-- 错误信息显示（仅添加模式） -->
      <div v-if="mode === 'add' && creationError" class="error-section">
        <div class="error-message">
          <i class="el-icon-warning"></i>
          <span>{{ creationError }}</span>
        </div>
      </div>
      
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="handleClose">
          取消
        </button>

        <button 
          type="button" 
          class="btn btn-primary"
          :disabled="!canSubmit || loading"
          @click="handleSubmit"
        >
          <i v-if="loading" class="el-icon-loading"></i>
          {{ loading ? (mode === 'add' ? '创建中...' : '保存中...') : (mode === 'add' ? '创建' : '保存') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import type { DataSource, DataSourceType } from '@/types/dataSource';
import { validateField } from '@/utils/validationUtils';
import { formatFileSize } from '@/utils/fileUtils';
import { getDataSourceTypeLabel } from '@/utils/formatUtils';
import { useDataSourceStore } from '@/store/dataSourceStore';
import { httpClient } from '@/services/httpClient';

// Props
interface Props {
  visible: boolean;
  mode: 'add' | 'edit';
  dataSource?: DataSource | null;
}

const props = withDefaults(defineProps<Props>(), {
  dataSource: null
});

// Emits
const emit = defineEmits(['close', 'success']);

// Store
const dataSourceStore = useDataSourceStore();

// 状态
const loading = ref(false);
const testing = ref(false);
const fileInput = ref<HTMLInputElement>();
const selectedFiles = ref<File[]>([]); // 用于添加模式的多文件选择
const editModeSelectedFiles = ref<File[]>([]); // 用于编辑模式的多文件选择

// 表单数据
const formData = reactive<DataSource>({
  id: '',
  name: '',
  description: '',
  type: 'excel' as DataSourceType,
  config: {},
  status: 'active',
  createdAt: '',
  updatedAt: ''
});

// 表单错误
const errors = reactive<Record<string, string>>({});

// 计算属性
const canTest = computed(() => {
    if (formData.type === 'api') {
      return !!formData.config.url;
    }
    if (formData.type === 'database') {
      return !!(formData.config.host && formData.config.port && formData.config.database && formData.config.username);
    }
    return false;
  });

const canSubmit = computed(() => {
  if (mode.value === 'add') {
    // 添加模式下，需要确保表单有效并且根据类型有相应的必要配置
    const hasRequiredConfig = formData.type === 'excel' ? selectedFiles.value.length > 0 : true;
    return formData.name && formData.type && Object.keys(errors).length === 0 && hasRequiredConfig;
  }
  // 编辑模式下的验证
  return formData.name && formData.type && Object.keys(errors).length === 0;
});

const mode = computed(() => props.mode);
const creationError = computed(() => mode.value === 'add' ? dataSourceStore.creationState.error : '');

// 判断是否有已上传文件
const hasUploadedFiles = computed(() => {
  if (mode.value === 'add') {
    return selectedFiles.value.length > 0;
  } else {
    // 统一使用多文件模式，只检查files数组
    return (Array.isArray(formData.config.files) && formData.config.files.length > 0) ||
           editModeSelectedFiles.value.length > 0;
  }
});

// 合并的文件列表（用于编辑模式）- 标记新文件
const mergedFileList = computed(() => {
  if (mode.value !== 'edit' || formData.type !== 'excel') return [];
  
  // 获取已上传文件列表
  const uploadedFiles = Array.isArray(formData.config.files) ? [...formData.config.files] : [];
  
  // 创建新添加文件的名称集合，用于快速查找
  const newFileNames = new Set(editModeSelectedFiles.value.map(file => file.name));
  
  // 合并文件列表并标记
  const result = uploadedFiles.map((file, index) => ({
    ...file,
    isNew: newFileNames.has(file.name || file.file_name),
    key: `original-${index}`
  }));
  
  // 对于新添加但不在已上传列表中的文件，也添加到结果中
  editModeSelectedFiles.value.forEach((file, index) => {
    // 检查文件是否已经在结果中（通过文件名匹配）
    const fileName = file.name;
    const exists = result.some(item => item.name === fileName || item.file_name === fileName);
    
    if (!exists) {
      result.push({
        ...file,
        isNew: true,
        key: `new-${index}`
      });
    }
  });
  
  return result;
});

// 清除错误
const clearErrors = () => {
  Object.keys(errors).forEach(key => {
    delete errors[key];
  });
};

// 重置表单（添加模式）
const resetForm = () => {
  Object.assign(formData, {
    id: '',
    name: '',
    description: '',
    type: 'excel' as DataSourceType,
    config: {
      files: []
    },
    status: 'active',
    createdAt: '',
    updatedAt: ''
  });
  
  clearErrors();
  
  // 重置文件选择
  selectedFiles.value = [];
  editModeSelectedFiles.value = [];
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 加载数据源数据（编辑模式）
const loadDataSource = (dataSource: DataSource) => {
  // 复制数据源数据
  const configCopy = { ...dataSource.config };
  
  // 将单文件模式转换为多文件模式
  if (formData.type === 'excel') {
    // 初始化files数组（如果不存在）
    if (!Array.isArray(configCopy.files)) {
      configCopy.files = [];
    }
    
    // 检查是否有单文件配置，如果有则添加到files数组
    if ((configCopy.fileName || configCopy.file_name) && !configCopy.files.length) {
      configCopy.files.push({
        name: configCopy.fileName || configCopy.file_name,
        file_name: configCopy.fileName || configCopy.file_name,
        file_size: configCopy.fileSize || configCopy.file_size || 0,
        size: configCopy.fileSize || configCopy.file_size || 0
      });
      
      // 删除单文件相关配置
      delete configCopy.fileName;
      delete configCopy.file_name;
      delete configCopy.fileSize;
      delete configCopy.file_size;
    }
  }
  
  Object.assign(formData, {
    ...dataSource,
    config: configCopy
  });
  
  // 清除错误
  clearErrors();
  
  // 重置文件选择
  selectedFiles.value = [];
  editModeSelectedFiles.value = []; // 初始化编辑模式的文件列表
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 监听弹窗显示状态和数据源变化
watch([() => props.visible, () => props.dataSource, () => props.mode], ([visible, dataSource, mode]) => {
  if (visible) {
    if (mode === 'edit' && dataSource) {
      loadDataSource(dataSource);
    } else if (mode === 'add') {
      resetForm();
    }
  }
}, { immediate: true });

// 处理数据源类型变化（添加模式）
const handleTypeChange = () => {
  if (formData.type) {
    // 同时更新store中的类型和配置
    dataSourceStore.setDataSourceType(formData.type);
    
    // 同步本地formData配置
    switch (formData.type) {
      case 'excel':
        formData.config = { files: [] };
        break;
      case 'api':
        formData.config = {
          url: '',
          method: 'GET',
          headers: {},
          params: {},
          dataPath: ''
        };
        break;
      case 'database':
        formData.config = {
          dbType: '',
          host: '',
          port: 3306,
          database: '',
          username: '',
          password: ''
        };
        break;
    }
    
    // 清除之前类型的错误
    clearErrors();
  }
  
  // 清除文件选择
  selectedFiles.value = [];
  editModeSelectedFiles.value = [];
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 获取类型图标
const getTypeIcon = (type: DataSourceType) => {
  const icons = {
    excel: 'icon-file-excel',
    api: 'el-icon-connection',
    database: 'el-icon-database'
  };
  return icons[type] || 'el-icon-document';
};

// 获取类型标签
const getTypeLabel = (type: DataSourceType) => {
  return getDataSourceTypeLabel(type);
};

// 获取数据库类型图标
const getDbTypeIcon = (dbType: string) => {
  const icons: Record<string, string> = {
    mysql: 'el-icon-database',
    postgresql: 'el-icon-database',
    sqlite: 'el-icon-database',
    oracle: 'el-icon-database',
    sqlserver: 'el-icon-database'
  };
  return icons[dbType] || 'el-icon-database';
};

// 获取数据库类型标签
const getDbTypeLabel = (dbType: string) => {
  const labels: Record<string, string> = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    sqlite: 'SQLite',
    oracle: 'Oracle',
    sqlserver: 'SQL Server'
  };
  return labels[dbType] || dbType;
};

// 处理文件选择
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  
  if (files && files.length > 0) {
    const validFiles: File[] = [];
    const allowedTypes = ['.xlsx', '.xls'];
    
    // 验证每个文件
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!allowedTypes.includes(fileExtension)) {
        errors.file = `文件 "${file.name}" 不是有效的Excel文件格式`;
        return;
      }
      
      // 验证文件大小（限制为10MB）
      if (file.size > 10 * 1024 * 1024) {
        errors.file = `文件 "${file.name}" 大小不能超过10MB`;
        return;
      }
      
      validFiles.push(file);
    }
    
    delete errors.file;
    loading.value = true;
    
    try {
        // 上传每个文件到服务器
        for (const file of validFiles) {
          const uploadFormData = new FormData();
          uploadFormData.append('file', file);
          
          // 使用项目的httpClient上传文件，自动处理基础URL和错误
          const response = await httpClient.upload('/datasource/upload-file', uploadFormData);
          
          if (response.success && response.data) {
            // 将服务器返回的文件配置添加到表单数据中
            if (!formData.config.files) {
              formData.config.files = [];
            }
            
            if (Array.isArray(formData.config.files)) {
              formData.config.files.push(response.data);
            }
          } else {
            throw new Error(response.message || '文件上传失败');
          }
        }
      
      // 根据模式更新本地文件列表显示
      if (mode.value === 'add') {
        selectedFiles.value = validFiles;
      } else {
        editModeSelectedFiles.value = [...editModeSelectedFiles.value, ...validFiles];
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      errors.file = '文件上传失败，请重试';
    } finally {
      loading.value = false;
    }
  }
};

// 移除单个文件
const removeFileByIndex = (index: number) => {
  if (mode.value === 'add' && index >= 0 && index < selectedFiles.value.length) {
    // 添加模式：从selectedFiles中移除
    selectedFiles.value.splice(index, 1);
  }
};

// 处理移除文件（统一使用多文件模式）
const handleRemoveNewFile = (file: any) => {
  if (mode.value === 'edit') {
    // 从editModeSelectedFiles中移除对应的文件
    const fileName = file.name || file.file_name;
    if (fileName) {
      // 移除本地选中的文件
      const index = editModeSelectedFiles.value.findIndex(f => f.name === fileName);
      if (index > -1) {
        editModeSelectedFiles.value.splice(index, 1);
      }
      
      // 同时从formData.config.files中移除对应的文件
      if (Array.isArray(formData.config.files)) {
        const fileIndex = formData.config.files.findIndex(
          f => f.name === fileName || f.file_name === fileName
        );
        if (fileIndex > -1) {
          formData.config.files.splice(fileIndex, 1);
        }
      }
    }
  }
};

// 移除所有文件（保留方法以避免破坏现有逻辑）
// eslint-disable-next-line @typescript-eslint/no-unused-vars, no-unused-vars
const removeFile = () => {
  if (mode.value === 'add') {
    selectedFiles.value = [];
    // 不直接更新config，只在提交时转换
  } else {
    editModeSelectedFiles.value = [];
  }
  
  // 重置文件输入
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  delete errors.file;
};



// 验证表单
const validateFormData = () => {
  const newErrors: Record<string, string> = {};
  
  // 基本信息验证
  if (!formData.name) {
    newErrors.name = '请输入数据源名称';
  } else if (formData.name.length > 50) {
    newErrors.name = '数据源名称不能超过50个字符';
  }
  
  if (mode.value === 'add' && !formData.type) {
    newErrors.type = '请选择数据源类型';
  }
  
  // 类型特定验证
  if (formData.type === 'api') {
    if (!formData.config.url) {
      newErrors.url = '请输入API地址';
    } else if (!validateField(formData.config.url, { type: 'url' }).valid) {
      newErrors.url = '请输入有效的API地址';
    }
  } else if (formData.type === 'database') {
    if (mode.value === 'add' && !formData.config.dbType) {
      newErrors.dbType = '请选择数据库类型';
    }
    if (!formData.config.host) {
      newErrors.host = '请输入主机地址';
    }
    if (!formData.config.port) {
      newErrors.port = '请输入端口号';
    } else if (formData.config.port < 1 || formData.config.port > 65535) {
      newErrors.port = '端口号必须在1-65535之间';
    }
    if (!formData.config.database) {
      newErrors.database = '请输入数据库名';
    }
    if (!formData.config.username) {
      newErrors.username = '请输入用户名';
    }
    if (!formData.config.password) {
      newErrors.password = '请输入密码';
    }
  }
  
  // 更新错误状态
  clearErrors();
  Object.assign(errors, newErrors);
  
  return Object.keys(newErrors).length === 0;
};

// 处理测试连接
const handleTest = async () => {
  if (!validateFormData()) {
    return;
  }
  
  testing.value = true;
  
  try {
    const testData = { ...formData };
    
    // 直接调用测试连接方法
    await dataSourceStore.testConnection(testData);
    
    // 显示成功消息
    dataSourceStore.setStatusMessage({
      type: 'success',
      message: '连接测试成功！'
    });
  } catch (error) {
    console.error('测试连接失败:', error);
  } finally {
    testing.value = false;
  }
};

// 处理提交
const handleSubmit = async () => {
  if (!validateFormData()) {
    return;
  }
  
  loading.value = true;
  
  try {
    // 创建一个深度复制的提交数据对象，确保嵌套的config对象被正确复制
    const submitData = {
      ...formData,
      config: { ...formData.config }
    };
    
    // 确保files数组存在且格式正确
    if (formData.type === 'excel' && !submitData.config.files) {
      submitData.config.files = [];
    }
    
    if (mode.value === 'add') {
      // 统一使用store的方法创建所有类型数据源
      // handleFileChange中已经上传文件并更新了formData.config.files
      // submitData中已包含完整的文件配置信息
      dataSourceStore.addDataSourceModalState.formData = submitData;
      
      // 调用store的submitAddDataSource方法创建数据源
      // 该方法会调用POST接口并在创建成功后刷新列表
      await dataSourceStore.submitAddDataSource();
    } else {
      // 更新模式下，使用store的updateDataSource方法更新数据源信息
      // 该方法会调用PUT接口并在更新成功后刷新列表
      await dataSourceStore.updateDataSource(formData.id, submitData);
    }
    
    emit('success');
    handleClose();
  } catch (error) {
    console.error(mode.value === 'add' ? '创建数据源失败:' : '更新数据源失败:', error);
  } finally {
    loading.value = false;
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
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-title {
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
}

.close-btn:hover {
  background: #f5f5f5;
  color: #595959;
}

.error-section {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fff2f0;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff4d4f;
  font-size: 14px;
}

.error-message i {
  font-size: 16px;
  flex-shrink: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.form-label.required::after {
  content: ' *';
  color: #ff4d4f;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input:hover,
.form-select:hover,
.form-textarea:hover {
  border-color: #40a9ff;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.form-input.error,
.form-select.error {
  border-color: #ff4d4f;
}

.form-input.error:focus,
.form-select.error:focus {
  box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.2);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #595959;
}

.checkbox-input {
  margin-right: 8px;
}

.type-display {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  color: #595959;
}

.type-display i {
  margin-right: 8px;
  font-size: 16px;
}

.type-note {
  margin-left: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

.current-file-info {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  margin-bottom: 8px;
}

.current-file-info i {
  font-size: 24px;
  color: #52c41a;
  margin-right: 12px;
}

.file-upload-area {
  position: relative;
  border: 2px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.file-upload-area:hover {
  border-color: #40a9ff;
  background: #f0f8ff;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-content {
  padding: 24px;
  text-align: center;
}

.upload-placeholder {
  color: #8c8c8c;
}

.upload-placeholder i {
  font-size: 32px;
  margin-bottom: 12px;
  display: block;
}

.upload-placeholder p {
  margin: 0 0 4px 0;
  font-size: 14px;
}

.upload-hint {
  font-size: 12px;
  color: #bfbfbf;
}

.file-info {
  display: flex;
  align-items: center;
  text-align: left;
}

.file-info i {
  font-size: 24px;
  color: #52c41a;
  margin-right: 12px;
}

.file-details {
  flex: 1;
}

.file-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.file-size {
  margin: 0;
  font-size: 12px;
  color: #8c8c8c;
}

.remove-file-btn {
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

.remove-file-btn:hover {
  background: #ff7875;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}

/* 已上传文件列表样式 */
.uploaded-files-list {
  margin-bottom: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.files-list-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.files-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.file-item i {
  font-size: 20px;
  color: #1890ff;
  margin-right: 12px;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
        margin: 0 0 4px 0;
        font-size: 14px;
        font-weight: 500;
        color: #262626;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      
      .new-file-tag {
        font-size: 12px;
        font-weight: 600;
        color: #1890ff;
        background: #e6f7ff;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
      }

.file-size {
  margin: 0;
  font-size: 12px;
  color: #8c8c8c;
}

.remove-file-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: #ff4d4f;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 8px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.remove-file-btn:hover {
  background: #ff7875;
}

.upload-message {
  text-align: center;
  padding: 20px;
  color: #595959;
}

.upload-message p {
  margin: 0 0 4px 0;
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

.icon-loading {
  animation: spin 1s linear infinite;
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
  
  .form-row {
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