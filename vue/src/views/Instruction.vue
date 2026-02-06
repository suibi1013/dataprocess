<template>
  <div class="instruction-page">
    <div class="page-header">
      <h1>指令管理</h1>
      <div class="header-actions">
        <el-button type="primary" icon="Plus" @click="showAddInstructionModal">
          新增指令
        </el-button>
        <el-button type="default" icon="Menu" @click="showCategoryManagement">
          分类管理
        </el-button>
        <el-button type="warning" icon="Download" @click="installDependencies">
          安装依赖包
        </el-button>
      </div>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="search-filter">
      <el-input 
        v-model="searchKeyword"
        placeholder="搜索指令名称或描述"
        prefix-icon="Search"
        @input="debouncedSearch"
        class="search-input"
      />
      <el-select v-model="selectedCategory" @change="handleFilterChange" class="filter-select" placeholder="选择分类">
        <el-option value="" label="全部分类" />
        <el-option v-for="category in categories" :key="category.id" :value="category.id" :label="category.name" />
      </el-select>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-message">{{ error }}</div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>
    
    <!-- 指令列表 -->
    <div v-else-if="filteredInstructions.length > 0" class="instruction-content">
      <table class="instruction-table">
        <thead>
          <tr>
            <th>分类</th>
            <th>指令名称</th>
            <th>描述</th>
            <th>排序</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="instruction in filteredInstructions"
            :key="instruction.id"
            :class="{ 'drag-over': dragOverItem?.id === instruction.id }"
            draggable="true"
            @dragstart="handleDragStart($event, instruction)"
            @dragover="handleDragOver($event, instruction)"
            @drop="handleDrop($event, instruction)"
            @dragend="handleDragEnd"
          >
            <td>{{ getCategoryName(instruction.category) }}</td>
            <td>{{ instruction.name }}</td>
            <td class="description-cell">{{ instruction.description }}</td>
            <td>{{ instruction.sort_order || 1 }}</td>
            <td>
              <span class="status-badge" :class="instruction.is_active ? 'status-active' : 'status-inactive'">
                {{ instruction.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>
              <div class="table-actions">
                <el-button type="primary" size="small" @click="editInstruction(instruction)">
                  编辑
                </el-button>
                <el-button 
                  size="small"
                  :type="instruction.is_active ? 'danger' : 'success'"
                  @click="toggleInstructionStatus(instruction)"
                >
                  {{ instruction.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button type="danger" size="small" @click="deleteInstruction(instruction)">
                  删除
                </el-button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📝</div>
      <h3>暂无指令数据</h3>
      <p>创建您的第一条指令开始数据处理流程</p>
      <div class="empty-actions">
        <el-button type="primary" icon="Plus" @click="showAddInstructionModal">
          新增指令
        </el-button>
        <el-button type="default" icon="Menu" @click="showCategoryManagement">
          管理分类
        </el-button>
      </div>
    </div>
    
    <!-- 分类管理模态框 -->
    <CategoryManagement
      v-model:visible="showCategoryModal"
      @close="showCategoryModal = false"
      @save="loadAllData"
    />
    
    <!-- 新增/编辑指令模态框 -->
    <AddInstructionModal
      v-model:visible="showAddInstruction"
      :instruction="editingInstruction"
      @close="handleCloseAddInstructionModal"
      @save="handleSaveInstruction"
    />
    
    <!-- 安装依赖包对话框 -->
    <el-dialog
      v-model="showInstallDependenciesDialog"
      title="安装依赖包"
      width="600px"
      @close="handleCloseInstallDialog"
    >
      <el-form label-width="80px">
        <el-form-item label="依赖包">
          <el-input
            v-model="dependenciesInput"
            type="textarea"
            :rows="8"
            placeholder="请输入要安装的依赖包，每行一个。支持格式：\nrequests==2.28.1\ndjango>=4.2\n--force-reinstall package==1.0.0"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCloseInstallDialog">取消</el-button>
          <el-button type="primary" @click="handleConfirmInstall">确认安装</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { Instruction } from '@/types/instruction';
import { instructionService } from '@/services/instructionService';
import { useInstructionStore } from '@/store/instructionStore';
import CategoryManagement from '@/components/Instruction/CategoryManagement.vue';
import AddInstructionModal from '@/components/Instruction/AddInstructionModal.vue';

export default defineComponent({
  name: 'InstructionPage',
  components: {
    CategoryManagement,
    AddInstructionModal
  },
  setup() {
    // 初始化store
    const instructionStore = useInstructionStore();
    
    // 状态定义
    const draggedItem = ref<Instruction | null>(null);
    const dragOverItem = ref<Instruction | null>(null);
    
    // 本地加载状态（用于组件内操作的加载指示）
    const localLoading = ref(false);
    
    // 本地错误状态（用于组件内操作的错误指示）
    const localError = ref<string | null>(null);
    
    // 模态框状态
    const showCategoryModal = ref(false);
    const showAddInstruction = ref(false);
    const editingInstruction = ref<Instruction | null>(null);
    const showInstallDependenciesDialog = ref(false);
    const dependenciesInput = ref('');
    
    // 搜索和筛选状态
    const searchKeyword = ref('');
    const selectedCategory = ref('');
    
    // 防抖计时器
    let searchTimeout: number | null = null;
    
    // 加载所有数据
    const loadAllData = async () => {
      // 重置搜索和筛选
      searchKeyword.value = '';
      selectedCategory.value = '';
      
      // 调用store中的方法加载数据
      await instructionStore.fetchAllData();
    };
    
    // 获取指定分类下的所有指令
    const getCategoryInstructions = computed(() => {
      return (categoryId: string) => {
        return allInstructions.value
          .filter(item => item.category === categoryId)
          .sort((a, b) => (a.sort_order || 1) - (b.sort_order || 1));
      };
    });
    
    // 获取分类名称
    const getCategoryName = (categoryId: string): string => {
      const category = categories.value.find(cat => cat.id === categoryId);
      return category ? category.name : '未分类';
    };
    
    // 筛选后的指令列表
    const filteredInstructions = computed(() => {
      let instructions = [...allInstructions.value];
      
      // 按分类筛选
      if (selectedCategory.value) {
        instructions = instructions.filter(inst => inst.category === selectedCategory.value);
      }
      
      // 按关键词搜索
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase();
        instructions = instructions.filter(inst => 
          inst.name.toLowerCase().includes(keyword) || 
          inst.description.toLowerCase().includes(keyword)
        );
      }
      
      // 保持后端返回的原始顺序，不进行额外排序
      return instructions;
    });
    
    // 从store获取分类数据
    const categories = computed(() => instructionStore.categories);
    
    // 从store获取指令数据
    const allInstructions = computed(() => instructionStore.instructions);
    
    // 从store获取加载状态
      const storeLoading = computed(() => instructionStore.loading);
      const storeError = computed(() => instructionStore.error);
      
      // 统一的加载状态（合并store加载状态和本地操作加载状态）
      const loading = computed(() => storeLoading.value || localLoading.value);
      
      // 统一的错误状态（优先显示本地操作的错误）
      const error = computed(() => localError.value || storeError.value);
    
    // 处理拖拽开始
    const handleDragStart = (event: DragEvent, instruction: Instruction) => {
      draggedItem.value = instruction;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('application/json', JSON.stringify(instruction));
      }
    };
    
    // 处理拖拽经过
    const handleDragOver = (event: DragEvent, instruction: Instruction) => {
      event.preventDefault();
      // 只有当拖拽项和目标项是同一分类且不是同一个项时，才允许放置
      if (draggedItem.value && draggedItem.value.id !== instruction.id && 
          draggedItem.value.category === instruction.category) {
        dragOverItem.value = instruction;
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = 'move';
        }
      } else {
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = 'none';
        }
      }
    };
    
    // 处理放置
    const handleDrop = async (event: DragEvent, targetInstruction: Instruction) => {
      event.preventDefault();
      
      // 确保是同一分类下的拖拽
      if (!draggedItem.value || draggedItem.value.id === targetInstruction.id || 
          draggedItem.value.category !== targetInstruction.category) {
        dragOverItem.value = null;
        return;
      }

      try {
        localLoading.value = true;
        localError.value = null;
        
        // 获取当前分类下的所有指令
        const categoryInstructions = allInstructions.value
          .filter(item => item.category === targetInstruction.category)
          .sort((a, b) => (a.sort_order || 1) - (b.sort_order || 1));

        // 找到拖拽项和目标项的位置
        const draggedIndex = categoryInstructions.findIndex(item => item.id === draggedItem.value!.id);
        const targetIndex = categoryInstructions.findIndex(item => item.id === targetInstruction.id);

        if (draggedIndex === -1 || targetIndex === -1) {
          dragOverItem.value = null;
          return;
        }

        // 创建新的排序数组
        const newInstructions = [...categoryInstructions];
        const [removed] = newInstructions.splice(draggedIndex, 1);
        newInstructions.splice(targetIndex, 0, removed);

        // 更新排序号
        const updatePromises = newInstructions.map((instruction, index) => {
          if (instruction.sort_order !== (index + 1)) {
            return instructionService.updateInstruction(instruction.id, {
              sort_order: index + 1
            });
          }
          return Promise.resolve({ success: true });
        });

        // 等待所有更新完成
        const results = await Promise.all(updatePromises);
        
        // 检查是否所有更新都成功
        const allSuccess = results.every(result => result.success);
        
        if (allSuccess) {
          // 更新本地状态
          newInstructions.forEach((instruction, index) => {
            const localInstruction = allInstructions.value.find(item => item.id === instruction.id);
            if (localInstruction) {
              localInstruction.sort_order = index + 1;
            }
          });
          ElMessage.success('指令排序已更新');
        } else {
          throw new Error('更新排序失败');
        }
      } catch (err) {
        localError.value = err instanceof Error ? err.message : '排序更新失败';
      } finally {
        localLoading.value = false;
        dragOverItem.value = null;
        draggedItem.value = null;
      }
    };
    
    // 处理拖拽结束
    const handleDragEnd = () => {
      dragOverItem.value = null;
      draggedItem.value = null;
    };

    // 获取参数预览
    const getParamsPreview = (params: any[]): string => {
      if (!params || params.length === 0) return '无参数';
      return `有 ${params.length} 个参数`;
    };
    
    // 安装依赖包
    const installDependencies = async () => {
      // 显示安装依赖包对话框
      showInstallDependenciesDialog.value = true;
    };
    
    // 关闭安装依赖包对话框
    const handleCloseInstallDialog = () => {
      showInstallDependenciesDialog.value = false;
      dependenciesInput.value = '';
    };
    
    // 确认安装依赖包
    const handleConfirmInstall = async () => {
      try {
        localLoading.value = true;
        localError.value = null;
        
        ElMessage.info('正在安装依赖包...');
        
        // 调用后端API安装依赖包
        const response = await instructionService.installDependencies(dependenciesInput.value);
        
        if (response.success) {
          ElMessage.success('依赖包安装成功');
          handleCloseInstallDialog();
        } else {
          ElMessage.error(response.message || '依赖包安装失败');
        }
      } catch (err) {
        ElMessage.error('依赖包安装失败');
        console.error('安装依赖包失败:', err);
      } finally {
        localLoading.value = false;
      }
    };
    
    // 显示分类管理
    const showCategoryManagement = () => {
      showCategoryModal.value = true;
    };

    // 显示新增指令模态框
    const showAddInstructionModal = (categoryId?: string) => {
      editingInstruction.value = null;
      showAddInstruction.value = true;
      
      // 如果指定了分类ID，可以在模态框中预设分类
      if (categoryId) {
        // 这里通过事件总线或状态管理传递分类ID给模态框
        // 或者在AddInstructionModal中添加一个prop来接收
      }
    };
    
    // 编辑指令
    const editInstruction = (instruction: Instruction) => {
      editingInstruction.value = instruction;
      showAddInstruction.value = true;
    };
    
    // 删除指令
    const deleteInstruction = async (instruction: Instruction) => {
      ElMessageBox.confirm(
        `确定要删除指令"${instruction.name}"吗？`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          localLoading.value = true;
          const response = await instructionService.deleteInstruction(instruction.id);
          if (response.success) {
            // 从本地移除指令
            const index = allInstructions.value.findIndex(item => item.id === instruction.id);
            if (index !== -1) {
              allInstructions.value.splice(index, 1);
            }
            ElMessage.success('指令删除成功');
          } else {
            ElMessage.error(response.message || '指令删除失败');
          }
        } catch (err) {
          ElMessage.error('指令删除失败');
          console.error('删除指令失败:', err);
        } finally {
          localLoading.value = false;
        }
      }).catch(() => {
        // 用户取消删除
      });
    };

    // 切换指令启用状态
    const toggleInstructionStatus = async (instruction: Instruction) => {
      try {
        localLoading.value = true;
        const newStatus = !instruction.is_active;
        const response = await instructionService.updateInstruction(instruction.id, {
          is_active: newStatus
        });
        
        if (response.success) {
          // 更新本地状态
          const localInstruction = allInstructions.value.find(item => item.id === instruction.id);
          if (localInstruction) {
            localInstruction.is_active = newStatus;
          }
          ElMessage.success(`指令已${newStatus ? '启用' : '禁用'}`);
        } else {
          ElMessage.error(response.message || `切换状态失败`);
        }
      } catch (err) {
        ElMessage.error('切换状态失败');
        console.error('切换指令状态失败:', err);
      } finally {
          localLoading.value = false;
        }
    };

    // 处理保存指令
    const handleSaveInstruction = async (instructionData: any) => {
      try {
        localLoading.value = true;
        
        let response;
        if (editingInstruction.value) {
          // 更新指令
          response = await instructionService.updateInstruction(editingInstruction.value.id, instructionData);
        } else {
          // 创建新指令
          response = await instructionService.createInstruction(instructionData);
        }
        
        if (response.success) {
          // 重新加载所有数据以确保状态一致
          await loadAllData();
          ElMessage.success(editingInstruction.value ? '指令更新成功' : '指令创建成功');
          handleCloseAddInstructionModal();
        } else {
          ElMessage.error(response.message || (editingInstruction.value ? '指令更新失败' : '指令创建失败'));
        }
      } catch (err) {
        ElMessage.error(editingInstruction.value ? '指令更新失败' : '指令创建失败');
        console.error('保存指令失败:', err);
      } finally {
          localLoading.value = false;
        }
    };
    
    // 关闭新增/编辑指令模态框
    const handleCloseAddInstructionModal = () => {
      showAddInstruction.value = false;
      editingInstruction.value = null;
    };
    
    // 处理筛选变化
    const handleFilterChange = () => {
      // 筛选变化时不需要防抖
    };
    
    // 防抖搜索
    const debouncedSearch = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      
      searchTimeout = window.setTimeout(() => {
        // 搜索逻辑已在computed中处理
      }, 300);
    };
    
    // 组件挂载时加载数据
    onMounted(() => {
      loadAllData();
    });
    
    // 组件卸载时清除定时器
    onUnmounted(() => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    });

    return {
      loading,
      error,
      categories,
      allInstructions,
      getCategoryInstructions: getCategoryInstructions.value,
      getCategoryName,
      filteredInstructions,
      showCategoryModal,
      showAddInstruction,
      editingInstruction,
      searchKeyword,
      selectedCategory,
      dragOverItem,
      handleDragStart,
      handleDragOver,
      handleDrop,
      handleDragEnd,
      getParamsPreview,
      showCategoryManagement,
      showAddInstructionModal,
      editInstruction,
      deleteInstruction,
      toggleInstructionStatus,
      handleSaveInstruction,
      handleCloseAddInstructionModal,
      handleFilterChange,
      debouncedSearch,
      installDependencies,
      showInstallDependenciesDialog,
      dependenciesInput,
      handleCloseInstallDialog,
      handleConfirmInstall,
      loadAllData
    };
  }
});
</script>

