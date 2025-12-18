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
                  <el-tree
                    v-if="finalResultTreeData.length > 0"
                    :data="finalResultTreeData"
                    :load="loadTreeNode"
                    lazy
                    node-key="key"
                    :expand-on-click-node="false"
                    :default-expand-all="false"
                  >
                    <template #default="{ data }">
                      <div class="tree-node-content">
                        <!-- 键名 -->
                        <span class="tree-node-key">{{ data.label }}: </span>
                        <!-- 值 -->
                        <span :class="['tree-node-value', `tree-node-value-${getValueType(data.value)}`]">
                          {{ formatValue(data.value) }}
                        </span>
                        <!-- 复制按钮 -->
                        <el-button
                          size="small"
                          type="text"
                          :icon="DocumentCopy"
                          @click="onCopyNodeValue(data.value)"
                          class="copy-button"
                        />
                      </div>
                    </template>
                  </el-tree>
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
                  <el-tree
                    v-if="detailsTreeData"
                    :data="detailsTreeData"
                    :load="loadTreeNode"
                    lazy
                    node-key="key"
                    :expand-on-click-node="false"
                    :default-expand-all="false"
                  >
                    <template #default="{ data }">
                      <div class="tree-node-content">
                        <!-- 键名 -->
                        <span class="tree-node-key">{{ data.label }}: </span>
                        <!-- 值 -->
                        <span :class="['tree-node-value', `tree-node-value-${getValueType(data.value)}`]">
                          {{ formatValue(data.value) }}
                        </span>
                        <!-- 复制按钮 -->
                        <el-button
                          size="small"
                          type="text"
                          :icon="DocumentCopy"
                          @click="onCopyNodeValue(data.value)"
                          class="copy-button"
                        />
                      </div>
                    </template>
                  </el-tree>
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
import { ElTabs, ElTabPane, ElMessage, ElTree, ElButton } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';
import { ref, watch } from 'vue';

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

const props = defineProps<Props>();

// Emits
interface Emits {
  'update:visible': [visible: boolean];
  'update:activeTab': [tab: string];
  handleResultModalOk: [];
}

const emit = defineEmits<Emits>();

// 树数据状态
const finalResultTreeData = ref<any[]>([]);
const detailsTreeData = ref<any>({});

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

