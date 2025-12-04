<template>
  <div id="templateEditor" class="page-content">
    <div class="main-container"> 
      <!-- 预览面板 -->
      <div class="preview-panel">
        <div class="preview-header">
          <h2>预览面板</h2>
        </div>
        <div class="preview-content">
          <div class="presentation-container" ref="presentationContainer">
            <!-- 动态生成的幻灯片内容 -->
            <div v-if="!pptConfig" class="loading-message">正在加载模板配置...</div>
            <template v-else>
              <div class="info-panel">
                <h3>📋 模板信息</h3>
                <p><strong>文件:</strong> {{ pptConfig.file_path || '未知' }}</p>
                <p><strong>幻灯片数量:</strong> {{ pptConfig.total_slides || 0 }}</p>
                <p><strong>尺寸:</strong> {{ pptConfig.slide_width || 800 }} x {{ pptConfig.slide_height || 600 }}</p>
                <p><strong>创建时间:</strong> {{ formatDate(pptConfig.createTime) || '未知' }}</p>
              </div>
              
              <div 
                v-for="(slide, slideIndex) in pptConfig.slides" 
                :key="slideIndex"
                class="slide"
                :id="`slide_${slideIndex}`"
                @click="previewSlideClick(slideIndex)"
                :style="{
                  width: `${slide.width || pptConfig.slide_width || 800}px`,
                  height: `${slide.height || pptConfig.slide_height || 600}px`
                }"
              >
                <div class="slide-background" :style="getBackgroundStyle(slide.background)"></div>
                
                <template v-if="slide.elements && Array.isArray(slide.elements)">
                  <div 
                    v-for="(element, elementIndex) in slide.elements" 
                    :key="elementIndex"
                    v-html="generateElementHTML(element)"
                    :class="['element', { 'selected': isElementSelected(slideIndex, elementIndex) }]"
                    @click.stop="selectElement(slideIndex, elementIndex)"
                  ></div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <!-- 配置编辑器面板 -->
      <div class="config-panel">
        <div class="config-content">
          <!-- 页面和元素的配置页面 -->
          <div class="tab-content">
            <div id="slide-info-display" v-if="selectedElementIndex >= 0">
              <p>幻灯片 {{ currentSlideIndex + 1 }} - 元素 {{ selectedElementIndex + 1 }}</p>
            </div>
            <select 
              class="element-dropdown" 
              @change="selectElementByDropdown"
              v-model="selectedElementDropdown"
            >
              <option value="-1">请选择元素</option>
              <option 
                v-for="(element, index) in getCurrentSlideElements()"
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
                  @click="switchElementEditorTab('style')"
                >
                  样式
                </button>
                <button 
                  class="config-tab" 
                  :class="{ active: currentTab === 'data' }"
                  @click="switchElementEditorTab('data')"
                >
                  数据
                </button>
              </div>
              
              <!-- 样式Tab内容 -->
              <div class="tab-content" id="style-tab-content" v-if="currentTab === 'style'">
                <div class="config-item">
                  <label>元素ID</label>
                  <input type="text" :value="getCurrentElement()?.id || ''" readonly>
                </div>
                <div class="config-item">
                  <label>元素类型</label>
                  <input type="text" :value="getCurrentElement()?.element_type_name || ''" readonly>
                </div>
                <div class="config-item">
                  <label>左边距 (px)</label>
                  <input 
                    type="number" 
                    :value="getCurrentElement()?.position?.left || 0"
                    @change="updateElementPosition('left', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>顶边距 (px)</label>
                  <input 
                    type="number" 
                    :value="getCurrentElement()?.position?.top || 0"
                    @change="updateElementPosition('top', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>宽度 (px)</label>
                  <input 
                    type="number" 
                    :value="getCurrentElement()?.position?.width || 0"
                    @change="updateElementPosition('width', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>高度 (px)</label>
                  <input 
                    type="number" 
                    :value="getCurrentElement()?.position?.height || 0"
                    @change="updateElementPosition('height', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>字体大小</label>
                  <input 
                    type="text" 
                    :value="getCurrentElement()?.style?.font_size || ''"
                    @change="updateElementStyle('font_size', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>字体颜色</label>
                  <input 
                    type="color" 
                    :value="getCurrentElement()?.style?.color || '#000000'"
                    @change="updateElementStyle('color', $event)"
                  >
                </div>
                <div class="config-item">
                  <label>背景颜色</label>
                  <input 
                    type="color" 
                    :value="getCurrentElement()?.style?.background_color || '#ffffff'"
                    @change="updateElementStyle('background_color', $event)"
                  >
                </div>
              </div>
              
              <!-- 数据Tab内容 -->
              <div class="tab-content" id="data-tab-content" v-if="currentTab === 'data'">
                <div class="config-item" v-if="getCurrentElement()?.element_type_name === 'text'">
                  <label>文本内容</label>
                  <textarea 
                    :value="getCurrentElement()?.data?.text_content || ''"
                    @change="updateElementContent($event)"
                  ></textarea>
                </div>
                <div 
                  class="config-item" 
                  id="image-upload-section" 
                  v-if="getCurrentElement()?.element_type_name === 'image'"
                >
                  <label>图片上传</label>
                  <input type="file" accept="image/*" @change="handleImageUpload">
                  <div 
                    class="image-preview" 
                    v-if="getCurrentElement()?.data?.text_content"
                    style="margin-top: 10px; max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;"
                  >
                    <img 
                      :src="getCurrentElement()?.data?.text_content || ''" 
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
                    @click="openDataPreviewModal"
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

import { toRaw } from 'vue';
import { Options, Vue } from 'vue-class-component'
import { useRoute } from 'vue-router'
import type { Template } from '@/types/template'
import type { DataSource } from '@/types/dataSource'
import { dataSourceService } from '@/services/dataSourceService'
import { TemplateEditorService } from '@/services/TemplateEditorService'
import type { PPTConfig, Element } from '@/services/TemplateEditorService'
import DataPreviewModal from '@/components/DataPreviewModal.vue'
import type { SheetData, DataSelection } from '@/types/dataExtraction'
import { httpClient } from '@/services/httpClient'

// 初始化服务
const templateEditorService = new TemplateEditorService()

interface BackgroundConfig {
  type: 'color' | 'image'
  value: string
}

