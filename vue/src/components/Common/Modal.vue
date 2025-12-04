<template>
  <div 
    v-show="visible" 
    class="modal-backdrop"
    :class="{ 'modal-backdrop-blur': backdropBlur }"
    @click.self="handleBackdropClick"
  >
    <div 
      class="modal-content"
      :class="{ 'modal-content-centered': center }"
      :style="computedContentStyle"
      ref="modalRef"
    >
      <!-- 模态框头部 -->
      <div v-if="title || showClose" class="modal-header">
        <div v-if="title" class="modal-title">{{ title }}</div>
        <button 
          v-if="showClose"
          type="button" 
          class="btn-close"
          @click="handleCancel"
          aria-label="Close"
        >
          <i class="icon-x"></i>
        </button>
      </div>

      <!-- 模态框主体 -->
      <div class="modal-body">
        <slot></slot>
      </div>

      <!-- 模态框底部 -->
      <div v-if="!footer" class="modal-footer">
        <button 
          v-if="cancelText"
          type="button" 
          class="btn btn-secondary"
          @click="handleCancel"
          :disabled="loading"
        >
          {{ cancelText }}
        </button>
        <button 
          v-if="okText"
          type="button" 
          class="btn btn-primary"
          @click="handleOk"
          :disabled="loading"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ okText }}
        </button>
      </div>
      <div v-else class="modal-footer">
        <slot name="footer"></slot>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';

export default defineComponent({
  name: 'BaseModal',
  props: {
    // 是否显示模态框
    visible: {
      type: Boolean,
      default: false
    },
    // 模态框标题
    title: {
      type: String,
      default: ''
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
    // 是否显示关闭按钮
    showClose: {
      type: Boolean,
      default: true
    },
    // 是否在点击遮罩层时关闭模态框
    closeOnClickModal: {
      type: Boolean,
      default: true
    },
    // 是否在按下ESC键时关闭模态框
    closeOnPressEscape: {
      type: Boolean,
      default: true
    },
    // 是否居中显示
    center: {
      type: Boolean,
      default: false
    },
    // 是否禁用滚动
    disableScroll: {
      type: Boolean,
      default: true
    },
    // 遮罩层是否模糊
    backdropBlur: {
      type: Boolean,
      default: false
    },
    // 加载状态
    loading: {
      type: Boolean,
      default: false
    },
    // 模态框宽度
    width: {
      type: [String, Number],
      default: ''
    },
    // 模态框高度
    height: {
      type: [String, Number],
      default: ''
    },
    // 自定义样式
    contentStyle: {
      type: Object,
      default: () => ({})
    },
    // 底部内容，自定义底部时使用
    footer: {
      type: [Boolean, Object],
      default: null
    }
  },
  emits: ['update:visible', 'ok', 'cancel'],
  setup(props, { emit }) {
    const modalRef = ref<HTMLElement>();
    const isKeydown = ref(false);

    // 计算模态框内容样式
    const computedContentStyle = computed(() => {
      const style: Record<string, string> = { ...props.contentStyle };
      if (props.width) {
        style.width = typeof props.width === 'number' ? `${props.width}px` : props.width;
      }
      if (props.height) {
        style.height = typeof props.height === 'number' ? `${props.height}px` : props.height;
      }
      return style;
    });

    // 处理遮罩层点击
    const handleBackdropClick = () => {
      if (props.closeOnClickModal && !props.loading) {
        handleCancel();
      }
    };

    // 处理确定按钮点击
    const handleOk = () => {
      if (!props.loading) {
        emit('ok');
      }
    };

    // 处理取消按钮点击
    const handleCancel = () => {
      if (!props.loading) {
        emit('cancel');
        emit('update:visible', false);
      }
    };

    // 处理键盘事件
    const handleKeydown = (e: KeyboardEvent) => {
      if (props.visible && props.closeOnPressEscape && e.key === 'Escape' && !isKeydown.value && !props.loading) {
        isKeydown.value = true;
        handleCancel();
        // 防止快速连续按下ESC键导致的问题
        setTimeout(() => {
          isKeydown.value = false;
        }, 100);
      }
    };

    // 设置或移除滚动条禁用
    const toggleScrollDisable = (disable: boolean) => {
      if (props.disableScroll) {
        const body = document.body;
        if (disable) {
          body.style.overflow = 'hidden';
          body.style.paddingRight = getScrollbarWidth() + 'px';
        } else {
          body.style.overflow = '';
          body.style.paddingRight = '';
        }
      }
    };

    // 获取滚动条宽度
    const getScrollbarWidth = (): number => {
      // 创建一个带有滚动条的div
      const outer = document.createElement('div');
      outer.style.visibility = 'hidden';
      outer.style.overflow = 'scroll';
      document.body.appendChild(outer);
      
      // 创建一个内部div来测量内容宽度
      const inner = document.createElement('div');
      outer.appendChild(inner);
      
      // 计算滚动条宽度
      const scrollbarWidth = outer.offsetWidth - inner.offsetWidth;
      
      // 清理
      outer.parentNode?.removeChild(outer);
      
      return scrollbarWidth;
    };

    // 监听可见性变化
    watch(() => props.visible, async (newValue) => {
      if (newValue) {
        // 显示模态框时，禁用滚动条
        toggleScrollDisable(true);
        
        // 等待DOM更新后，聚焦到模态框
        await nextTick();
        if (modalRef.value) {
          modalRef.value.focus({ preventScroll: true });
        }
      } else {
        // 隐藏模态框时，恢复滚动条
        toggleScrollDisable(false);
      }
    });

    // 组件挂载时添加键盘事件监听
    onMounted(() => {
      document.addEventListener('keydown', handleKeydown);
    });

    // 组件卸载时移除键盘事件监听
    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeydown);
      // 确保恢复滚动条
      toggleScrollDisable(false);
    });

    return {
      modalRef,
      computedContentStyle,
      handleBackdropClick,
      handleOk,
      handleCancel
    };
  }
});
</script>

<style scoped>
/* 遮罩层 */
.modal-backdrop {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  overflow-x: hidden;
  overflow-y: auto;
}

/* 遮罩层模糊效果 */
.modal-backdrop-blur {
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

/* 模态框内容 */
.modal-content {
  position: relative;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  max-width: 100%;
  max-height: 90vh;
  overflow: hidden;
  outline: none;
  display: flex;
  flex-direction: column;
}

/* 模态框居中 */
.modal-content-centered {
  align-self: center;
}

/* 模态框头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e1e8ed;
  min-height: 52px;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: #64748b;
  transition: background-color 0.2s, color 0.2s;
  font-size: 16px;
  line-height: 1;
}

.btn-close:hover {
  background-color: #f1f5f9;
  color: #334155;
}

/* 模态框主体 */
.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  min-height: 40px;
}

/* 模态框底部 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e1e8ed;
  background-color: #f8fafc;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 64px;
  justify-content: center;
}

.btn-primary {
  background-color: #3b82f6;
  color: #ffffff;
  border-color: #3b82f6;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
  border-color: #2563eb;
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #334155;
  border-color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e2e8f0;
  border-color: #cbd5e1;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载状态 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-backdrop {
    padding: 10px;
    align-items: flex-start;
  }
  
  .modal-content {
    margin-top: 10vh;
    height: auto;
    max-height: 80vh;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 12px 16px;
  }
  
  .modal-title {
    font-size: 16px;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .modal-backdrop {
    padding: 8px;
  }
  
  .modal-content {
    margin-top: 5vh;
  }
}

/* 滚动条样式 */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>