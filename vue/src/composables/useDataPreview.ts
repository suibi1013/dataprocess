import { ref } from 'vue';
import type { SheetData } from '@/types/dataExtraction';

/**
 * 数据预览组合式函数
 */
export function useDataPreview() {
  // 响应式状态
  const showPreviewModal = ref(false);
  const currentSheetData = ref<SheetData | null>(null);
  
  /**
   * 隐藏预览模态框
   */
  const hidePreviewModal = () => {
    showPreviewModal.value = false;
    currentSheetData.value = null;
  };
  
  return {
    // 状态
    showPreviewModal,
    currentSheetData,
    
    // 方法
    hidePreviewModal
  };
}