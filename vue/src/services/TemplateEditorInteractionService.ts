import type { PPTConfig, Element } from './TemplateEditorService';

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
   */
  updatePreviewPanelElements(
    currentSlideIndex: number, 
    selectedElementIndex: number, 
    getCurrentSlideElements: () => Element[]
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
}