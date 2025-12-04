<template>
  <Modal
    v-model:visible="localVisible"
    title="分类管理"
    width="600"
    :ok-text="''"
    :cancel-text="'关闭'"
    :loading="loading"
    @cancel="handleCancel"
    footer-align="center"
  >
    <div class="category-management">
      <div class="category-header">
        <h3>指令分类列表</h3>
        <button class="btn btn-primary" @click="startCreateCategory">
          <i class="icon-plus"></i> 新增分类
        </button>
      </div>
      
      <div v-if="categories.length === 0" class="empty-state">
        <p>暂无分类数据</p>
        <button class="btn btn-primary" @click="startCreateCategory">
          创建第一个分类
        </button>
      </div>
      
      <div v-else class="category-list">
        <div 
          v-for="category in categories"
          :key="category.id"
          class="category-item"
        >
          <div class="category-info">
            <h4>{{ category.name }}</h4>
            <p>{{ category.description || '无描述' }}</p>
            <div class="category-meta">
              <span>排序: {{ category.sort_order || 1 }}</span>
              <span v-if="category.is_active === false" class="status-disabled">已禁用</span>
              <span v-else class="status-enabled">已启用</span>
            </div>
          </div>
          <div class="category-actions">
            <button class="btn btn-sm btn-secondary" @click="editCategory(category)">
              编辑
            </button>
            <button 
              class="btn btn-sm btn-danger"
              @click="deleteCategory(category.id, category.name)"
              :disabled="category.instructions && category.instructions.length > 0"
              title="该分类下有指令，无法删除"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </Modal>
  
  <!-- 新增/编辑分类的独立模态框 -->
  <CategoryFormModal
    v-model:visible="formModalVisible"
    :category="selectedCategory"
    @save="handleCategorySave"
  />
</template>

<script lang="ts">
import { defineComponent, ref, watch, computed } from 'vue';
import Modal from '@/components/Common/Modal.vue';
import CategoryFormModal from './CategoryFormModal.vue';
import type { InstructionCategory } from '@/types/instruction';
import { instructionService } from '@/services/instructionService';
import messageService from '@/services/MessageService';
import { useInstructionStore } from '@/store/instructionStore';

export default defineComponent({
  name: 'CategoryManagement',
  components: {
    Modal,
    CategoryFormModal
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['save', 'close'],
  setup(props, { emit }) {
    // 初始化store
    const instructionStore = useInstructionStore();
    
    // 使用本地状态来控制Modal显示，避免直接修改props
    const localVisible = ref(props.visible);
    const formModalVisible = ref(false);
    const selectedCategory = ref<InstructionCategory | null>(null);
    
    // 本地加载状态（用于组件内操作的加载指示）
    const localLoading = ref(false);
    
    // 从store获取分类数据
    const categories = computed(() => instructionStore.categories);
    const storeLoading = computed(() => instructionStore.loading);
    
    // 统一的加载状态（合并store加载状态和本地操作加载状态）
    const loading = computed(() => storeLoading.value || localLoading.value);
    
    // 合并监听器，避免重复调用loadCategories
    watch(() => props.visible, (newValue) => {
      const oldValue = localVisible.value;
      localVisible.value = newValue;
      
      // 只在从false变为true时调用loadCategories()
      if (!oldValue && newValue) {
        loadCategories();
      } else if (!newValue) {
        emit('close');
      }
    });

    // 加载分类数据
    const loadCategories = async () => {
      // 调用store中的方法加载数据
      await instructionStore.fetchAllData();
    };

    // 开始创建分类 - 打开新的模态框
    const startCreateCategory = () => {
      selectedCategory.value = null;
      formModalVisible.value = true;
    };

    // 编辑分类 - 打开新的模态框
    const editCategory = (category: InstructionCategory) => {
      selectedCategory.value = category;
      formModalVisible.value = true;
    };

    // 删除分类
    const deleteCategory = async (categoryId: string, categoryName: string) => {
      if (confirm(`确定要删除分类"${categoryName}"吗？`)) {
        try {
          localLoading.value = true;
          const response = await instructionService.deleteCategory(categoryId);
          if (response.success) {
            messageService.success('分类删除成功');
            await loadCategories();
          } else {
            messageService.error(response.message || '分类删除失败');
          }
        } catch (err) {
          messageService.error('分类删除失败');
          console.error('删除分类失败:', err);
        } finally {
          localLoading.value = false;
        }
      }
    };

    // 处理分类保存成功
    const handleCategorySave = async () => {
      // 保存成功后重新加载分类列表
      await loadCategories();
      emit('save');
    };

    // 取消操作
    const handleCancel = () => {
      emit('close');
    };



    return {
      localVisible,
      loading,
      categories,
      formModalVisible,
      selectedCategory,
      startCreateCategory,
      editCategory,
      deleteCategory,
      handleCategorySave,
      handleCancel,
      loadCategories
    };
  }
});
</script>

<style scoped>
.category-management {
  padding: 10px 0;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.category-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.category-info {
  flex: 1;
}

.category-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
}

.category-info p {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #6b7280;
}

.category-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #9ca3af;
}

.status-enabled {
  color: #10b981;
}

.status-disabled {
  color: #ef4444;
}

.category-actions {
  display: flex;
  gap: 8px;
}
</style>