// 将文本中的URL转换为可点击链接
const formatTextWithUrls = (text: string): string => {
  if (!text) return '';
  // URL匹配正则表达式
  const urlPattern = /(https?:\/\/[\w\-_~:?#[\]@!$&'()*+,;=]+)|(ftp:\/\/[\w\-_~:?#[\]@!$&'()*+,;=]+)|(mailto:[\w\-_~:?#[\]@!$&'()*+,;=]+)/g;
  
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(urlPattern, '<a href="$&" target="_blank" class="url-link">$&</a>');
};

// 将JSON数据转换为树节点数据
const convertJsonToTreeNode = (data: any, parentKey: string = ''): any[] => {
  const treeNode: any[] = [];
  console.log('convertJsonToTreeNode',data,parentKey)
  // 处理null值
  if (data === null) {
    // 如果是子节点且数据为null，添加一个null节点
    if (parentKey) {
      treeNode.push({
        key: `${parentKey}.null`,
        label: `null`,
        value: null,
        isObject: false,
        isArray: false,
        leaf: true,
        parentKey: parentKey
      });
    }
  }
  // 处理非null对象类型
  else if (typeof data === 'object' && !Array.isArray(data)) {
    // 遍历对象属性，创建对应的树节点
    for (const key in data) {
      if (Object.prototype.hasOwnProperty.call(data, key)) {
        const nodeKey = parentKey ? `${parentKey}.${key}` : key;
        const value = data[key];
        const hasChildren = value && typeof value === 'object';
        
        treeNode.push({
          key: nodeKey,
          label: key,
          value: value,
          isObject: typeof value === 'object' && !Array.isArray(value),
          isArray: Array.isArray(value),
          leaf: !hasChildren,
          parentKey: parentKey
        });
      }
    }
  }
  // 处理数组类型
  else if (Array.isArray(data)) {
    // 遍历数组元素，创建对应的树节点
    data.forEach((item, index) => {
      const nodeKey = parentKey ? `${parentKey}[${index}]` : `[${index}]`;
      const hasChildren = item && typeof item === 'object';
      
      treeNode.push({
        key: nodeKey,
        label: `[${index}]`,
        value: item,
        isObject: typeof item === 'object' && !Array.isArray(item),
        isArray: Array.isArray(item),
        leaf: !hasChildren,
        parentKey: parentKey
      });
    });
  }
  // 处理基本类型（字符串、数字、布尔值、undefined）
  else {
    // 如果是子节点且为基本类型，添加一个叶子节点
    if (parentKey) {
      treeNode.push({
        key: `${parentKey}.${data}`,
        label: `${data}`,
        value: data,
        isObject: false,
        isArray: false,
        leaf: true,
        parentKey: parentKey
      });
    }
  }
  
  return treeNode;
};

// 懒加载树节点
const loadTreeNode = (node: any, resolve: (_data: any[]) => void) => {
  const nodeData = node.data;
  // 确定节点的实际值，考虑不同的数据结构
  const actualValue = nodeData.value !== undefined ? nodeData.value : nodeData;
  const parentKey = nodeData.key || '';
  const childrenData = convertJsonToTreeNode(actualValue, parentKey);
  resolve(childrenData);
};

// 获取值类型
const getValueType = (value: any): string => {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  return typeof value;
};

// 格式化值显示
const formatValue = (value: any): string => {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (typeof value === 'string') return `"${value}"`;
  if (typeof value === 'number' || typeof value === 'boolean') return value.toString();
  if (Array.isArray(value)) return `Array(${value.length})`;
  if (typeof value === 'object') return `Object`;
  return value.toString();
};

// 复制节点值
const onCopyNodeValue = (value: any) => {
  navigator.clipboard.writeText(JSON.stringify(value, null, 2)).then(() => {
    ElMessage.success('复制成功');
  });
};

// 监听结果数据变化，更新树数据
watch(() => props.resultModalData, (newData) => {
  if (newData) {
    // 更新最终结果树数据
    if (newData.finalResult && isJsonString(newData.finalResult)) {
      const parsedData = parseJson(newData.finalResult);
      if (parsedData) {
        // 检查parsedData是否包含data属性，如果有则使用data属性的内容，否则直接使用parsedData
        const dataToDisplay = parsedData.data || parsedData;
        finalResultTreeData.value = convertJsonToTreeNode(dataToDisplay);
      } else {
        finalResultTreeData.value = [];
      }
    } else {
      finalResultTreeData.value = [];
    }
    
    // 更新执行详情树数据
    detailsTreeData.value = {};
    if (newData.details && isJsonString(newData.details)) {
      const parsedData = parseJson(newData.details);
      if (parsedData) {
        // 总是优先使用data属性内部的内容，无论其他属性是什么
        // 确保只显示接口返回结果中的data属性对象内容
        const dataToDisplay = parsedData.data || parsedData;
        const arr=convertJsonToTreeNode(dataToDisplay)        
        for (const item of arr) {
          detailsTreeData.value[item.key] = item.value;
        }
      } 
    }
  }
}, { immediate: true, deep: true });
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

/* 标签页内容样式 */
.el-tabs {
  margin-top: 20px;
}

.tab-content {
  padding: 20px;
  background-color: #ffffff;
  min-height: 300px;
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
.json-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.json-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.json-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.json-container::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 树节点样式 */
:deep(.el-tree) {
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #303133;
}

/* 树节点内容样式 */
.tree-node-content {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 2px 0;
}

/* 键名样式 */
.tree-node-key {
  color: #293c55;
  font-weight: 500;
  margin-right: 8px;
}

/* 值样式 */
.tree-node-value {
  margin-right: 12px;
  word-break: break-all;
}

/* 值类型样式 */
.tree-node-value-string {
  color: #a52a2a;
}

.tree-node-value-number {
  color: #0e9a00;
}

.tree-node-value-boolean {
  color: #1890ff;
}

.tree-node-value-null,
.tree-node-value-undefined {
  color: #909399;
  font-style: italic;
}

.tree-node-value-object,
.tree-node-value-array {
  color: #722ed1;
}

/* 复制按钮样式 */
.copy-button {
  margin-left: auto;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.tree-node-content:hover .copy-button {
  opacity: 1;
}

/* 树节点连接线样式 */
:deep(.el-tree-node__content) {
  padding: 2px 0;
}

/* 树节点图标样式 */
:deep(.el-tree-node__expand-icon) {
  font-size: 10px;
  width: 16px;
  height: 16px;
  line-height: 16px;
}
</style>