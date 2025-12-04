<template>
  <Modal
    v-model:visible="localVisible"
    :title="editingCategory ? '编辑分类' : '新增分类'"
    width="500"
    :ok-text="'保存'"
    :cancel-text="'取消'"
    :loading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <div class="category-form">
      <div class="form-section">
        <h4>{{ editingCategory ? '编辑分类信息' : '新增分类信息' }}</h4>
        
        <div class="form-item">
          <label class="form-label required">分类名称</label>
          <input 
            v-model="formData.name"
            type="text"
            class="form-input"
            placeholder="请输入分类名称"
            maxlength="50"
            @blur="validateName"
          >
          <div v-if="errors.name" class="error-message">{{ errors.name }}</div>
        </div>
        
        <div class="form-item">
          <label class="form-label">分类描述</label>
          <textarea 
            v-model="formData.description"
            class="form-textarea"
            placeholder="请输入分类描述"
            rows="3"
            maxlength="200"
          ></textarea>
          <div class="char-count">{{ formData.description.length }}/200</div>
        </div>
        
        <div class="form-item">
          <label class="form-label">排序顺序</label>
          <input 
            v-model.number="formData.sort_order"
            type="number"
            class="form-input"
            placeholder="输入数字越小越靠前"
            min="1"
            max="999"
          >
          <div v-if="errors.sort_order" class="error-message">{{ errors.sort_order }}</div>
        </div>
        
        <div class="form-item checkbox-item">
          <div class="checkbox-wrapper">
            <input 
              v-model="formData.is_active"
              type="checkbox"
              id="is_active_category"
            >
            <label for="is_active_category">是否启用</label>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, watch } from 'vue';
import Modal from '@/components/Common/Modal.vue';
import type { InstructionCategory } from '@/types/instruction';
import { instructionService } from '@/services/instructionService';
import messageService from '@/services/MessageService';

interface FormData {
  name: string;
  description: string;
  sort_order?: number;
  is_active: boolean;
  icon?: string;
}

interface ErrorState {
  name?: string;
  sort_order?: string;
}

export default defineComponent({
  name: 'CategoryFormModal',
  components: {
    Modal
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    category: {
      type: Object as () => InstructionCategory | null,
      default: null
    }
  },
  emits: ['update:visible', 'save'],
  setup(props, { emit }) {
    // 使用本地状态来控制Modal显示，避免直接修改props
    const localVisible = ref(props.visible);
    const loading = ref(false);
    const errors = reactive<ErrorState>({});
    
    // 同步外部visible变化到本地状态
    watch(() => props.visible, (newValue) => {
      localVisible.value = newValue;
      if (newValue) {
        fillFormData(props.category);
      }
    });
    
    // 当本地状态变化时通知父组件
    watch(localVisible, (newValue) => {
      emit('update:visible', newValue);
    });

    // 表单数据
    const formData = reactive<FormData>({
      name: '',
      description: '',
      sort_order: 1,
      is_active: true
    });

    // 重置表单
    const resetForm = () => {
      formData.name = '';
      formData.description = '';
      formData.sort_order = 1;
      formData.is_active = true;
      formData.icon = undefined;
      
      // 清空错误信息
      errors.name = undefined;
      errors.sort_order = undefined;
    };

    // 填充表单数据
    const fillFormData = (category: InstructionCategory | null) => {
      resetForm();
      
      if (category) {
        formData.name = category.name || '';
        formData.description = category.description || '';
        formData.sort_order = category.sort_order || 1;
        // InstructionCategory接口没有is_active属性，保持默认值true
        formData.is_active = true;
        formData.icon = category.icon;
      }
    };

    // 表单验证
    const validateForm = (): boolean => {
      let isValid = true;
      
      // 清空所有错误
      errors.name = undefined;
      errors.sort_order = undefined;
      
      // 验证必填字段
      if (!formData.name.trim()) {
        errors.name = '请输入分类名称';
        isValid = false;
      }
      
      // 验证排序顺序
      if (formData.sort_order !== undefined && formData.sort_order !== null && 
          (formData.sort_order < 1 || formData.sort_order > 999 || !Number.isInteger(formData.sort_order))) {
        errors.sort_order = '排序顺序必须是1-999之间的整数';
        isValid = false;
      }
      
      return isValid;
    };

    // 单个字段验证
    const validateName = () => {
      if (!formData.name.trim()) {
        errors.name = '请输入分类名称';
      } else {
        delete errors.name;
      }
    };

    // 保存分类
    const handleSave = async () => {
      if (!validateForm()) {
        return;
      }
      
      try {
        loading.value = true;
        
        // 构建请求数据
        const requestData = {
          ...formData,
          // 确保排序号有值
          sort_order: formData.sort_order || 1
        };
        
        let response;
        if (props.category) {
          // 更新分类
          response = await instructionService.updateCategory(props.category.id, requestData);
        } else {
          // 创建新分类
          response = await instructionService.createCategory(requestData);
        }
        
        if (response.success) {
          messageService.success(props.category ? '分类更新成功' : '分类创建成功');
          localVisible.value = false;
          emit('save');
        } else {
          messageService.error(response.message || (props.category ? '分类更新失败' : '分类创建失败'));
        }
      } catch (err) {
        messageService.error(props.category ? '分类更新失败' : '分类创建失败');
        console.error('保存分类失败:', err);
      } finally {
        loading.value = false;
      }
    };

    // 取消操作
    const handleCancel = () => {
      localVisible.value = false;
    };

    // 提交表单（Modal的ok事件处理）
    const handleSubmit = () => {
      handleSave();
    };

    // 判断是否正在编辑分类
    const isEditing = () => {
      return props.category !== null;
    };

    return {
      localVisible,
      loading,
      errors,
      formData,
      validateName,
      handleSave,
      handleCancel,
      handleSubmit,
      isEditing
    };
  }
});
</script>

<style scoped>
.category-form {
  padding: 10px 0;
}

.form-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.form-label.required::after {
  content: '*';
  color: #ef4444;
  margin-left: 2px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
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
  min-height: 60px;
}

.error-message {
  margin-top: 4px;
  font-size: 12px;
  color: #ef4444;
}

.char-count {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
}

.checkbox-item {
  display: flex;
  align-items: center;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.checkbox-wrapper label {
  font-weight: normal;
  margin: 0;
  cursor: pointer;
}
</style>