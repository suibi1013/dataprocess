<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">添加数据源</h3>
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
                :value="formData.name"
                @input="handleInputChange('name', $event.target.value)"
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
              <select 
                :value="formData.type"
                @change="handleInputChange('type', $event.target.value); handleTypeChange()"
                class="form-select"
                :class="{ error: errors.type }"
              >
                <option value="">请选择数据源类型</option>
                <option value="excel">Excel文件</option>
                <option value="api">API接口</option>
                <option value="database">数据库</option>
              </select>
              <span v-if="errors.type" class="error-message">{{ errors.type }}</span>
            </div>
          </div>
          
          <!-- Excel配置 -->
          <div v-if="formData.type === 'excel'" class="form-section">
            <h4 class="section-title">Excel配置</h4>
            
            <div class="form-group">
              <label class="form-label required">Excel文件</label>
              <input 
                ref="fileInput"
                type="file"
                accept=".xlsx,.xls"
                multiple
                class="form-input"
                @change="handleFileChange"
              >
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
          </div>
          
          <!-- 数据库配置 -->
          <div v-if="formData.type === 'database'" class="form-section">
            <h4 class="section-title">数据库配置</h4>
            
            <div class="form-group">
              <label class="form-label required">数据库类型</label>
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
          </div>
        </form>
      </div>
      
      <!-- 错误信息显示 -->
      <div v-if="creationError" class="error-section">
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
          class="btn btn-outline"
          :disabled="!canTest || loading"
          @click="handleTest"
        >
          <i v-if="testing" class="el-icon-loading"></i>
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <button 
          type="button" 
          class="btn btn-primary"
          :disabled="!canSubmit || loading"
          @click="handleSubmit"
        >
          <i v-if="loading" class="el-icon-loading"></i>
          {{ loading ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useDataSourceStore } from '@/store/dataSourceStore';

// Store
const dataSourceStore = useDataSourceStore();

// 本地状态
const fileInput = ref<HTMLInputElement>();
const testing = ref(false);

// 计算属性 - 从store获取状态
const visible = computed(() => dataSourceStore.addDataSourceModalState.visible);
const formData = computed(() => dataSourceStore.addDataSourceModalState.formData);
const errors = computed(() => dataSourceStore.addDataSourceModalState.formErrors);
const loading = computed(() => dataSourceStore.addDataSourceModalState.isSubmitting || dataSourceStore.creationState.isCreating);
const creationError = computed(() => dataSourceStore.creationState.error);

// 其他计算属性
const canTest = computed(() => {
  if (formData.value.type === 'excel') {
    return formData.value.config.files && formData.value.config.files.length > 0;
  } else if (formData.value.type === 'api') {
    return formData.value.config.url;
  } else if (formData.value.type === 'database') {
    return formData.value.config.host && 
           formData.value.config.port && 
           formData.value.config.database && 
           formData.value.config.username && 
           formData.value.config.password;
  }
  return false;
});

const canSubmit = computed(() => {
  return dataSourceStore.isAddModalFormValid && canTest.value;
});

// 监听弹窗显示状态
watch(() => visible.value, (isVisible) => {
  if (isVisible) {
    resetForm();
  }
});

// 重置表单
const resetForm = () => {
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 处理数据源类型变化
const handleTypeChange = () => {
  dataSourceStore.setDataSourceType(formData.value.type);
  
  // 清除文件选择
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 处理文件选择（支持多选）
const handleFileChange = (event: Event) => {
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
        errors.value.file = `文件 "${file.name}" 不是有效的Excel文件格式`;
        return;
      }
      
      // 验证文件大小（限制为10MB）
      if (file.size > 10 * 1024 * 1024) {
        errors.value.file = `文件 "${file.name}" 大小不能超过10MB`;
        return;
      }
      
      validFiles.push(file);
    }
    
    delete errors.value.file;
    
    // 更新store中的文件配置
    dataSourceStore.updateFormData('config.files', validFiles);
  }
};

// 注意：表单验证逻辑已移至store中的isAddModalFormValid计算属性

// 处理测试连接
const handleTest = async () => {
  try {
    testing.value = true;
    const testData = { ...formData.value };
    
    // 如果是Excel类型，需要处理文件
    if (formData.value.type === 'excel' && formData.value.config.files && formData.value.config.files.length > 0) {
      // 这里应该调用测试Excel文件的API
      // 暂时模拟测试成功
      await new Promise(resolve => setTimeout(resolve, 1000));
    } else {
      await dataSourceStore.testConnection(testData);
    }
  } catch (error) {
    console.error('测试连接失败:', error);
  } finally {
    testing.value = false;
  }
};

// 处理提交
const handleSubmit = async () => {
  try {
    await dataSourceStore.submitAddDataSource();
    // 创建成功后，store会自动关闭窗口，这里不需要额外处理
  } catch (error) {
    console.error('创建数据源失败:', error);
    // 创建失败时，窗口保持打开状态，让用户可以重试
  }
};

// 处理关闭
const handleClose = () => {
  dataSourceStore.hideAddDataSourceModal();
};

// 处理遮罩层点击
const handleOverlayClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    handleClose();
  }
};

// 处理输入变化
const handleInputChange = (field: string, value: any) => {
  dataSourceStore.updateFormData(field, value);
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

.error-message {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #ff4d4f;
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