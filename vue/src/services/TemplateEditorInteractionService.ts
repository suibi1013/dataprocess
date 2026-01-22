import type { PPTConfig, Element } from './TemplateEditorService';
import { httpClient } from './httpClient';
import type { DataSelection } from '@/types/dataExtraction';

// 扩展Window接口，添加Chart属性
declare global {
  interface Window {
    Chart: any;
  }
  
  // 扩展HTMLCanvasElement接口，添加chartInstance属性
  interface HTMLCanvasElement {
    chartInstance: any;
  }
}

/**
 * 模板编辑器交互服务，处理模板编辑器的各种交互逻辑
 */
export class TemplateEditorInteractionService {
  /**
   * 更新Excel元素数据
   * @param element 元素对象
   * @param container 容器元素
   * @param dataSources 数据源列表
   * @param selectedDataSource 选中的数据源ID
   * @param showToastMessage 显示Toast消息的方法
   */
  async updateExcelElementData(
    element: Element, 
    container: HTMLElement, 
    dataSources: any[], 
    selectedDataSource: string, 
    showToastMessage: (_message: string, _type?: 'success' | 'error' | 'info') => void
  ) {
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
      const dataSourceObj = dataSources.find(source => source.name === dataSourceConfig.data_source_name);
      if (!dataSourceObj) return;
      
      const response = await httpClient.get(`/datasource/${encodeURIComponent(dataSourceObj.id)}/data`);
      
      if (response.success && response.data && response.data.data) {
        // 恢复原始内容
        targetContainer.innerHTML = originalContent;
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
      showToastMessage('数据更新失败，请刷新页面重试', 'error');
    }
  }

  /**
   * 重新初始化页面上所有的图表
   * @param pptConfig PPT配置对象
   */
  reinitializeCharts(pptConfig: PPTConfig | null) {
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
        if (pptConfig && pptConfig.slides) {
          for (const slide of pptConfig.slides) {
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

  /**
   * 更新预览面板中的元素数据
   * @param currentSlideIndex 当前幻灯片索引
   * @param selectedElementIndex 选中的元素索引
   * @param getCurrentSlideElements 获取当前幻灯片元素的方法
   * @param updateExcelElementData 更新Excel元素数据的方法
   */
  updatePreviewPanelElements(
    currentSlideIndex: number, 
    selectedElementIndex: number, 
    getCurrentSlideElements: () => Element[],
    updateExcelElementData: (_element: Element, _container: HTMLElement) => Promise<void>
  ) {
    // 检查是否有选中的元素
    const elements = getCurrentSlideElements();
    if (selectedElementIndex >= 0 && selectedElementIndex < elements.length) {
      const element = elements[selectedElementIndex];
      const slidePreview = document.querySelector(`#slide_${currentSlideIndex}`);
      
      if (slidePreview) {
        // 查找对应元素的DOM容器
        const elementId = element.id || `element-${currentSlideIndex}-${selectedElementIndex}`;
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
              updateExcelElementData(element, elementContainer);
            }
          }
        }
      }
    }
  }

