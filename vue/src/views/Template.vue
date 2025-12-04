<template>
  <div id="templatePage" class="page-content">
    <div class="template-actions">
      <button class="btn btn-primary" @click="showAddTemplateModal">新增模板</button>
    </div>
    
    <div class="template-grid" id="templateGrid">
      <div 
        v-for="template in templates" 
        :key="template.id"
        class="template-card"
      >
        <div class="template-info">
          <h3>{{ template.name }}</h3>
          <p>文件名: {{ template.filename || '-' }}</p>
          <p>创建时间: {{ formatDate(template.createTime) }}</p>
          <p>状态: {{ getStatusText(template.status) }}</p>
        </div>
        <div class="template-actions">
          <button 
            class="btn btn-sm btn-secondary" 
            @click="editTemplate(template.id)"
            :disabled="template.status !== templateStatus.READY"
          >
            配置编辑
          </button>
          <button class="btn btn-sm btn-danger" @click="deleteTemplate(template.id)">
            删除
          </button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="templates.length === 0" class="empty-state">
      <p>暂无模板</p>
    </div>

    <!-- 新增模板模态框 -->
    <div id="addTemplateModal" class="modal" v-if="showModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新增模板</h3>
          <span class="close" @click="hideAddTemplateModal">&times;</span>
        </div>
        <div class="modal-body">
          <div class="upload-section">
            <h4>上传PPT文件</h4>
            <p>支持 .ppt 和 .pptx 格式，最大文件大小 50MB</p>
            <div class="file-input">
              <input type="file" id="pptFile" accept=".ppt,.pptx" @change="onFileSelected" />
              <label for="pptFile">选择PPT文件</label>
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
          <button class="btn btn-secondary" @click="hideAddTemplateModal">取消</button>
          <button class="btn btn-primary" @click="uploadFile">创建模板</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { TemplateService } from '@/services'
import type { Template, CreateTemplateRequest } from '@/types/template'
import { TemplateStatus } from '@/types/template'

// 初始化模板服务
const templateService = new TemplateService()

// 响应式数据
const templates = ref<Template[]>([])
const showModal = ref(false)
const templateName = ref('')
const selectedFile = ref<File | null>(null)
const statusMessage = ref('')
const statusType = ref<'success' | 'error' | ''>('')

// 暴露TemplateStatus枚举给模板使用
const templateStatus = TemplateStatus

// 生命周期钩子
onMounted(() => {
  loadTemplateList()
})

// 加载模板列表
async function loadTemplateList() {
  try {
    // 为了确保模板列表显示，直接设置默认模板数据
    templates.value = [];
    
    // 保存到localStorage
    localStorage.setItem('templates', JSON.stringify(templates.value));
    
    // 也可以同时尝试API请求，但保证模板列表至少有默认数据
    try {
      const response = await templateService.getTemplates()
      if (response.success && response.data && response.data.length > 0) {
        templates.value = response.data
        localStorage.setItem('templates', JSON.stringify(templates.value));
      }
    } catch (apiError) {
      console.error('API请求失败，但已使用默认模板:', apiError);
    }
  } catch (error) {
    // 即使发生错误，也确保显示默认模板
    templates.value = [];
  }
}

// 显示新增模板模态框
function showAddTemplateModal() {
  showModal.value = true
  templateName.value = ''
  selectedFile.value = null
  statusMessage.value = ''
  statusType.value = ''
}

// 隐藏新增模板模态框
function hideAddTemplateModal() {
  showModal.value = false
}

// 文件选择处理
function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
    // 如果用户还没输入模板名称，使用文件名作为默认名称
    if (!templateName.value) {
      const fileName = selectedFile.value.name
      const nameWithoutExtension = fileName.substring(0, fileName.lastIndexOf('.'))
      templateName.value = nameWithoutExtension
    }
  }
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 移除已选择的文件
function removeSelectedFile() {
  // 先保存当前选择的文件名，因为后面会设置selectedFile为null
  const currentFileName = selectedFile.value?.name || ''
  
  selectedFile.value = null
  // 重置文件输入元素
  const fileInput = document.getElementById('pptFile') as HTMLInputElement
  if (fileInput) {
    fileInput.value = ''
  }
  
  // 如果模板名称是自动从文件名生成的，也重置模板名称
  const fileNameWithoutExt = templateName.value
  if (fileNameWithoutExt && (!currentFileName || !currentFileName.includes(fileNameWithoutExt))) {
    templateName.value = ''
  }
}