@Options({
  components: {
    // 可以在这里导入子组件
    DataPreviewModal
  }
})
export default class TemplateEditor extends Vue {
  // 路由
  route = useRoute()
  
  // 响应式数据
  pptConfig: PPTConfig | null = null
  templateId: string = ''
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
    // 获取模板ID
    this.templateId = this.route.query.template as string || ''
    
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
  
  // 获取背景样式
  getBackgroundStyle(background?: string | BackgroundConfig): Record<string, string> {
    const style: Record<string, string> = {}
    
    if (!background) return style
    
    if (typeof background === 'string') {
      // 旧格式直接是颜色字符串
      style.background = background
    } else if (background.type === 'color') {
      // 新格式：纯色背景
      style.background = background.value
    } else if (background.type === 'image') {
      // 新格式：图片背景
      style.backgroundImage = `url(${background.value})`
      style.backgroundSize = 'cover'
      style.backgroundPosition = 'center'
      style.backgroundRepeat = 'no-repeat'
    }
    
    return style
  }
  
  // 应用元素样式
  applyElementStyles(style?: any): string {
    if (!style) return ''
    let styleStr = ''
    if (style?.font_family) styleStr += `font-family: '${style.font_family}', Arial, sans-serif; `
    if (style?.font_size) styleStr += `font-size: ${style.font_size}; `
    if (style?.color) styleStr += `color: ${style.color}; `
    if (style?.background_color) styleStr += `background-color: ${style.background_color}; `
    if (style?.font_style) styleStr += `font-style: ${style.font_style}; `
    if (style?.font_weight) styleStr += `font-weight: ${style.font_weight}; `
    if (style?.text_decoration) styleStr += `text-decoration: ${style.text_decoration}; `
    if (style?.text_align) styleStr += `text-align: ${style.text_align}; `
    return styleStr
  }
  
  // 渲染文本框元素
  renderTextElement(element: Element): string {
    const data = element.data || {}
    const content = data.text_content || element.content || ''
    return `<div class="textbox">${content}</div>`
  }
  
  // 渲染图片元素
  renderImageElement(element: Element): string {
    const data = element.data || {}
    const imageData = data.image_data || element.content || ''
    
    if (!imageData || imageData === '') {
      return `<div style="border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; background: #f9f9f9; color: #666; font-size: 14px;">
        <div style="text-align: center;">
          <div>📷</div>
          <div>无图片数据</div>
        </div>
      </div>`
    } else if (imageData === "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==") {
      return `<div style="border: 2px dashed #ff9900; display: flex; align-items: center; justify-content: center; background: #fff9e6; color: #ff9900; font-size: 14px;">
        <div style="text-align: center;">
          <div>⚠️</div>
          <div>图片提取失败</div>
          <div style="font-size: 12px; margin-top: 5px;">使用占位符</div>
        </div>
      </div>`
    } else {
      return `<div class="image-container">
            <img src="${imageData}" alt="Image" 
                 style="max-width: 100%; max-height: 100%; object-fit: contain;"
                 onerror='this.parentElement.innerHTML = "<div style=&quot;border: 2px dashed #ff0000; display: flex; align-items: center; justify-content: center; background: #ffe6e6; color: #ff0000; font-size: 14px; height: 100%;&quot;>❌ 图片加载失败</div>"' />
        </div>`;
    }
    
  }
  
  // 渲染表格元素
  renderTableElement(element: Element): string {
    const data = element.data || {}
    if (data.table_data) {
      // 支持表格样式和数据渲染
      const tableData = data.table_data
      const rowHeights = data.table_row_heights || []
      const colWidths = data.table_col_widths || []
      const tableId = 'table_' + (element.id || Math.floor(Math.random() * 1000))
      
      // 生成列宽样式
      let colgroupHtml = '<colgroup>'
      if (Array.isArray(colWidths) && colWidths.length > 0) {
        colWidths.forEach(width => {
          colgroupHtml += `<col style="width: ${width}px;">`
        })
      }
      colgroupHtml += '</colgroup>'
      
      // 检查是否为OLE对象，动态设置overflow属性
      const isOLEObject = ['msoEmbeddedOLEObject'].includes(element.element_type_name || element.type);
      // 外部容器设置overflow: hidden，内部table-wrapper设置overflow: auto
      // 这样可以避免显示双重滚动条，只保留内部表格的滚动条
      const overflowStyle = 'hidden';
      let html = `<div id="${tableId}" class="embedded-table-container" style="height: 100%; width: 100%; overflow: ${overflowStyle};">
                   <style scoped>
                     /* 嵌入表格的tab页默认隐藏，悬停时显示 */
                     .embedded-tabs {
                       opacity: 0;
                       transition: opacity 0.3s ease;
                       pointer-events: none;
                     }
                     .embedded-table-container:hover .embedded-tabs {
                       opacity: 1;
                       pointer-events: auto;
                     }
                   </style>`
      
      // 处理多sheet情况
      const raw = toRaw(tableData);
      if (Array.isArray(raw)) {
        // 单一表格情况
        html += this.generateSingleSheetHTML(raw, tableId, colgroupHtml, rowHeights)
      } else {
        // 多sheet情况，添加tab切换
        const sheetNames = Object.keys(tableData)
        if (sheetNames.length > 0) {
          // 添加sheet标签栏，为OLE对象添加特殊类名以实现默认隐藏
          const tabsClass = isOLEObject ? 'sheet-tabs embedded-tabs' : 'sheet-tabs';
          html += `<div class="${tabsClass}" style="display: flex; border-bottom: 1px solid #ccc; background: #f5f5f5;">`
          sheetNames.forEach((sheetName, index) => {
            const isActive = index === 0
            html += `
              <div class="sheet-tab ${isActive ? 'active' : ''}"
                   style="padding: 6px 12px; cursor: pointer; border-right: 1px solid #ddd; ${isActive ? 'background: white; border-bottom: 2px solid #1890ff;' : ''}"
                   onclick="document.querySelectorAll('#${tableId} .sheet-content').forEach((el, i) => el.style.display = i === ${index} ? 'block' : 'none');
                           document.querySelectorAll('#${tableId} .sheet-tab').forEach((el, i) => {
                             el.classList.toggle('active', i === ${index});
                             el.style.background = i === ${index} ? 'white' : '#f5f5f5';
                             el.style.borderBottom = i === ${index} ? '2px solid #1890ff' : 'none';
                           });">
                ${sheetName}
              </div>
            `
          })
          html += `</div>`
          
          // 添加每个sheet的内容
          sheetNames.forEach((sheetName, index) => {
            const isActive = index === 0
            const sheetData = tableData[sheetName]
            if (Array.isArray(sheetData)) {
              html += `<div class="sheet-content" id="${tableId}_sheet_${index}" style="display: ${isActive ? 'block' : 'none'}; height: calc(100% - 30px);">`
              html += this.generateSingleSheetHTML(sheetData, `${tableId}_sheet_${index}`, colgroupHtml, rowHeights)
              html += `</div>`
            }
          })
        }
      }    
      html += `</div>`
      return html
    } else {
      return '<div style="border: 1px dashed #ccc; padding: 10px; color: #666;">无表格数据</div>'
    }
  }
  
