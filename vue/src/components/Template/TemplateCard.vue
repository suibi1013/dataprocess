<template>
  <div class="template-card">
    <div class="template-info">
      <h3>{{ props.template.name }}</h3>
      <p>文件名: {{ props.template.filename || '-' }}</p>
      <p>创建时间: {{ formatDate(props.template.createTime) }}</p>
      <p>状态: {{ getStatusText(props.template.status) }}</p>
    </div>
    <div class="template-actions">
      <button 
        class="btn btn-sm btn-secondary" 
        @click="editTemplate(props.template.id)"
        :disabled="props.template.status !== templateStatus.READY"
      >
        模板配置
      </button>
      <button 
        class="btn btn-sm btn-primary" 
        @click="exportData(props.template.id)"
        :disabled="props.template.status !== templateStatus.READY"
      >
        数据导出
      </button>
      <button class="btn btn-sm btn-danger" @click="deleteTemplate(props.template.id)">
        删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Template, TemplateStatus } from '@/types/template';

// 定义组件属性
interface Props {
  template: Template;
}

// 定义事件
const emit = defineEmits<{
  'edit': [_templateId: string];
  'delete': [_templateId: string];
  'export': [_templateId: string];
}>();

const props = defineProps<Props>();

// 暴露TemplateStatus枚举给模板使用
const templateStatus = TemplateStatus;

// 格式化日期
function formatDate(dateString: string): string {
  try {
    return new Date(dateString).toLocaleString();
  } catch (error) {
    return dateString;
  }
}

// 获取状态文本
function getStatusText(status: TemplateStatus): string {
  const statusMap: Record<TemplateStatus, string> = {
    [TemplateStatus.READY]: '已就绪',
    [TemplateStatus.PROCESSING]: '处理中',
    [TemplateStatus.ERROR]: '失败'
  };
  return statusMap[status] || '未知';
}

// 编辑模板
function editTemplate(templateId: string): void {
  emit('edit', templateId);
}

// 删除模板
function deleteTemplate(templateId: string): void {
  emit('delete', templateId);
}

// 数据导出
function exportData(templateId: string): void {
  emit('export', templateId);
}
</script>

<style scoped>
/* 模板卡片样式 */
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

/* 禁用状态 */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn:disabled:hover {
  background-color: inherit;
}
</style>