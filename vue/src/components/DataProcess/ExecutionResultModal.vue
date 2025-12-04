<template>
  <Modal
    :visible="visible"
    @update:visible="onUpdateVisible"
    title="执行结果"
    :ok-text="'关闭'"
    :cancel-text="''"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :center="true"
    @ok="onHandleResultModalOk"
  >
    <div class="result-modal-container">
      <div v-if="resultModalData" class="result-content">
        <!-- 状态文本区域 -->
        <div class="status-section">
          <div class="status-text">
            执行状态：{{ resultModalData.success ? '成功' : '失败' }}
          </div>
        </div>
        
        <!-- 结果标签页 -->
        <div v-if="resultModalData">
          <el-tabs :model-value="activeTab" type="border-card" @update:model-value="onUpdateActiveTab">
            <!-- 最终结果标签页 -->
            <el-tab-pane 
              label="最终结果"
              name="finalResult"
              :closable="false"
            >
              <div class="tab-content">
                <div v-if="isJsonString(resultModalData.finalResult)" class="json-container">
                  <vue-json-pretty 
                    v-if="parseJson(resultModalData.finalResult)"
                    :data="parseJson(resultModalData.finalResult)"
                    :highlight-key="highlightKey"
                    :show-line-number="true"
                    :highlight-value="highlightValue"
                    :selectable="false"
                    :expand-depth="2"
                    :show-ellipsis="true"
                    :copied-length="20"
                    :show-copy="true"
                    @copied="onCopied"
                  />
                </div>
                <div v-else class="text-container">
                  <div class="url-content" v-html="formatTextWithUrls(resultModalData.finalResult || '')"></div>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 执行详情标签页 -->
            <el-tab-pane 
              label="执行详情"
              name="details"
              :closable="false"
            >
              <div class="tab-content">
                <div v-if="isJsonString(resultModalData.details)" class="json-container">
                  <vue-json-pretty 
                    v-if="parseJson(resultModalData.details)"
                    :data="parseJson(resultModalData.details)"
                    :highlight-key="highlightKey"
                    :show-line-number="true"
                    :highlight-value="highlightValue"
                    :selectable="false"
                    :expand-depth="2"
                    :show-ellipsis="true"
                    :copied-length="20"
                    :show-copy="true"
                    @copied="onCopied"
                  />
                </div>
                <div v-else class="text-container">
                  <div class="url-content" v-html="formatTextWithUrls(resultModalData.details || '')"></div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">

import Modal from '@/components/Common/Modal.vue';
import { ElTabs, ElTabPane, ElMessage } from 'element-plus';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';

// Props
interface Props {
  visible: boolean;
  resultModalData: {
    success: boolean;
    title: string;
    message: string;
    details?: string;
    finalResult?: string;
  } | null;
  activeTab: string;
}

defineProps<Props>();

// Emits
interface Emits {
  'update:visible': [visible: boolean];
  'update:activeTab': [tab: string];
  handleResultModalOk: [];
}

const emit = defineEmits<Emits>();

// 更新可见性
const onUpdateVisible = (visible: boolean) => {
  emit('update:visible', visible);
};

// 更新活动标签页
const onUpdateActiveTab = (tab: string | number) => {
  emit('update:activeTab', tab as string);
};

// 处理结果模态框确定按钮点击
const onHandleResultModalOk = () => {
  emit('handleResultModalOk');
};

// 判断是否为JSON字符串
const isJsonString = (str: string | undefined): boolean => {
  if (!str) return false;
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
};

// 解析JSON字符串
const parseJson = (str: string | undefined): any => {
  if (!str) return null;
  try {
    return JSON.parse(str);
  } catch (e) {
    return null;
  }
};

// 高亮URL类型的值
const highlightValue = (value: string): boolean => {
  // 检测是否为URL
  const urlPattern = /^(https?:\/\/|ftp:\/\/|mailto:|file:\/\/)\S+$/i;
  return urlPattern.test(value);
};

// 高亮URL相关的键
const highlightKey = (key: string): boolean => {
  const urlRelatedKeys = ['url', 'link', 'href', 'path', 'uri', 'location'];
  return urlRelatedKeys.some(k => key.toLowerCase().includes(k));
};

// 将文本中的URL转换为可点击链接
const formatTextWithUrls = (text: string): string => {
  if (!text) return '';
  // URL匹配正则表达式 - 移除不必要的转义字符
  const urlPattern = /(https?:\/\/[\w\-._~:?#[\]@!$&'()*+,;=]+)|(ftp:\/\/[\w\-._~:?#[\]@!$&'()*+,;=]+)|(mailto:[\w\-._~:?#[\]@!$&'()*+,;=]+)/g;
  
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(urlPattern, '<a href="$&" target="_blank" class="url-link">$&</a>');
};

// 复制成功处理
const onCopied = () => {
  ElMessage.success('复制成功');
};
</script>

<style scoped>
/* 结果模态框样式 */
.result-modal-container {
  padding: 20px;
  min-height: 200px;
}

.result-content {
  width: 100%;
}

.status-section {
  margin-bottom: 16px;
}

.status-text {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  line-height: 1.5;
}

.details-section,
.final-result-section {
  background-color: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
}

.details-header {
  background-color: #f5f7fa;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.details-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
}

.details-title i {
  margin-right: 8px;
  color: #1890ff;
}

.details-content {
  max-height: 400px;
  overflow-y: auto;
}

.json-container {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.text-container {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.url-content {
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.url-link {
  color: #1890ff;
  text-decoration: underline;
  cursor: pointer;
  transition: color 0.3s ease;
}

.url-link:hover {
  color: #40a9ff;
}

/* 自定义vue-json-pretty样式 */
:deep(.vue-json-pretty) {
  font-size: 13px;
  line-height: 1.5;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

:deep(.json-key) {
  color: #293c55;
}

:deep(.json-value) {
  color: #0e9a00;
}

:deep(.json-string) {
  color: #a52a2a;
}

:deep(.json-url) {
  color: #1890ff;
  text-decoration: underline;
  cursor: pointer;
}

:deep(.json-url:hover) {
  color: #40a9ff;
}

:deep(.vue-json-pretty__line-number) {
  color: #909399;
  font-size: 12px;
  margin-right: 10px;
  user-select: none;
}

/* 复制按钮样式优化 */
:deep(.vue-json-pretty__copy) {
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

:deep(.vue-json-pretty__copy:hover) {
  opacity: 1;
}

/* 标签页内容样式 */
.el-tabs {
  margin-top: 20px;
}

.tab-content {
  padding: 20px;
  background-color: #ffffff;
  min-height: 300px; /* 确保标签页内容区域有足够的最小高度 */
}

.tab-content .json-pre {
  margin: 0;
  background-color: #fafafa;
  max-height: 400px;
  overflow-y: auto;
}

/* 当只有一个标签页时，隐藏关闭按钮 */
.el-tabs--border-card > .el-tabs__header .el-tabs__nav-wrap::after {
  height: 1px;
}

/* 动画效果 */
@keyframes successPulse {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 滚动条美化 */
.details-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.details-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.details-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.details-content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}
</style>