  // 生成单个sheet的HTML
  generateSingleSheetHTML(sheetData: any[], tableId: string, colgroupHtml: string, rowHeights: number[]): string {
    let html = `<div class="table-wrapper" style="height: 100%; width: 100%; overflow: auto;">
                <table id="${tableId}_table" style="border-collapse: collapse; table-layout: fixed;">`
    
    html += colgroupHtml;
    
    let rowIndex = 0;
    sheetData.forEach((row: any) => {
      // 应用行高
      const rowHeight = Array.isArray(rowHeights) && rowHeights[rowIndex] ? rowHeights[rowIndex] : 'auto';
      html += `<tr style="height: ${rowHeight}px;">`;
      if (Array.isArray(row)) {
        row.forEach((cell: any) => {
          html += this.renderTableCell(cell);
        });
      } else {
        // 处理row不是数组的情况
        html += `<td>${String(row)}</td>`;
      }
      
      html += '</tr>';
      rowIndex++;
    });
    
    html += '</table></div>';
    return html;
  }
  
  // 渲染表格单元格，处理样式和内容
  renderTableCell(cell: any): string {
    if (!cell) return '<td></td>'
    
    // 构建单元格样式
    let cellStyle = ''
    
    // 背景色
    if (cell.background_color) {
      cellStyle += `background-color: ${cell.background_color};`
    }
    
    // 文字颜色
    if (cell.text_color) {
      cellStyle += `color: ${cell.text_color};`
    }
    
    // 边框
    if (cell.border) {
      cellStyle += `border: ${cell.border};`
    }
    
    // 水平对齐
    if (cell.horizontal_align) {
      const alignMap: Record<string, string> = {
        'left': 'left',
        'center': 'center',
        'right': 'right'
      }
      cellStyle += `text-align: ${alignMap[cell.horizontal_align] || 'left'};`
    }
    
    // 垂直对齐
    if (cell.vertical_align) {
      const valignMap: Record<string, string> = {
        'top': 'top',
        'middle': 'middle',
        'bottom': 'bottom'
      }
      cellStyle += `vertical-align: ${valignMap[cell.vertical_align] || 'top'};`
    }
    
    // 字体样式
    if (cell.font_name) {
      cellStyle += `font-family: ${cell.font_name};`
    }
    
    if (cell.font_size) {
      cellStyle += `font-size: ${cell.font_size}px;`
    }
    
    if (cell.font_bold) {
      cellStyle += 'font-weight: bold;'
    }
    
    if (cell.font_italic) {
      cellStyle += 'font-style: italic;'
    }
    
    if (cell.font_underline) {
      cellStyle += 'text-decoration: underline;'
    }
    
    // 处理单元格内容
    const cellContent = cell.text || ''
    
    // 返回带样式的单元格HTML
    return `<td style="${cellStyle}">${cellContent}</td>`
  }
  
  // 渲染OLE元素
  renderOLEElement(element: Element): string {
    const data = element.data || {}
    // 优先检查ole_datas字段（OLE对象的专用数据字段）
    if (data.ole_datas && data.ole_datas.sheets && data.ole_datas.sheets.length > 0) {
      // 从ole_datas构建table_data格式
      const tableData: Record<string, any> = {}
      data.ole_datas.sheets.forEach((sheet: any) => {
        if (sheet.data && Array.isArray(sheet.data)) {
          tableData[sheet.name] = sheet.data
        }
      })
      
      if (Object.keys(tableData).length > 0) {
        return this.renderTableElement({ ...element, data: { ...data, table_data: tableData } })
      }
    }
    
    // 回退到检查table_data字段
    if (data.table_data) {
      return this.renderTableElement(element)
    }
    
    // 如果都没有数据，显示无数据提示
    return '<div style="border: 1px dashed #ff9900; padding: 10px; color: #ff9900;">OLE对象 - 无数据</div>'
  }
  
