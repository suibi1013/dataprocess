<template>
  <Modal
    v-model:visible="localVisible"
    title="分类管理"
    :cancel-text="'关闭'"
    :loading="loading"
    :width="600"
    :show-close="true"
    :close-on-click-modal="false"
    @cancel="handleClose"
    footer=""
  >
    <div class="category-management">
      <!-- 新增分类表单 -->
      <div class="add-category-form">
        <div class="form-grid">
          <div class="form-item">
            <input 
              v-model="newCategoryName"
              type="text"
              class="form-input"
              placeholder="请输入分类名称"
              maxlength="30"
              @keypress.enter="handleAddCategory"
            >
          </div>
          <div class="form-item">
            <textarea 
              v-model="newCategoryDescription"
              class="form-textarea"
              placeholder="请输入分类描述"
              rows="2"
              maxlength="100"
            ></textarea>
          </div>
          <div class="form-actions">
            <button 
              class="btn btn-primary"
              @click="handleAddCategory"
              :disabled="!newCategoryName.trim() || loading"
            >
              <i class="icon-plus"></i> 添加分类
            </button>
          </div>
        </div>
        <div v-if="errors.newCategory" class="error-message">{{ errors.newCategory }}</div>
      </div>

      <!-- 分类列表 -->
      <div class="category-list-container">
        <div class="list-header">
          <h3>分类列表</h3>
          <span class="list-count">(共 {{ categories.length }} 个分类)</span>
        </div>
        
        <div v-if="categories.length === 0" class="empty-list">
          <p>暂无分类，请添加第一个分类</p>
        </div>
        <!-- 分类列表 -->
      <div v-else class="category-list">
        <div 
          v-for="category in sortedCategories"
          :key="category.id"
          class="category-item"
          draggable="true"
          @dragstart="handleDragStart($event, category)"
          @dragover="handleDragOver($event)"
          @dragenter="handleDragEnter($event, category)"
          @dragleave="handleDragLeave"
          @drop="handleDrop($event, category)"
          @dragend="handleDragEnd"
          :class="{ 'drag-over': dragOverCategory?.id === category.id }"
        >
            <!-- 拖拽排序句柄 -->
            <div class="drag-handle">
              <i class="icon-drag"></i>
            </div>
            
            <!-- 分类信息 -->
            <div class="category-info" :class="{ editing: editingCategoryId === category.id }">
              <div v-if="editingCategoryId !== category.id" class="view-mode">
                <span class="category-icon">{{ category.icon || '📁' }}</span>
                <div class="category-details">
                  <span class="category-name">{{ category.name }}</span>
                  <span class="category-description">{{ category.description || '无描述' }}</span>
                </div>
                <span class="instruction-count">{{ getInstructionCount(category.id) }} 条指令</span>
              </div>
              
              <div v-else class="edit-mode">
                <input 
                  v-model="editForm.name"
                  type="text"
                  class="form-input"
                  placeholder="分类名称"
                  maxlength="30"
                >
                <textarea 
                  v-model="editForm.description"
                  class="form-textarea"
                  placeholder="分类描述"
                  rows="1"
                  maxlength="100"
                ></textarea>
                <input 
                  v-model="editForm.icon"
                  type="text"
                  class="form-input icon-input"
                  placeholder="图标"
                  maxlength="10"
                >
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="category-actions">
              <div v-if="editingCategoryId !== category.id">
                <button 
                  class="btn btn-sm btn-primary"
                  @click="startEditCategory(category)"
                  :disabled="loading"
                >
                  <i class="icon-edit"></i> 编辑
                </button>
                <button 
                  class="btn btn-sm btn-danger"
                  @click="confirmDeleteCategory(category)"
                  :disabled="loading || getInstructionCount(category.id) > 0"
                  :title="getInstructionCount(category.id) > 0 ? '分类下有指令，无法删除' : '删除分类'"
                >
                  <i class="icon-trash"></i> 删除
                </button>
              </div>
              
              <div v-else>
                <button 
                  class="btn btn-sm btn-success"
                  @click="handleUpdateCategory(category.id)"
                  :disabled="loading || !editForm.name.trim()"
                >
                  <i class="icon-check"></i> 保存
                </button>
                <button 
                  class="btn btn-sm btn-secondary"
                  @click="cancelEditCategory"
                  :disabled="loading"
                >
                  <i class="icon-x"></i> 取消
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示信息 -->
    <div class="tips">
      <p><i class="icon-info-circle"></i> 提示：拖拽分类可以调整显示顺序</p>
    </div>

    <!-- 删除确认对话框 -->
    <DeleteConfirmModal 
      :visible="showDeleteModal"
      :item-name="deletingCategoryName"
      :has-children="deletingCategoryHasInstructions"
      @confirm="handleDeleteCategory"
      @cancel="hideDeleteModal"
    />
  </Modal>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, computed, watch } from 'vue';
