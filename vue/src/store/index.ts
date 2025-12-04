// 状态管理入口文件
// 使用Pinia进行状态管理

import { createPinia } from 'pinia';

// 创建pinia实例
export const pinia = createPinia();

// 导出所有store
export * from './dataSourceStore';
export * from './instructionStore';