  // 渲染Excel数据源元素
  renderExcelDataSourceElement(element: Element): string {
    const data = element.data || {}
    const dataSourceConfig = (data.data_source_config || {}) as Record<string, any>
    const tableId = 'table_' + (new Date().getTime()) + '_' + Math.floor(Math.random() * 1000)
    
    let html = `<div id="${tableId}" class="table-loading">
        <div style="padding: 20px; text-align: center; color: #666;">正在从Excel数据源加载数据...</div>
      </div>`
    
    // 简化的脚本，避免复杂的模板字符串
    html += '<script>';
    html += '(function() {';
    html += 'const config = ' + JSON.stringify(dataSourceConfig) + ';';
    html += 'const tableId = "' + tableId + '";';
    html += 'function loadExcelData() {';
    html += 'let url = "/get_excel_cell_range?";';
    html += 'url += "unique_filename=" + encodeURIComponent(config.data_source_name);';
    html += 'url += "&sheet_name=" + encodeURIComponent(config.excel_sheet_name);';
    if (dataSourceConfig.excel_cell_range) {
      html += 'url += "&cell_range=" + encodeURIComponent(config.excel_cell_range);';
    }
    html += 'fetch(url)';
    html += '.then(response => {';
    html += 'if (!response.ok) {';
    html += 'return response.json().then(err => Promise.reject(err));';
    html += '}';
    html += 'return response.json();';
    html += '})';
    html += '.then(data => {';
    html += 'if (data.success && data.data) {';
    html += 'const tableElement = document.getElementById(tableId);';
    html += 'if (tableElement) {';
    html += 'const elementPos = {';
    html += 'width: ' + 400 + ',';
    html += 'height: ' + 300 + ',';
    html += 'x: ' + 0 + ',';
    html += 'y: ' + 0;
    html += '};';
    html += 'let tableData = {};';
    html += 'if (Array.isArray(data.data)) {';
    html += 'tableData[config.excel_sheet_name] = data.data;';
    html += '} else {';
    html += 'tableData = data.data;';
    html += '}';
    html += '// Vue版本中使用简化的表格渲染';
    html += `let tableHTML = '<div class="table-container"><table>';`;
    html += 'const sheetNames = Object.keys(tableData);';
    html += 'if (sheetNames.length > 0) {';
    html += 'const sheetData = tableData[sheetNames[0]];';
    html += 'if (Array.isArray(sheetData)) {';
    html += 'sheetData.forEach(row => {';
    html += 'tableHTML += "<tr>";';
    html += 'row.forEach(cell => {';
    html += 'tableHTML += "<td>" + (cell || "") + "</td>";';
    html += '});';
    html += 'tableHTML += "</tr>";';
    html += '});';
    html += '}';
    html += '}';
    html += 'tableHTML += "</table></div>";';
    html += 'tableElement.innerHTML = tableHTML;';
    html += '}';
    html += '} else {';
    html += 'console.error("加载Excel数据失败:", data.error);';
    html += 'const tableElement = document.getElementById(tableId);';
    html += 'if (tableElement) {';
    html += `tableElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #ff0000;">加载Excel数据失败: " + (data.error || "未知错误") + "</div>';`;
    html += '}';
    html += '}';
    html += '})';
    html += '.catch(error => {';
    html += 'console.error("加载Excel数据时发生网络错误:", error);';
    html += 'const tableElement = document.getElementById(tableId);';
    html += 'if (tableElement) {';
    html += `tableElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #ff0000;">无法连接到服务器，请检查网络连接</div>';`;
    html += '}';
    html += '});';
    html += '}';
    html += 'if (document.readyState === "loading") {';
    html += 'document.addEventListener("DOMContentLoaded", loadExcelData);';
    html += '} else {';
    html += 'loadExcelData();';
    html += '}';
    html += '})();';
    html += '</' + 'script>';  // 拆分结束标签以避免解析问题
    
    return html
  }
  
  // 渲染图表元素
  renderChartElement(element: Element): string {
    const data = element.data || {}
    const chartId = 'chart-' + (element.id || Math.floor(Math.random() * 1000))
    
    let html = `<div class="chart-container" style="width: ${element.position?.width}px; height: ${element.position?.height}px; position: relative;">
      <canvas id="${chartId}" style="width: 100%; height: 100%;"></canvas>
    </div>`
    
    // 添加图表初始化脚本，但在Vue中使用v-html时，内联脚本可能不会执行
    // 所以我们依赖mounted钩子中的reinitializeCharts方法来初始化图表
    if (data.chart_data) {
      // 我们不会在这里添加内联脚本，而是依赖reinitializeCharts方法
      // 但为了向后兼容，我们仍会添加一些基本的错误处理信息
      html += `
      <script>(function() {
        setTimeout(() => {
          const ctx = document.getElementById('${chartId}');
          if (ctx && typeof Chart === 'undefined') {

          }
        }, 100);
      })();</` + 'script>'
    } else {

      html += `<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #999; font-size: 14px;">
        无图表数据
      </div>`;
    }
    
    return html
  }
  
  // 渲染线条元素
  renderLineElement(element: Element): string {
    const style = element.style || {};
    // 获取边框样式信息
    const border = style.border || '2px solid #000000';
    
    // 构建线条样式
    let lineStyle = `border: ${border};`;
    
    // 如果元素有名称，显示名称
    const elementName = element['element_name'] || '';
    const nameDisplay = elementName ? `<div style="position: absolute; bottom: -20px; left: 0; font-size: 10px; color: #666;">${elementName}</div>` : '';
    
    return `<div style="${lineStyle}">${nameDisplay}</div>`;
  }
  
  // 渲染未知类型元素
  renderUnknownElement(element: Element): string {
    const data = element.data || {}
    const typeName = element.element_type_name || element.type || '未知'
    const content = data.text_content || element.content || ''
    return `<div style="border: 1px dashed #ccc; padding: 5px; font-size: 12px; color: #666;">${typeName.toUpperCase()}: ${content}</div>`
  }
  
