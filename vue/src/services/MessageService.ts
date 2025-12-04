import { h, createApp } from 'vue';
import Message from '../components/Common/Message.vue';

// 消息选项接口
export interface MessageOptions {
  type?: 'success' | 'error' | 'warning' | 'info' | 'loading';
  message: string;
  duration?: number;
  showClose?: boolean;
  position?: 'top-right' | 'top-center' | 'bottom-right' | 'bottom-center';
  onClose?: () => void;
}

// 消息实例接口
export interface MessageInstance {
  close: () => void;
}

class MessageService {
  // 消息队列
  private messageQueue: MessageInstance[] = [];
  private readonly defaultOptions = {
    type: 'info' as const,
    duration: 3000,
    showClose: true,
    position: 'top-right' as const,
  };

  // 创建消息
  private createMessage(options: MessageOptions): MessageInstance {
    const mergedOptions = {
      ...this.defaultOptions,
      ...options,
    };

    // 创建挂载容器
    const mountContainer = document.createElement('div');
    document.body.appendChild(mountContainer);

    // 记录消息实例
    const messageInstance: MessageInstance = {
      close: () => {
        this.closeMessage(messageInstance, mountContainer);
      },
    };

    this.messageQueue.push(messageInstance);

    // 创建消息选项对象
    const messageOptions = {
      ...mergedOptions,
      onClose: () => {
        // 调用用户提供的onClose回调
        if (mergedOptions.onClose) {
          mergedOptions.onClose();
        }
        // 关闭消息
        this.closeMessage(messageInstance, mountContainer);
      }
    } as any; // 使用类型断言解决类型不兼容问题

    // 渲染消息组件
    const app = createApp({
      render: () => h(Message, messageOptions)
    });

    // 挂载应用
    app.mount(mountContainer);

    // 如果设置了持续时间，自动关闭
    if (mergedOptions.duration !== undefined && mergedOptions.duration > 0) {
      setTimeout(() => {
        this.closeMessage(messageInstance, mountContainer);
      }, mergedOptions.duration);
    }

    return messageInstance;
  }

  // 关闭消息
  private closeMessage(instance: MessageInstance, container: HTMLElement): void {
    // 从队列中移除
    const index = this.messageQueue.indexOf(instance);
    if (index > -1) {
      this.messageQueue.splice(index, 1);
    }

    // 卸载应用
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  }

  // 关闭所有消息
  closeAll(): void {
    while (this.messageQueue.length > 0) {
      this.messageQueue[0].close();
    }
  }

  // 成功消息
  success(message: string, options?: Omit<MessageOptions, 'type' | 'message'>): MessageInstance {
    const finalOptions = {
      message,
      type: 'success' as const,
      ...options,
    };
    return this.createMessage(finalOptions);
  }

  // 警告消息
  warning(message: string, options?: Omit<MessageOptions, 'type' | 'message'>): MessageInstance {
    const finalOptions = {
      message,
      type: 'warning' as const,
      ...options,
    };
    return this.createMessage(finalOptions);
  }

  // 错误消息
  error(message: string, options?: Omit<MessageOptions, 'type' | 'message'>): MessageInstance {
    const finalOptions = {
      message,
      type: 'error' as const,
      ...options,
    };
    return this.createMessage(finalOptions);
  }

  // 信息消息
  info(message: string, options?: Omit<MessageOptions, 'type' | 'message'>): MessageInstance {
    const finalOptions = {
      message,
      type: 'info' as const,
      ...options,
    };
    return this.createMessage(finalOptions);
  }

  // 加载消息
  loading(message: string, options?: Omit<MessageOptions, 'type' | 'message'>): MessageInstance {
    const finalOptions = {
      message,
      type: 'loading' as const,
      ...options,
    };
    return this.createMessage(finalOptions);
  }
}

// 创建服务实例
const messageService = new MessageService();

export default messageService;

// 导出便捷方法
export const {
  success,
  error,
  warning,
  info,
  loading,
  closeAll
} = messageService;