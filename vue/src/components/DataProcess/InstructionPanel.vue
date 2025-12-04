<template>
  <div class="instructions-panel">
    <div class="panel-header">
      <h4 class="panel-title">指令列表</h4>
    </div>
    <div class="panel-content">
      <div v-if="instructionLoading" class="loading-state">
        <i class="icon-loading"></i>
        <span>加载中...</span>
      </div>
      <div v-else class="instruction-categories">
        
        <!-- 指令分类列表 -->
        <div 
          v-for="category in displayInstructionCategories"
          :key="category.id"
          class="instruction-category"
        >
          <div class="category-header" @click="onToggleCategory(category.id)">
            <i :class="category.expanded ? 'el-icon-arrow-down' : 'el-icon-arrow-right'"></i>
            <h5 class="category-name">{{ category.name }}</h5>
          </div>
          <div v-show="category.expanded" class="category-instructions">
            <div 
              v-for="instruction in category.instructions"
              :key="instruction.id"
              class="instruction-item"
              draggable="true"
              @dragstart="onInstructionDragStart($event, instruction)"
            >
              <div class="instruction-icon">
                <component v-if="instruction.icon && instruction.icon.startsWith('el-icon-')" :is="getIconComponent(instruction.icon)"></component>
                <i v-else :class="instruction.icon || 'icon-code'"></i>
              </div>
              <div class="instruction-info">
                  <div class="instruction-name">{{ instruction.name }}</div>
                  <div class="instruction-desc">{{ instruction.description }}</div>
                </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';

// Props
interface Props {
  instructionLoading: boolean;
  instructionCategories: any[];
}

const props = defineProps<Props>();

// 使用计算属性来显示指令分类
const displayInstructionCategories = computed(() => {
  return props.instructionCategories;
});

// Emits
interface Emits {
  toggleCategory: [categoryId: string];
  instructionDragStart: [event: DragEvent, instruction: any];
}

const emit = defineEmits<Emits>();

// 获取Element Plus图标组件
const getIconComponent = (iconName: string) => {
  if (!iconName || !iconName.startsWith('el-icon-')) return 'i';
  // 转换图标名称为组件名，例如 el-icon-document-copy 转为 DocumentCopy
  const componentName = iconName.replace('el-icon-', '')
    .split('-')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
  return ElementPlusIconsVue[componentName as keyof typeof ElementPlusIconsVue] || 'i';
};



// 处理指令拖拽开始
const onInstructionDragStart = (event: DragEvent, instruction: any) => {
  emit('instructionDragStart', event, instruction);
};

// 切换指令分类展开/收起状态
const onToggleCategory = (categoryId: string) => {
  const category = displayInstructionCategories.value.find(cat => cat.id === categoryId);
  if (category) {
    category.expanded = !category.expanded;
  }
};
</script>

<style scoped>
/* 左侧指令面板 */
.instructions-panel {
  width: 20%;
  min-width: 250px;
  background: #fafafa;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 90vh; /* 确保占满父容器高度 */
}

.instructions-panel .panel-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.instructions-panel .panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.instructions-panel .panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  max-height: calc(100% - 140px); /* 减去头部和底部间距，避免被modal-footer遮挡 */
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 16px;
  color: #8c8c8c;
}

.instruction-categories {
  display: flex;
  flex-direction: column;
  gap: 4px;
}



.instruction-category {
  background: white;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  background: #f9f9f9;
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.2s ease;
}

.category-header:hover {
  background: #f0f0f0;
}

.category-header i {
  font-size: 12px;
  color: #8c8c8c;
  transition: transform 0.2s ease;
}

.category-name {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.category-instructions {
  padding: 4px;
}

.instruction-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  margin: 2px 0;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s ease;
  background: white;
  border: 1px solid transparent;
}

.instruction-item:hover {
  background: #f0f8ff;
  border-color: #d6e4ff;
  transform: translateX(2px);
}

.instruction-item:active {
  cursor: grabbing;
}

.instruction-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #1890ff;
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.instruction-info {
  flex: 1;
  min-width: 0;
}

.instruction-name {
  font-size: 12px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.instruction-desc {
  font-size: 11px;
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>