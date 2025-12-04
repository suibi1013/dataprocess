<template>
  <div class="datasource-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">数据源</h1>
        <p class="page-description">管理和配置各种数据源，包括Excel文件、API接口和数据库连接</p>
      </div>
      <div class="header-actions">
        <button 
          class="btn btn-primary"
          @click="createDataSource"
          :disabled="loading"
        >
          <i class="icon-plus"></i>
          添加数据源
        </button>
      </div>
    </div>

    <!-- 数据源列表 -->
    <div class="datasource-list">
      <!-- 加载状态 -->
      <div v-if="loading && dataSources.length === 0" class="loading-container">
        <div class="loading-spinner"></div>
        <p>正在加载数据源...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="dataSources.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <i class="icon-database"></i>
        </div>
        <h3>暂无数据源</h3>
        <p>您还没有创建任何数据源，点击上方按钮开始添加</p>
        <button class="btn btn-primary" @click="createDataSource">
          添加第一个数据源
        </button>
      </div>

      <!-- 数据源卡片列表 -->
      <div v-else class="datasource-grid">
        <div 
          v-for="dataSource in dataSources" 
          :key="dataSource.id" 
          class="datasource-card"
        >
          <div class="card-header">
            <div class="datasource-info">
              <h3 class="datasource-name">{{ dataSource.name }}</h3>
              <span class="datasource-type">{{ getTypeLabel(dataSource.type) }}</span>
            </div>
            <div class="datasource-status" :class="dataSource.status">
              {{ getStatusLabel(dataSource.status) }}
            </div>
          </div>
          
          <div class="card-body">
            <div class="datasource-config">
              <div v-if="dataSource.type === 'excel'" class="config-info">
                <span class="label">文件数量:</span>
                <span class="value">{{ getExcelFileCount(dataSource.config) }}</span>
              </div>
              <div v-else-if="dataSource.type === 'api'" class="config-info">
                <span class="label">API地址:</span>
                <span class="value">{{ getApiUrl(dataSource.config) }}</span>
              </div>
              <div v-else-if="dataSource.type === 'database'" class="config-info">
                <span class="label">数据库:</span>
                <span class="value">{{ getDatabaseInfo(dataSource.config) }}</span>
              </div>
            </div>
            
            <div class="datasource-meta">
              <div class="meta-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ formatDate(dataSource.createdAt) }}</span>
              </div>
              <div class="meta-item">
                <span class="label">更新时间:</span>
                <span class="value">{{ formatDate(dataSource.updatedAt) }}</span>
              </div>
            </div>
          </div>
          
          <div class="card-actions">
            <button class="btn btn-sm btn-outline" @click="previewDataSource(dataSource.id)">
              预览
            </button>
            <button class="btn btn-sm btn-outline" @click="editDataSource(dataSource.id)">
              编辑
            </button>

            <button class="btn btn-sm btn-danger" @click="deleteDataSource(dataSource.id)">
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="dataSources.length > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="pagination.total"
        @size-change="handlePageSizeChange"
        @current-change="changePage"
      />
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <div class="error-content">
        <i class="icon-alert-circle"></i>
        <span>{{ error }}</span>
        <button class="btn-close" @click="clearError">
          <i class="icon-x"></i>
        </button>
      </div>
    </div>

    <!-- 新增数据源模态框 -->
    <AddEditDataSourceModal
        v-if="dataSourceStore.addDataSourceModalState.visible"
        mode="add"
        :visible="dataSourceStore.addDataSourceModalState.visible"
        @close="dataSourceStore.hideAddDataSourceModal"
        @success="handleDataSourceSuccess"
      />
    
    <!-- 数据预览模态框 -->
    <PreviewDataModal 
      :visible="showPreviewModal"
      :dataSource="dataSourceStore.currentDataSource"
      @close="closePreviewModal"
    />
    

    
    <!-- 编辑数据源模态框 -->
    <AddEditDataSourceModal
      v-if="dataSourceStore.showEditModal"
      mode="edit"
      :visible="dataSourceStore.showEditModal"
      :dataSource="dataSourceStore.currentDataSource"
      @close="dataSourceStore.closeEditModal"
      @success="handleDataSourceSuccess"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useDataSourceStore } from '@/store/dataSourceStore';
import type { ExcelConfig, ApiConfig, DatabaseConfig, DataSource } from '@/types/dataSource';
import AddEditDataSourceModal from '@/components/DataSource/AddEditDataSourceModal.vue';
import PreviewDataModal from '@/components/DataSource/PreviewDataModal.vue';