  // 生成元素HTML
  generateElementHTML(element: Element): string {
      if (!element) return ''
      
      // 处理位置信息，兼容HTML版本的position对象
      const position = element.position || {};
      const left = element.left || position.left || 0;
      const top = element.top || position.top || 0;
      const width = element.width || position.width || 0;
      const height = element.height || position.height || 0;
      
      const isEmbeddedTable = ['msoEmbeddedOLEObject'].includes(element.element_type_name || element.type);
      
      // 为所有元素应用正确的位置和大小样式
      let style: { [key: string]: string } = {
        position: 'absolute',
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`
      };
      
      let styleString = Object.entries(style)
        .map(([key, value]) => `${key}: ${value}`)
        .join('; ');
      if (styleString) {
        styleString += ';';
      }
      // 应用element.style对象中的样式
      styleString += ' ' + this.applyElementStyles(element.style);
      
      // 应用Vue版本的样式属性
      if (element.fontSize && !element.style?.font_size) styleString += `; font-size: ${element.fontSize}`;
      if (element.color && !element.style?.color) styleString += `; color: ${element.color}`;
      if (element.bgColor && !element.style?.background_color) styleString += `; background-color: ${element.bgColor}`;
      
      // 添加通用样式
      styleString += '; cursor: pointer;';
      
      // 对OLE对象特殊处理overflow属性，使其内容超出时显示滚动条
      if (isEmbeddedTable) {
        styleString += ' overflow: auto;';
      } else {
        styleString += ' overflow: hidden;';
      }
      
      let elementHTML = `<div style="${styleString}">`;
      
      const data = element.data || {};
      const dataSourceConfig = data.data_source_config;
      
      // 优先处理数据源配置元素
      if (dataSourceConfig && dataSourceConfig.type === 'excel' && dataSourceConfig.data_source_name && dataSourceConfig.excel_sheet_name) {
        elementHTML += this.renderExcelDataSourceElement(element);
      } else if (data.chart_data && data.chart_data.type) {
        // 处理图表元素
        elementHTML += this.renderChartElement(element);
      } else {
        // 根据元素类型渲染
        const elementType = element.element_type_name || element.type;
        switch (elementType) {
          case 'msoTextBox':
          case 'msoAutoShape':
          case 'text':
            elementHTML += this.renderTextElement(element);
            break;
          case 'msoTable':
            elementHTML += this.renderTableElement(element);
            break;
          case 'msoEmbeddedOLEObject':
            elementHTML += this.renderOLEElement(element);
            break;
          case 'msoChart':
          case 'chart':
            elementHTML += this.renderChartElement(element);
            break;
          case 'msoPicture':
          case 'image':
            elementHTML += this.renderImageElement(element);
            break;
          case 'msoLine':
            // 为线条类型元素添加专门的渲染逻辑
            elementHTML += this.renderLineElement(element);
            break;
          default:
            elementHTML += this.renderUnknownElement(element);
            break;
        }
      }
      
      elementHTML += '</div>';
      return elementHTML;
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
  
  // 检查元素是否被选中
  isElementSelected(slideIndex: number, elementIndex: number): boolean {
    return this.currentSlideIndex === slideIndex && this.selectedElementIndex === elementIndex
  }
  
  // 通过下拉选择元素
  selectElementByDropdown(event: Event) {
    const selectElement = event.target as HTMLSelectElement
    const elementIndex = parseInt(selectElement.value)
    
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
  
  // 获取元素显示名称
  getElementDisplayName(element: Element): string {
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
    }
    
    // 优先使用element_type_name，如果存在的话
    if (element.element_type_name) {
      return typeMap[element.element_type_name] || element.element_type_name
    }
    
    return typeMap[element.type] || '未知'
  }
  
  // 切换元素编辑器标签
  switchElementEditorTab(tab: 'style' | 'data') {
    this.currentTab = tab
  }
  
  // 更新元素位置和大小
  updateElementPosition(property: 'left' | 'top' | 'width' | 'height', event: Event) {
    const inputElement = event.target as HTMLInputElement
    const value = parseInt(inputElement.value)
    
    if (isNaN(value)) return
    
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      elements[this.selectedElementIndex][property] = value
      this.saveConfig()
    }
  }
  
  // 更新元素样式
  updateElementStyle(property: 'fontSize' | 'color' | 'bgColor', event: Event) {
    const inputElement = event.target as HTMLInputElement
    const value = inputElement.value
    
    const elements = this.getCurrentSlideElements()
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      elements[this.selectedElementIndex][property] = value
      this.saveConfig()
    }
  }
  
  // 更新元素内容
  updateElementContent(event: Event) {
    const textareaElement = event.target as HTMLTextAreaElement
    const value = textareaElement.value
    
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
    
    const startRow = Math.min(this.selectionStart.row, this.selectionEnd.row)
    const endRow = Math.max(this.selectionStart.row, this.selectionEnd.row)
    const startCol = Math.min(this.selectionStart.col, this.selectionEnd.col)
    const endCol = Math.max(this.selectionStart.col, this.selectionEnd.col)
    
    const startColStr = this.numberToColumn(startCol)
    const endColStr = this.numberToColumn(endCol)
    
    if (startRow === endRow && startCol === endCol) {
      this.selectedRange = `${startColStr}${startRow}`
    } else {
      this.selectedRange = `${startColStr}${startRow}:${endColStr}${endRow}`
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
      element.data.data_source_config.excel_cell_range = `${selection.startColumn}${selection.startRow}:${selection.endColumn}${selection.endRow}`
      
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
        this.showToastMessage(`已选择区域: 行${selection.startRow}-${selection.endRow}, 列${selection.startColumn}-${selection.endColumn}`, 'success')
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
    try {
      const elements = this.getCurrentSlideElements()
      if (this.selectedElementIndex < 0 || this.selectedElementIndex >= elements.length) {
        throw new Error('请先选择一个元素')
      }
      
      const element = elements[this.selectedElementIndex]
      
      // 请求数据源的实际数据
      this.showToastMessage('正在获取选中数据区域的数据...', 'info')
      
      const response = await httpClient.post(`/datasource/${encodeURIComponent(this.selectedDataSource)}/range`, {
        sheet_name: this.currentSelectedSheet,
        cell_range: `${selection.startColumn}${selection.startRow}:${selection.endColumn}${selection.endRow}`
      })
      
      if (!response.success) {
        throw new Error(response.error || '获取数据失败')
      }
      
      const newData = response.data.table_data
      const table_row_heights = response.data.table_row_heights
      const table_col_widths = response.data.table_col_widths
      
      if (!newData || (!Array.isArray(newData) && typeof newData !== 'object')) {
        throw new Error('返回的数据格式不正确')
      }
      
      // 根据元素类型更新数据
      if (!element.data) {
        element.data = {}
      }
      
      // 根据元素类型处理数据
      switch (element.element_type_name) {
        case 'msoTable':
          // 对于表格元素，更新 table_data
          if (Array.isArray(newData)) {
            element.data.table_data = newData
          } else {
            // 如果是对象格式（多工作表），只取当前工作表的数据
            element.data.table_data = newData[this.currentSelectedSheet] || newData
          }
          // 保存行列尺寸信息
          if (table_row_heights) element.data.table_row_heights = table_row_heights
          if (table_col_widths) element.data.table_col_widths = table_col_widths
          break
          
        case 'msoEmbeddedOLEObject':
        case 'msoEmbeddedOLEObjectWithSheets':
          // 对于OLE对象，更新 ole_datas 和 table_data
          if (Array.isArray(newData)) {
            // 单工作表数据
            element.data.table_data = { [this.currentSelectedSheet]: newData }
            element.data.ole_datas = {
              sheets: [{
                name: this.currentSelectedSheet,
                data: newData
              }]
            }
          } else if (typeof newData === 'object') {
            // 多工作表数据
            element.data.table_data = newData
            const sheets = Object.keys(newData).map(sheetName => ({
              name: sheetName,
              data: newData[sheetName]
            }))
            element.data.ole_datas = { sheets }
          }
          break
          
        case 'msoChart':
          // 对于图表元素，需要将数据转换为Chart.js格式
          try {
            const chartData = this.convertDataToChartFormat(newData, element.data.chart_data)
            element.data.chart_data = chartData
          } catch (chartError) {
    
            // 如果转换失败，保存原始数据作为表格数据
            element.data.table_data = Array.isArray(newData) ? newData : newData[this.currentSelectedSheet] || newData
          }
          break
          
        case 'msoTextBox':
        case 'msoAutoShape':
          // 对于文本元素，将数据转换为文本
          {
            let textContent = ''
            if (Array.isArray(newData) && newData.length > 0) {
            if (Array.isArray(newData[0])) {
              // 二维数组，取第一个单元格
              textContent = String(newData[0][0] || '')
            } else {
              // 一维数组，取第一个元素
              textContent = String(newData[0] || '')
            }
          } else if (typeof newData === 'object' && newData !== null) {
            // 对象格式，尝试获取第一个值
            const firstValue = Object.values(newData)[0]
            if (Array.isArray(firstValue) && firstValue.length > 0) {
              textContent = String(firstValue[0] || '')
            } else {
              textContent = String(firstValue || '')
            }
          } else {
            textContent = String(newData || '')
          }
          element.data.text_content = textContent
        }
        break
          
        default:
          // 对于其他类型，尝试保存为表格数据
          if (Array.isArray(newData)) {
            element.data.table_data = newData
          } else {
            element.data.table_data = newData[this.currentSelectedSheet] || newData
          }
          break
      }
    } catch (error) {
      console.error('替换元素数据失败:', error)
      throw error
    }
  }
  
  // 将数据转换为图表格式
  convertDataToChartFormat(newData: any, existingChartData: any): any {
    if (!existingChartData) {
      throw new Error('现有图表数据不存在')
    }
    
    // 复制现有图表配置
    const chartData = JSON.parse(JSON.stringify(existingChartData))
    
    // 将新数据转换为二维数组
    if (Array.isArray(newData) || typeof newData === 'object') {
      // 实际项目中需要实现数据到图表格式的转换逻辑
      // 这里只是保留了现有配置
    }
    
    return chartData
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
        startRow: 1,
        endRow: 10,
        startColumn: 'A',
        endColumn: 'Z',
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
    if (typeof window.Chart === 'undefined') {
      console.error('Chart.js 未加载，无法重新初始化图表');
      return;
    }
    
    // 查找页面上所有的图表容器
    const chartContainers = document.querySelectorAll('.chart-container canvas');
    chartContainers.forEach((canvas) => {
      // 将canvas元素断言为HTMLCanvasElement类型
      const canvasElement = canvas as HTMLCanvasElement;
      try {
        const chartId = canvasElement.id;
        const elementId = chartId.replace('chart-', '');
        
        // 查找对应的图表数据
        let chartData = null;
        if (this.pptConfig && this.pptConfig.slides) {
          for (const slide of this.pptConfig.slides) {
            if (slide.elements) {
              for (const element of slide.elements) {
                if (element.id === elementId && element.data && element.data.chart_data) {
                  chartData = element.data.chart_data;
                  break;
                }
              }
            }
            if (chartData) break;
          }
        }
        
        if (chartData) {
          // 销毁可能存在的旧图表实例
          if (canvasElement.chartInstance) {
            canvasElement.chartInstance.destroy();
          }
          
          // 确保图例位置正确设置
          if (!chartData.options) {
            chartData.options = {};
          }
          if (!chartData.options.plugins) {
            chartData.options.plugins = {};
          }
          if (!chartData.options.plugins.legend) {
            chartData.options.plugins.legend = {};
          }
          // 设置图例位置为bottom，这是一个比较合理的默认位置
          chartData.options.plugins.legend.position = 'bottom';
          
          // 创建新的图表实例
          const ctx = canvasElement.getContext('2d');
          canvasElement.chartInstance = new window.Chart(ctx, chartData);
        }
      } catch (error) {
        console.error('重新初始化图表失败:', error);
      }
    });
  }
  
  // 当元素数据更新时重新初始化图表和处理OLE对象滚动
  handleElementDataUpdate() {
    this.$nextTick(() => {
      this.reinitializeCharts();
      this.scrollToActiveCellInOLEObjects();
      
      // 直接更新预览面板中的元素数据
      this.updatePreviewPanelElements();
    });
  }
  
  // 更新预览面板中的元素数据
  updatePreviewPanelElements() {
    // 检查是否有选中的元素
    const elements = this.getCurrentSlideElements();
    if (this.selectedElementIndex >= 0 && this.selectedElementIndex < elements.length) {
      const element = elements[this.selectedElementIndex];
      const slidePreview = document.querySelector(`#slide_${this.currentSlideIndex}`);
      
      if (slidePreview) {
        // 查找对应元素的DOM容器
        const elementId = element.id || `element-${this.currentSlideIndex}-${this.selectedElementIndex}`;
        let elementContainer = slidePreview.querySelector(`[data-element-id="${elementId}"]`);
        
        // 如果没找到带有data-element-id的容器，尝试其他方式
        if (!elementContainer) {
          // 对于图表元素
          const chartContainer = slidePreview.querySelector(`.chart-container canvas[id="chart-${elementId}"]`);
          if (chartContainer) {
            elementContainer = chartContainer.closest('.chart-container');
          }
          
          // 对于表格或OLE对象
          if (!elementContainer) {
            const tableContainer = slidePreview.querySelector(`[id^="table_${elementId}"]`);
            if (tableContainer) {
              elementContainer = tableContainer;
            }
          }
        }
        
        // 如果找到了元素容器，根据元素类型执行特定的更新逻辑
        if (elementContainer && element.data) {
          if (element.data.data_source_config && element.data.data_source_config.type === 'excel') {
            // 对于Excel数据源元素，重新加载数据
            if (elementContainer instanceof HTMLElement) {
              this.updateExcelElementData(element, elementContainer);
            }
          } 
        }
      }
    }
  }
  