<style scoped>
.instruction-page {
  padding: 20px;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
}

.category-section {
  margin-bottom: 30px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.category-title {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}

.instruction-content {
  margin-top: 15px;
}

.instruction-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.instruction-table th:first-child,
.instruction-table td:first-child {
  min-width: 120px;
}

.instruction-table th,
.instruction-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.instruction-table th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #333;
}

.instruction-table tbody tr {
  cursor: move;
  transition: background-color 0.2s;
}

.instruction-table tbody tr:hover {
  background-color: #f9f9f9;
}

.instruction-table tbody tr.drag-over {
  background-color: #e3f2fd;
  border: 2px dashed #2196f3;
}

.description-cell {
  max-width: 300px;
  word-break: break-word;
}

/* 适配element-plus组件样式 */
.search-filter {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.filter-select {
  width: 200px;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-actions .el-button {
  margin: 0;
}

/* 使用element-plus的状态标签 */
.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background-color: #f0f9eb;
  color: #67c23a;
  border-color: #e1f3d8;
}

.status-inactive {
  background-color: #fef0f0;
  color: #f56c6c;
  border-color: #fbc4c4;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-actions button {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.edit-btn {
  background-color: #2196f3;
  color: white;
}

.edit-btn:hover {
  background-color: #1976d2;
}

.toggle-btn {
  background-color: #4caf50;
  color: white;
}

.toggle-btn:hover {
  background-color: #388e3c;
}

.toggle-disabled {
  background-color: #f44336 !important;
}

.toggle-disabled:hover {
  background-color: #d32f2f !important;
}

.delete-btn {
  background-color: #f44336;
  color: white;
}

.delete-btn:hover {
  background-color: #d32f2f;
}

.empty-instructions {
  text-align: center;
  padding: 40px 20px;
  background-color: white;
  border-radius: 6px;
  border: 1px dashed #ddd;
}

.empty-instructions p {
  margin: 0 0 15px 0;
  color: #666;
}
</style>