<template>
  <div class="datasource-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="datasource-info">
        <div class="datasource-icon">
          <i :class="getTypeIcon(dataSource.type)"></i>
        </div>
        <div class="datasource-meta">
          <h3 class="datasource-name">{{ dataSource.name }}</h3>
          <span class="datasource-type">{{ getDataSourceTypeLabel(dataSource.type) }}</span>
        </div>
      </div>
      <div class="datasource-status">
        <span 
          class="status-indicator"
          :class="dataSource.status || 'inactive'"
          :title="getStatusText(dataSource.status || 'inactive')"
        ></span>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="card-content">
      <div class="datasource-description">
        <p v-if="dataSource.description">{{ truncateText(dataSource.description, 80) }}</p>
        <p v-else class="no-description">暂无描述</p>
      </div>
      
      <div class="datasource-config">
        <div class="config-info">
          <span class="config-label">配置:</span>
          <span class="config-value">{{ getDataSourceConfigInfo(dataSource) }}</span>
        </div>
        <div class="datasource-stats">
          <div class="stat-item">
            <span class="stat-label">创建时间:</span>
            <span class="stat-value">{{ formatDate(dataSource.created_at) }}</span>
          </div>
          <div v-if="dataSource.updated_at !== dataSource.created_at" class="stat-item">
            <span class="stat-label">更新时间:</span>
            <span class="stat-value">{{ formatDate(dataSource.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片操作 -->
    <div class="card-actions">
      <button 
        class="btn btn-outline btn-sm"
        @click="$emit('preview', dataSource)"
        title="预览数据"
      >
        <i class="el-icon-view"></i>
        预览
      </button>
      <button 
        class="btn btn-outline btn-sm"
        @click="$emit('process', dataSource)"
        title="数据处理"
      >
        <i class="el-icon-setting"></i>
        处理
      </button>
      <div class="action-dropdown">
        <button class="btn btn-outline btn-sm dropdown-toggle" @click="toggleDropdown">
          <i class="el-icon-more"></i>
        </button>
        <div v-if="showDropdown" class="dropdown-menu">
          <button 
            class="dropdown-item"
            @click="handleEdit"
          >
            <i class="el-icon-edit"></i>
            编辑
          </button>
          <button 
            class="dropdown-item"
            @click="handleDuplicate"
          >
            <i class="el-icon-copy-document"></i>
            复制
          </button>
          <div class="dropdown-divider"></div>
          <button 
            class="dropdown-item danger"
            @click="handleDelete"
          >
            <i class="el-icon-delete"></i>
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import type { DataSource } from '@/types';
import { formatDate, truncateText, getDataSourceTypeLabel, getDataSourceConfigInfo } from '@/utils';

// Props
interface Props {
  dataSource: DataSource;
}

const props = defineProps<Props>();

// Emits
interface Emits {
  edit: [dataSource: DataSource];
  delete: [dataSource: DataSource];
  preview: [dataSource: DataSource];
  process: [dataSource: DataSource];
}

const emit = defineEmits<Emits>();

// 状态
const showDropdown = ref(false);

// 获取数据源类型图标
const getTypeIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'excel': 'el-icon-document',
    'api': 'el-icon-connection',
    'database': 'el-icon-document-copy'
  };
  return iconMap[type] || 'el-icon-question';
};

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'active': '活跃',
    'inactive': '未激活',
    'error': '错误',
    'connecting': '连接中'
  };
  return statusMap[status] || '未知';
};

// 切换下拉菜单
const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

// 处理编辑
const handleEdit = () => {
  showDropdown.value = false;
  emit('edit', props.dataSource);
};

// 处理复制
const handleDuplicate = () => {
  showDropdown.value = false;
  // TODO: 实现复制功能
};

// 处理删除
const handleDelete = () => {
  showDropdown.value = false;
  emit('delete', props.dataSource);
};

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.action-dropdown')) {
    showDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.datasource-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.datasource-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 20px 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.datasource-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.datasource-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  flex-shrink: 0;
}

.datasource-icon i {
  font-size: 20px;
  color: #1890ff;
}

.datasource-meta {
  flex: 1;
  min-width: 0;
}

.datasource-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
  word-break: break-word;
}

.datasource-type {
  display: inline-block;
  padding: 2px 8px;
  background: #e6f7ff;
  color: #1890ff;
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
}

.datasource-status {
  margin-left: 12px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  position: relative;
}

.status-indicator.active {
  background: #52c41a;
  box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
}

.status-indicator.inactive {
  background: #d9d9d9;
}

.status-indicator.error {
  background: #ff4d4f;
  box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.2);
}

.status-indicator.connecting {
  background: #faad14;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(250, 173, 20, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(250, 173, 20, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(250, 173, 20, 0);
  }
}

.card-content {
  padding: 16px 20px;
}

.datasource-description {
  margin-bottom: 16px;
}

.datasource-description p {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.no-description {
  color: #bfbfbf !important;
  font-style: italic;
}

.datasource-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

.config-value {
  font-size: 13px;
  color: #1a1a1a;
  font-weight: 500;
  word-break: break-all;
}

.datasource-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.stat-value {
  font-size: 12px;
  color: #595959;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  background: white;
  color: #595959;
}

.btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-sm {
  padding: 6px 10px;
  font-size: 12px;
}

.btn i {
  font-size: 14px;
}

.action-dropdown {
  position: relative;
  margin-left: auto;
}

.dropdown-toggle {
  padding: 6px 8px;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 1000;
  min-width: 120px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-top: 4px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  font-size: 13px;
  color: #595959;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-align: left;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.dropdown-item.danger {
  color: #ff4d4f;
}

.dropdown-item.danger:hover {
  background: #fff2f0;
}

.dropdown-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 4px 0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .card-header {
    padding: 16px;
  }
  
  .card-content {
    padding: 12px 16px;
  }
  
  .card-actions {
    padding: 12px 16px;
    flex-wrap: wrap;
  }
  
  .datasource-name {
    font-size: 15px;
  }
  
  .stat-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}
</style>