<template>
  <div id="addTemplateModal" class="modal" v-if="visible">
    <div class="modal-content">
      <div class="modal-header">
        <h3>新增模板</h3>
        <span class="close" @click="handleCancel">&times;</span>
      </div>
      <div class="modal-body">
        <div class="upload-section">
          <h4>上传模板文件</h4>
          <p>支持 .ppt 和 .pptx 格式，最大文件大小 50MB</p>
          <div class="file-input">
            <input type="file" id="pptFile" accept=".ppt,.pptx" @change="onFileSelected" />
            <label for="pptFile">选择模板文件</label>
          </div>
          <!-- 显示已选择的文件信息 -->
          <div v-if="selectedFile" class="selected-file-info">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
            <button class="remove-file" @click="removeSelectedFile">移除</button>
          </div>
          <div class="template-info">
            <label for="templateName">模板名称:</label>
            <input type="text" id="templateName" v-model="templateName" placeholder="请输入模板名称" />
          </div>
        </div>
        <div id="status" class="status" :class="{ 'success': statusType === 'success', 'error': statusType === 'error', 'visible': statusMessage }">
          {{ statusMessage }}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="handleCancel">取消</button>
        <button class="btn btn-primary" @click="handleUpload">创建模板</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

// 定义组件属性
interface Props {
  visible: boolean;
}

const props = defineProps<Props>();

// 定义事件
const emit = defineEmits<{
  '_cancel': [];
  '_upload': [_templateName: string, _file: File];
}>();

// 响应式数据
const templateName = ref('');
const selectedFile = ref<File | null>(null);
const statusMessage = ref('');
const statusType = ref<'success' | 'error' | ''>('');

// 监听visible变化，重置表单
watch(() => props.visible, (newValue) => {
  if (newValue) {
    resetForm();
  }
});

// 文件选择处理
function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0];
    // 如果用户还没输入模板名称，使用文件名作为默认名称
    if (!templateName.value) {
      const fileName = selectedFile.value.name;
      const nameWithoutExtension = fileName.substring(0, fileName.lastIndexOf('.'));
      templateName.value = nameWithoutExtension;
    }
  }
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 移除已选择的文件
function removeSelectedFile() {
  // 先保存当前选择的文件名，因为后面会设置selectedFile为null
  const currentFileName = selectedFile.value?.name || '';
  
  selectedFile.value = null;
  // 重置文件输入元素
  const fileInput = document.getElementById('pptFile') as HTMLInputElement;
  if (fileInput) {
    fileInput.value = '';
  }
  
  // 如果模板名称是自动从文件名生成的，也重置模板名称
  const fileNameWithoutExt = templateName.value;
  if (fileNameWithoutExt && (!currentFileName || !currentFileName.includes(fileNameWithoutExt))) {
    templateName.value = '';
  }
}

// 处理上传
function handleUpload() {
  const templateNameValue = templateName.value.trim();
  
  if (!selectedFile.value) {
    showStatus('请选择要上传的PPT文件', 'error');
    return;
  }

  if (!templateNameValue) {
    showStatus('请输入模板名称', 'error');
    return;
  }

  // 文件类型验证
  if (!selectedFile.value.name.match(/\.(ppt|pptx)$/i)) {
    showStatus('请选择有效的PPT文件 (.ppt 或 .pptx)', 'error');
    return;
  }

  // 触发上传事件
  emit('upload', templateNameValue, selectedFile.value);
}

// 处理取消
function handleCancel() {
  emit('cancel');
}

// 显示状态消息
function showStatus(message: string, type: 'success' | 'error') {
  statusMessage.value = message;
  statusType.value = type;
}

// 重置表单
function resetForm() {
  templateName.value = '';
  selectedFile.value = null;
  statusMessage.value = '';
  statusType.value = '';
  
  // 重置文件输入元素
  const fileInput = document.getElementById('pptFile') as HTMLInputElement;
  if (fileInput) {
    fileInput.value = '';
  }
}
</script>

<style scoped>
/* 模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1rem;
  border-bottom: 1px solid #dee2e6;
  border-top-left-radius: calc(0.5rem - 1px);
  border-top-right-radius: calc(0.5rem - 1px);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-content .close {
  font-size: 24px;
  cursor: pointer;
  color: #666;
  line-height: 1;
}

.modal-content .close:hover {
  color: #000;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex: 1 1 auto;
}

.upload-section {
  border: 2px dashed #ddd;
  padding: 40px;
  text-align: center;
  border-radius: 8px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.upload-section:hover {
  border-color: #007bff;
  background: #f8f9ff;
}

.upload-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.upload-section p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

.file-input {
  margin: 20px 0;
}

.file-input input[type="file"] {
  display: none;
}

.file-input label {
  display: inline-block;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.file-input label:hover {
  background-color: #0056b3;
}

.selected-file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 15px;
  padding: 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.file-name {
  font-weight: 500;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}

.file-size {
  color: #666;
  font-size: 14px;
  margin-right: 15px;
}

.remove-file {
  padding: 4px 12px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.remove-file:hover {
  background-color: #c82333;
}

.template-info {
  margin-top: 20px;
  text-align: left;
}

.template-info label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.template-info input[type="text"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.template-info input[type="text"]:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.status {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
  display: none;
}

.status.visible {
  display: block;
}

.status.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0.75rem;
  border-top: 1px solid #dee2e6;
  border-bottom-right-radius: calc(0.5rem - 1px);
  border-bottom-left-radius: calc(0.5rem - 1px);
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-content {
    margin: 20px;
  }
}
</style>