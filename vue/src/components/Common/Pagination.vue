<template>
  <div class="pagination-wrapper">
    <div class="pagination-info">
      <span class="info-text">
        共 {{ total }} 条记录，第 {{ current }} / {{ totalPages }} 页
      </span>
    </div>
    
    <div class="pagination-controls">
      <!-- 上一页 -->
      <button 
        class="pagination-btn"
        :disabled="current <= 1"
        @click="handlePageChange(current - 1)"
        title="上一页"
      >
        <i class="el-icon-arrow-left"></i>
      </button>
      
      <!-- 页码列表 -->
      <div class="page-numbers">
        <!-- 第一页 -->
        <button 
          v-if="showFirstPage"
          class="page-btn"
          :class="{ active: current === 1 }"
          @click="handlePageChange(1)"
        >
          1
        </button>
        
        <!-- 前省略号 -->
        <span v-if="showStartEllipsis" class="ellipsis">...</span>
        
        <!-- 中间页码 -->
        <button 
          v-for="page in visiblePages"
          :key="page"
          class="page-btn"
          :class="{ active: current === page }"
          @click="handlePageChange(page)"
        >
          {{ page }}
        </button>
        
        <!-- 后省略号 -->
        <span v-if="showEndEllipsis" class="ellipsis">...</span>
        
        <!-- 最后一页 -->
        <button 
          v-if="showLastPage"
          class="page-btn"
          :class="{ active: current === totalPages }"
          @click="handlePageChange(totalPages)"
        >
          {{ totalPages }}
        </button>
      </div>
      
      <!-- 下一页 -->
      <button 
        class="pagination-btn"
        :disabled="current >= totalPages"
        @click="handlePageChange(current + 1)"
        title="下一页"
      >
        <i class="el-icon-arrow-right"></i>
      </button>
    </div>
    
    <!-- 页面大小选择器 -->
    <div class="page-size-selector">
      <span class="selector-label">每页</span>
      <select 
        class="page-size-select"
        :value="pageSize"
        @change="handlePageSizeChange"
      >
        <option 
          v-for="size in pageSizeOptions"
          :key="size"
          :value="size"
        >
          {{ size }}
        </option>
      </select>
      <span class="selector-label">条</span>
    </div>
    
    <!-- 快速跳转 -->
    <div class="quick-jumper">
      <span class="jumper-label">跳至</span>
      <input 
        v-model.number="jumpPage"
        class="jump-input"
        type="number"
        :min="1"
        :max="totalPages"
        @keyup.enter="handleJump"
        @blur="handleJump"
      >
      <span class="jumper-label">页</span>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'BasePagination'
}
</script>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

// Props
interface Props {
  current: number;
  total: number;
  pageSize: number;
  pageSizeOptions?: number[];
  showQuickJumper?: boolean;
  showSizeChanger?: boolean;
  showTotal?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  pageSizeOptions: () => [10, 20, 50, 100],
  showQuickJumper: true,
  showSizeChanger: true,
  showTotal: true
});

// Emits
interface Emits {
  change: [page: number, pageSize?: number];
}

const emit = defineEmits<Emits>();

// 状态
const jumpPage = ref<number>(props.current);

// 计算属性
const totalPages = computed(() => {
  return Math.ceil(props.total / props.pageSize);
});

// 可见页码范围
const visiblePages = computed(() => {
  const delta = 2; // 当前页前后显示的页数
  const range = [];
  const rangeWithDots = [];
  
  for (let i = Math.max(2, props.current - delta); 
       i <= Math.min(totalPages.value - 1, props.current + delta); 
       i++) {
    range.push(i);
  }
  
  if (props.current - delta > 2) {
    rangeWithDots.push(2);
  } else {
    rangeWithDots.push(...range.filter(i => i >= 2));
  }
  
  if (props.current + delta < totalPages.value - 1) {
    rangeWithDots.push(...range.filter(i => i <= totalPages.value - 1));
  } else {
    rangeWithDots.push(...range);
  }
  
  return [...new Set(rangeWithDots)].sort((a, b) => a - b);
});

// 是否显示第一页
const showFirstPage = computed(() => {
  return totalPages.value > 1 && !visiblePages.value.includes(1);
});

// 是否显示最后一页
const showLastPage = computed(() => {
  return totalPages.value > 1 && !visiblePages.value.includes(totalPages.value);
});

// 是否显示开始省略号
const showStartEllipsis = computed(() => {
  return visiblePages.value.length > 0 && visiblePages.value[0] > 2;
});

// 是否显示结束省略号
const showEndEllipsis = computed(() => {
  return visiblePages.value.length > 0 && 
         visiblePages.value[visiblePages.value.length - 1] < totalPages.value - 1;
});

// 监听当前页变化，同步跳转输入框
watch(() => props.current, (newCurrent) => {
  jumpPage.value = newCurrent;
});

// 处理页码变化
const handlePageChange = (page: number) => {
  if (page < 1 || page > totalPages.value || page === props.current) {
    return;
  }
  emit('change', page);
};

// 处理页面大小变化
const handlePageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const newPageSize = parseInt(target.value);
  
  // 计算新的页码，保持当前数据位置
  const currentIndex = (props.current - 1) * props.pageSize;
  const newPage = Math.floor(currentIndex / newPageSize) + 1;
  
  emit('change', newPage, newPageSize);
};

// 处理快速跳转
const handleJump = () => {
  if (jumpPage.value && jumpPage.value >= 1 && jumpPage.value <= totalPages.value) {
    handlePageChange(jumpPage.value);
  } else {
    // 重置为当前页
    jumpPage.value = props.current;
  }
};
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-info {
  color: #595959;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #595959;
}

.pagination-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.pagination-btn:disabled {
  background: #f5f5f5;
  border-color: #d9d9d9;
  color: #bfbfbf;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #595959;
  font-size: 14px;
}

.page-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.page-btn.active:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

.ellipsis {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: #bfbfbf;
  font-size: 14px;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #595959;
  font-size: 14px;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.page-size-select:hover {
  border-color: #1890ff;
}

.page-size-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.quick-jumper {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #595959;
  font-size: 14px;
}

.jump-input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.jump-input:hover {
  border-color: #1890ff;
}

.jump-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 隐藏数字输入框的箭头 */
.jump-input::-webkit-outer-spin-button,
.jump-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.jump-input[type=number] {
  -moz-appearance: textfield;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pagination-wrapper {
    flex-direction: column;
    gap: 16px;
  }
  
  .pagination-controls {
    order: 1;
  }
  
  .pagination-info {
    order: 2;
  }
  
  .page-size-selector,
  .quick-jumper {
    order: 3;
  }
}

@media (max-width: 480px) {
  .pagination-wrapper {
    gap: 12px;
  }
  
  .page-numbers {
    gap: 2px;
  }
  
  .page-btn,
  .pagination-btn {
    min-width: 28px;
    height: 28px;
    font-size: 13px;
  }
  
  .pagination-info {
    font-size: 13px;
  }
  
  .page-size-selector,
  .quick-jumper {
    font-size: 13px;
  }
}
</style>