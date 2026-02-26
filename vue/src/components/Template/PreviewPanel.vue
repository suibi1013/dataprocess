<template>
  <div class="preview-panel">
    <div class="preview-content">
      <div class="presentation-container" ref="presentationContainer">
        <!-- 动态生成的幻灯片内容 -->
        <div v-if="!pptConfig" class="loading-message">正在加载模板配置...</div>
        <template v-else>
          
          <div 
            v-for="(slide, slideIndex) in pptConfig.slides" 
            :key="slideIndex"
            class="slide"
            :id="`slide_${slideIndex}`"
            @click="handleSlideClick(slideIndex)"
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
                @click.stop="handleElementClick(slideIndex, elementIndex)"
              ></div>
            </template>
          </div>
        </template>
      </div>
    </div>
    <!-- 固定显示在底部的信息面板 -->
    <div class="info-panel" v-if="pptConfig">
      <p><strong>模板名称:</strong> {{ pptConfig.templateName }}</p>
      <p><strong>文件名称:</strong> {{ pptConfig.filename}}</p>
      <p><strong>幻灯片数量:</strong> {{ pptConfig.total_slides || 0 }}</p>
      <p><strong>尺寸:</strong> {{ pptConfig.slide_width || 800 }} x {{ pptConfig.slide_height || 600 }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import type { PPTConfig, Element } from '@/services/TemplateEditorService';

// 定义组件属性
interface Props {
  pptConfig: PPTConfig | null;
  currentSlideIndex: number;
  selectedElementIndex: number;
}

const props = defineProps<Props>();

// 定义事件
const emit = defineEmits<{
  '_slide-click': [_slideIndex: number];
  '_element-click': [_slideIndex: number, _elementIndex: number];
}>();

// 引用
const presentationContainer = ref<HTMLElement | null>(null);
const active_cell_dict: { [key: string]: any }  = {};// 存储所有活动单元格信息

// 监听pptConfig变化，当数据更新时检查并滚动到活动单元格
watch(
  () => props.pptConfig,
  () => {
    checkAndScrollToActiveCells();
  },
  { deep: true }
);

// 组件挂载后检查并滚动到活动单元格
onMounted(() => {
  checkAndScrollToActiveCells();
});

// 监听当前幻灯片和选中元素变化，更新滚动位置
watch(
  [() => props.currentSlideIndex, () => props.selectedElementIndex],
  () => {
    checkAndScrollToActiveCells();
  }
);


// 执行滚动到活动单元格的操作
function performScrollToActiveCell(activeCellData: any, tableElement: HTMLElement) {  
  // 查找滚动容器
  const scrollContainer = tableElement.closest('.table-wrapper') as HTMLElement;
  if (!scrollContainer) {
    console.error('未找到滚动容器');
    return;
  }
  
  // 确保activeCellData是正确的格式
  let targetRow = 0;
  let targetCol = 0;
  
  // 解析活动单元格数据
  if (activeCellData && typeof activeCellData === 'object') {
    if ('row' in activeCellData && 'col' in activeCellData) {
      targetRow = activeCellData.row;
      targetCol = activeCellData.col;
    } else if ('row' in activeCellData && 'column' in activeCellData) {
      targetRow = activeCellData.row - 1;
      targetCol = activeCellData.column - 1;
    }
  } else if (typeof activeCellData === 'string') {
    try {
      // 支持多种字符串格式
      if (activeCellData.includes(',')) {
        // 格式：rowIndex,colIndex
        const [row, col] = activeCellData.split(',').map(Number);
        targetRow = row;
        targetCol = col;
      } else {
        // 格式：A1样式
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
      }
    } catch (error) {
      console.error('解析活动单元格字符串失败:', error);
      return;
    }
  }
  
  // 获取表格行和单元格
  const rows = tableElement.querySelectorAll('tr');
  if (rows.length > targetRow) {
    const cells = rows[targetRow].querySelectorAll('td, th');
    if (cells.length > targetCol) {
      const cell = cells[targetCol] as HTMLElement;
      if (cell) {
        // 计算滚动位置
        const cellRect = cell.getBoundingClientRect();
        const containerRect = scrollContainer.getBoundingClientRect();
        
        const relativeTop = cellRect.top - containerRect.top;
        const relativeLeft = cellRect.left - containerRect.left;
        
        const scrollTop = scrollContainer.scrollTop + relativeTop - (containerRect.height / 2) + (cellRect.height / 2);
        const scrollLeft = scrollContainer.scrollLeft + relativeLeft - (containerRect.width / 2) + (cellRect.width / 2);
        
        // 执行滚动
        scrollContainer.scrollTo({
          top: Math.max(0, scrollTop),
          left: Math.max(0, scrollLeft),
          behavior: 'smooth'
        });
      }
    }
  }
}

// 检查并滚动到活动单元格
function checkAndScrollToActiveCells() {
  // 等待DOM更新完成
  setTimeout(() => {
    if (!presentationContainer.value) return;
    
    // 查找所有表格容器
    const embeddedTables = presentationContainer.value.querySelectorAll('.embedded-table-container, .table-preview-wrapper');
    
    embeddedTables.forEach(container => {
      // 获取表格ID
      const tableId = container.id;
      if (!tableId) return;
      
      performImmediateScroll(tableId);
    });
  }, 100);
}

// 为指定表格ID执行滚动操作
function performImmediateScroll(tableId: string) {
  try {    
    // 查找对应的元素数据以获取活动单元格信息{index:index,active_cell:active_cell}
    let activeCellInfo = active_cell_dict[tableId] || {index:0,active_cell:{ row: 1, column: 1 }};    
    
    // 滚动到活动单元格
    setTimeout(() => {
      // 查找对应的表格元素
      const tableElement = document.querySelector(`#${tableId}_sheet_${activeCellInfo.index}_table`);
      if (tableElement) {
        performScrollToActiveCell(activeCellInfo.active_cell, tableElement as HTMLElement);
      }
    }, 100);
  } catch (error) {
    console.error('滚动到活动单元格失败:', error);
  }
}

// 获取背景样式
function getBackgroundStyle(background?: string | any): Record<string, string> {
  const style: Record<string, string> = {};
  
  if (!background) return style;
  
  if (typeof background === 'string') {
    // 旧格式直接是颜色字符串
    style.background = background;
  } else if (background.type === 'color') {
    // 新格式：纯色背景
    style.background = background.value;
  } else if (background.type === 'image') {
    // 新格式：图片背景
    style.backgroundImage = `url(${background.value})`;
    style.backgroundSize = 'cover';
    style.backgroundPosition = 'center';
    style.backgroundRepeat = 'no-repeat';
  }
  
  return style;
}

// 检查元素是否被选中
function isElementSelected(slideIndex: number, elementIndex: number): boolean {
  return props.currentSlideIndex === slideIndex && props.selectedElementIndex === elementIndex;
}

// 幻灯片点击事件
function handleSlideClick(slideIndex: number) {
  emit('slide-click', slideIndex);
}

// 元素点击事件
function handleElementClick(slideIndex: number, elementIndex: number) {
  emit('element-click', slideIndex, elementIndex);
}

// 生成元素HTML
function generateElementHTML(element: Element): string {
  if (!element) return '';
  
  // 处理位置信息，兼容HTML版本的position对象
  const position = element.position || {};
  const left = element.left || position.left || 0;
  const top = element.top || position.top || 0;
  const width = element.width || position.width || 0;
  const height = element.height || position.height || 0;
  
  const isEmbeddedTable = ['msoEmbeddedOLEObject'].includes(element.element_type_name || element.type || '');
  
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
  styleString += applyElementStyles(element.style || {});
  
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
  
  // 直接根据元素类型渲染，不再优先处理数据源配置元素
  if (data.chart_data && data.chart_data.type) {
    // 处理图表元素
    elementHTML += renderChartElement(element);
  } else {
    // 根据元素类型渲染
    const elementType = element.element_type_name || element.type;
    switch (elementType) {
      case 'msoTextBox':
      case 'msoAutoShape':
      case 'text':
        elementHTML += renderTextElement(element);
        break;
      case 'msoTable':
        elementHTML += renderTableElement(element);
        break;
      case 'msoEmbeddedOLEObject':
        elementHTML += renderOLEElement(element);
        break;
      case 'msoChart':
      case 'chart':
        elementHTML += renderChartElement(element);
        break;
      case 'msoPicture':
      case 'image':
        elementHTML += renderImageElement(element);
        break;
      case 'msoLine':
        // 为线条类型元素添加专门的渲染逻辑
        elementHTML += renderLineElement(element);
        break;
      default:
        elementHTML += renderUnknownElement(element);
        break;
    }
  }
  
  elementHTML += '</div>';
  return elementHTML;
}

// 应用元素样式
function applyElementStyles(style?: any): string {
  if (!style) return '';
  let styleStr = '';
  if (style?.font_family) styleStr += `font-family: '${style.font_family}', Arial, sans-serif; `;
  if (style?.font_size) styleStr += `font-size: ${style.font_size}; `;
  if (style?.color) styleStr += `color: ${style.color}; `;
  if (style?.background_color) styleStr += `background-color: ${style.background_color}; `;
  if (style?.font_style) styleStr += `font-style: ${style.font_style}; `;
  if (style?.font_weight) styleStr += `font-weight: ${style.font_weight}; `;
  if (style?.text_decoration) styleStr += `text-decoration: ${style.text_decoration}; `;
  if (style?.text_align) styleStr += `text-align: ${style.text_align}; `;
  return styleStr;
}

// 渲染文本框元素
function renderTextElement(element: Element): string {
  const data = element.data || {};
  const content = data.text_content || element.content || '';
  return `<div class="textbox">${content}</div>`;
}

// 渲染图片元素
function renderImageElement(element: Element): string {
  const data = element.data || {};
  const imageData = data.image_data || element.content || '';
  
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
function renderTableElement(element: Element): string {
  const data = element.data || {};
  if (data.table_data) {
    const tableOptions = {
      rowHeights: data.table_row_heights || [],
      colWidths: data.table_col_widths || [],
      mergedCells: data.merged_cells || [],
      activeCell: data.active_cell || '',
      isOLEObject: false
    };
    return generateTableHTML(data.table_data, tableOptions,element.id);
  } else {
    return '<div style="border: 1px dashed #ccc; padding: 10px; color: #666;">无表格数据</div>';
  }
}

// 渲染OLE元素
function renderOLEElement(element: Element): string {
  const data = element.data || {};
  // 优先检查ole_datas字段（OLE对象的专用数据字段）
  if (data.ole_datas && data.ole_datas.sheets && data.ole_datas.sheets.length > 0) {
    // 从ole_datas构建table_data格式和每个sheet的选项
    const tableData: Record<string, any> = {};
    const sheetOptions: Record<string, any> = {};
    
    data.ole_datas.sheets.forEach((sheet: any,index: number) => {
      if (sheet.data && Array.isArray(sheet.data)) {
        tableData[sheet.name] = sheet.data;
        // 为每个sheet保存自己的样式信息
        sheetOptions[sheet.name] = {
          rowHeights: sheet.row_heights || [],
          colWidths: sheet.col_widths || [],
          mergedCells: sheet.merged_cells || [],
          activeCell: '',
          isOLEObject: true
        };
        const active_cell=data.active_cell
        if (active_cell.sheet_name===sheet.name){
          sheetOptions[sheet.name].activeCell = active_cell;
          active_cell_dict[element.id]={index:index,active_cell:active_cell}
        }
      }
    });
    
    if (Object.keys(tableData).length > 0) {
      return generateTableHTML(tableData, sheetOptions,element.id);
    }
  }
  
  // 回退到检查table_data字段
  if (data.table_data) {
    const tableOptions = {
      rowHeights: data.table_row_heights || [],
      colWidths: data.table_col_widths || [],
      mergedCells: data.merged_cells || [],
      activeCell: '',
      isOLEObject: true
    };
    return generateTableHTML(data.table_data, tableOptions,element.id);
  }
  
  // 如果都没有数据，显示无数据提示
  return '<div style="border: 1px dashed #ff9900; padding: 10px; color: #ff9900;">OLE对象 - 无数据</div>';
}

// 渲染Excel数据源元素
// function renderExcelDataSourceElement(element: Element): string {
//   const data = element.data || {};
//   if (data.data_source_config) {
//     return `<div style="padding: 20px; text-align: center; color: #666;">
//               Excel数据源: ${data.data_source_config.data_source_name}<br>
//               工作表: ${data.data_source_config.excel_sheet_name}<br>
//               范围: ${data.data_source_config.excel_cell_range}
//             </div>`;
//   }
//   return '<div style="padding: 20px; text-align: center; color: #666;">Excel数据源元素</div>';
// }

// 生成表格HTML
function generateTableHTML(tableData: any, tableOptions: any = {},elementId: string = ''): string {  
  // 检查是否为多sheet情况
  if (Array.isArray(tableData)) {
    // 单一表格情况
    return generateSingleSheetHTML(tableData, tableOptions);
  } else {
    // 多sheet情况，添加tab切换
    const sheetNames = Object.keys(tableData);
    if (sheetNames.length > 0) {
      const tableId = elementId;
      let html = '<div class="table-container">';
      
      // 检查是否为OLE对象，动态设置overflow属性
      // 对于多sheet情况，tableOptions可能是一个包含每个sheet选项的对象
      const isOLEObject = (tableOptions.isOLEObject || (sheetNames.length > 0 && tableOptions[sheetNames[0]]?.isOLEObject)) || false;
      // 外部容器设置overflow: hidden，内部table-wrapper设置overflow: auto
      // 这样可以避免显示双重滚动条，只保留内部表格的滚动条
      const overflowStyle = 'hidden';
      
      html += `<div id="${tableId}" class="embedded-table-container" style="height: 100%; width: 100%; overflow: ${overflowStyle};">`;
      
      // 添加特殊样式
      html += `<style scoped>
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
               </style>`;
      
      // 检查是否为OLE对象，动态设置tab样式
      const tabsClass = isOLEObject ? 'sheet-tabs embedded-tabs' : 'sheet-tabs';
      
      // 添加sheet标签栏
      html += `<div class="${tabsClass}" style="display: flex; border-bottom: 1px solid #ccc; background: #f5f5f5;">`;
      sheetNames.forEach((sheetName, index) => {
        const isActive = index === 0;
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
          </div>`;
      });
      html += '</div>';
      
      // 添加sheet内容容器
      html += '<div class="sheet-contents" style="border: 1px solid #ccc; border-top: none;">';
      sheetNames.forEach((sheetName, index) => {
        const isActive = index === 0;
        // 对于多sheet情况，获取当前sheet的选项
        const currentSheetOptions = typeof tableOptions === 'object' && tableOptions[sheetName] ? tableOptions[sheetName] : tableOptions;
        html += `
          <div class="sheet-content" id="${tableId}_sheet_${index}" style="display: ${isActive ? 'block' : 'none'}; height: calc(100% - 30px);">
            ${generateSingleSheetHTML(tableData[sheetName], currentSheetOptions, `${tableId}_sheet_${index}`)}
          </div>`;
      });
      html += '</div>';
      
      html += '</div>';
      html += '</div>';
      return html;
    }
  }
  return '<div style="border: 1px dashed #ccc; padding: 10px; color: #666;">无表格数据</div>';
}



// 渲染表格单元格，处理样式和内容
function renderTableCell(cell: any): string {
  if (!cell) return '<td></td>';
  
  // 构建单元格样式
  let cellStyle = '';
  
  // 背景色
  if (cell.background_color) {
    cellStyle += `background-color: ${cell.background_color};`;
  }
  
  // 文字颜色
  if (cell.text_color) {
    cellStyle += `color: ${cell.text_color};`;
  }
  
  // 边框
  if (cell.border) {
    cellStyle += `border: ${cell.border};`;
  } else {
    // 默认边框样式
    cellStyle += `border: 1px solid #ddd;`;
  }
  
  // 水平对齐
  if (cell.horizontal_align) {
    const alignMap: Record<string, string> = {
      'left': 'left',
      'center': 'center',
      'right': 'right'
    };
    cellStyle += `text-align: ${alignMap[cell.horizontal_align] || 'left'};`;
  }
  
  // 垂直对齐
  if (cell.vertical_align) {
    const valignMap: Record<string, string> = {
      'top': 'top',
      'middle': 'middle',
      'bottom': 'bottom'
    };
    cellStyle += `vertical-align: ${valignMap[cell.vertical_align] || 'top'};`;
  }
  
  // 字体样式
  if (cell.font_name) {
    cellStyle += `font-family: ${cell.font_name};`;
  }
  
  if (cell.font_size) {
    cellStyle += `font-size: ${cell.font_size}px;`;
  }
  
  if (cell.font_bold) {
    cellStyle += 'font-weight: bold;';
  }
  
  if (cell.font_italic) {
    cellStyle += 'font-style: italic;';
  }
  
  if (cell.font_underline) {
    cellStyle += 'text-decoration: underline;';
  }
  
  // 处理单元格内容
  const cellContent = cell.text || cell.value || '';
  
  // 返回带样式的单元格HTML
  return `<td style="${cellStyle}">${cellContent}</td>`;
}

// 生成单个sheet的HTML
function generateSingleSheetHTML(sheetData: any[], tableOptions: any = {}, tableId?: string): string {
  if (!Array.isArray(sheetData) || sheetData.length === 0) {
    return '<div style="padding: 10px; color: #666;">无数据</div>';
  }
  
  const { rowHeights = [], colWidths = [], mergedCells = [], activeCell = '' } = tableOptions;
  
  // 生成列宽样式
  let colgroupHtml = '<colgroup>';
  if (Array.isArray(colWidths) && colWidths.length > 0) {
    colWidths.forEach(width => {
      colgroupHtml += `<col style="width: ${width}px;">`;
    });
  }
  colgroupHtml += '</colgroup>';
  
  // 生成表格ID，确保即使是单一表格也有ID
  const generatedTableId = tableId || 'table_' + (Math.floor(Math.random() * 1000));
  
  // 移除data-active-cell属性，改为使用performImmediateScroll方法处理滚动
  const dataActiveCellAttr = '';
  
  let html = `<div class="table-wrapper" style="height: 100%; width: 100%; overflow: auto;">
                <table id="${generatedTableId}_table"${dataActiveCellAttr} style="border-collapse: collapse; table-layout: fixed;">`;
  
  html += colgroupHtml;
  
  let rowIndex = 0;
  sheetData.forEach((row: any) => {
    // 应用行高
    const rowHeight = Array.isArray(rowHeights) && rowHeights[rowIndex] ? rowHeights[rowIndex] : 'auto';
    html += `<tr style="height: ${rowHeight}px;">`;
    
    if (Array.isArray(row)) {
      let colIndex = 0;
      row.forEach((cell: any) => {
        // 检查当前单元格是否需要跳过（已被合并）
        let shouldSkip = false;
        for (const mc of mergedCells) {
          // 确保mc.start和mc.end存在且为字符串
          if (mc.start && mc.end && typeof mc.start === 'string' && typeof mc.end === 'string') {
            const [startRow, startCol] = mc.start.split(',').map(Number);
            const [endRow, endCol] = mc.end.split(',').map(Number);
            // 如果当前单元格在合并范围内但不是起始单元格，则跳过
            if (rowIndex > startRow && rowIndex <= endRow && colIndex > startCol && colIndex <= endCol) {
              shouldSkip = true;
              break;
            }
          }
        }
        
        if (shouldSkip) {
          colIndex++;
          return;
        }
        
        // 检查当前单元格是否是合并单元格的起始
        let rowspan = 1;
        let colspan = 1;
        for (const mc of mergedCells) {
          // 确保mc.start和mc.end存在且为字符串
          if (mc.start && mc.end && typeof mc.start === 'string' && typeof mc.end === 'string') {
            const [startRow, startCol] = mc.start.split(',').map(Number);
            const [endRow, endCol] = mc.end.split(',').map(Number);
            if (rowIndex === startRow && colIndex === startCol) {
              rowspan = endRow - startRow + 1;
              colspan = endCol - startCol + 1;
              break;
            }
          }
        }
        
        // 渲染单元格，参考TemplateEditor副本中的实现
        let cellHTML = renderTableCell(cell);
        
        // 如果是合并单元格，添加rowspan和colspan属性
        if (rowspan > 1 || colspan > 1) {
          cellHTML = cellHTML.replace('<td', `<td rowspan="${rowspan}" colspan="${colspan}"`);
        }
        
        // 如果是活动单元格，添加特殊样式
        let isActive = false;
        if (activeCell) {
          if (typeof activeCell === 'string') {
            isActive = activeCell === `${rowIndex},${colIndex}`;
          } else if (typeof activeCell === 'object') {
            isActive = activeCell.row === rowIndex && activeCell.col === colIndex;
          }
        }
        if (isActive) {
          cellHTML = cellHTML.replace('style="', 'style="border: 2px solid #1890ff;');
        }
        
        html += cellHTML;
        colIndex++;
      });
    } else {
      // 处理row不是数组的情况，参考TemplateEditor副本中的实现
      html += `<td>${String(row)}</td>`;
    }
    
    html += '</tr>';
    rowIndex++;
  });
  
  html += '</table></div>';
  
  return html;
}

// 渲染图表元素
function renderChartElement(element: Element): string {
  const chartId = 'chart-' + (element.id || Math.floor(Math.random() * 1000));
  
  let html = `<div class="chart-container" style="width: ${element.position?.width}px; height: ${element.position?.height}px; position: relative;">
      <canvas id="${chartId}" style="width: 100%; height: 100%;"></canvas>
    </div>`;
  
  // 添加图表初始化脚本占位符
  html += `<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #999; font-size: 14px;">
        图表元素
      </div>`;
  
  return html;
}

// 渲染线条元素
function renderLineElement(element: Element): string {
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
function renderUnknownElement(element: Element): string {
  const data = element.data || {};
  const typeName = element.element_type_name || element.type || '未知';
  const content = data.text_content || element.content || '';
  return `<div style="border: 1px dashed #ccc; padding: 5px; font-size: 12px; color: #666;">${typeName.toUpperCase()}: ${content}</div>`;
}
</script>

<style scoped>
/* 预览面板样式 */
.preview-panel {
  width: 72%;
  height: 100%;
  border-right: 1px solid #eee;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 15px;
  border-bottom: 1px solid #eee;
  background-color: white;
  flex-shrink: 0;
}

.preview-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.preview-content {
  overflow: auto;
  flex: 1;
}

.presentation-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  padding:10px 0px;
}

.loading-message {
  text-align: center;
  padding: 50px;
  color: #666;
  font-size: 16px;
}

/* 固定在底部的信息面板 */
.info-panel {
  background-color: white;
  padding: 10px 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: flex-start;
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
}

.info-panel p {
  margin: 0;
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

/* 幻灯片样式 */
.slide {
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
}

.slide:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.slide-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* 元素样式 */
.element {
  position: absolute;
  z-index: 2;
  transition: all 0.2s ease;
}

.element.selected {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .preview-panel {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .preview-panel {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid #eee;
  }
}
</style>