  // 更新Excel元素数据
  async updateExcelElementData(element: Element, container: HTMLElement) {
    const dataSourceConfig = element.data?.data_source_config;
    if (!dataSourceConfig || !dataSourceConfig.data_source_name || !dataSourceConfig.excel_sheet_name || !dataSourceConfig.excel_cell_range) {
      return;
    }
    
    try {
      // 显示加载状态
      const loadingHTML = '<div style="padding: 20px; text-align: center; color: #666;">数据加载中...</div>';
      
      // 查找正确的容器来显示加载状态
      const htmlElement = container as unknown as HTMLElement;
      let targetContainer = htmlElement;
      
      if (htmlElement.classList && htmlElement.classList.contains('chart-container')) {
        // 对于图表，加载状态会显示在图表下方
        targetContainer = htmlElement.parentElement || htmlElement;
      }
      
      // 保存原始内容，以便在加载失败时恢复
      const originalContent = targetContainer.innerHTML;
      targetContainer.innerHTML = loadingHTML;
      
      // 调用API获取更新后的数据
      const dataSourceObj = this.dataSources.find(source => source.name === dataSourceConfig.data_source_name);
      if (!dataSourceObj) return;
      
      const response = await httpClient.get(`/datasource/${encodeURIComponent(dataSourceObj.id)}/data`);
      
      if (response.success && response.data && response.data.data) {
        // 恢复原始内容
        targetContainer.innerHTML = originalContent;
        
        // 对于表格和OLE对象，重新滚动到活动单元格
        this.$nextTick(() => {
          this.scrollToActiveCellInOLEObjects();
        });
      } else {
        // 加载失败，显示错误信息
        targetContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #ff0000;">数据加载失败</div>';
        setTimeout(() => {
          // 3秒后恢复原始内容
          targetContainer.innerHTML = originalContent;
        }, 3000);
      }
    } catch (error) {
      console.error('更新Excel元素数据失败:', error);
      // 发生错误时显示提示
      this.showToastMessage('数据更新失败，请刷新页面重试', 'error');
    }
  }
  
