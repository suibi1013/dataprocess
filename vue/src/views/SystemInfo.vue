<template>
  <div class="SystemInfo-page">    
    <div class="SystemInfo-content">
      <div class="info-section">
        <h2>系统介绍</h2>
        <p>
          数据可视化是一个功能强大的数据管理和流程可视化设计工具，提供直观易用的用户界面和丰富的功能特性。
        </p>
      </div>
      
      <div class="features-section">
        <h2>主要功能</h2>
        <div class="features-grid">
          <div class="feature-item">
            <div class="feature-icon">🎨</div>
            <h3>模板管理</h3>
            <p>创建和管理自定义转换模板，支持多种样式和布局选项</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <h3>数据源集成</h3>
            <p>连接多种数据库，实现动态数据展示和实时更新</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon">⚡</div>
            <h3>快速转换</h3>
            <p>高效的转换引擎，快速将PPT文件转换为响应式HTML页面</p>
          </div>
        </div>
      </div>      
      <!-- 数据备份还原功能 -->
      <div class="backup-section">
        <h2>数据备份与还原</h2>
        <div class="backup-content">
          <!-- 备份操作 -->
          <div class="backup-actions">
            <div class="action-card">
              <h3>数据备份</h3>
              <p>创建当前数据库的备份文件，不包含指令相关表</p>
              <button 
                class="action-btn backup-btn" 
                @click="handleBackup" 
                :disabled="isLoading"
              >
                <span v-if="isLoading">⏳ 备份中...</span>
                <span v-else>💾 创建备份</span>
              </button>
            </div>
            
            <div class="action-card">
              <h3>数据还原</h3>
              <p>从备份文件中还原数据库数据</p>
              <div class="restore-actions">
                <input 
                  type="file" 
                  ref="restoreFileInput"
                  style="display: none" 
                  accept=".zip" 
                  @change="handleFileSelect"
                >
                <button 
                  class="action-btn restore-btn" 
                  @click="handleRestoreClick"
                  :disabled="isLoading"
                >
                  <span v-if="isLoading">⏳ 还原中...</span>
                  <span v-else>📂 选择备份文件</span>
                </button>
              </div>
              <div v-if="selectedFile" class="selected-file">
                已选择: {{ selectedFile.name }}
                <button class="remove-file" @click="selectedFile = null">✕</button>
              </div>
            </div>
          </div>
          
          <!-- 备份列表 -->
          <div class="backup-list-section">
            <h3>备份文件列表</h3>
            <div class="backup-list">
              <div 
                v-for="backup in backupList" 
                :key="backup.filename"
                class="backup-item"
              >
                <div class="backup-info">
                  <div class="backup-name">{{ backup.filename }}</div>
                  <div class="backup-meta">
                    <span>{{ backup.create_time }}</span>
                    <span class="backup-size">{{ formatFileSize(backup.size) }}</span>
                  </div>
                </div>
                <div class="backup-actions">
                  <button 
                    class="icon-btn" 
                    @click="handleDownload(backup.filename)"
                    title="下载备份文件"
                  >
                    ⬇️
                  </button>
                  <button 
                    class="icon-btn delete-btn" 
                    @click="handleDelete(backup.filename)"
                    title="删除备份文件"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <div v-if="backupList.length === 0" class="empty-backups">
                暂无备份文件
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="contact-section">
        <h2>联系信息</h2>
        <div class="contact-grid">
          <div class="contact-item">
            <div class="contact-icon">📧</div>
            <div>
              <strong>邮箱支持</strong>
              <p>support@dataprocess.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">🌐</div>
            <div>
              <strong>官方网站</strong>
              <p>www.dataprocess.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">📚</div>
            <div>
              <strong>文档中心</strong>
              <p>docs.dataprocess.com</p>
            </div>
          </div>
        </div>
      </div>      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { systemService, type BackupFile } from '../services/systemService';

// 状态变量
const isLoading = ref(false);
const backupList = ref<BackupFile[]>([]);
const selectedFile = ref<File | null>(null);
const restoreFileInput = ref<HTMLInputElement | null>(null);

// 处理还原按钮点击
const handleRestoreClick = () => {
  if (restoreFileInput.value) {
    restoreFileInput.value.click();
  }
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 加载备份列表
const loadBackupList = async () => {
  try {
    const response = await systemService.getBackupList();
    if (response.success && response.data) {
      backupList.value = response.data;
    }
  } catch (error) {
    console.error('获取备份列表失败:', error);
  }
};

// 处理备份
const handleBackup = async () => {
  try {
    isLoading.value = true;
    const response = await systemService.backupDatabase();
    if (response.success) {
      alert('备份成功！');
      await loadBackupList(); // 刷新备份列表
    } else {
      alert('备份失败: ' + (response.message || '未知错误'));
    }
  } catch (error) {
    console.error('备份失败:', error);
    alert('备份失败，请检查控制台日志');
  } finally {
    isLoading.value = false;
  }
};

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
    handleRestore();
  }
};