export default defineComponent({
  name: 'DataSourcePage',
  components: {
     AddEditDataSourceModal,
      PreviewDataModal
    },
  setup() {
    const dataSourceStore = useDataSourceStore();
    // 使用storeToRefs保持响应性
    const { dataSources, loading, error, pagination, showPreviewModal } = storeToRefs(dataSourceStore);

    // 页面加载时获取数据源列表
    onMounted(() => {
      dataSourceStore.fetchDataSources();
    });

    // 获取类型标签
    const getTypeLabel = (type: string) => {
      const labels = {
        excel: 'Excel文件',
        api: 'API接口',
        database: '数据库'
      };
      return labels[type as keyof typeof labels] || type;
    };

    // 获取状态标签
    const getStatusLabel = (status: string) => {
      const labels = {
        active: '正常',
        inactive: '未激活',
        error: '错误'
      };
      return labels[status as keyof typeof labels] || status;
    };

    // 获取Excel文件数量
    const getExcelFileCount = (config: any) => {
      const excelConfig = config as ExcelConfig;
      return excelConfig.files?.length || 0;
    };

    // 获取API地址
    const getApiUrl = (config: any) => {
      const apiConfig = config as ApiConfig;
      return apiConfig.url || '未配置';
    };

    // 获取数据库信息
    const getDatabaseInfo = (config: any) => {
      const dbConfig = config as DatabaseConfig;
      return `${dbConfig.type}://${dbConfig.host}:${dbConfig.port}/${dbConfig.database}` || '未配置';
    };

    // 格式化日期
    const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleString('zh-CN');
    };

    // 创建数据源
    const createDataSource = () => {
      dataSourceStore.showAddDataSourceModal();
    };

    // 预览数据源
    const previewDataSource = async (id: string) => {
      try {
        // 从当前数据源列表中找到对应的数据源
        const dataSource = dataSources.value.find((ds: DataSource) => ds.id === id);
        if (dataSource) {
          // 直接打开预览模态框
          dataSourceStore.openPreviewModal(dataSource);
        } else {
          console.error('未找到数据源:', id);
        }
      } catch (err) {
        console.error('预览数据源失败:', err);
      }
    };
    
    // 关闭预览模态框
    const closePreviewModal = () => {
      dataSourceStore.closePreviewModal();
    };
    




    // 编辑数据源
    const editDataSource = async (id: string) => {
      try {
        // 从当前数据源列表中找到对应的数据源
        const dataSource = dataSources.value.find((ds: DataSource) => ds.id === id);
        if (dataSource) {
          // 打开编辑模态框
          dataSourceStore.editDataSource(dataSource);
        } else {
          console.error('未找到数据源:', id);
        }
      } catch (err) {
        console.error('打开编辑失败:', err);
      }
    };
    
    // 删除数据源
    const deleteDataSource = (id: string) => {
      if (confirm('确定要删除这个数据源吗？')) {
        dataSourceStore.deleteDataSource(id);
      }
    };

    // 切换页面
    const changePage = (page: number) => {
      dataSourceStore.fetchDataSources({ page });
    };
    
    // 处理每页条数变化
    const handlePageSizeChange = (size: number) => {
      // 当每页条数改变时，重置到第一页并重新获取数据
      dataSourceStore.fetchDataSources({ page: 1, pageSize: size });
    };

    // 清除错误
    const clearError = () => {
      dataSourceStore.clearError();
    }
    
    // 处理数据源创建/更新成功
    const handleDataSourceSuccess = async () => {
      // 创建或更新成功后，强制刷新数据源列表
      await dataSourceStore.fetchDataSources();
      // 确保模态框关闭
      if (dataSourceStore.addDataSourceModalState.visible) {
        dataSourceStore.hideAddDataSourceModal();
      }
      if (dataSourceStore.showEditModal) {
        dataSourceStore.closeEditModal();
      }
    };

    return {
      // Store状态 - 使用响应式引用
      dataSources,
      loading,
      error,
      pagination,
      showPreviewModal,
      
      // Store实例
      dataSourceStore,
      
      // 方法
      getTypeLabel,
      getStatusLabel,
      getExcelFileCount,
      getApiUrl,
      getDatabaseInfo,
      formatDate,
      createDataSource,
      previewDataSource,
      editDataSource,
      deleteDataSource,
      changePage,
      handlePageSizeChange,
      clearError,
      closePreviewModal,
      handleDataSourceSuccess
    };
  }
});
</script>

<style scoped>
@import '@/styles/dataSource.css';
.datasource-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background: #f9fafb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 13px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: #9ca3af;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 16px;
  color: #6b7280;
  margin: 0 0 24px 0;
}

.datasource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.datasource-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s;
}

.datasource-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.datasource-info {
  flex: 1;
}

.datasource-name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 4px 0;
}

.datasource-type {
  display: inline-block;
  padding: 4px 8px;
  background: #f3f4f6;
  color: #374151;
  font-size: 12px;
  border-radius: 4px;
}

.datasource-status {
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
}

.datasource-status.active {
  background: #d1fae5;
  color: #065f46;
}

.datasource-status.inactive {
  background: #fef3c7;
  color: #92400e;
}

.datasource-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.card-body {
  margin-bottom: 20px;
}

.config-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.datasource-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.label {
  color: #6b7280;
  font-weight: 500;
}

.value {
  color: #374151;
}

.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  outline: none;
}

.page-size-select:hover {
  border-color: #9ca3af;
}

.page-size-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  max-width: 400px;
  z-index: 1000;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #991b1b;
}

.btn-close {
  background: none;
  border: none;
  color: #991b1b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.btn-close:hover {
  background: #fecaca;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .datasource-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .datasource-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .error-message {
    left: 16px;
    right: 16px;
    top: 16px;
    max-width: none;
  }
}
</style>