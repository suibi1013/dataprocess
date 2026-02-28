<template>
  <div class="config-panel">
    <div class="config-content">
      <!-- 页面和元素的配置页面 -->
      <div class="tab-content">
        <div id="slide-info-display">
          <p>幻灯片 {{ currentSlideIndex + 1 }} - 元素 {{ selectedElementIndex + 1 }}</p>
        </div>
        <el-select v-model="selectedElementDropdown" placeholder="请选择元素" style="width: 100%; margin-top: 10px;"
          @change="handleElementSelect">
          <el-option v-for="option in elementOptions" :key="option.value" :value="option.value" :label="option.label">
          </el-option>
        </el-select>

        <div class="config-section" v-if="selectedElementIndex >= 0" id="element-editor">
          <!-- Tab切换 -->
          <el-tabs v-model="currentTab" type="card">
            <el-tab-pane label="数据" name="data">
              <!-- 数据Tab内容 -->
              <div class="tab-content" id="data-tab-content">
                <!-- 数据源配置部分 -->
                <div class="config-item" id="data-source-section">
                  <label>数据源文件选择</label>
                  <el-cascader v-model="currentElementDataSourceConfig.data_source_path"
                    :options="cascaderOptions" :placeholder="'请选择数据源文件'" :loading="loading" @change="onCascaderChange"
                    separator="/" :props="{ expandTrigger: 'hover' }" popper-class="custom-cascader-popper" />
                </div>
                <div class="button-row">
                  <el-button type="primary" @click="openDataPreview"
                    :disabled="!currentElementDataSourceConfig.data_source_path">
                    选择数据区域
                  </el-button>
                </div>
                <div class="config-item">
                  <label>数据源信息</label>
                  <div class="data-source-info">
                    工作表：{{ currentElementDataSourceConfig.excel_sheet_name }},
                    单元格范围：{{ currentElementDataSourceConfig.excel_cell_range }}
                  </div>
                </div>
              </div>
            </el-tab-pane><el-tab-pane label="样式" name="style">
              <!-- 样式Tab内容 -->
              <div class="tab-content" id="style-tab-content">
                <div class="config-item">
                  <label>元素ID</label>
                  <el-input :value="currentElement?.id || ''" :disabled="true" />
                </div>
                <div class="config-item">
                  <label>元素类型</label>
                  <el-input :value="currentElement?.element_type_name || ''" :disabled="true" />
                </div>
                <div class="config-item">
                  <label>左边距 (px)</label>
                  <el-input-number :value="currentElement?.position?.left || 0"
                    @change="(value) => updateElementPosition('left', value)" :min="0" :precision="0" :step="1"
                    :disabled="true" />
                </div>
                <div class="config-item">
                  <label>顶边距 (px)</label>
                  <el-input-number :value="currentElement?.position?.top || 0"
                    @change="(value) => updateElementPosition('top', value)" :min="0" :precision="0" :step="1"
                    :disabled="true" />
                </div>
                <div class="config-item">
                  <label>宽度 (px)</label>
                  <el-input-number :value="currentElement?.position?.width || 0"
                    @change="(value) => updateElementPosition('width', value)" :min="0" :precision="0" :step="1"
                    :disabled="true" />
                </div>
                <div class="config-item">
                  <label>高度 (px)</label>
                  <el-input-number :value="currentElement?.position?.height || 0"
                    @change="(value) => updateElementPosition('height', value)" :min="0" :precision="0" :step="1"
                    :disabled="true" />
                </div>
                <div class="config-item">
                  <label>字体大小</label>
                  <el-input :value="currentElement?.style?.font_size || ''"
                    @change="(value) => updateElementStyle('font_size', value)" :disabled="true" />
                </div>
                <div class="config-item">
                  <label>字体颜色</label>
                  <el-color-picker :value="currentElement?.style?.color || '#000000'"
                    @change="(value) => updateElementStyle('color', value)" show-alpha :disabled="true" />
                </div>
                <div class="config-item">
                  <label>背景颜色</label>
                  <el-color-picker :value="currentElement?.style?.background_color || '#ffffff'"
                    @change="(value) => updateElementStyle('background_color', value)" show-alpha :disabled="true" />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import { ElCascader, ElSelect, ElOption, ElInput, ElInputNumber, ElColorPicker, ElButton, ElTabs, ElTabPane } from 'element-plus';
import type { Element, PPTConfig } from '@/services/TemplateEditorService';
import { httpClient } from '@/services/httpClient';

