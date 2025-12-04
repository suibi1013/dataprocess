<template>
  <div class="test-page">
    <h1>测试页面</h1>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import { success } from '@/services/MessageService';
import { instructionService } from '@/services';
import type { Instruction, InstructionCategory } from '@/types/instruction';

export default defineComponent({
  name: 'TestInstructionPage',
  setup() {
    // 状态定义
    const loading = ref(false);
    const error = ref<string | null>(null);
    const categories = ref<InstructionCategory[]>([]);
    const allInstructions = ref<Instruction[]>([]);
    const draggedItem = ref<Instruction | null>(null);
    // 拖拽悬停项 (暂时未使用)

    // 处理放置
    const handleDrop = async (event: DragEvent, targetInstruction: Instruction) => {
      event.preventDefault();
      
      // 确保是同一分类下的拖拽
      if (!draggedItem.value || draggedItem.value.id === targetInstruction.id ||
          draggedItem.value.category !== targetInstruction.category) {
        return;
      }

      try {
        loading.value = true;
        
        // 获取当前分类下的所有指令
        const categoryInstructions = allInstructions.value
          .filter(item => item.category === targetInstruction.category)
          .sort((a, b) => (a.sort_order || 1) - (b.sort_order || 1));

        // 找到拖拽项和目标项的位置
        const draggedIndex = categoryInstructions.findIndex(item => item.id === draggedItem.value!.id);
        const targetIndex = categoryInstructions.findIndex(item => item.id === targetInstruction.id);

        if (draggedIndex === -1 || targetIndex === -1) return;

        // 创建新的排序数组
        const newInstructions = [...categoryInstructions];
        const [removed] = newInstructions.splice(draggedIndex, 1);
        newInstructions.splice(targetIndex, 0, removed);

        // 更新排序号
        const updatePromises = newInstructions.map((instruction, index) => {
          // 只更新排序发生变化的指令
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
          success('指令排序已更新');
        } else {
          throw new Error('更新排序失败');
        }
      } catch (err) {
        error.value = err instanceof Error ? err.message : '排序更新失败';
      } finally {
        loading.value = false;
      }
    };

    // 获取分类名称
    const getCategoryName = (categoryId: string): string => {
      const category = categories.value.find(cat => cat.id === categoryId);
      return category ? category.name : '未分类';
    };

    // 获取脚本预览
    const getScriptPreview = (script: string): string => {
      if (!script) return '';
      return script.length > 100 ? script.substring(0, 100) + '...' : script;
    };

    return {
      handleDrop,
      getCategoryName,
      getScriptPreview
    };
  }
});
</script>

<style scoped>
.test-page {
  padding: 20px;
}
</style>