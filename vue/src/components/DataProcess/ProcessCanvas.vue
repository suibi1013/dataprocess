<template>
  <div class="canvas-panel">
    <!-- 画布顶部工具栏 -->
    <div class="canvas-toolbar">
      <div class="toolbar-group">
        <button class="toolbar-btn" @click="zoomIn" title="放大">
          <el-icon>
            <ZoomIn />
          </el-icon>
        </button>
        <button class="toolbar-btn" @click="zoomOut" title="缩小">
          <el-icon>
            <ZoomOut />
          </el-icon>
        </button>
        <button class="toolbar-btn" @click="resetZoom" title="重置缩放">
          <el-icon>
            <Refresh />
          </el-icon>
        </button>
      </div>
      <div class="toolbar-group">
        <button class="toolbar-btn" @click="handleDeleteNode" :disabled="!props.selectedNode" title="删除节点">
          <el-icon>
            <Remove />
          </el-icon>
        </button>
        <button class="toolbar-btn" @click="handleDeleteEdge" :disabled="!props.selectedEdge" title="删除连线">
          <el-icon>
            <Connection />
          </el-icon>
        </button>
        <button class="toolbar-btn" @click="clearCanvas" title="清空画布">
          <el-icon>
            <Delete />
          </el-icon>
        </button>
        <button class="toolbar-btn" @click="toggleNodeTooltips" :class="{ active: showNodeTooltips }" title="显示/隐藏节点提示框">
          <el-icon><ChatLineSquare /></el-icon>
        </button>
      </div>
    </div>

    <div id="data-process-canvas-container"  class="canvas-container">
      <div id="data-process-canvas" class="data-process-canvas"></div>
      <div v-if="!canvasInitialized" class="canvas-placeholder">
        <i class="el-icon-document-copy"></i>
        <p>从左侧拖拽指令到此处开始构建流程</p>
      </div>
    </div>
  </div>
  
  <!-- 节点描述信息编辑模态框 -->
  <el-dialog
    v-model="nodeDescriptionEditor.visible"
    title="编辑节点描述信息"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
  >
    <el-form label-position="top">
      <el-form-item label="节点名称">
        <el-input v-model="nodeNameDisplay" disabled />
      </el-form-item>
      <el-form-item label="节点ID">
        <el-input v-model="nodeIdDisplay" disabled />
      </el-form-item>
      <el-form-item label="描述信息">
        <el-input
          v-model="nodeDescriptionEditor.description"
          type="textarea"
          :rows="6"
          placeholder="请输入节点描述信息"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="cancelNodeDescription">取消</el-button>
        <el-button type="primary" @click="saveNodeDescription">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElIcon, ElDialog, ElForm, ElFormItem, ElInput, ElButton } from 'element-plus';
import { onMounted, watch, computed ,onUnmounted} from 'vue';
import { ZoomIn, ZoomOut, Refresh, Delete, Remove, Connection} from '@element-plus/icons-vue';
import { useDataProcess } from '@/composables/useDataProcess';

// Props
interface Props {
  canvasInitialized: boolean;
  selectedNode: any;
  selectedEdge: any;
  paramsPanel: any;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'node-selected': [node: any]
  'edge-selected': [edge: any]
}>();

// 使用数据处理组合式函数获取canvasGraph和相关方法（单例模式）
const { 
  canvasGraph, 
  deleteSelectedNode, 
  deleteSelectedEdge, 
  clearCanvas, 
  nodeDescriptionEditor,
  saveNodeDescription,
  cancelNodeDescription,
  showNodeTooltips,
  toggleNodeTooltips,
  resizeCanvas
} = useDataProcess();

// 计算属性：节点名称显示（避免在v-model中使用可选链）
const nodeNameDisplay = computed(() => {
  if (!nodeDescriptionEditor.node) return '';
  const nodeData = nodeDescriptionEditor.node.getData();
  return nodeData?.label || '';
});

// 计算属性：节点ID显示
const nodeIdDisplay = computed(() => {
  if (!nodeDescriptionEditor.node) return '';
  // 从节点实例获取ID
  return nodeDescriptionEditor.node.id || '';
});

