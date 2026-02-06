<template>
  <Modal
    :visible="visible"
    @update:visible="onUpdateVisible"
    :title="nodeName || '节点执行信息'"
    :ok-text="'关闭'"
    :cancel-text="''"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :center="true"
    width="60%"
    height="70%"
    @ok="onHandleOk"
  >
    <div class="node-execution-modal">
      <!-- 基本信息区域 -->
      <div class="basic-info-section">
        <div class="basic-info-row">
          <div class="basic-info-item">
            <span class="info-label">执行状态：</span>
            <span :class="['info-value', executionStatus === '成功' ? 'status-success' : 'status-failed']">
              {{ executionStatus || '-' }}--{{ message || '-' }}
            </span>
          </div>
          <div class="basic-info-item">
            <span class="info-label">执行时间：</span>
            <span class="info-value">
              {{ executionTimeBegin || '-' }}--{{ executionTimeEnd || '-' }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- 参数信息标签页 -->
      <div class="params-tabs">
        <el-tabs :model-value="activeTab" type="border-card" @update:model-value="onUpdateActiveTab">
          <!-- 输入参数标签页 -->
          <el-tab-pane 
            label="输入参数"
            name="paramsIn"
            :closable="false"
          >
            <div class="tab-content">
              <div v-if="paramsIn" class="params-container">
                <div v-if="Object.keys(paramsIn).length > 0" class="params-list">
                  <div v-for="(value, key) in paramsIn" :key="key" class="param-item">
                    <div class="param-name">
                      {{ getParamLabel(key) }}({{ key }}):
                    </div>
                    <div class="param-value">
                      <span :class="['value-text', `value-type-${getValueType(value)}`]">
                        {{ formatValue(value) }}
                      </span>
                      <!-- 复制按钮 -->
                      <el-button
                        size="small"
                        type="text"
                        :icon="DocumentCopy"
                        @click="onCopyNodeValue(value)"
                        class="copy-button"
                      />
                    </div>
                  </div>
                </div>
                <div v-else class="empty-state">
                  无输入参数
                </div>
              </div>
              <div v-else class="empty-state">
                无输入参数
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 输出参数标签页 -->
          <el-tab-pane 
            label="输出参数"
            name="paramsOut"
            :closable="false"
          >
            <div class="tab-content">
              <div v-if="paramsOut" class="params-container">
                <div v-if="Object.keys(paramsOut).length > 0" class="params-list">
                  <div v-for="(value, key) in paramsOut" :key="key" class="param-item">
                    <div class="param-name">
                      {{ getParamLabel(key) }}({{ key }}):
                    </div>
                    <div class="param-value">
                      <span :class="['value-text', `value-type-${getValueType(value)}`]">
                        {{ formatValue(value) }}
                      </span>
                      <!-- 复制按钮 -->
                      <el-button
                        size="small"
                        type="text"
                        :icon="DocumentCopy"
                        @click="onCopyNodeValue(value)"
                        class="copy-button"
                      />
                    </div>
                  </div>
                </div>
                <div v-else class="empty-state">
                  无输出参数
                </div>
              </div>
              <div v-else class="empty-state">
                无输出参数
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">

import Modal from '@/components/Common/Modal.vue';
import { ElTabs, ElTabPane, ElMessage, ElButton } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';

// Props
interface Props {
  visible: boolean;
  nodeName?: string;
  executionStatus?: string;
  executionTimeBegin?: string;
  executionTimeEnd?: string;
  message?: string;
  paramsIn?: any;
  paramsOut?: any;
  activeTab: string;
  instructionId?: string;
  paramsPanel?: any;
  instructionCategories?: any[];
}

const props = defineProps<Props>();

// Emits
interface Emits {
  'update:visible': [visible: boolean];
  'update:activeTab': [tab: string];
  handleOk: [];
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

// 处理确定按钮点击
const onHandleOk = () => {
  emit('handleOk');
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

// 获取参数标签（中文名称）
const getParamLabel = (paramName: string): string => {
  // 首先从paramsPanel.paramFormItems中查找对应的中文名称（与参数设置区域保持一致）
  if (props.paramsPanel && props.paramsPanel.paramFormItems) {
    const formItem = props.paramsPanel.paramFormItems.find((item: any) => 
      item.param?.name === paramName || item.name === paramName
    );
    if (formItem && (formItem.param?.label || formItem.label)) {
      return formItem.param?.label || formItem.label;
    }
  }
  // 如果paramsPanel.paramFormItems为空，尝试从指令列表中获取参数信息
  if (props.instructionId && props.instructionCategories) {
    // 查找对应指令
    for (const category of props.instructionCategories) {
      const instruction = category.instructions.find((inst: any) => inst.id === props.instructionId);
      if (instruction && instruction.params) {
        // 查找对应参数
        const param = instruction.params.find((p: any) => p.name === paramName);
        if (param && param.label) {
          return param.label;
        }
      }
    }
  }
  // 如果没有找到，返回参数名作为默认值
  return paramName;
};
</script>

<style scoped>
/* 节点执行模态框样式 */
.node-execution-modal {
  padding: 16px;
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
  width: 100px;
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

/* 参数标签页样式 */
.params-tabs {
  margin-top: 16px;
}

.tab-content {
  padding: 16px;
  background-color: #ffffff;
  min-height: 250px;
}

/* 参数容器样式 */
.params-container {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 14px;
}

/* 参数列表样式 */
.params-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 参数项样式 */
.param-item {
  display: flex;
  align-items: flex-start;
  padding: 10px;
  background-color: #ffffff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 参数名称样式 */
.param-name {
  font-weight: 500;
  color: #293c55;
  margin-right: 12px;
  min-width: 150px;
  font-size: 13px;
  padding-top: 2px;
}

/* 参数值样式 */
.param-value {
  flex: 1;
  display: flex;
  align-items: center;
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 值文本样式 */
.value-text {
  flex: 1;
  word-break: break-all;
}

/* 值类型样式 */
.value-type-string {
  color: #a52a2a;
}

.value-type-number {
  color: #0e9a00;
}

.value-type-boolean {
  color: #1890ff;
}

.value-type-null,
.value-type-undefined {
  color: #909399;
  font-style: italic;
}

.value-type-object,
.value-type-array {
  color: #722ed1;
}

/* 复制按钮样式 */
.copy-button {
  margin-left: 10px;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.param-item:hover .copy-button {
  opacity: 1;
}

/* 滚动条美化 */
.params-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.params-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.params-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.params-container::-webkit-scrollbar-thumb:hover {
  background: #909399;
}
</style>