import Modal from '@/components/Common/Modal.vue';
import DeleteConfirmModal from '@/components/Common/DeleteConfirmModal.vue';
import type { InstructionCategory } from '@/types/instruction';

interface EditForm {
  name: string;
  description: string;
  icon?: string;
}

interface ErrorState {
  newCategory?: string;
  [key: string]: string | undefined;
}

export default defineComponent({
  name: 'CategoryManagementModal',
  components: {
    Modal,
    DeleteConfirmModal
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    categories: {
      type: Array as () => InstructionCategory[],
      default: () => []
    },
    // 指令计数映射，用于显示每个分类下的指令数量
    instructionCountMap: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'update'],
  setup(props, { emit }) {
    const loading = ref(false);
    const errors = reactive<ErrorState>({});
    const localVisible = ref(props.visible);

    // 监听外部visible变化，同步到本地状态
    watch(() => props.visible, (newValue) => {
      localVisible.value = newValue;
    });

    // 监听本地visible变化，通知父组件
    watch(localVisible, (newValue) => {
      if (!newValue) {
        emit('close');
      }
    });
    
    // 新增分类表单数据
    const newCategoryName = ref('');
    const newCategoryDescription = ref('');
    
    // 编辑状态
    const editingCategoryId = ref<string>('');
    const editForm = reactive<EditForm>({
      name: '',
      description: '',
      icon: ''
    });
    
    // 删除确认状态
    const showDeleteModal = ref(false);
    const deletingCategoryId = ref<string>('');
    const deletingCategoryName = ref('');
    const deletingCategoryHasInstructions = ref(false);
    
    // 拖拽状态
    const draggedCategory = ref<InstructionCategory | null>(null);
    const dragOverCategory = ref<InstructionCategory | null>(null);
    
    // 排序后的分类列表
    const sortedCategories = computed(() => {
      return [...props.categories].sort((a, b) => (a.sort_order || 1) - (b.sort_order || 1));
    });

    // 获取分类下的指令数量
    const getInstructionCount = (categoryId: string): number => {
      return props.instructionCountMap[categoryId] || 0;
    };

    // 添加分类
    const handleAddCategory = async () => {
      // 重置错误信息
      delete errors.newCategory;
      
      // 验证表单
      if (!newCategoryName.value.trim()) {
        errors.newCategory = '请输入分类名称';
        return;
      }
      
      // 检查分类名称是否重复
      if (props.categories.some(cat => cat.name === newCategoryName.value.trim())) {
        errors.newCategory = '分类名称已存在';
        return;
      }
      
      try {
        loading.value = true;
        
        // 构建新分类数据
        const newCategory: Omit<InstructionCategory, 'id' | 'instructions'> = {
          name: newCategoryName.value.trim(),
          description: newCategoryDescription.value.trim(),
          icon: '📁', // 默认图标
          expanded: true,
          sort_order: props.categories.length // 新分类放在最后
        };
        
        // 触发保存事件
        emit('update', { action: 'create', data: newCategory });
        
        // 重置表单
        newCategoryName.value = '';
        newCategoryDescription.value = '';
      } catch (error) {
        console.error('添加分类失败:', error);
        errors.newCategory = '添加分类失败，请重试';
      } finally {
        loading.value = false;
      }
    };
    
    // 拖拽开始
    const handleDragStart = (event: DragEvent, category: InstructionCategory) => {
      draggedCategory.value = category;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        // 设置拖拽数据
        event.dataTransfer.setData('text/plain', category.id);
      }
      // 添加拖拽样式
      if (event.currentTarget) {
        (event.currentTarget as HTMLElement).classList.add('dragging');
      }
    };
    
    // 拖拽经过
    const handleDragOver = (event: DragEvent) => {
      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = 'move';
      }
    };
    
    // 拖拽进入
    const handleDragEnter = (event: DragEvent, category: InstructionCategory) => {
      event.preventDefault();
      if (draggedCategory.value && draggedCategory.value.id !== category.id) {
        dragOverCategory.value = category;
      }
    };
    
    // 拖拽离开
    const handleDragLeave = () => {
      dragOverCategory.value = null;
    };
    
    // 拖拽结束
    const handleDragEnd = (_event: DragEvent) => {
      draggedCategory.value = null;
      dragOverCategory.value = null;
      // 移除所有拖拽样式
      document.querySelectorAll('.category-item.dragging').forEach(el => {
        el.classList.remove('dragging');
      });
      document.querySelectorAll('.category-item.drag-over').forEach(el => {
        el.classList.remove('drag-over');
      });
    };
    
    // 处理放置
    const handleDrop = async (event: DragEvent, targetCategory: InstructionCategory) => {
      event.preventDefault();
      
      if (!draggedCategory.value || draggedCategory.value.id === targetCategory.id) {
        return;
      }
      
      try {
        loading.value = true;
        
        // 获取排序后的分类列表
        const sortedCategories = [...props.categories].sort((a, b) => (a.sort_order || 1) - (b.sort_order || 1));
        
        // 找到拖拽项和目标项的位置
        const draggedIndex = sortedCategories.findIndex(cat => cat.id === draggedCategory.value!.id);
        const targetIndex = sortedCategories.findIndex(cat => cat.id === targetCategory.id);
        
        if (draggedIndex === -1 || targetIndex === -1) return;
        
        // 创建新的排序数组
        const newCategories = [...sortedCategories];
        const [removed] = newCategories.splice(draggedIndex, 1);
        newCategories.splice(targetIndex, 0, removed);
        
        // 更新排序号
        const updatePromises = newCategories.map((category, index) => {
          // 只更新排序发生变化的分类
          if (category.sort_order !== index) {
            return Promise.resolve({
              id: category.id,
              data: { sort_order: index }
            });
          }
          return Promise.resolve(null);
        });
        
        // 等待所有更新数据准备完成
        const updateData = (await Promise.all(updatePromises)).filter(Boolean) as Array<{id: string, data: {sort_order: number}}>;
        
        if (updateData.length > 0) {
          // 触发排序更新事件
          emit('update', { action: 'sort', data: updateData });
        }
      } catch (error) {
        console.error('更新分类排序失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 开始编辑分类
    const startEditCategory = (category: InstructionCategory) => {
      editingCategoryId.value = category.id;
      editForm.name = category.name;
      editForm.description = category.description || '';
      editForm.icon = category.icon || '';
    };

    // 取消编辑分类
    const cancelEditCategory = () => {
      editingCategoryId.value = '';
      editForm.name = '';
      editForm.description = '';
      editForm.icon = '';
    };

    // 更新分类
    const handleUpdateCategory = async (categoryId: string) => {
      // 验证表单
      if (!editForm.name.trim()) {
        return;
      }
      
      // 检查分类名称是否重复（排除当前编辑的分类）
      if (props.categories.some(cat => cat.id !== categoryId && cat.name === editForm.name.trim())) {
        errors[`edit_${categoryId}`] = '分类名称已存在';
        return;
      }
      
      try {
        loading.value = true;
        
        // 构建更新数据
        const updateData: Partial<InstructionCategory> = {
          name: editForm.name.trim(),
          description: editForm.description.trim(),
          icon: editForm.icon || '📁'
        };
        
        // 触发更新事件
        emit('update', { action: 'update', id: categoryId, data: updateData });
        
        // 结束编辑状态
        cancelEditCategory();
      } catch (error) {
        console.error('更新分类失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 确认删除分类
    const confirmDeleteCategory = (category: InstructionCategory) => {
      deletingCategoryId.value = category.id;
      deletingCategoryName.value = category.name;
      deletingCategoryHasInstructions.value = getInstructionCount(category.id) > 0;
      showDeleteModal.value = true;
    };

    // 隐藏删除确认对话框
    const hideDeleteModal = () => {
      showDeleteModal.value = false;
      deletingCategoryId.value = '';
      deletingCategoryName.value = '';
      deletingCategoryHasInstructions.value = false;
    };

    // 删除分类
    const handleDeleteCategory = async () => {
      try {
        loading.value = true;
        
        // 触发删除事件
        emit('update', { action: 'delete', id: deletingCategoryId.value });
        
        // 关闭删除确认对话框
        hideDeleteModal();
      } catch (error) {
        console.error('删除分类失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 取消操作
  const handleClose = () => {
    // 重置表单和状态
    newCategoryName.value = '';
    newCategoryDescription.value = '';
    cancelEditCategory();
    hideDeleteModal();
    
    // 清空错误信息
    Object.keys(errors).forEach(key => {
      delete errors[key];
    });
    
    // 更新本地状态，将通过watch触发close事件
    localVisible.value = false;
  };

    // 监听可见性变化，重置状态
    watch(() => props.visible, (newValue) => {
      if (!newValue) {
        // 外部触发关闭时不需要处理，通过localVisible的watch已经处理
      }
    });

    return {
      loading,
      errors,
      localVisible,
      newCategoryName,
      newCategoryDescription,
      editingCategoryId,
      editForm,
      showDeleteModal,
      deletingCategoryName,
      deletingCategoryHasInstructions,
      draggedCategory,
      dragOverCategory,
      sortedCategories,
      
      // 方法
      getInstructionCount,
      handleAddCategory,
      startEditCategory,
      cancelEditCategory,
      handleUpdateCategory,
      confirmDeleteCategory,
      hideDeleteModal,
      handleDeleteCategory,
      handleClose,
      handleDragStart,
      handleDragOver,
      handleDragEnter,
      handleDragLeave,
      handleDragEnd,
      handleDrop
    };
  }
});
</script>

<style scoped>
.category-management {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

/* 新增分类表单 */
.add-category-form {
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 6px;
}

.form-grid {
  display: grid;
  grid-template-columns: 2fr 3fr auto;
  gap: 12px;
  align-items: flex-end;
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-input,
.form-textarea {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 40px;
}

.form-actions {
  display: flex;
  gap: 8px;
}

.error-message {
  margin-top: 8px;
  font-size: 12px;
  color: #ef4444;
}

/* 分类列表容器 */
.category-list-container {
  margin-bottom: 16px;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.list-count {
  font-size: 14px;
  color: #64748b;
}

.empty-list {
  padding: 32px;
  text-align: center;
  color: #64748b;
  background-color: #f8fafc;
  border-radius: 6px;
}

/* 分类列表 */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: background-color 0.2s, border-color 0.2s;
}

.category-item:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

/* 拖拽相关样式 */
.category-item {
  transition: all 0.2s ease;
}

.category-item.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  cursor: grabbing;
}

.category-item.drag-over {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.category-item.drag-over:before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #3b82f6;
  top: -1px;
}

/* 拖拽句柄 */
.drag-handle {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  color: #94a3b8;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.drag-handle:hover {
  background-color: #e2e8f0;
  color: #64748b;
}

/* 分类信息 */
.category-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-mode {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.category-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f9ff;
  border-radius: 6px;
}

.category-details {
  flex: 1;
  min-width: 0;
}

.category-name {
  display: block;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-description {
  display: block;
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.instruction-count {
  font-size: 12px;
  color: #64748b;
  background-color: #f1f5f9;
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

/* 编辑模式 */
.edit-mode {
  display: flex;
  gap: 8px;
  width: 100%;
  align-items: flex-end;
}

.edit-mode .form-input {
  flex: 1;
}

.edit-mode .form-textarea {
  flex: 2;
  min-height: 36px;
}

.icon-input {
  width: 60px;
  text-align: center;
}

/* 操作按钮 */
.category-actions {
  display: flex;
  gap: 8px;
  white-space: nowrap;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

/* 提示信息 */
.tips {
  padding: 12px;
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  font-size: 12px;
  color: #0c4a6e;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 禁用状态 */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    justify-content: flex-end;
  }
  
  .category-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .drag-handle {
    align-self: flex-start;
  }
  
  .category-info {
    flex-direction: column;
    align-items: stretch;
  }
  
  .view-mode {
    flex-direction: column;
    align-items: stretch;
    text-align: left;
  }
  
  .category-icon {
    align-self: flex-start;
  }
  
  .instruction-count {
    align-self: flex-start;
    margin-top: 4px;
  }
  
  .edit-mode {
    flex-direction: column;
  }
  
  .category-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .category-actions {
    flex-direction: column;
  }
  
  .btn-sm {
    width: 100%;
  }
}
</style>