// 处理还原
const handleRestore = async () => {
  if (!selectedFile.value) return;
  
  try {
    isLoading.value = true;
    const response = await systemService.uploadAndRestore(selectedFile.value);
    if (response.success) {
      alert('还原成功！');
      selectedFile.value = null; // 清空选择的文件
      await loadBackupList(); // 刷新备份列表
    } else {
      alert('还原失败: ' + (response.message || '未知错误'));
    }
  } catch (error) {
    console.error('还原失败:', error);
    alert('还原失败，请检查控制台日志');
  } finally {
    isLoading.value = false;
  }
};

// 处理下载
const handleDownload = async (filename: string) => {
  try {
    await systemService.downloadBackup(filename);
  } catch (error) {
    console.error('下载失败:', error);
    alert('下载失败，请检查控制台日志');
  }
};

// 处理删除
const handleDelete = async (filename: string) => {
  if (!confirm(`确定要删除备份文件 ${filename} 吗？`)) return;
  
  try {
    const response = await systemService.deleteBackup(filename);
    if (response.success) {
      alert('删除成功！');
      await loadBackupList(); // 刷新备份列表
    } else {
      alert('删除失败: ' + (response.message || '未知错误'));
    }
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败，请检查控制台日志');
  }
};

// 页面加载时获取备份列表
onMounted(() => {
  loadBackupList();
});
</script>

<style scoped>
/* 原有样式保持不变 */
.SystemInfo-page {
  padding: 30px;
  max-width: 1000px;
  margin: 0 auto;
  line-height: 1.6;
}

.SystemInfo-header {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px solid #ecf0f1;
}

.SystemInfo-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.version {
  color: #7f8c8d;
  font-size: 1.1rem;
  font-weight: 500;
}

.SystemInfo-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.info-section,
.features-section,
.tech-section,
.contact-section,
.system-info,
.backup-section {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.info-section h2,
.features-section h2,
.tech-section h2,
.contact-section h2,
.system-info h2,
.backup-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 600;
}

.info-section p {
  color: #7f8c8d;
  font-size: 1.1rem;
  text-align: justify;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 25px;
}

.feature-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #ecf0f1;
  border-radius: 8px;
  transition: transform 0.2s ease;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.feature-item h3 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 1.2rem;
}

.feature-item p {
  color: #7f8c8d;
  font-size: 0.95rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.tech-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.tech-item strong {
  color: #2c3e50;
}

.tech-item span {
  color: #7f8c8d;
  font-family: 'Courier New', monospace;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.contact-icon {
  font-size: 2rem;
}

.contact-item strong {
  color: #2c3e50;
  display: block;
  margin-bottom: 5px;
}

.contact-item p {
  color: #7f8c8d;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.info-label {
  color: #2c3e50;
  font-weight: 500;
}

.info-value {
  color: #7f8c8d;
  font-family: 'Courier New', monospace;
}

/* 新增备份还原样式 */
.backup-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.backup-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.action-card {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 10px;
  text-align: center;
  border: 1px solid #ecf0f1;
  transition: all 0.2s ease;
}

.action-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.action-card h3 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 1.2rem;
}

.action-card p {
  color: #7f8c8d;
  margin-bottom: 20px;
  font-size: 0.95rem;
}

.action-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.backup-btn {
  background-color: #3498db;
  color: white;
}

.backup-btn:hover:not(:disabled) {
  background-color: #2980b9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
}

.restore-btn {
  background-color: #27ae60;
  color: white;
}

.restore-btn:hover:not(:disabled) {
  background-color: #229954;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selected-file {
  margin-top: 15px;
  padding: 10px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.remove-file {
  background: none;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  font-size: 1rem;
  margin-left: 10px;
}

.backup-list-section {
  margin-top: 20px;
}

.backup-list-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1.2rem;
}

.backup-list {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.backup-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #ecf0f1;
  transition: background-color 0.2s ease;
}

.backup-item:last-child {
  border-bottom: none;
}

.backup-item:hover {
  background: white;
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.backup-name {
  font-weight: 500;
  color: #2c3e50;
}

.backup-meta {
  font-size: 0.85rem;
  color: #7f8c8d;
  display: flex;
  gap: 15px;
}

.backup-size {
  color: #95a5a6;
}

.backup-actions {
  display: flex;
  gap: 10px;
}

.icon-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.2s ease;
  color: #7f8c8d;
}

.icon-btn:hover {
  background: white;
  color: #2c3e50;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.delete-btn:hover {
  color: #e74c3c;
}

.empty-backups {
  padding: 30px;
  text-align: center;
  color: #95a5a6;
  font-style: italic;
}

@media (max-width: 768px) {
  .SystemInfo-page {
    padding: 20px;
  }
  
  .SystemInfo-header h1 {
    font-size: 2rem;
  }
  
  .features-grid,
  .tech-grid,
  .contact-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-section,
  .features-section,
  .tech-section,
  .contact-section,
  .system-info,
  .backup-section {
    padding: 20px;
  }
  
  .backup-actions {
    grid-template-columns: 1fr;
  }
  
  .backup-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .backup-actions {
    align-self: flex-end;
  }
}
</style>