<template>
  <div v-if="visible" class="template-editor-modal-overlay" @click="handleClose">
    <div class="template-editor-modal-content" @click.stop>
      <div class="template-editor-modal-header">
        <h2>模板配置</h2>
        <button type="button" class="close-btn" @click="handleClose">&times;</button>
      </div>
      <div class="template-editor-modal-body">
        <div class="main-container"> 
          <!-- 预览面板 -->
          <preview-panel
            :ppt-config="pptConfig"
            :current-slide-index="currentSlideIndex"
            :selected-element-index="selectedElementIndex"
            @slide-click="previewSlideClick"
            @element-click="selectElement"
          />
          
          <!-- 配置编辑器面板 -->
          <config-panel
            :ppt-config="pptConfig"
            :current-slide-index="currentSlideIndex"
            :selected-element-index="selectedElementIndex"
            :data-sources="dataSources"
            @element-select="handleElementSelect"
            @position-update="updateElementPosition"
            @style-update="updateElementStyle"
            @content-update="updateElementContent"
            @image-upload="handleImageUpload"
            @reset-image="resetImage"
            @data-source-change="onDataSourceChange"
            @open-data-preview="openDataPreviewModal"
          />
        </div>
        
        <!-- 数据预览模态框 - 组件版 -->
        <DataPreviewModal
          :visible="showDataPreviewModal"
          :sheet-data="previewSheetData"
          :available-sheets="availableSheets"
          :current-sheet="currentSelectedSheet"
          :is-loading="isLoadingDataSource"
          @cancel="closeDataPreviewModal"
          @sheet-change="onSheetChange"
          @confirm-selection="handleConfirmDataSelection"
        />
        
        <!-- 数据预览窗口 - 旧版，仅在新组件不可用时显示 -->
        <div 
          class="modal" 
          id="data-preview-modal" 
          v-if="showDataPreviewModal && !previewSheetData"
          @click="closeDataPreviewModal"
        >
          <div class="modal-content" @click.stop>
            <div class="modal-header">
              <h2>Excel数据预览</h2>
              <button type="button" class="close-btn" @click="closeDataPreviewModal">&times;</button>
            </div>
            <div class="modal-body">
              <div class="preview-section">
                <!-- Excel风格工作表标签 -->
                <div class="sheet-tabs-container">
                  <div id="sheet-tabs" class="sheet-tabs">
                    <div 
                      v-for="(sheet, index) in excelSheets"
                      :key="index"
                      class="sheet-tab"
                      :class="{ active: currentSheetIndex === index }"
                      @click="selectSheet(index)"
                    >
                      {{ sheet }}
                    </div>
                  </div>
                  <div id="add-sheet-tab" class="add-sheet-tab">+</div>
                </div>
                <div class="data-preview-container">
                  <div class="table-preview-wrapper" style="overflow: auto; max-height: 400px; border: 1px solid #ddd;">
                    <table id="data-preview-table" class="preview-table">
                      <thead>
                        <tr>
                          <th></th>
                          <th v-for="col in currentSheetData.columns" :key="col">{{ col }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, rowIndex) in currentSheetData.data" :key="rowIndex">
                          <td>{{ rowIndex + 1 }}</td>
                          <td 
                            v-for="(cell, colIndex) in row"
                            :key="colIndex"
                            :class="{
                              'selected': isCellInSelectedRange(rowIndex + 1, colIndex + 1)
                            }"
                            @click="selectCell(rowIndex + 1, colIndex + 1)"
                          >
                            {{ cell || '' }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                <div class="selection-info">
                  <p>已选择: <span>{{ selectedRange || '无' }}</span></p>
                  <button 
                    type="button" 
                    class="btn btn-success"
                    @click="confirmDataSourceSelection"
                    :disabled="!selectedRange"
                  >
                    确认选择
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 提示消息 -->
        <div class="toast" :class="{ show: showToast, error: toastType === 'error', success: toastType === 'success' }" ref="toast">
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
import DataPreviewModal from '@/components/DataPreviewModal.vue'
import PreviewPanel from '@/components/Template/PreviewPanel.vue'
import ConfigPanel from '@/components/Template/ConfigPanel.vue'
import type { SheetData, DataSelection } from '@/types/dataExtraction'
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
  selectedDataSource: string = ''
  currentDataSourceInfo: {
    sheet: string
    range: string
  } = { sheet: '', range: '' }
  
  // 数据预览相关
  showDataPreviewModal: boolean = false
  previewSheetData: any = null
  currentSelectedSheet: string = ''
  availableSheets: string[] = []
  dataSourceSheetsData: Record<string, any> = {}
  isLoadingDataSource: boolean = false
  excelSheets: string[] = []
  currentSheetIndex: number = 0
  currentSheetData: SheetData = { columns: [], rows: [] }
  selectedRange: string = ''
  selectionStart: { row: number, col: number } | null = null
  selectionEnd: { row: number, col: number } | null = null
  
  // Toast提示相关
  showToast: boolean = false
  toastMessage: string = ''
  toastType: 'success' | 'error' | 'info' = 'info'
  
  // 生命周期钩子
  async mounted() {
    if (!this.templateId) {
      this.showToastMessage('未找到模板ID', 'error')
      return
    }
    
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
      // 尝试从API获取配置
      const response = await templateEditorService.loadTemplateConfig(this.templateId)
      
      if (response.success && response.data) {
        this.pptConfig = response.data
        // 保存到sessionStorage以便快速访问
        sessionStorage.setItem('pptConfig', JSON.stringify(this.pptConfig))
        
        // 从配置中获取选中的数据源信息
        if (this.selectedElementIndex >= 0) {
          const current_element = this.getCurrentElement()
          const data_source_config=current_element?.data?.data_source_config
          if (data_source_config) {
            // 查找与data_source_name匹配的数据源ID
            const matchedDataSource = this.dataSources.find(source => source.name === data_source_config.data_source_name);
            this.selectedDataSource = matchedDataSource ? matchedDataSource.id : '';
            this.currentDataSourceInfo = {
              sheet: data_source_config.excel_sheet_name || '',
              range: data_source_config.excel_cell_range || ''
            }
          }
        }
      // 如果API调用失败，尝试从本地存储获取
        const configStr = sessionStorage.getItem('pptConfig')
        if (configStr) {
          this.pptConfig = JSON.parse(configStr)
        }
      }
      
      // 保存模板信息
      sessionStorage.setItem('templateId', this.templateId)
      sessionStorage.setItem('pptConfigMode', 'edit')
      sessionStorage.setItem('pptFilename', this.templateId)
      
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
      if (response.success && response.data_sources) {
        this.dataSources = response.data_sources
      // 如果API调用失败
        this.dataSources = []
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
  }
  
  // 处理元素选择
  handleElementSelect(elementIndex: number) {
    if (elementIndex >= 0) {
      this.selectedElementIndex = elementIndex
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
  
  // 更新元素位置和大小
  updateElementPosition(property: string, value: number) {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      // 使用类型断言解决索引访问问题
      (elements[this.selectedElementIndex] as any)[property] = value
      this.saveConfig()
    }
  }
  
  // 更新元素样式
  updateElementStyle(property: string, value: string) {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      // 使用类型断言解决索引访问问题
      (elements[this.selectedElementIndex] as any)[property] = value
      this.saveConfig()
    }
  }
  
  // 更新元素内容
  updateElementContent(value: string) {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      elements[this.selectedElementIndex].content = value
      this.saveConfig()
      
      // 内容更新后重新初始化图表
      this.handleElementDataUpdate()
    }
  }
  
  // 处理图片上传
  handleImageUpload(event: Event) {
    const inputElement = event.target as HTMLInputElement
    const file = inputElement.files?.[0]
    
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (e) => {
      const elements = this.getCurrentSlideElements()
      if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
        elements[this.selectedElementIndex].content = e.target?.result as string
        this.saveConfig()
        this.showToastMessage('图片上传成功', 'success')
      }
    }
    reader.readAsDataURL(file)
  }
  
  // 重置图片
  resetImage() {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      elements[this.selectedElementIndex].content = ''
      this.saveConfig()
      this.showToastMessage('图片已重置', 'info')
    }
  }
  
  // 数据源变更事件
  onDataSourceChange() {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      // 查找选中的数据源对象以获取其名称
      const selectedDataSourceObj = this.dataSources.find(source => source.id === this.selectedDataSource);
      const element = elements[this.selectedElementIndex];
      if (element) {
        if (!element.data) {
          element.data = {};
        }
        if (!element.data.data_source_config) {
          element.data.data_source_config = {
            type: '', // 默认值根据实际需求填写，比如 'excel'
            data_source_name: '',
            excel_sheet_name: ''
          };
        }
        // 更新数据源名称
        element.data.data_source_config.data_source_name = selectedDataSourceObj ? selectedDataSourceObj.name : '';
      }
      this.saveConfig()
    }
  }
  
  // 打开数据预览模态框
  openDataPreviewModal() {
    if (!this.selectedDataSource) {
      this.showToastMessage('请先选择数据源', 'error')
      return
    }
    
    this.isLoadingDataSource = true
    this.showDataPreviewModal = true
    
    // 加载数据源数据
    this.loadDataSourceData(this.selectedDataSource)
  }
  
  // 关闭数据预览模态框
  closeDataPreviewModal() {
    this.showDataPreviewModal = false
    this.previewSheetData = null
    this.availableSheets = []
    this.currentSelectedSheet = ''
    this.dataSourceSheetsData = {}
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
        // 使用模拟数据
        this.useMockData()
      }
    } catch (error) {
      console.error('加载数据源数据异常:', error)
      this.showToastMessage('加载数据源数据异常', 'error')
      // 使用模拟数据
      this.useMockData()
    } finally {
      this.isLoadingDataSource = false
    }
  }
  
  // 使用模拟数据
  useMockData() {
    this.availableSheets = ['Sheet1', 'Sheet2', 'Sheet3']
    this.currentSelectedSheet = 'Sheet1'
    this.dataSourceSheetsData = {
      'Sheet1': {
        columns: ['A', 'B', 'C', 'D', 'E'],
        rows: [
          { A: '产品A', B: 100, C: 120, D: 150, E: 180 },
          { A: '产品B', B: 80, C: 90, D: 110, E: 130 },
          { A: '产品C', B: 150, C: 160, D: 170, E: 190 },
          { A: '产品D', B: 70, C: 75, D: 80, E: 90 },
          { A: '产品E', B: 200, C: 220, D: 240, E: 260 }
        ]
      }
    }
    
    this.updatePreviewSheetData(this.dataSourceSheetsData['Sheet1'])
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
  
  // 选择工作表
  selectSheet(index: number) {
    this.currentSheetIndex = index
    
    // 模拟不同工作表的数据
    if (index === 0) {
      this.currentSheetData = {
        columns: ['A', 'B', 'C', 'D', 'E'],
        rows: [
          ['产品A', 100, 120, 150, 180],
          ['产品B', 80, 90, 110, 130],
          ['产品C', 150, 160, 170, 190],
          ['产品D', 70, 75, 80, 90],
          ['产品E', 200, 220, 240, 260]
        ]
      }
    } else if (index === 1) {
      this.currentSheetData = {
        columns: ['A', 'B', 'C'],
        rows: [
          ['一月', 5000, 4500],
          ['二月', 5200, 4800],
          ['三月', 5500, 5100],
          ['四月', 6000, 5600]
        ]
      }
    } else {
      this.currentSheetData = {
        columns: ['A', 'B', 'C', 'D'],
        rows: [
          ['华东区', 1200, 1300, 1400],
          ['华南区', 900, 950, 1000],
          ['华北区', 1500, 1600, 1700],
          ['西区', 800, 850, 900]
        ]
      }
    }
    
    this.selectedRange = ''
    this.selectionStart = null
    this.selectionEnd = null
  }
  
  // 选择单元格
  selectCell(row: number, col: number) {
    if (!this.selectionStart) {
      this.selectionStart = { row, col }
      this.selectionEnd = { row, col }
    } else {
      this.selectionEnd = { row, col }
    }
    
    this.updateSelectedRange()
  }
  
  // 更新选中范围
  updateSelectedRange() {
    if (!this.selectionStart || !this.selectionEnd) {
      this.selectedRange = ''
      return
    }
    
    const start_row = Math.min(this.selectionStart.row, this.selectionEnd.row)
    const end_row = Math.max(this.selectionStart.row, this.selectionEnd.row)
    const startCol = Math.min(this.selectionStart.col, this.selectionEnd.col)
    const endCol = Math.max(this.selectionStart.col, this.selectionEnd.col)
    
    const startColStr = this.numberToColumn(startCol)
    const endColStr = this.numberToColumn(endCol)
    
    if (start_row === end_row && startCol === endCol) {
      this.selectedRange = `${startColStr}${start_row}`
    } else {
      this.selectedRange = `${startColStr}${start_row}:${endColStr}${end_row}`
    }
  }
  
  // 数字转列字母 (1 -> A, 2 -> B, ...)
  numberToColumn(num: number): string {
    let column = ''
    let temp = num
    
    while (temp > 0) {
      const modulo = (temp - 1) % 26
      column = String.fromCharCode(65 + modulo) + column
      temp = Math.floor((temp - modulo) / 26)
    }
    
    return column
  }
  
  // 检查单元格是否在选中范围内
  isCellInSelectedRange(row: number, col: number): boolean {
    if (!this.selectionStart || !this.selectionEnd) {
      return false
    }
    
    const minRow = Math.min(this.selectionStart.row, this.selectionEnd.row)
    const maxRow = Math.max(this.selectionStart.row, this.selectionEnd.row)
    const minCol = Math.min(this.selectionStart.col, this.selectionEnd.col)
    const maxCol = Math.max(this.selectionStart.col, this.selectionEnd.col)
    
    return row >= minRow && row <= maxRow && col >= minCol && col <= maxCol
  }
  
  // 切换工作表
  onSheetChange(sheetName: string) {
    if (sheetName && this.dataSourceSheetsData && this.dataSourceSheetsData[sheetName]) {
      this.currentSelectedSheet = sheetName
      this.updatePreviewSheetData(this.dataSourceSheetsData[sheetName])
    }
  }
  
  // 处理数据选择确认
  handleConfirmDataSelection(selection: DataSelection) {
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      const element = elements[this.selectedElementIndex]
      
      if (!element.data) {
        element.data = {}
      }
      
      // 更新数据源配置
      if (!element.data.data_source_config) {
        element.data.data_source_config = {
          type: 'excel',
          data_source_name: '',
          excel_sheet_name: '',
          excel_cell_range: ''
        }
      }
      
      // 设置选择的工作表和范围
      element.data.data_source_config.excel_sheet_name = this.currentSelectedSheet
      element.data.data_source_config.excel_cell_range = `${selection.start_column}${selection.start_row}:${selection.end_column}${selection.end_row}`
      
      // 查找选中的数据源对象以获取其名称
      const selectedDataSourceObj = this.dataSources.find(source => source.id === this.selectedDataSource)
      if (selectedDataSourceObj) {
        element.data.data_source_config.data_source_name = selectedDataSourceObj.name
      }
      
      // 更新显示信息
      this.currentDataSourceInfo = {
        sheet: this.currentSelectedSheet,
        range: element.data.data_source_config.excel_cell_range
      }
      
      // 获取实际数据并更新元素
      this.replaceElementDataWithSelectedRange(selection).then(() => {
        this.saveConfig()
        this.showToastMessage(`已选择区域: 行${selection.start_row}-${selection.end_row}, 列${selection.start_column}-${selection.end_column}`, 'success')
        this.closeDataPreviewModal()
        
        // 数据源更新后重新初始化图表
        this.handleElementDataUpdate()
      }).catch(error => {
        console.error('获取和更新数据失败:', error)
        this.showToastMessage('数据更新失败: ' + (error as Error).message, 'error')
      })
    }
  }
  
  // 替换元素数据为选中的数据区域
  async replaceElementDataWithSelectedRange(selection: DataSelection) {
    await templateEditorInteractionService.replaceElementDataWithSelectedRange(
      selection,
      this.selectedDataSource,
      this.currentSelectedSheet,
      () => this.getCurrentSlideElements(),
      this.selectedElementIndex,
      (message, type) => this.showToastMessage(message, type)
    )
  }
  
  // 将数据转换为图表格式
  convertDataToChartFormat(newData: any, existingChartData: any): any {
    return templateEditorInteractionService.convertDataToChartFormat(newData, existingChartData)
  }
  
  // 确认数据源选择
  confirmDataSourceSelection() {
    if (!this.selectedRange) return
    
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      const element = elements[this.selectedElementIndex];
      if (!element) return;
      // 查找选中的数据源对象以获取其名称
      const selectedDataSourceObj = this.dataSources.find(source => source.id === this.selectedDataSource);
      // 确保元素有data对象
      if (!element.data) {
        element.data = {};
      }
      // 设置数据源配置
      element.data.data_source_config = {
        type: 'excel',
        data_source_name: selectedDataSourceObj ? selectedDataSourceObj.name : '',
        excel_sheet_name: this.excelSheets[this.currentSheetIndex],
        excel_cell_range: this.selectedRange
      }
      
      // 更新数据源信息显示
      this.currentDataSourceInfo = {
        sheet: this.excelSheets[this.currentSheetIndex],
        range: this.selectedRange
      }
      
      // 获取实际数据并更新元素
      this.replaceElementDataWithSelectedRange({
        sheetName:'',
        start_row: 1,
        end_row: 10,
        start_column: 'A',
        end_column: 'Z',
        startColIndex: 0, // 添加缺失的属性
        endColIndex: 25   // Z列对应索引25
      }).then(() => {
        this.saveConfig()
        this.closeDataPreviewModal()
        this.showToastMessage('数据源配置成功', 'success')
        
        // 数据源更新后重新初始化图表
        this.handleElementDataUpdate()
      }).catch(error => {
        console.error('获取和更新数据失败:', error)
        this.showToastMessage('数据更新失败: ' + (error as Error).message, 'error')
      })
    }
  }
  
  // 保存配置
  async saveConfig() {
    if (this.pptConfig) {
      // 保存到本地存储
      sessionStorage.setItem('pptConfig', JSON.stringify(this.pptConfig))
      
      try {
        // 尝试保存到服务器
        await templateEditorService.saveTemplateConfig(this.templateId, this.pptConfig)
      } catch (error) {
        console.error('保存配置到服务器失败:', error)
        // 不抛出错误，因为本地保存已经成功
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
  
  // 当元素数据更新时重新初始化图表
  handleElementDataUpdate() {
    this.$nextTick(() => {
      this.reinitializeCharts();
      
      // 直接更新预览面板中的元素数据
      this.updatePreviewPanelElements();
    });
  }
  
  // 更新预览面板中的元素数据
  updatePreviewPanelElements() {
    templateEditorInteractionService.updatePreviewPanelElements(
      this.currentSlideIndex,
      this.selectedElementIndex,
      () => this.getCurrentSlideElements(),
      (element, container) => this.updateExcelElementData(element, container)
    );
  }
  
  // 更新Excel元素数据
  async updateExcelElementData(element: Element, container: HTMLElement) {
    await templateEditorInteractionService.updateExcelElementData(
      element, 
      container, 
      this.dataSources, 
      this.selectedDataSource, 
      (message, type) => this.showToastMessage(message, type)
    );
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