  /**
   * 动态加载Chart.js库
   * @param pptConfig PPT配置对象
   * @param reinitializeCharts 重新初始化图表的方法
   * @param showToastMessage 显示Toast消息的方法
   */
  async loadChartJs(
    pptConfig: PPTConfig | null,
    reinitializeCharts: (_pptConfig: PPTConfig | null) => void,
    showToastMessage: (_message: string, _type?: 'success' | 'error' | 'info') => void
  ) {
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
        if (pptConfig && pptConfig.slides) {
          setTimeout(() => {
            reinitializeCharts(pptConfig);
          }, 0);
        }
      }
    } catch (error) {
      console.error('Chart.js 加载失败:', error);
      showToastMessage('图表库加载失败，图表可能无法显示', 'error');
    }
  }

  /**
   * 将数据转换为图表格式
   * @param newData 新数据
   * @param existingChartData 现有图表数据
   * @returns 转换后的图表数据
   */
  convertDataToChartFormat(newData: any, existingChartData: any): any {
    if (!existingChartData) {
      throw new Error('现有图表数据不存在');
    }
    
    // 复制现有图表配置
    const chartData = JSON.parse(JSON.stringify(existingChartData));
    
    // 将新数据转换为二维数组
    if (Array.isArray(newData) || typeof newData === 'object') {
      // 实际项目中需要实现数据到图表格式的转换逻辑
      // 这里只是保留了现有配置
    }
    
    return chartData;
  }

  /**
   * 替换元素数据为选中的数据区域
   * @param selection 数据选择对象
   * @param selectedDataSource 选中的数据源ID
   * @param currentSelectedSheet 当前选中的工作表
   * @param getCurrentSlideElements 获取当前幻灯片元素的方法
   * @param selectedElementIndex 选中的元素索引
   * @param showToastMessage 显示Toast消息的方法
   * @param selectedData 已提取的数据（可选）
   */
  async replaceElementDataWithSelectedRange(
    selection: DataSelection,
    selectedDataSource: string,
    currentSelectedSheet: string,
    getCurrentSlideElements: () => Element[],
    selectedElementIndex: number,
    showToastMessage: (_message: string, _type?: 'success' | 'error' | 'info') => void,
    selectedData?: any
  ) {
    try {
      const elements = getCurrentSlideElements();
      if (selectedElementIndex < 0 || selectedElementIndex >= elements.length) {
        throw new Error('请先选择一个元素');
      }
      
      const element = elements[selectedElementIndex];
      
      // 请求数据源的实际数据
      showToastMessage('正在获取选中数据区域的数据...', 'info');
      
      // 如果提供了已提取的数据，直接使用
      let newData = selectedData;
      let table_row_heights: number[] = [];
      let table_col_widths: number[] = [];
      
      // 如果没有提供数据，尝试从API获取（保留原有逻辑，作为备份）
      if (!newData) {
        const response = await httpClient.post(`/datasource/${encodeURIComponent(selectedDataSource)}/range`, {
          sheet_name: currentSelectedSheet,
          cell_range: `${selection.start_column}${selection.start_row}:${selection.end_column}${selection.end_row}`
        });
        
        if (!response.success) {
          throw new Error(response.error || '获取数据失败');
        }
        
        newData = response.data.table_data;
        table_row_heights = response.data.table_row_heights || [];
        table_col_widths = response.data.table_col_widths || [];
      }
      
      if (!newData || (!Array.isArray(newData) && typeof newData !== 'object')) {
        throw new Error('返回的数据格式不正确');
      }
      
      // 根据元素类型更新数据
      if (!element.data) {
        element.data = {};
      }
      
      // 根据元素类型处理数据
      switch (element.element_type_name) {
        case 'msoTable':
          // 对于表格元素，更新 table_data
          if (Array.isArray(newData)) {
            element.data.table_data = newData;
          } else {
            // 如果是对象格式（多工作表），只取当前工作表的数据
            element.data.table_data = newData[currentSelectedSheet] || newData;
          }
          // 保存行列尺寸信息
          if (table_row_heights) element.data.table_row_heights = table_row_heights;
          if (table_col_widths) element.data.table_col_widths = table_col_widths;
          break;
          
        case 'msoEmbeddedOLEObject':
        case 'msoEmbeddedOLEObjectWithSheets':
          // 对于OLE对象，更新 ole_datas 和 table_data
          if (Array.isArray(newData)) {
            // 单工作表数据
            element.data.table_data = { [currentSelectedSheet]: newData };
            element.data.ole_datas = {
              sheets: [{
                name: currentSelectedSheet,
                data: newData
              }]
            };
          } else if (typeof newData === 'object') {
            // 多工作表数据
            element.data.table_data = newData;
            const sheets = Object.keys(newData).map(sheetName => ({
              name: sheetName,
              data: newData[sheetName]
            }));
            element.data.ole_datas = { sheets };
          }
          break;
          
        case 'msoChart':
          // 对于图表元素，需要将数据转换为Chart.js格式
          try {
            const chartData = this.convertDataToChartFormat(newData, element.data.chart_data);
            element.data.chart_data = chartData;
          } catch (chartError) {
            
            // 如果转换失败，保存原始数据作为表格数据
            element.data.table_data = Array.isArray(newData) ? newData : newData[currentSelectedSheet] || newData;
          }
          break;
          
        case 'msoTextBox':
        case 'msoAutoShape':
          // 对于文本元素，将数据转换为文本
          {
            let textContent = '';
            if (Array.isArray(newData) && newData.length > 0) {
              if (Array.isArray(newData[0])) {
                // 二维数组，取第一个单元格
                textContent = String(newData[0][0] || '');
              } else {
                // 一维数组，取第一个元素
                textContent = String(newData[0] || '');
              }
            } else if (typeof newData === 'object' && newData !== null) {
              // 对象格式，尝试获取第一个值
              const firstValue = Object.values(newData)[0];
              if (Array.isArray(firstValue) && firstValue.length > 0) {
                textContent = String(firstValue[0] || '');
              } else {
                textContent = String(firstValue || '');
              }
            } else {
              textContent = String(newData || '');
            }
            element.data.text_content = textContent;
          }
          break;
          
        default:
          // 对于其他类型，尝试保存为表格数据
          if (Array.isArray(newData)) {
            element.data.table_data = newData;
          } else {
            element.data.table_data = newData[currentSelectedSheet] || newData;
          }
          break;
      }
    } catch (error) {
      console.error('替换元素数据失败:', error);
      throw error;
    }
  }
}