<template>
  <div v-show="visible" class="template-editor-modal-overlay" @click="handleClose">
    <div class="template-editor-modal-content" @click.stop>
      <div class="template-editor-modal-header">
        <h2>模板配置</h2>
        <button type="button" class="close-btn" @click="handleClose">&times;</button>
      </div>
      <div class="template-editor-modal-body">
        <div class="main-container">
          <!-- 预览面板 -->
          <preview-panel :ppt-config="pptConfig" :current-slide-index="currentSlideIndex"
            :selected-element-index="selectedElementIndex" @slide-click="previewSlideClick"
            @element-click="selectElement" />

          <!-- 配置编辑器面板 -->
          <config-panel :ppt-config="pptConfig" :current-slide-index="currentSlideIndex"
            :selected-element-index="selectedElementIndex" :data-sources="dataSources"
            @element-select="handleElementSelect" @position-update="updateElementPosition"
            @style-update="updateElementStyle" @reset-image="resetImage" @data-source-change="onDataSourceChange"
            @open-data-preview="openDataPreviewModal" />
        </div>

        <!-- 数据预览模态框 - 组件版 -->
        <DataPreviewModal v-model:visible="showDataPreviewModal"
          :file-path="currentElementDataSourceConfig.data_source_path" @cancel="closeDataPreviewModal"
          @confirm-selection="handleConfirmDataSelection" @confirm-sheet="onSheetChange" />

        <!-- 提示消息 -->
        <div class="toast" :class="{ show: showToast, error: toastType === 'error', success: toastType === 'success' }"
          ref="toast">
          {{ toastMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
// TypeScript类型声明
declare global {
  interface Window {
    Chart: any;
  }
  interface HTMLCanvasElement {
    chartInstance: any;
  }
}

import { Options, Vue } from 'vue-class-component'
import type { Template } from '@/types/template'
import type { DataSource } from '@/types/dataSource'
import { dataSourceService } from '@/services/dataSourceService'
import { TemplateEditorService } from '@/services/TemplateEditorService'
import type { PPTConfig, Element } from '@/services/TemplateEditorService'
import DataPreviewModal from '@/components/Common/DataPreviewModal.vue'
import PreviewPanel from '@/components/Template/PreviewPanel.vue'
import ConfigPanel from '@/components/Template/ConfigPanel.vue'
import type { DataSelection } from '@/types/dataExtraction'
import { httpClient } from '@/services/httpClient'
// 引入模板编辑器样式
import '@/styles/templateEditor.css'

// 初始化服务
const templateEditorService = new TemplateEditorService()
// 初始化交互服务
import { TemplateEditorInteractionService } from '@/services/TemplateEditorInteractionService'
const templateEditorInteractionService = new TemplateEditorInteractionService()

@Options({
  components: {
    // 导入子组件
    DataPreviewModal,
    PreviewPanel,
    ConfigPanel
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    templateId: {
      type: String,
      default: ''
    }
  },
  emits: ['close', 'update:visible'],
  watch: {
    visible: {
      handler: 'watchVisible',
      immediate: false
    }
  }
})
export default class TemplateEditor extends Vue {
  // Props
  templateId!: string
  visible!: boolean

  // 响应式数据
  pptConfig: PPTConfig | null = null
  template: Template | null = null
  currentSlideIndex: number = 0
  selectedElementIndex: number = -1
  selectedElementDropdown: string = '-1'
  currentTab: 'style' | 'data' = 'style'
  dataSources: DataSource[] = []
  currentElementDataSourceConfig: any = {};
  // 数据预览相关
  showDataPreviewModal: boolean = false
  previewSheetData: any = null
  currentSelectedSheet: string = ''
  availableSheets: string[] = []
  dataSourceSheetsData: Record<string, any> = {}
  isLoadingDataSource: boolean = false

  // Toast提示相关
  showToast: boolean = false
  toastMessage: string = ''
  toastType: 'success' | 'error' | 'info' = 'info'

  // 生命周期钩子
  mounted() {
    if (!this.templateId) {
      this.showToastMessage('未找到模板ID', 'error')
      return
    }
  }

  // 监听visible属性变化，当visible变为true时重新加载数据
  async watchVisible(newVal: boolean) {
    if (newVal && this.templateId) {
      try {
        // 先加载数据源列表
        await this.loadDataSources()
        // 再加载模板配置
        await this.loadTemplateConfig()
        // 加载Chart.js库并初始化图表
        this.loadChartJs();
      } catch (error) {
        console.error('初始化失败:', error)
        this.showToastMessage('初始化失败: ' + (error as Error).message, 'error')
      }
    }
  }

  // 关闭弹窗
  handleClose() {
    this.$emit('close')
    this.$emit('update:visible', false)
  }

  // 加载模板配置
  async loadTemplateConfig() {
    try {
      // 只从API获取配置
      const response = await templateEditorService.loadTemplateConfig(this.templateId)
      if (response.success && response.data) {
        this.pptConfig = response.data
      }

    } catch (error) {
      console.error('加载模板配置失败:', error)
      throw error
    }
  }

  // 加载数据源列表
  async loadDataSources() {
    try {
      // 使用dataSourceService获取数据源列表
      const response: any = await dataSourceService.getDataSources()
      if (response.success && response.data) {
        this.dataSources = response.data
      } else {
        // 如果API调用失败或返回的数据不符合预期，使用空数组
        this.dataSources = []
        this.showToastMessage('未获取到数据源列表', 'info')
      }
    } catch (error) {
      console.error('加载数据源失败:', error)
      this.showToastMessage('加载数据源失败', 'error')

      // 使用模拟数据作为后备
      this.dataSources = []
    }
  }

  // 格式化日期
  formatDate(dateString?: string): string {
    if (!dateString) return ''
    try {
      return new Date(dateString).toLocaleString()
    } catch (error) {
      return dateString
    }
  }

  // 幻灯片点击事件
  previewSlideClick(slideIndex: number) {
    this.currentSlideIndex = slideIndex
    this.selectedElementIndex = -1
    this.selectedElementDropdown = '-1'
  }

  // 元素点击事件
  selectElement(slideIndex: number, elementIndex: number) {
    this.currentSlideIndex = slideIndex
    this.selectedElementIndex = elementIndex
    this.selectedElementDropdown = elementIndex.toString()
    this.setCurrentElementDataSourceConfig()
  }

  // 处理元素选择
  handleElementSelect(elementIndex: number) {
    if (elementIndex >= 0) {
      this.selectedElementIndex = elementIndex
      this.setCurrentElementDataSourceConfig()
    } else {
      this.selectedElementIndex = -1
    }
  }

  // 获取当前幻灯片的元素列表
  getCurrentSlideElements(): Element[] {
    if (!this.pptConfig || !this.pptConfig.slides || !this.pptConfig.slides[this.currentSlideIndex]) {
      return []
    }

    return this.pptConfig.slides[this.currentSlideIndex].elements || []
  }

  // 获取当前选中的元素
  getCurrentElement(): Element | undefined {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      return elements[this.selectedElementIndex]
    }
    return undefined
  }
  setCurrentElementDataSourceConfig(): any {
    const currentElement = this.getCurrentElement()
    let data_source_config_info = this.pptConfig?.slides?.[this.currentSlideIndex]?.data_source_config_info || {};
    if (currentElement && currentElement.element_name) {
      if (!data_source_config_info) {
        data_source_config_info = {};
      }
      if (!data_source_config_info[currentElement.element_name]) {
        data_source_config_info[currentElement.element_name] = {
          element_name: currentElement.element_name,
          element_type: currentElement.element_type,
          element_type_name: currentElement.element_type_name,
          data_source_path: '',
          excel_sheet_name: '',
          excel_cell_range: ''
        };
      }
      this.currentElementDataSourceConfig = data_source_config_info[currentElement.element_name];
    }
  }
  // 更新元素位置和大小
  updateElementPosition(property: string, value: number) {
    const currentElement = this.getCurrentElement()
    if (currentElement) {
      // 使用类型断言解决索引访问问题
      (currentElement as any)[property] = value
      this.saveConfig()
    }
  }

  // 更新元素样式
  updateElementStyle(property: string, value: string) {
    const currentElement = this.getCurrentElement()
    if (currentElement) {
      // 使用类型断言解决索引访问问题
      (currentElement as any)[property] = value
      this.saveConfig()
    }
  }
  // 数据源变更事件
  onDataSourceChange(sourceFilePath: string) {
    const currentElement = this.getCurrentElement()
    if (!currentElement) {
      return;
    }
    this.setCurrentElementDataSourceConfig()
    // 更新数据源文件路径
    if (this.currentElementDataSourceConfig.data_source_path == sourceFilePath) {
      return;
    }
    this.currentElementDataSourceConfig.data_source_path = sourceFilePath;
    const data_source_config_info = this.pptConfig?.slides?.[this.currentSlideIndex]?.data_source_config_info || {};
    if (data_source_config_info) {
      // 更新当前元素的数据源配置
      if (currentElement.element_name) {
        data_source_config_info[currentElement.element_name] = this.currentElementDataSourceConfig;
      }
    }
    this.saveConfig()
  }

  // 打开数据预览模态框
  openDataPreviewModal() {
    if (!this.currentElementDataSourceConfig.data_source_path) {
      this.showToastMessage('请先选择数据源', 'error')
      return
    }

    this.showDataPreviewModal = true
  }

  // 关闭数据预览模态框
  closeDataPreviewModal() {
    this.showDataPreviewModal = false
  }

  // 加载数据源数据
  async loadDataSourceData(dataSourceId: string) {
    try {
      // 调用API获取数据源数据
      const response = await httpClient.get(`/datasource/${encodeURIComponent(dataSourceId)}/data`)

      if (response.success && response.data && response.data.data) {
        const allSheetsData = response.data.data
        this.availableSheets = Object.keys(allSheetsData)
        this.dataSourceSheetsData = allSheetsData

        if (this.availableSheets.length > 0) {
          this.currentSelectedSheet = this.availableSheets[0]
          this.updatePreviewSheetData(allSheetsData[this.currentSelectedSheet])
          this.showToastMessage(`找到 ${this.availableSheets.length} 个工作表`, 'success')
        } else {
          this.showToastMessage('未找到工作表或工作表为空', 'error')
        }
      } else {
        this.showToastMessage('加载数据源数据失败', 'error')
        console.error('加载数据源数据失败:', response)
      }
    } catch (error) {
      console.error('加载数据源数据异常:', error)
      this.showToastMessage('加载数据源数据异常', 'error')
    } finally {
      this.isLoadingDataSource = false
    }
  }

  // 更新预览数据
  updatePreviewSheetData(sheetData: any) {
    if (!sheetData || (!sheetData.columns && !sheetData.rows)) {
      this.previewSheetData = null
      return
    }

    // 确保数据格式正确
    this.previewSheetData = {
      columns: sheetData.columns || Object.keys(sheetData.rows[0] || {}),
      rows: sheetData.rows || []
    }
  }

  // 切换工作表
  onSheetChange(sheetName: string) {
    this.currentSelectedSheet = sheetName
  }

  // 处理数据选择确认
  handleConfirmDataSelection(selection: DataSelection) {
    const currentElement = this.getCurrentElement()
    if (!currentElement) {
      return;
    }
    this.setCurrentElementDataSourceConfig()
    this.currentElementDataSourceConfig.excel_sheet_name = this.currentSelectedSheet
    this.currentElementDataSourceConfig.excel_cell_range = `${selection.start_column}${selection.start_row}:${selection.end_column}${selection.end_row}`
    const data_source_config_info = this.pptConfig?.slides?.[this.currentSlideIndex]?.data_source_config_info || {};
    if (data_source_config_info) {
      // 更新当前元素的数据源配置
      if (currentElement.element_name) {
        data_source_config_info[currentElement.element_name] = this.currentElementDataSourceConfig;
      }
    }

    this.saveConfig()
    this.showToastMessage(`已选择区域: 行${selection.start_row}-${selection.end_row}, 列${selection.start_column}-${selection.end_column}`, 'success')
    this.closeDataPreviewModal()
  }


  // 保存配置
  async saveConfig() {
    if (this.pptConfig) {
      try {
        const data_source_config_info = this.pptConfig?.slides?.[this.currentSlideIndex]?.data_source_config_info || {};
        // 只保存到服务器
        await templateEditorService.saveTemplateConfig(this.templateId, this.currentSlideIndex, data_source_config_info)
      } catch (error) {
        console.error('保存配置到服务器失败:', error)
        // 服务器保存失败时，显示错误提示
        this.showToastMessage('配置保存失败，请检查网络连接', 'error')
      }
    }
  }

  // 显示Toast消息
  showToastMessage(message: string, type: 'success' | 'error' | 'info' = 'info') {
    this.toastMessage = message
    this.toastType = type
    this.showToast = true

    // 3秒后自动隐藏
    setTimeout(() => {
      this.showToast = false
    }, 3000)
  }

  // 重新初始化页面上所有的图表
  reinitializeCharts() {
    templateEditorInteractionService.reinitializeCharts(this.pptConfig);
  }

  // 滚动到OLE对象中的活动单元格逻辑已移至PreviewPanel组件
  scrollToActiveCellInOLEObjects() {
    // 该功能现在由PreviewPanel组件内部处理
  }

  // 动态加载Chart.js库
  async loadChartJs() {
    await templateEditorInteractionService.loadChartJs(
      this.pptConfig,
      (_pptConfig) => this.reinitializeCharts(),
      (message, type) => this.showToastMessage(message, type)
    );
  }
}

</script>