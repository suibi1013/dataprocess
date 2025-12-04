<template>
  <Modal
    v-model:visible="isVisible"
    :title="title"
    :ok-text="okText"
    :cancel-text="cancelText"
    :loading="loading"
    :width="width"
    :center="true"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <div class="confirm-dialog-content">
      <!-- 图标区域 -->
      <div v-if="icon" class="confirm-dialog-icon">
        <i :class="icon"></i>
      </div>
      
      <!-- 消息内容 -->
      <div class="confirm-dialog-message">
        <div v-if="message" class="message-text" v-html="message"></div>
        <slot v-else></slot>
      </div>
      
      <!-- 额外内容 -->
      <div v-if="extraContent" class="confirm-dialog-extra">
        {{ extraContent }}
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch } from 'vue';
import Modal from './Modal.vue';

export default defineComponent({
  name: 'ConfirmDialog',
  components: {
    Modal
  },
  props: {
    // 是否显示对话框
    visible: {
      type: Boolean,
      default: false
    },
    // 对话框标题
    title: {
      type: String,
      default: '确认操作'
    },
    // 确认按钮文本
    okText: {
      type: String,
      default: '确定'
    },
    // 取消按钮文本
    cancelText: {
      type: String,
      default: '取消'
    },
    // 确认按钮类型，用于控制样式
    okType: {
      type: String,
      default: 'primary',
      validator: (value: string) => ['primary', 'danger', 'success', 'warning'].includes(value)
    },
    // 消息内容
    message: {
      type: String,
      default: ''
    },
    // 图标类型
    iconType: {
      type: String,
      default: 'warning',
      validator: (value: string) => ['info', 'success', 'warning', 'error', 'question'].includes(value)
    },
    // 是否显示图标
    showIcon: {
      type: Boolean,
      default: true
    },
    // 加载状态
    loading: {
      type: Boolean,
      default: false
    },
    // 对话框宽度
    width: {
      type: [String, Number],
      default: 420
    },
    // 额外内容
    extraContent: {
      type: String,
      default: ''
    }
  },
  emits: ['update:visible', 'confirm', 'cancel'],
  setup(props, { emit }) {
    const isVisible = ref(props.visible);

    // 计算图标类名
    const icon = computed(() => {
      if (!props.showIcon) return '';
      
      const iconMap: Record<string, string> = {
        info: 'icon-info-circle text-info',
        success: 'icon-check-circle text-success',
        warning: 'icon-exclamation-circle text-warning',
        error: 'icon-times-circle text-error',
        question: 'icon-question-circle text-info'
      };
      
      return iconMap[props.iconType] || iconMap.warning;
    });

    // 处理确认按钮点击
    const handleOk = () => {
      if (!props.loading) {
        emit('confirm');
        emit('update:visible', false);
      }
    };

    // 处理取消按钮点击
    const handleCancel = () => {
      if (!props.loading) {
        emit('cancel');
      }
    };

    // 监听外部visible变化
    watch(() => props.visible, (newValue) => {
      isVisible.value = newValue;
    });

    // 监听内部visible变化，同步到外部
    watch(isVisible, (newValue) => {
      emit('update:visible', newValue);
    });

    return {
      isVisible,
      icon,
      handleOk,
      handleCancel
    };
  }
});
</script>

<style scoped>
.confirm-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.confirm-dialog-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.confirm-dialog-icon i {
  font-size: 48px;
  line-height: 1;
}

.confirm-dialog-message {
  text-align: center;
}

.message-text {
  font-size: 16px;
  line-height: 1.5;
  color: #334155;
  word-wrap: break-word;
  word-break: break-word;
}

.confirm-dialog-extra {
  text-align: center;
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

/* 图标颜色 */
.text-info {
  color: #3b82f6;
}

.text-success {
  color: #10b981;
}

.text-warning {
  color: #f59e0b;
}

.text-error {
  color: #ef4444;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .confirm-dialog-content {
    gap: 10px;
  }
  
  .confirm-dialog-icon i {
    font-size: 40px;
  }
  
  .message-text {
    font-size: 15px;
  }
  
  .confirm-dialog-extra {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .confirm-dialog-icon i {
    font-size: 32px;
  }
  
  .message-text {
    font-size: 14px;
  }
}

/* 动画效果 */
.confirm-dialog-content {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>