  // 滚动到OLE对象中的活动单元格
  scrollToActiveCellInOLEObjects() {    
    // 查找页面上所有的嵌入式表格容器，使用更通用的选择器
    const embeddedTables = document.querySelectorAll('.embedded-table-container, .table-preview-wrapper');
    
    if (embeddedTables.length === 0) {
      // 如果没有找到，尝试使用其他可能的表格容器选择器
      const alternativeTables = document.querySelectorAll('[id^="table_"]');
      Array.from(alternativeTables).forEach(table => {
        if (table.id) {
          // 直接为每个表格执行滚动
          this.performImmediateScroll(table.id);
        }
      });
      return;
    }
    
    embeddedTables.forEach(container => {
      // 获取表格ID
      const tableId = container.id;
      if (!tableId) return;
      
      this.performImmediateScroll(tableId);
    });
  }
  
  // 为指定表格ID执行滚动操作
  performImmediateScroll(tableId: string) {
    try {
      // 查找对应的元素数据以获取活动单元格信息
      interface CellPosition {
        row: number;
        column: number;
      }
      let activeCell: string | CellPosition | null = null;
      
      // 先尝试通过ID精确匹配
      if (this.pptConfig && this.pptConfig.slides) {
        for (const slide of this.pptConfig.slides) {
          if (slide.elements) {
            for (const element of slide.elements) {
              // 查找匹配的元素ID
              if (element.id) {
                const elementTableId = 'table_' + element.id;
                if (tableId === elementTableId || tableId.startsWith(elementTableId + '_')) {
                  if (element.data && element.data.active_cell) {
                    activeCell = element.data.active_cell;
                  }
                  break;
                }
              }
            }
          }
          if (activeCell) break;
        }
      }
      
      // 如果没有找到活动单元格，使用默认值
      if (!activeCell) {
        activeCell = { row: 1, column: 1 };
      }
      
      // 滚动到活动单元格
      setTimeout(() => {
        this.performScrollToActiveCell(activeCell as string | null, tableId);
      }, 100);
    } catch (error) {
      console.error('滚动到活动单元格失败:', error);
    }
  }
  
  // 执行滚动到活动单元格的操作
  performScrollToActiveCell(activeCellData: any, tableId: string) {    
    // 获取滚动容器
    const scrollContainer = document.querySelector('#' + tableId + ' .table-wrapper');
    if (!scrollContainer) {

      
      // 尝试使用更通用的选择器
      const altScrollContainer = document.querySelector('#' + tableId + ' .table-preview-wrapper');
      if (altScrollContainer && altScrollContainer instanceof HTMLElement) {
        this.performScrollWithContainer(activeCellData, altScrollContainer);
      }
      return;
    }
    
    if (scrollContainer instanceof HTMLElement) {
      this.performScrollWithContainer(activeCellData, scrollContainer);
    } else {
      console.error('滚动容器不是HTMLElement类型');
    }
  }
  
  // 实际执行滚动操作的辅助方法
  performScrollWithContainer(activeCellData: any, scrollContainer: HTMLElement) {
    // 确保activeCellData是正确的格式
    let targetRow = 0;
    let targetCol = 0;
    
    if (activeCellData && typeof activeCellData === 'object' && 'row' in activeCellData && 'column' in activeCellData) {
      // 如果是对象格式，Excel行和列从1开始，表格行和列从0开始
      targetRow = activeCellData.row - 1;
      targetCol = activeCellData.column - 1;
    } else if (typeof activeCellData === 'string') {
      // 如果是字符串格式（如'A1'），需要解析
      try {
        const match = activeCellData.match(/([A-Z]+)(\d+)/);
        if (match) {
          // 解析列字母（A=0, B=1等）
          const colLetters = match[1].toUpperCase();
          for (let i = 0; i < colLetters.length; i++) {
            targetCol = targetCol * 26 + (colLetters.charCodeAt(i) - 65);
          }
          // 解析行号
          targetRow = parseInt(match[2]) - 1;
        }
      } catch (error) {
        console.error('解析活动单元格字符串失败:', error);
      }
    }
    
    
    // 查找活动单元格
    const table = scrollContainer.querySelector('table');
    if (table) {
      if (table.rows && table.rows[targetRow]) {
        const cell = table.rows[targetRow].cells[targetCol];
        if (cell) {
          // 计算滚动位置
          const cellRect = cell.getBoundingClientRect();
          const containerRect = scrollContainer.getBoundingClientRect();
            
          // 计算相对于容器的位置
          const relativeTop = cellRect.top - containerRect.top;
          const relativeLeft = cellRect.left - containerRect.left;
            
          // 计算滚动目标位置，使单元格居中
          const scrollTop = scrollContainer.scrollTop + relativeTop - (containerRect.height / 2) + (cellRect.height / 2);
          const scrollLeft = scrollContainer.scrollLeft + relativeLeft - (containerRect.width / 2) + (cellRect.width / 2);
            
          // 平滑滚动
          (scrollContainer as HTMLElement).scrollTo({
            top: Math.max(0, scrollTop),
            left: Math.max(0, scrollLeft),
            behavior: 'smooth'
          });
        } else {
    
          // 如果找不到指定单元格，滚动到表格顶部
          (scrollContainer as HTMLElement).scrollTo({ top: 0, left: 0, behavior: 'smooth' });
        }
      } else {
  
        // 如果找不到指定行，滚动到表格顶部
        (scrollContainer as HTMLElement).scrollTo({ top: 0, left: 0, behavior: 'smooth' });
      }

  }
  }
  
