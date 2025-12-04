<template>
  <div 
    v-if="visible && forParam === paramName && (paramType === 'string' || paramType === 'number')"
    class="variable-selector"
    :style="selectorStyle"
    @mouseleave="onMouseLeave"
  >
    <div class="variable-search" style="margin-bottom: 10px;">
      <input 
        type="text" 
        :value="searchKeyword"
        @input="onSearchInput(($event.target as HTMLInputElement).value)"
        placeholder="搜索变量..."
        class="variable-search-input"
        style="width: 100%; padding: 5px; border: 1px solid #dcdfe6; border-radius: 4px;"
      />
    </div>
    <div class="variable-tree">
      <div v-if="Object.keys(filteredVariables).length === 0" style="text-align: center; color: #909399; padding: 20px;">
        暂无可用变量
      </div>
      <div v-else>
        <div 
          v-for="(nodeVars, nodeName) in filteredVariables" 
          :key="nodeName"
          class="node-variable-group"
        >
          <div 
            class="node-title tree-node-header"
            style="font-size: 14px; font-weight: bold; color: #606266; margin-bottom: 8px; padding: 8px 0; border-bottom: 1px solid #ebeef5; cursor: pointer;"
            @click="onToggleTreeNode(nodeName)"
          >
            <span class="tree-expand-icon" :class="{ expanded: expandedNodes[nodeName] }">
              {{ expandedNodes[nodeName] ? '▼' : '▶' }}
            </span>
            {{ nodeName }} ({{ nodeVars.length }})
          </div>
          <div 
            class="variable-list tree-node-children"
            v-show="expandedNodes[nodeName]"
            style="padding-left: 16px;"
          >
            <div 
              v-for="variable in nodeVars" 
              :key="variable.name"
              class="variable-item"
              @click="onSelectVariable(paramName, variable.name)"
              style="padding: 6px 10px; margin-bottom: 4px; border-radius: 4px; cursor: pointer; transition: background-color 0.2s;"
              :style="{ backgroundColor: hoveredVariable === variable.name ? '#ecf5ff' : 'transparent' }"
              @mouseenter="onVariableItemMouseEnter(variable.name)"
              @mouseleave="onVariableItemMouseLeave"
            >
              <div style="font-size: 14px; color: #303133;">{{ variable.label }}</div>
              <div style="font-size: 12px; color: #909399; margin-top: 2px;">{{ variable.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Props
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  forParam: {
    type: String,
    required: true
  },
  paramName: {
    type: String,
    required: true
  },
  paramType: {
    type: String,
    required: true
  },
  searchKeyword: {
    type: String,
    default: ''
  },
  filteredVariables: {
    type: Object as () => Record<string, Array<{name: string; label: string; value?: any}>>,
    required: true
  },
  expandedNodes: {
    type: Object as () => Record<string, boolean>,
    required: true
  },
  hoveredVariable: {
    type: String,
    default: ''
  },
  selectorStyle: {
    type: Object as () => {
      position: string;
      zIndex: number;
      background: string;
      border: string;
      borderRadius: string;
      padding: string;
      boxShadow: string;
      minWidth: string;
      maxHeight: string;
      overflowY: string;
      top?: string;
      bottom?: string;
    },
    required: true
  }
});

// Emits
interface Emits {
  mouseLeave: [];
  searchInput: [value: string];
  toggleTreeNode: [nodeName: string];
  selectVariable: [paramName: string, variableName: string];
  variableItemMouseEnter: [variableName: string];
  variableItemMouseLeave: [];
}

const emit = defineEmits<Emits>();

// 鼠标离开
const onMouseLeave = () => {
  emit('mouseLeave');
};

// 搜索输入
const onSearchInput = (value: string) => {
  emit('searchInput', value);
};

// 切换树节点
const onToggleTreeNode = (nodeName: string) => {
  emit('toggleTreeNode', nodeName);
};

// 选择变量
const onSelectVariable = (paramName: string, variableName: string) => {
  emit('selectVariable', paramName, variableName);
};

// 变量项鼠标进入
const onVariableItemMouseEnter = (variableName: string) => {
  emit('variableItemMouseEnter', variableName);
};

// 变量项鼠标离开
const onVariableItemMouseLeave = () => {
  emit('variableItemMouseLeave');
};
</script>

<style scoped>
.variable-selector {
  position: relative;
  margin-top: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.variable-search {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.variable-search-input {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.variable-tree {
  max-height: 200px;
  overflow-y: auto;
}

.variable-node-group {
  margin-bottom: 4px;
}

.variable-node-title {
  padding: 8px 12px;
  background: #f5f5f5;
  font-weight: 500;
  font-size: 13px;
  color: #333;
  border-bottom: 1px solid #e8e8e8;
}

/* 树形结构样式 */
.tree-node-header {
  display: flex;
  align-items: center;
  user-select: none;
}

.tree-expand-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  text-align: center;
  line-height: 16px;
  font-size: 10px;
  transition: transform 0.2s;
  color: #606266;
}

.tree-expand-icon.expanded {
  color: #1890ff;
}

.tree-node-children {
  transition: all 0.3s ease;
}

.variable-item {
  padding: 6px 12px 6px 24px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.2s;
}

.variable-item:hover {
  background: #f0f8ff;
  color: #1890ff;
}
</style>