// 定义组件属性
interface Props {
  pptConfig: PPTConfig | null;
  currentSlideIndex: number;
  selectedElementIndex: number;
  dataSources?: any[];
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
const currentTab = ref<'style' | 'data'>('data');
const selectedElementDropdown = ref<string | number>(-1);
let currentElementDataSourceConfig = ref<any>({});

// 级联选择器相关数据
const dataSourcesOptions = ref<any[]>([]);
const loading = ref(false);

const cascaderOptions = computed(() => {
  return dataSourcesOptions.value;
});

// 从接口获取数据源选项
async function fetchDataSourceOptions() {
  loading.value = true;
  try {
    const response = await httpClient.get('/datasource/all-options');
    if (response.success && response.data) {
      dataSourcesOptions.value = response.data;
    }
  } catch (error) {
    console.error('获取数据源选项失败:', error);
    dataSourcesOptions.value = [];
  } finally {
    loading.value = false;
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchDataSourceOptions();
  // 初始化selectedElementDropdown
  selectedElementDropdown.value = props.selectedElementIndex;

  // 初始化数据源信息
  if (props.selectedElementIndex >= 0) {
    const element = currentSlideElements.value[props.selectedElementIndex];
    updateDataSourceInfo(element);
  }
});

// 监听selectedElementIndex变化，更新selectedElementDropdown和数据源信息
watch(() => props.selectedElementIndex, (newIndex) => {
  selectedElementDropdown.value = newIndex;
  // 更新数据源信息
  if (newIndex >= 0) {
    const element = currentSlideElements.value[newIndex];
    updateDataSourceInfo(element);
  }
  if (Object.keys(currentElementDataSourceConfig).length === 0) {
    currentElementDataSourceConfig.value = {
      data_source_path: '',
      excel_sheet_name: '',
      excel_cell_range: ''
    };
  }
});


// 计算属性：当前幻灯片的元素列表
const currentSlideElements = computed(() => {
  if (!props.pptConfig || !props.pptConfig.slides || !props.pptConfig.slides[props.currentSlideIndex]) {
    return [];
  }
  return props.pptConfig.slides[props.currentSlideIndex].elements || [];
});

// 计算属性：元素选项列表
const elementOptions = computed(() => {
  const options = [{ value: -1, label: '请选择元素' }];
  currentSlideElements.value.forEach((element, index) => {
    options.push({
      value: index,
      label: `${getElementDisplayName(element)}-${element.id}`
    });
  });
  return options;
});

// 计算属性：当前选中的元素
const currentElement = computed(() => {
  const elements = currentSlideElements.value;
  if (props.selectedElementIndex >= 0 && props.selectedElementIndex < elements.length) {
    return elements[props.selectedElementIndex];
  }
  return undefined;
});

function updateDataSourceInfo(element: Element) {
  if (props.pptConfig && props.pptConfig.slides && props.pptConfig.slides[props.currentSlideIndex] && element.element_name) {
    currentElementDataSourceConfig.value = props.pptConfig.slides[props.currentSlideIndex].data_source_config_info?.[`${element.element_name}`] || {};
  }
  if (Object.keys(currentElementDataSourceConfig).length === 0) {
    currentElementDataSourceConfig.value = {
      data_source_path: '',
      excel_sheet_name: '',
      excel_cell_range: ''
    };
  }
}

// 处理元素选择
function handleElementSelect(elementIndex: string | number) {
  const index = parseInt(elementIndex.toString());
  emit('element-select', index);
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

  return typeMap[element.element_type_name || ''] || '未知';
}

// 更新元素位置和大小
function updateElementPosition(property: 'left' | 'top' | 'width' | 'height', value: number) {
  if (!isNaN(value)) {
    emit('position-update', property, value);
  }
}

// 更新元素样式
function updateElementStyle(property: string, value: string) {
  emit('style-update', property, value);
}
// 处理级联选择器变化
function onCascaderChange(value: string[]) {
  if (value && value.length > 0) {
    // 最后一级是文件路径
    currentElementDataSourceConfig.value.data_source_path = value[value.length - 1];
    emit('data-source-change', currentElementDataSourceConfig.value.data_source_path);
  } else {
    currentElementDataSourceConfig.value.data_source_path = '';
    emit('data-source-change', '');
  }
}



// 打开数据预览
function openDataPreview() {
  emit('open-data-preview');
}
</script>

<style scoped>
/* 配置项样式 */
.config-item {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.config-item label {
  display: block;
  margin-bottom: 0;
  margin-right: 10px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
  min-width: 100px;
}

.config-item .el-input,
.config-item .el-input-number,
.config-item .el-color-picker,
.config-item .el-upload {
  flex: 1;
}

/* 文本域特殊处理 */
.config-item .el-input--textarea {
  flex: 1;
}

/* 图片上传特殊处理 */
#image-upload-section {
  flex-direction: column;
  align-items: flex-start;
}

#image-upload-section label {
  margin-bottom: 10px;
}

#image-upload-section .upload-container {
  display: flex;
  align-items: center;
  width: 100%;
}

#image-upload-section .el-upload {
  flex: 1;
  margin-bottom: 0;
  margin-right: 10px;
}

#image-upload-section .button-container {
  display: flex;
  align-items: center;
}

/* 数据源配置特殊处理 */
#data-source-section {
  width: 100%;
}

/* 按钮行样式 */
.button-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

/* 数据源信息特殊处理 */
.data-source-info {
  flex: 1;
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
}
</style>