  // 动态加载Chart.js库
  async loadChartJs() {
    try {
      // 检查Chart对象是否已经存在
      if (typeof window.Chart === 'undefined') {
        // 动态创建script标签加载Chart.js
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.async = true;
        
        await new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
        
        // 加载完成后，如果有已渲染的图表，尝试重新初始化
        if (this.pptConfig && this.pptConfig.slides) {
          this.$nextTick(() => {
            this.reinitializeCharts();
            this.scrollToActiveCellInOLEObjects();
          });
        }
      }
    } catch (error) {
      console.error('Chart.js 加载失败:', error);
      this.showToastMessage('图表库加载失败，图表可能无法显示', 'error');
    }
  }
  
  // 在组件更新后检查并处理OLE对象的滚动
  updated() {
    this.$nextTick(() => {
      this.scrollToActiveCellInOLEObjects();
    });
  }
}

</script>

<style scoped>
/* 模板编辑器页面样式 */
.main-container {
  display: flex;
  height: calc(100vh - 120px);
  margin: 20px;
  gap: 20px;
}

/* 预览面板样式 */
.preview-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.preview-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  background-color: #f8f9fa;
}

.preview-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.preview-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.presentation-container {
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

.loading-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #666;
  font-size: 16px;
}

.info-panel {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  width: 100%;
}

.info-panel h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.info-panel p {
  margin: 5px 0;
  font-size: 14px;
  color: #666;
}

/* 幻灯片样式 */
.slide {
  position: relative;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.slide:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.slide-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.element {
  position: absolute;
  z-index: 1;
  transition: box-shadow 0.2s ease;
}

.element.selected {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* 配置面板样式 */
.config-panel {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.config-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.element-dropdown {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-bottom: 20px;
}

.config-section {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.config-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
}

/* 配置标签页样式 */
.config-tabs {
  display: flex;
  border-bottom: 1px solid #ddd;
  margin-bottom: 15px;
}

.config-tab {
  padding: 8px 16px;
  border: none;
  background-color: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.config-tab:hover {
  color: #333;
  background-color: #e9ecef;
}

.config-tab.active {
  color: #007bff;
  border-bottom-color: #007bff;
  background-color: white;
}

/* 配置项样式 */
.config-item {
  margin-bottom: 15px;
}

.config-item label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.config-item input[type="text"],
.config-item input[type="number"],
.config-item select,
.config-item textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.config-item input[type="text"]:read-only,
.config-item input[type="number"]:read-only {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.config-item textarea {
  min-height: 100px;
  resize: vertical;
}

/* 数据源信息样式 */
.data-source-info {
  background-color: white;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

/* 数据预览模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.close-btn:hover {
  background-color: #f5f5f5;
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.preview-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Excel风格工作表标签样式 */
.sheet-tabs-container {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ddd;
  margin-bottom: 2px;
  background-color: #f8f9fa;
  padding: 0 5px;
  position: relative;
  height: 32px;
}

.sheet-tabs {
  display: flex;
  overflow-x: auto;
  flex: 1;
  white-space: nowrap;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.sheet-tabs::-webkit-scrollbar {
  display: none;
}

.sheet-tab {
  padding: 5px 15px;
  margin-right: 2px;
  background-color: #e0e0e0;
  border: 1px solid #ccc;
  border-bottom: none;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-family: Arial, sans-serif;
  height: 25px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.sheet-tab:hover {
  background-color: #f0f0f0;
}

.sheet-tab.active {
  background-color: white;
  border-bottom: 1px solid white;
  z-index: 1;
  position: relative;
}

.add-sheet-tab {
  width: 25px;
  height: 25px;
  background-color: #e0e0e0;
  border: 1px solid #ccc;
  border-bottom: none;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  margin-left: 5px;
  transition: background-color 0.2s;
}

.add-sheet-tab:hover {
  background-color: #f0f0f0;
}

/* 表格预览样式 */
.table-preview-wrapper {
  overflow: auto;
  max-height: 400px;
  border: 1px solid #ddd;
  margin: 10px 0;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-family: Arial, sans-serif;
  font-size: 12px;
}

.preview-table th,
.preview-table td {
  padding: 8px;
  text-align: left;
  border: 1px solid #ddd;
  min-width: 60px;
}

.preview-table th {
  background-color: #f8f9fa;
  font-weight: bold;
  position: sticky;
  top: 0;
  z-index: 10;
}

.preview-table th:first-child,
.preview-table td:first-child {
  background-color: #f8f9fa;
  font-weight: bold;
  position: sticky;
  left: 0;
  z-index: 5;
}

.preview-table td.selected {
  background-color: #e3f2fd;
  outline: 2px solid #2196f3;
}

.selection-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.selection-info p {
  margin: 0;
  font-size: 14px;
  color: #333;
}

/* Toast消息样式 */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  z-index: 2000;
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  pointer-events: none;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.toast.show {
  opacity: 1;
  transform: translateY(0);
}

.toast.success {
  background-color: #28a745;
}

.toast.error {
  background-color: #dc3545;
}

.toast.info {
  background-color: #17a2b8;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #218838;
}

.btn-success:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-container {
    flex-direction: column;
    height: auto;
  }
  
  .preview-panel,
  .config-panel {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .main-container {
    margin: 10px;
    gap: 10px;
  }
  
  .preview-content,
  .config-content {
    padding: 15px;
  }
  
  .modal-content {
    width: 95%;
    margin: 10px;
  }
  
  .modal-header,
  .modal-body {
    padding: 15px;
  }
}
</style>