// 监听画布事件
const setupCanvasEventListeners = () => {
  if (!canvasGraph.value) return;

  // 添加节点点击事件监听
  canvasGraph.value.on('node:click', (event: any) => {
    const node = event.node;
    if (node && node !== props.selectedNode) {
      // 通过emit事件通知父组件节点被选中
      emit('node-selected', node);
    }
  });

  // 监听边点击事件
  canvasGraph.value.on('edge:click', (event: any) => {
    const edge = event.edge;
    if (edge && edge !== props.selectedEdge) {
      // 发射边选中事件，通知父组件
      emit('edge-selected', edge);
    }
  });
};

// 添加窗口大小变化事件监听器，处理浏览器窗口大小变化
let resizeObserver: ResizeObserver | null = null;
// 组件挂载时设置事件监听器
onMounted(() => {
  setupCanvasEventListeners(); 
  
  // 添加ResizeObserver监听画布容器大小变化
  // const canvasContainer = document.getElementById('data-process-canvas');
  const canvasContainer = document.getElementById('data-process-canvas-container');
  console.log('canvasContainer:', canvasContainer);
  if (canvasContainer) {
    resizeObserver = new ResizeObserver(() => {
      resizeCanvas();
    });
    resizeObserver.observe(canvasContainer);
  }
});
onUnmounted(() => {
  // 组件卸载时清理
  try {    
    // 移除ResizeObserver
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
  } catch (error) {
    console.error('清理资源失败:', error);
  }
});
// 使用watch监听canvasGraph变化，确保事件监听器被正确设置
watch(() => canvasGraph.value, (newGraph) => {
  if (newGraph) {
    setupCanvasEventListeners();
  }
}, { immediate: true });

// 监听画布初始化状态变化，当画布初始化完成后设置事件监听器
watch(() => props.canvasInitialized, (initialized) => {
  if (initialized && canvasGraph.value) {
    setupCanvasEventListeners();
  }
});

// 处理删除节点
const handleDeleteNode = () => {
  if (deleteSelectedNode && props.selectedNode) {
    // 显示确认对话框
    if (window.confirm('确定要删除当前选中的节点吗？')) {
      // 调用组合式函数中的方法删除节点
      deleteSelectedNode();
    }
  }
};

// 处理删除连线
const handleDeleteEdge = () => {
  if (deleteSelectedEdge && props.selectedEdge) {
    // 显示确认对话框
    if (window.confirm('确定要删除当前选中的连线吗？')) {
      // 调用组合式函数中的方法删除连线
      deleteSelectedEdge();
    }
  }
};

// 放大
const zoomIn = () => {
  if (canvasGraph.value) {
    const currentScale = canvasGraph.value.zoom();
    canvasGraph.value.zoomTo(currentScale + 0.1);
  }
};

// 缩小
const zoomOut = () => {
  if (canvasGraph.value) {
    const currentScale = canvasGraph.value.zoom();
    canvasGraph.value.zoomTo(currentScale - 0.1);
  }
};

// 重置缩放
const resetZoom = () => {
  if (canvasGraph.value) {
    canvasGraph.value.zoomTo(1);
    canvasGraph.value.centerContent();
  }
};
</script>

<style scoped>
/* 中间画布区域 */
.canvas-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  position: relative;
  min-width: 400px;
}

/* 画布顶部工具栏 */
.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  z-index: 100;
}

.toolbar-group {
  display: flex;
  gap: 4px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  color: #595959;
  transition: all 0.2s ease;
  font-size: 16px;
}

.toolbar-btn:hover {
  background: #f0f8ff;
  border-color: #91d5ff;
  color: #1890ff;
}

.toolbar-btn.active {
  background: #e6f7ff;
  border-color: #1890ff;
  color: #1890ff;
}

.btn-text {
  margin-left: 4px;
  font-size: 12px;
}

.toolbar-btn:active {
  background: #e6f7ff;
}

.toolbar-btn i {
  font-size: 16px;
}

/* 拖拽悬停效果 */
.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 拖拽悬停效果 */
.canvas-container.drag-over {
  background-color: rgba(24, 144, 255, 0.1);
  border: 2px dashed #1890ff;
}

.canvas-container.drag-over::after {
  content: '释放以添加指令节点';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(24, 144, 255, 0.9);
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
}

.data-process-canvas {
  width: 100%;
  height: 100%;
  background: #f9f9f9;
  background-image:
    linear-gradient(rgba(0, 0, 0, .1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, .1) 1px, transparent 1px);
  background-size: 20px 20px;
}

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #8c8c8c;
  pointer-events: none;
}

.canvas-placeholder i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.canvas-placeholder p {
  margin: 0;
  font-size: 14px;
}
</style>