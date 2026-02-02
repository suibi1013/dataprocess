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
    width="50%"
    height="70%"
    @ok="onHandleResultModalOk"
  >
    <div class="result-modal-container">
      <div v-if="resultModalData" class="result-content">
        <!-- 基本信息区域 -->
        <div class="basic-info-section">
          <div class="basic-info-row">
            <div class="basic-info-item">
              <span class="info-label">流程名称：</span>
              <span class="info-value">{{ flowData?.flow_name || '-' }}</span>
            </div>
            <div class="basic-info-item">
              <span class="info-label">执行状态：</span>
              <span :class="['info-value', resultModalData.success ? 'status-success' : 'status-failed']">
                {{ resultModalData.success ? '成功' : '失败' }}
              </span>
            </div>
          </div>
          <div class="basic-info-row">
            <div class="basic-info-item">
              <span class="info-label">执行耗时：</span>
              <span class="info-value">{{ flowData?.execution_time || 0 }}秒</span>
            </div>
            <div class="basic-info-item">
              <span class="info-label">执行节点数量：</span>
              <span class="info-value">{{ flowData?.total_nodes_executed || 0 }}个</span>
            </div>
          </div>
        </div>
        
        <!-- 结果标签页 -->
        <div class="result-tabs">
          <el-tabs :model-value="activeTab" type="border-card" @update:model-value="onUpdateActiveTab">
            <!-- 执行结果标签页 -->
            <el-tab-pane 
              label="执行结果"
              name="finalResult"
              :closable="false"
            >
              <div class="tab-content">
                <div v-if="isJsonString(flowData?.final_result) && (typeof flowData?.final_result === 'object' || (typeof flowData?.final_result === 'string' && isJsonObjectString(flowData.final_result)))" class="json-container">
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
                  <div v-else class="text-container">
                    <div class="url-content">{{ flowData?.final_result || '-' }}</div>
                  </div>
                </div>
                <div v-else class="text-container">
                  <div class="url-content">{{ flowData?.final_result || '-' }}</div>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 执行顺序标签页 -->
            <el-tab-pane 
              label="执行顺序"
              name="executionOrder"
              :closable="false"
            >
              <div class="tab-content">
                <div class="execution-order-container">
                  <div v-for="(nodeId, index) in flowData?.execution_order" :key="index" class="execution-order-item">
                    <span class="order-index">{{ index + 1 }}.</span>
                    <span class="order-node">{{ nodeId }}</span>
                  </div>
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

// 流程数据
const flowData = ref<any>(null);

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
const isJsonString = (str: any): boolean => {
  if (!str) return false;
  try {
    JSON.parse(typeof str === 'string' ? str : JSON.stringify(str));
    return true;
  } catch (e) {
    return false;
  }
};

// 判断是否为JSON对象字符串
const isJsonObjectString = (str: string): boolean => {
  if (!str) return false;
  try {
    const parsed = JSON.parse(str);
    return typeof parsed === 'object' && parsed !== null;
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



// 将JSON数据转换为树节点数据
const convertJsonToTreeNode = (data: any, parentKey: string = ''): any[] => {
  const treeNode: any[] = [];
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
    // 解析流程数据
    if (newData.details && isJsonString(newData.details)) {
      const parsedData = parseJson(newData.details);
      if (parsedData) {
        // 检查parsedData是否包含data属性，如果有则使用data属性的内容，否则直接使用parsedData
        flowData.value = parsedData.data || parsedData;
      }
    }
    
    // 更新最终结果树数据
    if (flowData.value?.final_result && isJsonString(flowData.value.final_result)) {
      try {
        const finalResult = typeof flowData.value.final_result === 'string' ? JSON.parse(flowData.value.final_result) : flowData.value.final_result;
        finalResultTreeData.value = convertJsonToTreeNode(finalResult);
      } catch (e) {
        finalResultTreeData.value = [];
      }
    } else {
      finalResultTreeData.value = [];
    }
  }
}, { immediate: true, deep: true });
</script>

<style scoped>
/* 结果模态框样式 */
.result-modal-container {
  padding: 10px;
  min-height: 180px;
}

.result-content {
  width: 100%;
}

/* 基本信息区域样式 */
.basic-info-section {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.basic-info-row {
  display: flex;
  margin-bottom: 10px;
}

.basic-info-row:last-child {
  margin-bottom: 0;
}

.basic-info-item {
  display: flex;
  align-items: center;
  flex: 1;
  margin-right: 10px;
}

.basic-info-item:last-child {
  margin-right: 0;
}

.info-label {
  font-weight: 500;
  color: #606266;
  width: 120px;
  font-size: 14px;
}

.info-value {
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.status-success {
  color: #67c23a !important;
}

.status-failed {
  color: #f56c6c !important;
}

/* 结果标签页样式 */
.result-tabs {
  margin-top: 16px;
}

.tab-content {
  padding: 16px;
  background-color: #ffffff;
  min-height: 250px;
}

/* 执行顺序容器样式 */
.execution-order-container {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
}

.execution-order-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.execution-order-item:last-child {
  border-bottom: none;
}

.order-index {
  font-weight: 500;
  color: #1890ff;
  margin-right: 12px;
  width: 30px;
}

.order-node {
  font-size: 14px;
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* JSON容器样式 */
.json-container {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

/* 文本容器样式 */
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

/* 当只有一个标签页时，隐藏关闭按钮 */
.el-tabs--border-card > .el-tabs__header .el-tabs__nav-wrap::after {
  height: 1px;
}

/* 滚动条美化 */
.json-container::-webkit-scrollbar,
.text-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.json-container::-webkit-scrollbar-track,
.text-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.json-container::-webkit-scrollbar-thumb,
.text-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.json-container::-webkit-scrollbar-thumb:hover,
.text-container::-webkit-scrollbar-thumb:hover {
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