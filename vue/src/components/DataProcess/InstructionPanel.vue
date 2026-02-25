<template>
  <div class="instructions-panel">
    <div class="panel-header">
      <h4 class="panel-title">指令列表</h4>
      <div class="search-box">
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索指令名称或描述..."
          clearable
          prefix-icon="el-icon-search"
        >
        </el-input>
      </div>
    </div>
    <div class="panel-content">
      <div v-if="instructionLoading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
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
                <i v-else :class="instruction.icon || 'icon-code'" ></i>
              </div>
              <div class="instruction-info">
                <div class="instruction-name">{{ instruction.name }}</div>
                <div class="instruction-desc">{{ instruction.description }}</div>
              </div>
              <el-popover
                :content="instruction.description"
                placement="right"
                trigger="hover"
                effect="dark"
              >
                <template #reference>
                  <el-button 
                    type="text" 
                    size="small" 
                    class="desc-button"
                  >
                    <el-icon><InfoFilled /></el-icon>
                  </el-button>
                </template>
              </el-popover>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import { Loading, InfoFilled } from '@element-plus/icons-vue';

// Props
interface Props {
  instructionLoading: boolean;
  instructionCategories: any[];
}

const props = defineProps<Props>();

// 搜索关键词
const searchKeyword = ref('');

// 使用计算属性来显示指令分类，支持搜索
const displayInstructionCategories = computed(() => {
  const keyword = searchKeyword.value.toLowerCase().trim();
  
  // 如果没有搜索关键词，直接返回所有分类
  if (!keyword) {
    return props.instructionCategories;
  }
  
  // 过滤包含匹配指令的分类
  return props.instructionCategories.map(category => {
    // 过滤当前分类下匹配的指令
    const filteredInstructions = category.instructions.filter((instruction: any) => {
      const name = instruction.name?.toLowerCase() || '';
      const description = instruction.description?.toLowerCase() || '';
      return name.includes(keyword) || description.includes(keyword);
    });
    
    // 如果当前分类有匹配的指令，返回包含过滤后指令的分类
    if (filteredInstructions.length > 0) {
      return {
        ...category,
        instructions: filteredInstructions
      };
    }
    
    // 否则返回null，后续会过滤掉
    return null;
  }).filter((category: any) => category !== null);
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
  padding: 10px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.instructions-panel .panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.search-box {
  width: 100%;
}

.instructions-panel .panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  max-height: calc(100% - 220px); /* 减去头部和底部间距，避免被modal-footer遮挡 */
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 16px;
  color: #8c8c8c;
}

.loading-state .is-loading {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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

.desc-button {
  flex-shrink: 0;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
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