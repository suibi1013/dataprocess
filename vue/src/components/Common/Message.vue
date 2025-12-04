<template>
  <div 
    v-show="visible"
    class="message-container"
    :class="[`message-${type}`, messageClass]"
    :style="containerStyle"
    @mouseenter="clearTimer"
    @mouseleave="startTimer"
  >
    <div class="message-content">
      <i v-if="showIcon" :class="icon" class="message-icon"></i>
      <div class="message-text">
        <slot>{{ message }}</slot>
      </div>
      <button 
        v-if="showClose"
        type="button" 
        class="message-close-btn"
        @click="close"
        aria-label="Close"
      >
        <i class="icon-x"></i>
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, onMounted, onUnmounted, type PropType } from 'vue';

export default defineComponent({
  name: 'BaseMessage',
  props: {
    // 消息类型
    type: {
      type: String,
      default: 'info',
      validator: (value: string) => ['success', 'warning', 'error', 'info', 'loading'].includes(value)
    },
    // 消息内容
    message: {
      type: String,
      default: ''
    },
    // 显示时长（毫秒），设置为0则不会自动关闭
    duration: {
      type: Number,
      default: 3000
    },
    // 是否显示图标
    showIcon: {
      type: Boolean,
      default: true
    },
    // 是否显示关闭按钮
    showClose: {
      type: Boolean,
      default: true
    },
    // 自定义类名
    customClass: {
      type: String,
      default: ''
    },
    // 消息位置
    position: {
      type: String,
      default: 'top-right',
      validator: (value: string) => ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'].includes(value)
    },
    // 偏移量
    offset: {
      type: Number,
      default: 20
    },
    // z-index
    zIndex: {
      type: Number,
      default: 1010
    },
    // 关闭回调
    onClose: {
      type: Function as PropType<() => void>,
      default: undefined
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const visible = ref(false);
    const timer = ref<number | null>(null);

    // 计算图标类名
    const icon = computed(() => {
      const iconMap: Record<string, string> = {
        success: 'icon-check-circle',
        warning: 'icon-exclamation-triangle',
        error: 'icon-times-circle',
        info: 'icon-info-circle',
        loading: 'icon-spinner spinner'
      };
      return iconMap[props.type] || iconMap.info;
    });

    // 计算消息类名
    const messageClass = computed(() => {
      const classes = [props.customClass];
      if (props.position) {
        classes.push(`message-${props.position}`);
      }
      return classes.filter(Boolean).join(' ');
    });

    // 计算容器样式
    const containerStyle = computed(() => {
      const style: Record<string, string | number> = {
        zIndex: props.zIndex
      };
      
      // 根据位置设置偏移量
      if (props.position.includes('top')) {
        style.top = `${props.offset}px`;
      } else if (props.position.includes('bottom')) {
        style.bottom = `${props.offset}px`;
      }
      
      if (props.position.includes('left')) {
        style.left = `${props.offset}px`;
      } else if (props.position.includes('right')) {
        style.right = `${props.offset}px`;
      }
      
      return style;
    });

    // 开始计时
    const startTimer = () => {
      if (props.duration > 0 && !timer.value) {
        timer.value = window.setTimeout(() => {
          close();
        }, props.duration);
      }
    };

    // 清除计时器
    const clearTimer = () => {
      if (timer.value) {
        clearTimeout(timer.value);
        timer.value = null;
      }
    };

    // 关闭消息
    const close = () => {
      visible.value = false;
      clearTimer();
      
      // 触发关闭回调
      if (props.onClose) {
        props.onClose();
      }
      
      // 通知父组件
      emit('close');
    };

    // 显示消息
    const show = () => {
      visible.value = true;
      startTimer();
    };

    // 监听可见性变化
    watch(visible, (newValue) => {
      if (newValue) {
        startTimer();
      } else {
        clearTimer();
      }
    });

    // 组件挂载时显示消息
    onMounted(() => {
      // 延迟显示，确保动画效果正常
      setTimeout(() => {
        show();
      }, 10);
    });

    // 组件卸载时清除计时器
    onUnmounted(() => {
      clearTimer();
    });

    return {
      visible,
      icon,
      messageClass,
      containerStyle,
      startTimer,
      clearTimer,
      close
    };
  }
});
</script>

<style scoped>
.message-container {
  position: fixed;
  max-width: 360px;
  min-width: 280px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  animation: fadeIn 0.3s ease-out;
  transition: all 0.3s ease;
  pointer-events: auto;
  z-index: 1010;
}

/* 消息位置 */
.message-top-right {
  top: 20px;
  right: 20px;
}

.message-top-left {
  top: 20px;
  left: 20px;
}

.message-bottom-right {
  bottom: 20px;
  right: 20px;
}

.message-bottom-left {
  bottom: 20px;
  left: 20px;
}

.message-top-center {
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.message-bottom-center {
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
}

/* 消息内容 */
.message-content {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

/* 消息图标 */
.message-icon {
  font-size: 18px;
  flex-shrink: 0;
  line-height: 1;
}

/* 消息文本 */
.message-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
  color: #334155;
  word-wrap: break-word;
  word-break: break-word;
}

/* 关闭按钮 */
.message-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 2px;
  color: #94a3b8;
  transition: background-color 0.2s, color 0.2s;
  flex-shrink: 0;
  font-size: 14px;
}

.message-close-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: #64748b;
}

/* 消息类型样式 */
.message-success {
  background-color: #f0fdf4;
  border-left: 4px solid #10b981;
}

.message-success .message-icon {
  color: #10b981;
}

.message-warning {
  background-color: #fffbeb;
  border-left: 4px solid #f59e0b;
}

.message-warning .message-icon {
  color: #f59e0b;
}

.message-error {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
}

.message-error .message-icon {
  color: #ef4444;
}

.message-info {
  background-color: #eff6ff;
  border-left: 4px solid #3b82f6;
}

.message-info .message-icon {
  color: #3b82f6;
}

.message-loading {
  background-color: #f8fafc;
  border-left: 4px solid #64748b;
}

.message-loading .message-icon {
  color: #64748b;
}

/* 加载动画 */
.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 消息容器悬停效果 */
.message-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-container {
    max-width: calc(100vw - 40px);
    min-width: auto;
    width: auto;
  }
  
  .message-top-right,
  .message-top-left,
  .message-bottom-right,
  .message-bottom-left {
    left: 50%;
    transform: translateX(-50%);
  }
  
  .message-text {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .message-container {
    max-width: calc(100vw - 20px);
    padding: 10px 12px;
  }
  
  .message-icon {
    font-size: 16px;
  }
  
  .message-text {
    font-size: 12px;
  }
}
</style>