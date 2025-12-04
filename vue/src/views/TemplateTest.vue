<template>
  <div id="templateTestPage" class="page-content">
    <h1>模板测试页面</h1>
    
    <div class="template-test-info">
      <p>模板数量: {{ templates.length }}</p>
      <pre>{{ JSON.stringify(templates, null, 2) }}</pre>
    </div>
    
    <div class="template-grid">
      <div 
        v-for="template in templates" 
        :key="template.id"
        class="template-card"
      >
        <div class="template-preview">
          <div class="template-placeholder">模板预览</div>
        </div>
        <div class="template-info">
          <h3>{{ template.name }}</h3>
          <p>文件名: {{ template.filename || '-' }}</p>
          <p>创建时间: {{ formatDate(template.createTime) }}</p>
          <p>状态: {{ getStatusText(template.status) }}</p>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="templates.length === 0" class="empty-state">
      <p>暂无模板</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { TemplateStatus } from '@/types/template'
import type { Template } from '@/types/template'

// 直接设置默认模板数据进行测试
const defaultTemplates: Template[] = [
  {
    id: 'test-1',
    name: '测试模板1',
    status: TemplateStatus.READY,
    createTime: new Date().toISOString(),
    filename: 'test-1.pptx'
  },
  {
    id: 'test-2',
    name: '测试模板2',
    status: TemplateStatus.READY,
    createTime: new Date().toISOString(),
    filename: 'test-2.pptx'
  }
]

// 响应式数据
const templates = ref<Template[]>(defaultTemplates)

// 生命周期钩子
onMounted(() => {
  // 可以在这里添加初始化逻辑
})

// 格式化日期
function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  } catch (error) {
    return '-' 
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
.template-test-info {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.template-test-info pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-top: 10px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.template-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.template-preview {
  height: 150px;
  background-color: #f0f0f0;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.template-placeholder {
  color: #999;
}

.template-info h3 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 16px;
}

.template-info p {
  margin: 4px 0;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>