<template>
  <div class="config-panel">
    <div class="config-content">
      <!-- 页面和元素的配置页面 -->
      <div class="tab-content">
        <div id="slide-info-display" v-if="selectedElementIndex >= 0">
          <p>幻灯片 {{ currentSlideIndex + 1 }} - 元素 {{ selectedElementIndex + 1 }}</p>
        </div>
        <select 
          class="element-dropdown" 
          @change="handleElementSelect" 
          v-model="selectedElementDropdown"
        >
          <option value="-1">请选择元素</option>
          <option 
            v-for="(element, index) in currentSlideElements"
            :key="index"
            :value="index"
          >
            {{ getElementDisplayName(element) }}-{{ element.id }}
          </option>
        </select>
        
        <div class="config-section" v-if="selectedElementIndex >= 0" id="element-editor">
          <h4>✏️ 元素编辑</h4>
          
          <!-- Tab切换 -->
          <div class="config-tabs">
            <button 
              class="config-tab" 
              :class="{ active: currentTab === 'style' }"
              @click="switchTab('style')"
            >
              样式
            </button>
            <button 
              class="config-tab" 
              :class="{ active: currentTab === 'data' }"
              @click="switchTab('data')"
            >
              数据
            </button>
          </div>
          
          <!-- 样式Tab内容 -->
          <div class="tab-content" id="style-tab-content" v-if="currentTab === 'style'">
            <div class="config-item">
              <label>元素ID</label>
              <input type="text" :value="currentElement?.id || ''" readonly>
            </div>
            <div class="config-item">
              <label>元素类型</label>
              <input type="text" :value="currentElement?.element_type_name || ''" readonly>
            </div>
            <div class="config-item">
              <label>左边距 (px)</label>
              <input 
                type="number" 
                :value="currentElement?.position?.left || 0"
                @change="updateElementPosition('left', $event)"
              >
            </div>
            <div class="config-item">
              <label>顶边距 (px)</label>
              <input 
                type="number" 
                :value="currentElement?.position?.top || 0"
                @change="updateElementPosition('top', $event)"
              >
            </div>
            <div class="config-item">
              <label>宽度 (px)</label>
              <input 
                type="number" 
                :value="currentElement?.position?.width || 0"
                @change="updateElementPosition('width', $event)"
              >
            </div>
            <div class="config-item">
              <label>高度 (px)</label>
              <input 
                type="number" 
                :value="currentElement?.position?.height || 0"
                @change="updateElementPosition('height', $event)"
              >
            </div>
            <div class="config-item">
              <label>字体大小</label>
              <input 
                type="text" 
                :value="currentElement?.style?.font_size || ''"
                @change="updateElementStyle('font_size', $event)"
              >
            </div>
            <div class="config-item">
              <label>字体颜色</label>
              <input 
                type="color" 
                :value="currentElement?.style?.color || '#000000'"
                @change="updateElementStyle('color', $event)"
              >
            </div>
            <div class="config-item">
              <label>背景颜色</label>
              <input 
                type="color" 
                :value="currentElement?.style?.background_color || '#ffffff'"
                @change="updateElementStyle('background_color', $event)"
              >
            </div>
          </div>
          
          <!-- 数据Tab内容 -->
          <div class="tab-content" id="data-tab-content" v-if="currentTab === 'data'">
            <div class="config-item" v-if="currentElement?.element_type_name === 'text'">
              <label>文本内容</label>
              <textarea 
                :value="currentElement?.data?.text_content || ''"
                @change="updateElementContent($event)"
              ></textarea>
            </div>
            <div 
              class="config-item" 
              id="image-upload-section" 
              v-if="currentElement?.element_type_name === 'image'"
            >
              <label>图片上传</label>
              <input type="file" accept="image/*" @change="handleImageUpload">
              <div 
                class="image-preview" 
                v-if="currentElement?.data?.text_content"
                style="margin-top: 10px; max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;"
              >
                <img 
                  :src="currentElement?.data?.text_content || ''" 
                  style="width: 100%; height: 100%; object-fit: contain;" 
                  alt="预览"
                >
              </div>
              <button 
                type="button" 
                class="btn btn-secondary"
                @click="resetImage"
                style="margin-top: 5px;"
              >
                重置图片
              </button>
            </div>
            <!-- 数据源配置部分 -->
            <div class="config-item" id="data-source-section">
              <label>数据源选择</label>
              <select 
                v-model="selectedDataSource"
                @change="onDataSourceChange"
              >
                <option value="">请选择数据源</option>
                <option 
                  v-for="source in dataSources"
                  :key="source.id"
                  :value="source.id"
                >
                  {{ source.name }}
                </option>
              </select>
              <button 
                type="button" 
                class="btn btn-primary"
                @click="openDataPreview"
                style="margin-top: 5px;"
                :disabled="!selectedDataSource"
              >
                选择数据区域
              </button>
              
              <label>数据源信息</label>
              <div class="data-source-info">
                工作表：{{ currentDataSourceInfo.sheet || '--' }}, 
                单元格范围：{{ currentDataSourceInfo.range || '--' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Element, PPTConfig } from '@/services/TemplateEditorService';
import type { DataSource } from '@/types/dataSource';

// 定义组件属性
interface Props {
  pptConfig: PPTConfig | null;
  currentSlideIndex: number;
  selectedElementIndex: number;
  dataSources: DataSource[];
}

const props = defineProps<Props>();

// 定义事件
const emit = defineEmits<{
  'element-select': [_elementIndex: number];
  'position-update': [_property: string, _value: number];
  'style-update': [_property: string, _value: string];
  'content-update': [_value: string];
  'image-upload': [_file: File];
  'reset-image': [];
  'data-source-change': [_sourceId: string];
  'open-data-preview': [];
}>();

// 响应式数据
const currentTab = ref<'style' | 'data'>('style');
const selectedElementDropdown = ref('-1');
const selectedDataSource = ref('');
const currentDataSourceInfo = ref({
  sheet: '',
  range: ''
});

// 计算属性：当前幻灯片的元素列表
const currentSlideElements = computed(() => {
  if (!props.pptConfig || !props.pptConfig.slides || !props.pptConfig.slides[props.currentSlideIndex]) {
    return [];
  }
  return props.pptConfig.slides[props.currentSlideIndex].elements || [];
});

// 计算属性：当前选中的元素
const currentElement = computed(() => {
  const elements = currentSlideElements.value;
  if (props.selectedElementIndex >= 0 && props.selectedElementIndex < elements.length) {
    return elements[props.selectedElementIndex];
  }
  return undefined;
});

// 切换标签页
function switchTab(tab: 'style' | 'data') {
  currentTab.value = tab;
}

// 处理元素选择
function handleElementSelect(event: Event) {
  const selectElement = event.target as HTMLSelectElement;
  const elementIndex = parseInt(selectElement.value);
  emit('element-select', elementIndex);
}

// 获取元素显示名称
function getElementDisplayName(element: Element): string {
  const typeMap: Record<string, string> = {
    'text': '文本',
    'image': '图片',
    'chart': '图表',
    'table': '表格',
    'msoTextBox': '文本框',
    'msoAutoShape': '形状',
    'msoTable': '表格',
    'msoEmbeddedOLEObject': 'OLE对象',
    'msoChart': '图表',
    'msoPicture': '图片',
    'msoLine': '线条'
  };
  
  // 优先使用element_type_name，如果存在的话
  if (element.element_type_name) {
    return typeMap[element.element_type_name] || element.element_type_name;
  }
  
  return typeMap[element.type || ''] || '未知';
}

// 更新元素位置和大小
function updateElementPosition(property: 'left' | 'top' | 'width' | 'height', event: Event) {
  const inputElement = event.target as HTMLInputElement;
  const value = parseInt(inputElement.value);
  
  if (!isNaN(value)) {
    emit('position-update', property, value);
  }
}

// 更新元素样式
function updateElementStyle(property: string, event: Event) {
  const inputElement = event.target as HTMLInputElement;
  const value = inputElement.value;
  emit('style-update', property, value);
}

// 更新元素内容
function updateElementContent(event: Event) {
  const textareaElement = event.target as HTMLTextAreaElement;
  const value = textareaElement.value;
  emit('content-update', value);
}

// 处理图片上传
function handleImageUpload(event: Event) {
  const inputElement = event.target as HTMLInputElement;
  const file = inputElement.files?.[0];
  
  if (file) {
    emit('image-upload', file);
  }
}

// 重置图片
function resetImage() {
  emit('reset-image');
}

// 数据源变更
function onDataSourceChange() {
  emit('data-source-change', selectedDataSource.value);
}

// 打开数据预览
function openDataPreview() {
  emit('open-data-preview');
}
</script>

<style scoped>
/* 配置面板样式 */
.config-panel {
  width: 40%;
  height: 100%;
  background-color: #f9f9f9;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.config-content {
  padding: 20px;
  overflow: auto;
  flex: 1;
}

/* 配置部分样式 */
.config-section {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
}

.config-section h4 {
  margin: 0 0 20px 0;
  font-size: 16px;
  color: #333;
}

/* 标签切换样式 */
.config-tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.config-tab {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.config-tab:hover {
  color: #007bff;
}

.config-tab.active {
  color: #007bff;
  border-bottom-color: #007bff;
  font-weight: 500;
}

/* 配置项样式 */
.config-item {
  margin-bottom: 20px;
}

.config-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.config-item input[type="text"],
.config-item input[type="number"],
.config-item textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.config-item textarea {
  min-height: 100px;
  resize: vertical;
}

.config-item input[type="color"] {
  width: 100%;
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

/* 元素下拉选择样式 */
.element-dropdown {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 20px;
}

/* 数据源信息样式 */
.data-source-info {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .config-panel {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .config-panel {
    width: 100%;
    height: auto;
  }
}
</style>