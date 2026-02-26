<template>
  <div id="templatePage" class="page-content">
    <div class="template-actions">
      <button class="btn btn-primary" @click="showModal = true">新增模板</button>
    </div>
    
    <div class="template-grid" id="templateGrid">
      <template v-if="templates.length > 0">
        <template-card 
          v-for="template in templates" 
          :key="template.id"
          :template="template"
          @edit="editTemplate"
          @delete="deleteTemplate"
          @export="exportTemplateData"
          ref="templateCards"
        />
      </template>
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <p>暂无模板</p>
      </div>
    </div>
    
    <!-- 新增模板模态框 -->
    <add-template-modal
      :visible="showModal"
      @cancel="showModal = false"
      @upload="handleUpload"
    />
    
    <!-- 模板配置编辑器模态框 -->
    <template-editor
      v-model:visible="showEditorModal"
      :template-id="selectedTemplateId"
      @close="showEditorModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { TemplateService } from '@/services'
import type { Template, CreateTemplateRequest } from '@/types/template'
import TemplateCard from '@/components/Template/TemplateCard.vue'
import AddTemplateModal from '@/components/Template/AddTemplateModal.vue'
import TemplateEditor from '@/components/Template/TemplateEditor.vue'

// 初始化模板服务
const templateService = new TemplateService()

// 响应式数据
const templates = ref<Template[]>([])
const showModal = ref(false)
const showEditorModal = ref(false)
const selectedTemplateId = ref('')

// 模板卡片引用
const templateCards = ref<InstanceType<typeof TemplateCard>[]>([])

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
      }
    } catch (apiError) {
      console.error('API请求失败，但已使用默认模板:', apiError);
    }
  } catch (error) {
    // 即使发生错误，也确保显示默认模板
    templates.value = [];
  }
}

// 处理上传
async function handleUpload(templateName: string, file: File) {
  try {
    // 创建模板请求数据
    const createRequest: CreateTemplateRequest = {
      name: templateName,
      file: file
    }
    
    // 调用API上传文件并创建模板
    const response = await templateService.createTemplate(createRequest)
    
    if (response.success && response.data) {
      try {
        // 构建配置数据
        const configData = {
          template_name: templateName,
          file_name: file.name,
          file_size: file.size,
          file_path: response.data.file_path || '',
          create_time: response.data.create_time,
          slides: response.data.slides || [],
          slide_width: response.data.slide_width || 800,
          slide_height: response.data.slide_height || 600,
          total_slides: response.data.total_slides || 0,
          id: response.data.template_unique_id || '',
        };
        
        // 保存配置到服务器
        await templateService.saveTemplateConfig(configData)
        
        // 刷新模板管理列表
        loadTemplateList()
        
        // 关闭模态框
        showModal.value = false
      } catch (configError) {
        console.error('保存配置失败:', configError)
        alert('模板创建成功，但保存配置失败')
        
        // 即使保存配置失败，也刷新模板列表
        loadTemplateList()
      }
    } else {
      // API调用成功但返回了错误信息
      alert(`创建失败: ${response.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('创建模板失败:', error)
    // 错误对象可能是API错误对象或普通错误
    const errorMessage = (error as any)?.message || '上传失败，请检查网络连接和服务器状态'
    alert(errorMessage)
  }
}

// 编辑模板
function editTemplate(templateId: string) {
  // 设置选中的模板ID并显示模板配置编辑器
  selectedTemplateId.value = templateId
  showEditorModal.value = true
}

// 删除模板
async function deleteTemplate(templateId: string) {
  if (confirm('确定要删除这个模板吗？')) {
    try {
      const response = await templateService.deleteTemplate(templateId)
      if (response.success) {
        // 刷新模板管理列表
        loadTemplateList()
      }
    } catch (error) {
      console.error('删除模板失败:', error)
      alert('删除模板失败，请重试')
    }
  }
}

// 模板生成
async function exportTemplateData(templateId: string) {
  try {
    await templateService.replaceTemplateData(templateId)
  } catch (error) {
    console.error('模板生成失败:', error)
    alert(`模板生成失败: ${(error as Error).message || '未知错误'}`)
  } finally {
    // 重置对应模板卡片的加载状态
    const cardIndex = templates.value.findIndex(t => t.id === templateId)
    if (cardIndex !== -1 && templateCards.value[cardIndex]) {
      templateCards.value[cardIndex].resetExportStatus()
    }
  }
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

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
  grid-column: 1 / -1;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>