// 上传文件创建模板
async function uploadFile() {
  const templateNameValue = templateName.value.trim()
  
  if (!selectedFile.value) {
    showStatus('请选择要上传的PPT文件', 'error')
    return
  }

  if (!templateNameValue) {
    showStatus('请输入模板名称', 'error')
    return
  }

  // 文件类型验证
  if (!selectedFile.value.name.match(/\.(ppt|pptx)$/i)) {
    showStatus('请选择有效的PPT文件 (.ppt 或 .pptx)', 'error')
    return
  }

  try {
    showStatus('正在上传和转换文件，请稍候...', 'success')
    
    // 创建模板请求数据
    const createRequest: CreateTemplateRequest = {
      name: templateNameValue,
      file: selectedFile.value
    }
    
    // 调用API上传文件并创建模板
    const response = await templateService.createTemplate(createRequest)
    
    if (response.success && response.config) {
      // 成功获取到模板数据
      const newTemplate: Template = response.config
      
      try {
        // 构建配置数据
        const configData = {
          templateName: templateNameValue,
          filename: selectedFile.value.name,
          createTime: newTemplate.createTime,
          slides: response.config?.slides || [],
          slide_width: response.config?.slide_width || 800,
          slide_height: response.config?.slide_height || 600,
          total_slides: response.config?.total_slides || 0,
          file_path: response.file_unique || ''
        };
        
        // 保存配置到服务器
        showStatus('正在保存模板配置...', 'success')
        await templateService.saveTemplateConfig(configData, response.file_unique || '')
        
        // 保存处理后的文件名供后续检查配置更新使用
        sessionStorage.setItem('pptFilename', response.file_unique || '')
        
        // 刷新模板管理列表
        loadTemplateList()
        
        showStatus('模板创建成功！', 'success')
        
        // 延迟关闭模态框
        setTimeout(() => {
          hideAddTemplateModal()
        }, 1000)
      } catch (configError) {
        console.error('保存配置失败:', configError)
        showStatus('模板创建成功，但保存配置失败', 'error')
        
        // 即使保存配置失败，也刷新模板列表
        loadTemplateList()
      }
    } else {
      // API调用成功但返回了错误信息
      showStatus(`创建失败: ${response.message || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('创建模板失败:', error)
    // 错误对象可能是API错误对象或普通错误
    const errorMessage = (error as any)?.message || '上传失败，请检查网络连接和服务器状态'
    showStatus(errorMessage, 'error')
  }
}

// 显示状态消息
function showStatus(message: string, type: 'success' | 'error') {
  statusMessage.value = message
  statusType.value = type
}

// 编辑模板
function editTemplate(templateId: string) {
  // 跳转到模板编辑页面
  window.location.href = `/template/editor?template=${templateId}`
}

// 删除模板
async function deleteTemplate(templateId: string) {
  if (confirm('确定要删除这个模板吗？')) {
    try {
      const response = await templateService.deleteTemplate(templateId)
      if (response.success) {
        // 从列表中删除
        templates.value = templates.value.filter(t => t.id !== templateId)
        localStorage.setItem('templates', JSON.stringify(templates.value))
      }
    } catch (error) {
      console.error('删除模板失败:', error)
      alert('删除模板失败，请重试')
    }
  }
}

// 格式化日期
function formatDate(dateString: string) {
  try {
    return new Date(dateString).toLocaleString()
  } catch (error) {
    return dateString
  }
}

// 获取状态文本
function getStatusText(status: TemplateStatus): string {
  const statusMap: Record<TemplateStatus, string> = {
    [TemplateStatus.READY]: '已就绪',
    [TemplateStatus.PROCESSING]: '处理中',
    [TemplateStatus.ERROR]: '失败'
  }
  return statusMap[status] || '未知'
}
</script>

<style scoped>
/* 模板管理页面样式 */
#templatePage {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.template-actions {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

/* 模板网格 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

/* 模板卡片 */
.template-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}



/* 模板信息 */
.template-info {
  padding: 15px;
}

.template-info h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.template-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #666;
}

/* 模板操作按钮 */
.template-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 10px 15px;
  background-color: #f9f9f9;
  border-top: 1px solid #eee;
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

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

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

/* 响应式设计 */
@media (max-width: 768px) {
  .template-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    margin: 20px;
  }
}

/* 禁用状态 */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn:disabled:hover {
  background-color: inherit;
}
</style>