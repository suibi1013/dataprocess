// 数据处理相关的组合式函数
// 管理数据处理模态框的状态、画布操作、指令执行等逻辑

import { ref, reactive, computed, nextTick } from 'vue';
import { Graph, Node, Selection, Clipboard, Keyboard, Scroller, History } from '@antv/x6';

// 扩展Window接口声明
declare global {
  interface Window {
    createConnection?: (_sourceNodeId: string, _sourcePortId: string, _targetNodeId: string, _targetPortId: string) => string | null;
  }
}

// 添加全局ResizeObserver错误处理，解决ResizeObserver loop completed with undelivered notifications错误
if (typeof window !== 'undefined' && window.ResizeObserver) {
  const originalResizeObserver = window.ResizeObserver;
  window.ResizeObserver = class ResizeObserver extends originalResizeObserver {
    // eslint-disable-next-line no-unused-vars
    constructor(callback: (entries: ResizeObserverEntry[], observer: ResizeObserver) => void) {
      super((_entries, _observer) => {
        // 使用requestAnimationFrame避免同步执行导致的循环
        requestAnimationFrame(() => {
          try {
            callback(_entries, _observer);
          } catch (error) {
            // 捕获并忽略ResizeObserver循环错误
            console.warn('ResizeObserver callback error:', error);
          }
        });
      });
    }
  };
}
import { dataProcessService } from '@/services/dataProcessService';
import { instructionService } from '@/services/instructionService';
import type { DataProcessModalState } from '@/types/dataSource';
import type {
  InstructionCategory,
  Instruction,
  CanvasNode,
  InstructionExecutionResult,
  DataProcessFlow
} from '@/types/instruction';

// 数据源信息缓存（避免重复API调用）
export const dataSourceInfoCache = ref<Map<string, any>>(new Map());

// 当前加载的流程ID
const currentFlowId = ref<string | null | undefined>(null);
// 当前加载的流程信息（保存名称和描述）
const currentFlowInfo = ref<{ name: string; description: string } | null>(null);

/**
 * 数据处理组合式函数 - 单例模式实现
 */

// 单例实例缓存
let instance: any = null;

/**
 * 获取数据处理组合式函数的单例实例
 */
export function useDataProcess() {
  // 如果实例不存在，则创建新实例
  if (!instance) {
    // 创建新实例
    instance = createDataProcessInstance();
  }

  // 返回单例实例
  return instance;
}

/**
 * 创建数据处理实例的内部函数
 */
function createDataProcessInstance() {
  // 创建全局tooltip容器（只需一次）
  let globalTooltip: HTMLDivElement | null = null;

  // 初始化全局tooltip
  const initGlobalTooltip = () => {
    if (!globalTooltip) {
      globalTooltip = document.createElement('div');
      Object.assign(globalTooltip.style, {
        position: 'absolute',
        display: 'none',
        background: '#f5f7fa',
        color: '#2c3e50',
        borderRadius: '6px',
        padding: '10px 12px',
        fontSize: '13px',
        pointerEvents: 'auto',
        zIndex: 9999,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        border: '1px solid #e1e4e8',
        width: '280px',
        maxWidth: '350px',
        maxHeight: '200px',
        overflowY: 'auto',
        overflowX: 'hidden',
        wordWrap: 'break-word',
        wordBreak: 'break-all',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        lineHeight: '1.5'
      });

      // 添加tooltip鼠标移出事件监听器
      globalTooltip.addEventListener('mouseleave', () => {
        // 当鼠标移出tooltip时隐藏它
        globalTooltip!.style.display = 'none';
      });

      document.body.appendChild(globalTooltip);
    }
  };

  // ==================== 响应式状态 ====================

  // 模态框状态
  const modalState = reactive<DataProcessModalState>({
    visible: false,
    loading: false,
    saving: false,
    executing: false,
    dataLoading: false, // 新增：数据源数据加载状态
    instructions: [],
    selectedNodes: [],
    executionProgress: {
      visible: false,
      current: 0,
      total: 0,
      stepName: ''
    }
  });

  // 选中的节点状态
  const selectedNode = ref<Node | null>(null);
  // 选中的边状态
  const selectedEdge = ref<any>(null);
  // 是否有选中的节点
  const hasSelectedNodes = ref(false);

  // 指令列表
  const instructionCategories = ref<InstructionCategory[]>([]);
  const instructionLoading = ref(false);
  // 控制节点描述信息的显示状态
  const showNodeDescriptions = ref(true);

  // 控制节点提示框的显示状态
  const showNodeTooltips = ref(false);

  // 选择模式状态：true为框选模式，false为平移模式
  const isRubberbandMode = ref(false);

  // 节点描述编辑器状态
  const nodeDescriptionEditor = reactive({
    visible: false,
    node: null as Node | null,
    description: ''
  });

  // 画布实例
  const canvasGraph = ref<Graph | null>(null);
  const canvasContainer = ref<HTMLElement | null>(null);

  // 序号标识与节点id的映射字典
  const nodeIdToSerialMap = ref<Map<string, number>>(new Map());
  // 节点序号计数器
  const serialCounter = ref(1);

  // 拖拽事件监听器引用，用于清理
  const dragEventListeners = ref<{
    dragover?: (_e: DragEvent) => void;
    dragleave?: (_e: DragEvent) => void;
    drop?: (_e: DragEvent) => void;
  }>({});

  // 工具栏引用，用于清理
  const toolbars = ref<Array<HTMLElement>>([]);

  // 参数面板状态
  const paramsPanel = reactive<any>({
    visible: false,
    collapsed: false,
    selectedNode: null,
    selectedEdge: null,
    params: {},
    nodeData: null,
    paramFormItems: []
  });

  // 执行状态
  const executionState = reactive({
    progress: 0,
    currentStep: '',
    results: [] as InstructionExecutionResult[],
    error: null as string | null
  });

  // ==================== 计算属性 ====================

  const isExecuting = computed(() => modalState.executing);

  // ==================== 模态框控制 ====================

  /**
   * 显示数据处理模态框
   */
  const showDataProcessModal = async (processId?: string) => {
    modalState.visible = true;
    modalState.loading = true;

    try {
      // 每次打开模态框都重新请求指令列表数据
      await loadInstructionList();

      // 先确保画布初始化完成
      await nextTick();
      if (!canvasGraph.value) {
        await initializeCanvas();
        // 再等待一次确保画布完全初始化
        await nextTick();
      }

      // 确保画布已初始化后再加载流程（重要：避免时序问题）
      if (processId && canvasGraph.value) {
        await loadProcessById(processId);
      }

    } catch (error) {
      console.error('❌ 初始化数据处理模态框失败:', error);
    } finally {
      modalState.loading = false;
    }
  };

  /**
   * 根据流程ID加载流程并绘制到画布
   */
  const loadProcessById = async (processId: string) => {
    try {
      modalState.loading = true;

      // 获取流程配置
      const response = await dataProcessService.getProcessById(processId);
      if (response.success && response.data) {
        // 直接使用返回的流程对象
        currentFlowId.value = response.data.id || null;
        // 保存流程名称和描述信息
        currentFlowInfo.value = {
          name: response.data.name || '',
          description: response.data.description || ''
        };

        // 验证流程数据的完整性
        if (!response.data.nodes) {
          console.warn(`⚠️ 流程 ${response.data.name || response.data.id} 缺少节点信息`);
          response.data.nodes = [];
        }

        if (!response.data.edges) {
          console.warn(`⚠️ 流程 ${response.data.name || response.data.id} 缺少边信息`);
          response.data.edges = [];
        }

        // 确保画布已初始化
        if (!canvasGraph.value) {
          console.warn('🎨 画布未初始化，先初始化画布');
          await initializeCanvas();
          await nextTick();
        }

        if (canvasGraph.value) {
          await loadProcessToCanvas(response.data);
          // 为加载的节点添加连接桩显示控制事件
          addPortEventsToAllNodes();
        } else {
          console.error('❌ 画布初始化失败，无法绘制流程');
        }
      } else if (response.success && !response.data) {
        console.warn(`ℹ️ 未找到流程 ${processId} 的配置`);
      } else {
        console.error(`❌ API返回错误: ${response.message || '未知错误'}`);
      }
    } catch (error) {
      console.error('❌ 加载流程失败:', error);
    } finally {
      modalState.loading = false;
    }
  };

  /**
   * 隐藏数据处理模态框
   */
  const hideDataProcessModal = () => {
    modalState.visible = false;
    // 完全清理画布资源，避免事件监听器和Graph实例残留导致的错误
    cleanupCanvas();
    resetExecutionState();
    hideParamsPanel();

    // 清理选中的节点引用避免 vnode 错误
    if (selectedNode.value) {
      try {
        selectedNode.value = null;
      } catch (error) {
        console.warn('清理选中节点引用时出现错误:', error);
      }
    }
  };

  /**
   * 完全重置模态框（包括清理画布）
   */
  const resetDataProcessModal = () => {
    modalState.visible = false;
    cleanupCanvas();
    resetExecutionState();
    hideParamsPanel();
  };

  // ==================== 指令管理 ====================

  /**
   * 加载指令列表
   * 优化：一次性获取分类和指令数据，避免重复调用API
   */
  const loadInstructionList = async () => {
    if (instructionLoading.value) return;

    instructionLoading.value = true;
    try {
      // 使用新的统一接口一次性获取指令分类和指令数据
      const response = await instructionService.getInstructionCategoriesWithInstructionsActive();

      if (response.success && response.data) {
        instructionCategories.value = response.data;
      } else {
        throw new Error(response.message || '获取指令分类和指令失败');
      }
    } catch (error) {
      console.error('加载指令列表失败:', error);
      instructionCategories.value = [];
    } finally {
      instructionLoading.value = false;
    }
  };

  // ==================== 画布管理 ====================

  /**
   * 调整画布大小
   */
  const resizeCanvas = () => {
    setTimeout(() => {
      const container = document.getElementById('data-process-canvas-container');
      if (canvasGraph.value && container) {
        const rect = container.getBoundingClientRect()
        // canvasGraph.value?.zoomTo(1);
        // canvasGraph.value?.centerContent();
        canvasGraph.value.resize(rect.width, rect.height);

      }
    }, 200);
  };

  /**
   * 初始化画布
   */
  const initializeCanvas = async () => {
    cleanupCanvas();
    await nextTick();

    // 重置节点序号映射和计数器
    nodeIdToSerialMap.value.clear();
    serialCounter.value = 1;

    const container = document.getElementById('data-process-canvas');
    if (!container) {
      console.error('画布容器未找到');
      return;
    }

    canvasContainer.value = container;
    container.innerHTML = '';

    // 创建X6图实例
    canvasGraph.value = new Graph({
      container: container,
      width: container.clientWidth,
      height: container.clientHeight,
      grid: {
        size: 10,
        visible: true,
        type: 'dot',
        args: {
          color: '#e0e0e0',
          thickness: 1
        }
      },
      background: {
        color: '#f9f9f9'
      },

      // 确保工具可交互

      connecting: {
        router: {
          name: 'manhattan',
          args: {
            padding: 10,
            startDirections: ['right', 'left', 'top', 'bottom'],
            endDirections: ['left', 'right', 'bottom', 'top']
          }
        },
        connector: {
          name: 'rounded',
          args: { radius: 15 }
        },
        // 使用center锚点类型
        anchor: 'center',
        // 简化的连接点计算函数
        connectionPoint: { name: 'anchor' },

        allowBlank: false,
        allowLoop: false,
        allowNode: false,
        allowEdge: false,
        allowPort: true,
        allowMulti: false,
        highlight: true,
        snap: {
          radius: 20
        },
        createEdge() {
          return this.createEdge({
            shape: 'edge',
            attrs: {
              line: {
                stroke: '#3199FF',
                strokeWidth: 2,
                strokeDasharray: '0',
                targetMarker: {
                  name: 'classic',
                  width: 12,
                  height: 12,
                  fill: '#3199FF',
                  stroke: '#3199FF'
                }
              }
            },
            router: {
              name: 'manhattan',
              args: {
                padding: 10,
                startDirections: ['right', 'left', 'top', 'bottom'],
                endDirections: ['left', 'right', 'bottom', 'top']
              }
            },
            connector: {
              name: 'rounded',
              args: { radius: 15 }
            },
            zIndex: 0
          });
        },
        validateConnection({ sourceCell, targetCell }) {
          // 根据箭头方向确定输入输出关系，只检查自连接
          if (sourceCell && targetCell && sourceCell.id === targetCell.id) {
            // 不允许自连接
            return false;
          }
          return true;
        }
      },
      interacting: {
        nodeMovable: true,
        magnetConnectable: true,
        // 允许拖动边
        edgeMovable: true,
        // 允许移动边上的顶点
        vertexMovable: true,
        arrowheadMovable: true,
      },
      mousewheel: {
        enabled: true,
        modifiers: ['ctrl', 'meta'],
        minScale: 0.5,
        maxScale: 2
      },
      panning: {
        enabled: false
      },
      highlighting: {
        magnetAdsorbed: {
          name: 'stroke',
          args: {
            attrs: {
              fill: '#5F95FF',
              stroke: '#5F95FF',
              strokeWidth: 2,
              r: 8
            }
          }
        },
        magnetAvailable: {
          name: 'stroke',
          args: {
            attrs: {
              fill: '#47C769',
              stroke: '#47C769',
              strokeWidth: 2,
              r: 8
            }
          }
        }
      }
    });
    // 启用Selection插件，内置了Rubberband功能
    canvasGraph.value!.use(
      new Selection({
        enabled: true,
        multiple: true,
        showNodeSelectionBox: false, // 禁用虚线选择框，避免遮挡连接桩
        rubberband: isRubberbandMode.value, // 根据模式设置框选功能
      })
    );
    // 启用Clipboard插件，内置了复制粘贴功能
    canvasGraph.value!.use(
      new Clipboard({
        enabled: true,
      }),
    );
    // 启用Keyboard插件，用于处理键盘快捷键
    canvasGraph.value!.use(
      new Keyboard({
        enabled: true,
      }),
    );
    // 启用Scroller插件，提供画布滚动能力
    canvasGraph.value!.use(
      new Scroller({
        enabled: true,
        pageVisible: true,
        pageBreak: false,
        pannable: true,
        autoResize: true,
      }),
    );
    // 启用History插件，提供撤销重做功能
    canvasGraph.value!.use(
      new History({
        enabled: true,
        ignoreAdd: false,
        ignoreRemove: false,
      }),
    );
    bindCanvasEvents();
    initializeCanvasDrop();
    // 初始化画布模式为平移模式，因为toggleSelectionMode会切换模式，这里设置为true
    isRubberbandMode.value = true;
    toggleSelectionMode();
    resizeCanvas();
  };
  const removeAllNodesPorts = () => {
    // 隐藏所有节点的连接桩 - 解决启用Selection插件后点击空白处连接桩无法隐藏的问题
    const allNodes = canvasGraph.value!.getNodes();
    allNodes.forEach((node: any) => {
      const ports = node.getPorts();
      ports.forEach((port: any) => {
        node.portProp(port.id, `attrs/circle/opacity`, 0);
      });
    });
  };

  /**
   * 绑定画布事件
   */
  const bindCanvasEvents = () => {
    if (!canvasGraph.value) return;

    // 初始化全局tooltip
    initGlobalTooltip();

    // 节点双击事件 - 打开参数面板
    canvasGraph.value.on('node:dblclick', ({ node }) => {
      const nodeData = node.getData();
      if (nodeData) {
        selectedNode.value = node;
        showParamsPanel(node);
      }
    });

    // 监听Selection插件的选择变化事件
    const selectionPlugin = canvasGraph.value.getPlugin('selection') as Selection;
    if (selectionPlugin) {
      selectionPlugin.on('selection:changed', (e: { selected?: any[] }) => {
        const selectedCells = e.selected || [];
        // 更新选中状态
        hasSelectedNodes.value = selectedCells.length > 0;
      });
    }

    // 节点鼠标悬停事件 - 显示连接桩和节点信息提示
    canvasGraph.value.on('node:mouseenter', ({ node }) => {
      if (node) {
        // 显示连接桩
        const ports = node.getPorts();
        ports.forEach((port: any) => {
          node.portProp(port.id, `attrs/circle/opacity`, 1);
        });
        const nodeSize = node.getSize();
        const nodeData = node.getData();

        // 添加编辑按钮
        node.addTools([
          {
            name: 'button',
            args: {
              markup: [
                {
                  tagName: 'circle',
                  selector: 'button',
                  attrs: {
                    r: 8,
                    fill: '#1890ff',
                    stroke: '#fff',
                    strokeWidth: 1,
                    cursor: 'pointer',
                    visibility: 'visible',
                    opacity: 1,
                    pointerEvents: 'visiblePainted'
                  },
                },
                {
                  tagName: 'text',
                  selector: 'icon',
                  textContent: '📝', // 或者用 '✏'
                  attrs: {
                    y: '4',
                    textAnchor: 'middle',
                    textVerticalAnchor: 'middle',
                    fontSize: 12,
                    fill: '#666',
                    pointerEvents: 'none', // 防止文字拦截点击事件
                  },
                },
              ],
              x: 0,
              y: 0,
              offset: { x: nodeSize.width - 4, y: 4 }, // 调整位置，确保按钮在节点内
              // 点击事件处理
              onClick: () => {
                showNodeDescriptionEditor(node);
              }
            },
          },
        ]);

        // 使用全局tooltip显示节点信息
        if (globalTooltip && showNodeTooltips.value) {
          // 格式化参数信息 - 每个参数作为单独的表单项显示
          let paramsHtml = '';
          if (nodeData.params && typeof nodeData.params === 'object' && Object.keys(nodeData.params).length > 0) {
            // 处理参数值中的节点id，替换为序号标识
            const processParamValue = (value: any) => {
              if (typeof value === 'string') {
                // 使用正则表达式匹配 {{节点id.节点参数名}} 格式，确保匹配下划线
                return value.replace(/\{\{([\w_]+)\.(\w+)\}\}/g, (match, nodeId, paramName) => {
                  // 从映射字典中获取序号标识
                  const serialNumber = nodeIdToSerialMap.value.get(nodeId);
                  if (serialNumber) {
                    // 替换为【序号标识.节点参数名】格式
                    return `{{#${serialNumber}.${paramName}}}`;
                  }
                  // 如果没有找到对应的序号，保持原样
                  return match;
                });
              }
              return value;
            };

            // 为每个参数创建单独的表单项元素，确保每行显示一个参数
            paramsHtml = Object.entries(nodeData.params)
              .map(([key, value]) => {
                // 处理参数值
                const processedValue = processParamValue(value);
                return `
                  <div style="margin-bottom: 3px; display: flex; align-items: flex-start;">
                    <div style="font-weight: 500; color: #2c5282; font-size: 12px; margin-right: 6px; min-width: 60px;">${key}:</div>
                    <div style="color: #4a5759; font-size: 12px; flex: 1; word-break: break-all;">${JSON.stringify(processedValue)}</div>
                  </div>
                `;
              })
              .join('');
          } else {
            paramsHtml = '<div style="color: #2d3748; font-size: 12px;">无参数</div>';
          }

          // 设置提示内容 - 优化排版和视觉效果，每个表单项占一行
          globalTooltip.innerHTML =
            '<div style="font-size: 14px; margin-bottom: 6px; font-weight: 600; padding-bottom: 6px; border-bottom: 1px solid #e1e4e8; color: #2c5282;">节点信息</div>' +
            '<div style="margin-bottom: 8px;"><strong style="color: #2c5282;">ID:</strong> <span style="color: #4a5759;">' + node.id + '</span></div>' +
            '<div style="margin-bottom: 4px;"><strong style="color: #2c5282;">参数:</strong></div>' +
            '<div style="margin-top: 4px; background: #f8f9fa; padding: 6px 8px; border-radius: 4px;">' +
            paramsHtml +
            '</div>';

          // 获取节点在画布坐标系中的包围盒
          const bbox = node.getBBox();
          console.log('bbox', bbox)
          // 将画布坐标转换为页面坐标（处理缩放和平移）
          const clientRect = canvasGraph.value!.localToClient(bbox);

          // 计算右上角位置并添加偏移
          const tooltipX = clientRect.x + clientRect.width + 8; // 右侧偏移8px
          const tooltipY = clientRect.y - 4; // 向上微调4px

          // 设置位置并显示
          globalTooltip.style.left = `${tooltipX}px`;
          globalTooltip.style.top = `${tooltipY}px`;
          globalTooltip.style.display = 'block';
        }
      }
    });

    // 节点鼠标移出事件 - 隐藏连接桩，但保持tooltip显示
    canvasGraph.value.on('node:mouseleave', ({ node }) => {
      if (node) {
        // 隐藏连接桩
        const ports = node.getPorts();
        ports.forEach((port: any) => {
          node.portProp(port.id, `attrs/circle/opacity`, 0);
        });
        node.removeTools(); // 删除所有的工具

        // 不再在这里隐藏tooltip，让tooltip在鼠标移出它自己时隐藏
      }
    });

    // 节点单击事件 - 支持按住Ctrl键进行多选
    canvasGraph.value.on('node:click', ({ node, e }) => {
      // 恢复之前选中边的默认样式
      if (selectedEdge.value) {
        selectedEdge.value.attr('line/stroke', '#1890ff');
        selectedEdge.value.attr('line/strokeWidth', 2);
        // 恢复默认箭头样式
        selectedEdge.value.attr('line/targetMarker', {
          name: 'classic',
          width: 10,
          height: 6,
          fill: '#666',
          stroke: '#666'
        });
        selectedEdge.value = null;
      }

      if (node) {
        // 判断是否按住了Ctrl键（多选）
        const isMultiSelect = e.ctrlKey || e.metaKey;

        if (isMultiSelect) {
          // 多选模式：切换节点的选中状态
          const currentStroke = node.attr('body/stroke');
          const isSelected = currentStroke === '#FF4500';

          if (isSelected) {
            // 取消选中
            node.attr('body/stroke', '#1890ff');
            node.attr('body/strokeWidth', 1);
            // 如果是当前单选节点，清空单选状态
            if (selectedNode.value === node) {
              selectedNode.value = null;
            }
          } else {
            // 添加选中
            node.attr('body/stroke', '#FF4500');
            node.attr('body/strokeWidth', 3);
            // 更新单选节点为当前节点（保持与原有逻辑兼容）
            selectedNode.value = node;
          }
        } else {
          // 单选模式：先恢复所有节点的默认样式
          const allNodes = canvasGraph.value!.getNodes();
          allNodes.forEach((n: any) => {
            n.attr('body/stroke', '#1890ff');
            n.attr('body/strokeWidth', 1);
          });

          // 然后选中当前节点
          node.attr('body/stroke', '#FF4500');
          node.attr('body/strokeWidth', 3);
          selectedNode.value = node;
        }
      }
    });

    // 监听Selection插件的选择变化事件
    canvasGraph.value.on('selection:changed', ({ selected }) => {
      // 先恢复所有节点的默认样式
      const allNodes = canvasGraph.value!.getNodes();
      allNodes.forEach((node: any) => {
        node.attr('body/stroke', '#1890ff');
        node.attr('body/strokeWidth', 1);
      });

      // 为选中的节点设置高亮样式
      selected.forEach((cell: any) => {
        if (cell.isNode()) {
          cell.attr('body/stroke', '#FF4500');
          cell.attr('body/strokeWidth', 3);
        }
      });

      // 更新单选节点（保持与原有逻辑兼容）
      if (selected.length > 0 && selected[0].isNode()) {
        selectedNode.value = selected[0];
      } else {
        selectedNode.value = null;
      }
    });

    // 添加节点移动中事件监听器，用于动态更新连接桩（实时更新）
    canvasGraph.value.on('node:moving', ({ node }: any) => {
      // 获取与当前节点相连的所有边
      const edges = canvasGraph.value!.getEdges().filter((edge: any) =>
        edge.getSourceCellId() === node.id || edge.getTargetCellId() === node.id
      );

      // 遍历所有相连的边，更新连接桩
      edges.forEach((edge: any) => {
        try {
          // 获取源节点和目标节点
          const sourceNode = canvasGraph.value!.getCellById(edge.getSourceCellId());
          const targetNode = canvasGraph.value!.getCellById(edge.getTargetCellId());

          if (sourceNode && targetNode) {
            // 计算节点之间的相对位置
            const sourceBBox = sourceNode.getBBox();
            const targetBBox = targetNode.getBBox();

            // 计算节点中心坐标
            const sourceCenter = {
              x: sourceBBox.x + sourceBBox.width / 2,
              y: sourceBBox.y + sourceBBox.height / 2
            };
            const targetCenter = {
              x: targetBBox.x + targetBBox.width / 2,
              y: targetBBox.y + targetBBox.height / 2
            };

            // 计算水平和垂直方向的距离差
            const dx = Math.abs(targetCenter.x - sourceCenter.x);
            const dy = Math.abs(targetCenter.y - sourceCenter.y);

            // 根据距离差决定是水平方向还是垂直方向优先
            // 源节点的连接桩
            let sourcePortId = 'output';
            // 目标节点的连接桩
            let targetPortId = 'input';

            if (dx > dy) {
              // 水平方向优先
              if (sourceCenter.x < targetCenter.x) {
                // 源在左，目标在右
                sourcePortId = 'output'; // 源的右侧连接桩
                targetPortId = 'input';  // 目标的左侧连接桩
              } else {
                // 源在右，目标在左
                sourcePortId = 'input';  // 源的左侧连接桩
                targetPortId = 'output'; // 目标的右侧连接桩
              }
            } else {
              // 垂直方向优先
              if (sourceCenter.y < targetCenter.y) {
                // 源在上，目标在下
                sourcePortId = 'bottom'; // 源的底部连接桩
                targetPortId = 'top';    // 目标的顶部连接桩
              } else {
                // 源在下，目标在上
                sourcePortId = 'top';    // 源的顶部连接桩
                targetPortId = 'bottom'; // 目标的底部连接桩
              }
            }

            // 使用X6正确的API设置边的连接桩
            // 首先设置源节点和源连接桩
            edge.setSource({
              cell: sourceNode.id,
              port: sourcePortId
            });

            // 然后设置目标节点和目标连接桩
            edge.setTarget({
              cell: targetNode.id,
              port: targetPortId
            });

            // 强制重新计算边的路径
            edge.setVertices([]);

            // 刷新边以确保连接正确显示
            // edge.refresh();

            // 确保画布更新
            canvasGraph.value!.trigger('cell:change', { cell: edge });
          }
        } catch (error) {
          console.error('更新边连接桩失败:', error);
        }
      });
    });
    // 画布点击事件 - 清空选中节点和边
    canvasGraph.value.on('blank:click', () => {
      // 恢复之前选中边的默认样式
      if (selectedEdge.value) {
        selectedEdge.value.attr('line/stroke', '#1890ff');
        selectedEdge.value.attr('line/strokeWidth', 2);
        // 恢复默认箭头样式
        selectedEdge.value.attr('line/targetMarker', {
          name: 'classic',
          width: 10,
          height: 6,
          fill: '#666',
          stroke: '#666'
        });
      }

      // 恢复之前选中节点的默认样式
      if (selectedNode.value) {
        selectedNode.value.attr('body/stroke', '#1890ff');
        selectedNode.value.attr('body/strokeWidth', 1);
      }
      removeAllNodesPorts();
      selectedNode.value = null;
      selectedEdge.value = null;
      hideParamsPanel();
    });

    // 边点击事件 - 选中边
    canvasGraph.value.on('edge:click', ({ edge }) => {
      // 恢复之前选中边的默认样式
      if (selectedEdge.value && selectedEdge.value !== edge) {
        selectedEdge.value.attr('line/stroke', '#1890ff');
        selectedEdge.value.attr('line/strokeWidth', 2);
        // 恢复默认箭头样式
        selectedEdge.value.attr('line/targetMarker', {
          name: 'classic',
          width: 10,
          height: 6,
          fill: '#666',
          stroke: '#666'
        });
      }

      // 恢复之前选中节点的默认样式
      if (selectedNode.value) {
        selectedNode.value.attr('body/stroke', '#1890ff');
        selectedNode.value.attr('body/strokeWidth', 1);
      }

      selectedNode.value = null; // 清空选中的节点
      selectedEdge.value = edge; // 设置选中的边      
      // 为选中的边设置高亮样式      
      if (edge) {
        const edge_attrs = edge.getAttrs()
        edge_attrs['line']['stroke'] = '#FF4500'
        edge_attrs['line']['strokeWidth'] = 3
        edge_attrs['line']['targetMarker'] = {
          name: 'classic',
          width: 12,
          height: 8,
          fill: '#FF4500',
          stroke: '#FF4500'
        }
        edge.setAttrs(edge_attrs)

        // 显示参数面板，编辑边的标签
        showParamsPanelForEdge(edge);
      }
    });
    // 监听连接尝试
    canvasGraph.value.on('edge:connecting', ({ edge }: any) => {
      // 设置连接中的箭头样式
      edge.attr('line/targetMarker', {
        name: 'classic',
        width: 10,
        height: 6,
        fill: '#666',
        stroke: '#666'
      });
      console.warn('正在尝试创建连接:', edge);
    });

    // 连线创建完成事件
    canvasGraph.value.on('edge:connected', ({ edge, _isNew }: any) => {
      // 确保连线样式正确
      edge.attr('line/stroke', '#1890ff');
      edge.attr('line/strokeWidth', 2);
      // 确保箭头样式正确设置
      edge.attr('line/targetMarker', {
        name: 'classic',
        width: 10,
        height: 6,
        fill: '#666',
        stroke: '#666'
      });
    });

    // 监听连接开始事件
    canvasGraph.value.on('edge:mouseenter', ({ edge }) => {
      // 设置鼠标悬停时的样式与选中时一致
      edge.attr('line/stroke', '#FF4500');
      edge.attr('line/strokeWidth', 3);
      edge.attr('line/targetMarker', {
        name: 'classic',
        width: 12,
        height: 8,
        fill: '#FF4500',
        stroke: '#FF4500'
      });
    });

    canvasGraph.value.on('edge:mouseleave', ({ edge }) => {
      // 确保只有非选中状态的边才恢复默认样式
      if (selectedEdge.value !== edge) {
        edge.attr('line/stroke', '#1890ff');
        edge.attr('line/strokeWidth', 2);
        edge.attr('line/targetMarker', {
          name: 'classic',
          width: 10,
          height: 6,
          fill: '#666',
          stroke: '#666'
        });
      }
    });
    // Ctrl+C：复制选中的节点
    canvasGraph.value!.bindKey(['ctrl+c', 'meta+c'], () => {
      // 检查当前焦点是否在画布区域内，只有焦点在画布内才执行画布相关操作
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement) {
        // 检查焦点是否在画布容器内
        const isInCanvas = canvasContainer.value &&
          (canvasContainer.value.contains(activeElement) ||
            activeElement === canvasContainer.value);

        // 如果焦点不在画布内，则不执行画布复制操作，允许默认的浏览器行为
        if (!isInCanvas) {
          return true; // 允许默认浏览器行为（复制文本）
        }
      }

      const cells = canvasGraph.value!.getSelectedCells()
      if (cells.length) {
        // 保存原始节点数据，用于恢复
        const originalDataMap = new Map<string, any>()

        // 临时清理节点数据，移除可能导致循环引用的属性
        cells.forEach((cell: any) => {
          if (cell.isNode() || cell.isEdge()) {
            const originalData = cell.getData()
            originalDataMap.set(cell.id, originalData)

            // 创建一个纯净的节点数据副本，只包含必要的属性
            cell.setData(originalData)
          }
        })

        try {
          // 复制到剪贴板
          canvasGraph.value!.copy(cells)
        } finally {
          // 恢复原始节点数据
          cells.forEach((cell: any) => {
            if (cell.isNode() || cell.isEdge()) {
              const originalData = originalDataMap.get(cell.id)
              if (originalData) {
                cell.setData(originalData)
              }
            }
          })
        }
      }
      return false // 阻止默认浏览器行为（如复制文本）
    })

    // Ctrl+V：粘贴为新节点
    canvasGraph.value!.bindKey(['ctrl+v', 'meta+v'], () => {
      // 检查当前焦点是否在画布区域内，只有焦点在画布内才执行画布相关操作
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement) {
        // 检查焦点是否在画布容器内
        const isInCanvas = canvasContainer.value &&
          (canvasContainer.value.contains(activeElement) ||
            activeElement === canvasContainer.value);

        // 如果焦点不在画布内，则不执行画布粘贴操作，允许默认的浏览器行为
        if (!isInCanvas) {
          return true; // 允许默认浏览器行为（粘贴文本）
        }
      }

      if (!canvasGraph.value!.isClipboardEmpty()) {
        // 粘贴到鼠标位置 or 偏移位置
        const pastedCells = canvasGraph.value!.paste({
          offset: 20, // 每次粘贴向右下偏移 20px，避免重叠
        })

        // 更新粘贴节点的序号标识
        pastedCells.forEach((cell: any) => {
          if (cell.isNode()) {
            // 为新节点分配新序号
            const serialNumber = serialCounter.value++;
            const nodeId = cell.id;

            // 更新映射字典
            nodeIdToSerialMap.value.set(nodeId, serialNumber);

            // 获取原始节点数据
            const originalData = cell.getData();
            const instructionName = originalData.label.split('-')[1] || originalData.label;

            // 生成新的带序号的节点名称
            const newNodeLabel = `${serialNumber}-${instructionName}`;

            // 更新节点数据
            const updatedData = {
              ...originalData,
              label: newNodeLabel
            };
            cell.setData(updatedData);

            // 更新节点显示标签
            cell.attr('label/text', newNodeLabel);
          }
        });

        // 可选：自动选中新粘贴的节点
        canvasGraph.value!.cleanSelection()
        canvasGraph.value!.select(pastedCells)
      }
      return false
    })

    // 支持Delete键
    canvasGraph.value!.bindKey('delete', () => {
      // 检查当前焦点是否在画布区域内，只有焦点在画布内才执行画布相关操作
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement) {
        // 检查焦点是否在画布容器内
        const isInCanvas = canvasContainer.value &&
          (canvasContainer.value.contains(activeElement) ||
            activeElement === canvasContainer.value);

        // 如果焦点不在画布内，则不执行画布删除操作
        if (!isInCanvas) {
          return true; // 允许默认浏览器行为
        }
      }

      const cells = canvasGraph.value!.getSelectedCells()
      if (cells.length) {
        if (window.confirm(`确定要删除选中的${cells.length}个元素吗？`)) {
          canvasGraph.value!.removeCells(cells)
        }
      }
      return false
    })

    // Ctrl+Z：撤销操作
    canvasGraph.value!.bindKey(['ctrl+z', 'meta+z'], () => {
      // 检查当前焦点是否在画布区域内，只有焦点在画布内才执行画布相关操作
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement) {
        // 检查焦点是否在画布容器内
        const isInCanvas = canvasContainer.value &&
          (canvasContainer.value.contains(activeElement) ||
            activeElement === canvasContainer.value);

        // 如果焦点不在画布内，则不执行画布撤销操作
        if (!isInCanvas) {
          return true; // 允许默认浏览器行为
        }
      }

      if (canvasGraph.value!.canUndo()) {
        canvasGraph.value!.undo()
      }
      return false
    })

    // Ctrl+Y 或 Ctrl+Shift+Z：重做操作
    canvasGraph.value!.bindKey(['ctrl+y', 'meta+y', 'ctrl+shift+z', 'meta+shift+z'], () => {
      // 检查当前焦点是否在画布区域内，只有焦点在画布内才执行画布相关操作
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement) {
        // 检查焦点是否在画布容器内
        const isInCanvas = canvasContainer.value &&
          (canvasContainer.value.contains(activeElement) ||
            activeElement === canvasContainer.value);

        // 如果焦点不在画布内，则不执行画布重做操作
        if (!isInCanvas) {
          return true; // 允许默认浏览器行为
        }
      }

      if (canvasGraph.value!.canRedo()) {
        canvasGraph.value!.redo()
      }
      return false
    })
  };

  // handleKeyDown函数已移除

  /**
   * 删除边
   */
  const deleteEdge = (edge: any) => {
    if (!canvasGraph.value || !edge) return;

    try {
      // 删除边
      canvasGraph.value.removeEdge(edge);

      // 清空选中的边
      if (selectedEdge.value === edge) {
        selectedEdge.value = null;
      }
    } catch (error) {
      console.error('删除边失败:', error);
    }
  };

  /**
   * 删除选中的边
   */
  const deleteSelectedEdge = () => {
    if (selectedEdge.value) {
      deleteEdge(selectedEdge.value);
    }
  };

  /**
   * 删除节点
   */
  const deleteNode = (node: any) => {
    if (!canvasGraph.value || !node) return;

    try {
      // 获取与该节点相连的所有边
      const edges = canvasGraph.value.getEdges().filter(edge =>
        edge.getSourceCellId() === node.id || edge.getTargetCellId() === node.id
      );

      // 先删除相关的边
      edges.forEach(edge => canvasGraph.value!.removeEdge(edge));

      // 再删除节点
      canvasGraph.value.removeNode(node);

      // 清空选中节点
      if (selectedNode.value === node) {
        selectedNode.value = null;
      }
    } catch (error) {
      console.error('删除节点失败:', error);
    }
  };

  /**
   * 删除选中的节点
   */
  const deleteSelectedNode = () => {
    if (selectedNode.value) {
      deleteNode(selectedNode.value);
    }
  };

  /**
   * 为节点添加连接桩显示控制事件
   */
  const addPortVisibilityEvents = (node: any) => {
    // 确保只添加一次事件监听器，避免重复绑定
    if (!node._portEventsAdded) {
      // 添加鼠标悬停事件监听器，控制连接桩的显示和隐藏
      node.on('mouseenter', () => {
        // 显示所有连接桩
        const ports = node.getPorts();
        ports.forEach((port: any) => {
          node.portProp(port.id, `attrs/circle/opacity`, 1);
        });
      });

      node.on('mouseleave', () => {
        // 只有非选中状态的节点才隐藏连接桩
        if (selectedNode.value !== node) {
          const ports = node.getPorts();
          ports.forEach((port: any) => {
            node.portProp(port.id, `attrs/circle/opacity`, 0);
          });
        }
      });

      // 标记已添加事件监听器
      node._portEventsAdded = true;
    }
  };

  /**
   * 为画布中的所有节点添加连接桩显示控制事件
   */
  const addPortEventsToAllNodes = () => {
    if (!canvasGraph.value) return;

    const nodes = canvasGraph.value.getNodes();
    nodes.forEach((node: any) => {
      addPortVisibilityEvents(node);

      // 确保所有节点的连接桩默认隐藏，除非是当前选中的节点
      if (selectedNode.value !== node) {
        const ports = node.getPorts();
        ports.forEach((port: any) => {
          // 使用节点API设置端口属性
          node.portProp(port.id, `attrs/circle/opacity`, 0);
        });
      }
    });
  };

  /**
   * 清除画布拖拽事件监听器
   */
  const clearCanvasDragListeners = () => {
    if (!canvasContainer.value) return;

    // 移除旧的事件监听器
    if (dragEventListeners.value.dragover) {
      canvasContainer.value.removeEventListener('dragover', dragEventListeners.value.dragover);
    }
    if (dragEventListeners.value.dragleave) {
      canvasContainer.value.removeEventListener('dragleave', dragEventListeners.value.dragleave);
    }
    if (dragEventListeners.value.drop) {
      canvasContainer.value.removeEventListener('drop', dragEventListeners.value.drop);
    }

    // 清空引用
    dragEventListeners.value = {};
  };

  /**
   * 初始化画布拖拽功能
   */
  const initializeCanvasDrop = () => {
    if (!canvasGraph.value || !canvasContainer.value) return;

    // 先清除旧的事件监听器，避免重复绑定
    clearCanvasDragListeners();

    // 创建事件处理函数
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      e.dataTransfer!.dropEffect = 'copy';

      // 添加拖拽悬停效果
      canvasContainer.value!.classList.add('drag-over');
    };

    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      canvasContainer.value!.classList.remove('drag-over');
    };

    const handleDrop = (e: DragEvent) => {
      e.preventDefault();

      // 重要：在移除 drag-over 类之前获取坐标，因为该类会添加边框影响尺寸
      const rect = canvasContainer.value!.getBoundingClientRect();
      const clientX = e.clientX;
      const clientY = e.clientY;

      // 检查是否有 drag-over 类的边框影响
      const hasDragOverBorder = canvasContainer.value!.classList.contains('drag-over');
      const borderOffset = hasDragOverBorder ? 2 : 0; // drag-over 类添加了 2px 边框

      // 计算相对于容器的坐标
      let x = clientX - rect.left - borderOffset;
      let y = clientY - rect.top - borderOffset;

      // 考虑画布的缩放和滚动状态
      if (canvasGraph.value) {
        const zoom = canvasGraph.value.zoom();
        const translate = canvasGraph.value.translate();

        // 应用缩放的逆变换，获取正确的画布坐标系中的位置
        // 注意：根据@antv/x6的API，translate()返回的是一个包含平移值的数组或对象
        // 使用解构赋值来安全地获取平移值
        const [tx, ty] = Array.isArray(translate) ? translate : [translate.tx || 0, translate.ty || 0];

        // 应用缩放和滚动的逆变换
        x = (x - tx) / zoom;
        y = (y - ty) / zoom;
      }

      // 现在移除 drag-over 类
      canvasContainer.value!.classList.remove('drag-over');

      try {
        const instructionData = e.dataTransfer?.getData('application/json');
        if (!instructionData) {
          console.warn('未找到拖拽的指令数据');
          return;
        }

        const instruction: Instruction = JSON.parse(instructionData);

        // 添加节点到画布
        addNodeToCanvas(instruction, x, y);
      } catch (error) {
        console.error('处理拖拽放置失败:', error);
      }
    };

    // 绑定事件监听器并保存引用
    canvasContainer.value.addEventListener('dragover', handleDragOver);
    canvasContainer.value.addEventListener('dragleave', handleDragLeave);
    canvasContainer.value.addEventListener('drop', handleDrop);

    // 保存事件监听器引用，用于后续清理
    dragEventListeners.value = {
      dragover: handleDragOver,
      dragleave: handleDragLeave,
      drop: handleDrop
    };
  };

  /**
   * 向画布添加节点
   */
  const addNodeToCanvas = (instruction: Instruction, x: number, y: number) => {
    if (!canvasGraph.value) {
      console.error('画布实例不存在');
      return null;
    }

    const nodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // 为新节点分配序号
    const serialNumber = serialCounter.value++;
    // 将序号和节点id添加到映射字典
    nodeIdToSerialMap.value.set(nodeId, serialNumber);

    // 调整坐标，使鼠标位置对应节点中心
    const nodeWidth = 120;
    const nodeHeight = 40;
    const adjustedX = x - nodeWidth / 2;
    const adjustedY = y - nodeHeight / 2;

    // 初始化节点参数，应用指令定义的默认值
    const nodeParams: Record<string, any> = {};

    // 遍历指令的参数定义，应用默认值
    if (instruction.params && instruction.params.length > 0) {
      instruction.params.forEach(param => {
        // 如果参数有默认值，则应用到节点参数中
        if (param.default_value !== undefined) {
          nodeParams[param.name] = param.default_value;
        }
      });
    }

    // 生成带序号的节点名称
    const nodeLabel = `${serialNumber}-${instruction.name}`;

    const nodeData: CanvasNode = {
      id: nodeId,
      instructionId: instruction.id,
      x: adjustedX,
      y: adjustedY,
      params: nodeParams,
      label: nodeLabel, // 添加label字段，设置为带序号的指令名称
      description: '' // 初始化描述信息为空字符串
    };

    // 设置节点样式
    const fillColor = '#f6ffed';
    const strokeColor = '#b7eb8f';

    try {
      const node = canvasGraph.value.addNode({
        id: nodeId,
        x: adjustedX,
        y: adjustedY,
        width: nodeWidth,
        height: nodeHeight,
        shape: 'rect',
        data: nodeData,

        attrs: {
          body: {
            fill: fillColor,
            stroke: strokeColor,
            strokeWidth: 1,
            rx: 4,
            ry: 4
          },
          label: {
            text: nodeLabel,
            fill: '#333',
            fontSize: 12,
            textAnchor: 'middle',
            textVerticalAnchor: 'middle'
          },
          // 描述信息
          description: {
            text: '',
            fill: '#ce6c0bff',
            fontSize: 10,
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            y: 0,
            visibility: 'hidden'
          }
        },
        markup: [
          {
            tagName: 'rect',
            selector: 'body',
          },
          {
            tagName: 'text',
            selector: 'label',
          },
          {
            tagName: 'text',
            selector: 'description',
          },
        ],
        ports: {
          groups: {
            input: {
              position: 'left',
              attrs: {
                circle: {
                  r: 6,
                  magnet: true,
                  stroke: '#1890ff',
                  strokeWidth: 1,
                  fill: '#fff',
                  opacity: 0, // 默认隐藏连接桩
                  transition: 'opacity 0.2s ease' // 添加过渡效果
                }
              }
            },
            output: {
              position: 'right',
              attrs: {
                circle: {
                  r: 6,
                  magnet: true,
                  stroke: '#1890ff',
                  strokeWidth: 1,
                  fill: '#fff',
                  opacity: 0, // 默认隐藏连接桩
                  transition: 'opacity 0.2s ease' // 添加过渡效果
                }
              }
            },
            top: {
              position: 'top',
              attrs: {
                circle: {
                  r: 6,
                  magnet: true,
                  stroke: '#1890ff',
                  strokeWidth: 1,
                  fill: '#fff',
                  opacity: 0, // 默认隐藏连接桩
                  transition: 'opacity 0.2s ease' // 添加过渡效果
                }
              }
            },
            bottom: {
              position: 'bottom',
              attrs: {
                circle: {
                  r: 6,
                  magnet: true,
                  stroke: '#1890ff',
                  strokeWidth: 1,
                  fill: '#fff',
                  opacity: 0, // 默认隐藏连接桩
                  transition: 'opacity 0.2s ease' // 添加过渡效果
                }
              }
            }
          },
          items: [
            { group: 'input', id: 'input' },
            { group: 'output', id: 'output' },
            { group: 'top', id: 'top' },
            { group: 'bottom', id: 'bottom' }
          ]
        }
      });

      // 添加连接桩显示控制事件
      addPortVisibilityEvents(node);

      // 确保没有其他工具
      node.removeTools();
      return node;
    } catch (error) {
      console.error('添加节点到画布失败:', error);
      return null;
    }
  };

  /**
   * 清空画布
   */
  const clearCanvas = () => {
    if (!canvasGraph.value) return;
    canvasGraph.value.clearCells();
    resetExecutionState();
  };

  /**
   * 清理画布资源
   */
  const cleanupCanvas = () => {
    try {
      // 清除拖拽事件监听器
      clearCanvasDragListeners();
      // 清理工具栏
      toolbars.value.forEach(toolbar => {
        if (toolbar.parentNode) {
          toolbar.parentNode.removeChild(toolbar);
        }
      });
      toolbars.value = [];

      // 清理画布中的所有节点和边
      if (canvasGraph.value) {
        try {
          // 移除所有事件监听器
          canvasGraph.value.off('*');

          // 先清空画布内容
          canvasGraph.value.clearCells();

          // 然后销毁画布实例
          canvasGraph.value.dispose();
        } catch (error) {
          console.warn('画布清理过程中出现错误:', error);
        }
        canvasGraph.value = null;
      }

      canvasContainer.value = null;
      selectedNode.value = null;

      if (window.createConnection) {
        delete window.createConnection;
      }
    } catch (error) {
      console.warn('画布资源清理出现错误:', error);
    }
  };

  // ==================== 参数面板管理 ====================

  /**
   * 显示参数面板（节点）
   */
  const showParamsPanel = (node: Node) => {
    const nodeData = node.getData() as CanvasNode;
    // 使用markRaw标记X6节点实例，避免Vue响应式系统深度监听导致无限递归
    paramsPanel.selectedNode = node;
    paramsPanel.selectedEdge = null;
    paramsPanel.params = nodeData.params || {};
    paramsPanel.visible = true;
  };

  /**
   * 显示参数面板（边）
   */
  const showParamsPanelForEdge = (edge: any) => {
    // 获取边的当前标签文字和逻辑表达式
    const edgeData = edge.getData() || {};
    const currentLabel = edgeData.label || '';
    const currentLogicExpress = edgeData.logic_express || '';

    paramsPanel.selectedNode = null;
    // 使用markRaw标记X6边实例，避免Vue响应式系统深度监听导致无限递归
    paramsPanel.selectedEdge = edge;
    paramsPanel.params = {
      label: currentLabel,
      logic_express: currentLogicExpress
    };
    paramsPanel.visible = true;
  };

  /**
   * 隐藏参数面板
   */
  const hideParamsPanel = () => {
    paramsPanel.visible = false;
    paramsPanel.selectedNode = null;
    paramsPanel.selectedEdge = null;
    paramsPanel.params = {};
  };

  /**
   * 保存节点参数
   */
  const saveNodeParams = (params: Record<string, any>) => {
    if (!paramsPanel.selectedNode) return;

    // 使用深拷贝避免循环引用
    const nodeData = paramsPanel.selectedNode.getData() as CanvasNode;
    nodeData.params = { ...params };
    paramsPanel.selectedNode.setData(nodeData);

    hideParamsPanel();
  };

  /**
   * 保存边标签
   */
  const saveEdgeLabel = (params: Record<string, any>) => {
    if (!paramsPanel.selectedEdge) {
      return;
    }

    const edge = paramsPanel.selectedEdge;
    const newLabel = params.label?.trim() || '';
    const newLogicExpress = params.logic_express?.trim() || '';

    // 更新边的数据 - 使用深拷贝避免循环引用
    const edgeData = edge.getData() || {};
    if (newLabel) {
      edgeData.label = newLabel;
    } else {
      delete edgeData.label;
    }

    // 更新逻辑表达式
    if (newLogicExpress) {
      edgeData.logic_express = newLogicExpress;
    } else {
      delete edgeData.logic_express;
    }

    // 先更新边的数据
    edge.setData(edgeData);

    // 直接更新边的标签显示 - 修复标签不显示的问题
    // 使用更直接的方式更新X6边的标签
    try {
      if (newLabel) {
        edge.setLabels([
          {
            position: 0.5,
            attrs: {
              text: {
                text: newLabel,
                fill: '#333',
                fontSize: 10,
                textAnchor: 'middle',
                textVerticalAnchor: 'middle'
              },
              // 添加背景以提高可读性
              rect: {
                fill: 'white',
                stroke: '#ddd',
                strokeWidth: 1,
                rx: 4,
                ry: 4,
                padding: [4, 8]
              }
            }
          }
        ]);
      } else {
        // 移除标签显示
        edge.setLabels([]);
      }

      // 强制刷新边的显示
      // edge.refresh();
    } catch (error) {
      console.error('❌ 标签显示更新失败:', error);
    }

    hideParamsPanel();
  };

  /**
   * 保存当前参数（根据选中的是节点还是边）
   */
  const saveCurrentParams = () => {
    if (paramsPanel.selectedNode) {
      saveNodeParams(paramsPanel.params);
    } else if (paramsPanel.selectedEdge) {
      saveEdgeLabel(paramsPanel.params);
    }
  };

  /**
   * 保存当前选中节点的参数
   */
  const saveCurrentNodeParams = () => {
    // 检查当前组件中的参数面板状态
    if (paramsPanel.selectedNode && paramsPanel.params) {
      saveNodeParams(paramsPanel.params);
    }
  };

  // ==================== 流程执行 ====================

  // 状态检查相关变量
  let statusCheckInterval: number | null = null;
  let currentExecutingFlowId: string | null = null;

  /**
   * 获取流程执行状态
   */
  const getFlowStatus = async (flowId: string) => {
    try {
      const response = await dataProcessService.getFlowExecutionStatus(flowId);
      return response;
    } catch (error) {
      console.error(`获取流程状态失败: ${flowId}`, error);
      return null;
    }
  };

  /**
   * 终止正在执行的流程
   */
  const terminateFlow = async () => {
    if (!currentExecutingFlowId) return null;

    try {
      const response = await dataProcessService.terminateDataProcessFlow(currentExecutingFlowId);
      // 清除状态检查定时器
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
      }
      return response;
    } catch (error) {
      console.error(`终止流程失败: ${currentExecutingFlowId}`, error);
      return null;
    } finally {
      modalState.executing = false;
      currentExecutingFlowId = null;
    }
  };

  /**
   * 开始定期检查流程状态
   */
  const startStatusCheck = (flowId: string | undefined) => {
    // 清除之前的定时器
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
      statusCheckInterval = null;
    }

    // 如果flowId为undefined，不启动状态检查
    if (!flowId) {
      return;
    }

    currentExecutingFlowId = flowId;

    // 每隔3秒检查一次状态
    statusCheckInterval = window.setInterval(async () => {
      const statusResponse = await getFlowStatus(flowId);
      if (statusResponse && statusResponse.success) {
        const status = statusResponse.data.status;
        // 如果状态不是running，清除定时器
        if (status !== 'running') {
          if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
            modalState.executing = false;
            currentExecutingFlowId = null;
          }
        }
      }
    }, 3000);
  };

  /**
   * 执行数据处理流程
   */
  const executeProcess = async () => {
    if (!canvasGraph.value || modalState.executing) return null;

    // 检查是否有节点
    const nodes = canvasGraph.value.getNodes();
    if (nodes.length === 0) {
      console.warn('没有找到任何节点，无法执行流程');
      // 可以添加用户提示
      return null;
    }

    modalState.executing = true;
    resetExecutionState();

    try {
      // 自动保存当前选中节点的参数（如果有）
      saveCurrentNodeParams();

      const nodes = canvasGraph.value.getNodes();
      const edges = canvasGraph.value.getEdges();

      // 构建流程数据
      const flowId = currentFlowId.value || undefined;
      currentFlowId.value = flowId;

      // 创建流程对象时保留原有信息或使用默认值
      const flow: DataProcessFlow = {
        id: flowId,
        // 使用保存的流程名称和描述（如果有），否则使用默认值
        name: currentFlowInfo.value?.name || `流程_${Date.now()}`,
        description: currentFlowInfo.value?.description || '',
        nodes: nodes.map(node => {
          const nodeData = node.getData() as CanvasNode;
          const position = node.getPosition();
          // 保存节点描述信息

          // 直接使用原始参数名称（不再进行格式转换）
          const convertParams = (params: Record<string, any>): Record<string, any> => {
            // 返回原始参数对象的深拷贝，保留用户定义的参数名称
            return params ? params : {};
          };
          // 处理输入类型：将inputTypes对象转换为所需的格式
          // {t: [paramName1, paramName2], e: [paramName3, paramName4]}
          const inputTypes = nodeData.inputTypes || {};
          const formattedInputTypes: { t: string[], e: string[] } = { t: [], e: [] };

          for (const [paramName, isExpression] of Object.entries(inputTypes)) {
            if (isExpression) {
              formattedInputTypes.e.push(paramName);
            } else {
              formattedInputTypes.t.push(paramName);
            }
          }

          return {
            id: node.id,
            instructionId: nodeData.instructionId,
            x: position.x,
            y: position.y,
            params: convertParams(nodeData.params),
            input_types: formattedInputTypes, // 使用正确的属性名（注意是intput_types，不是input_types）
            description: nodeData.description // 保存节点描述信息
          };
        }),
        edges: edges.map(edge => {
          // 获取边的标签 - 优先从getData()中获取，也检查labels属性作为备选
          let edgeLabel = '';
          const edgeData = edge.getData();
          if (edgeData && edgeData.label) {
            edgeLabel = edgeData.label;
          } else if (edge.getLabels && edge.getLabels().length > 0) {
            // 尝试从labels属性中获取标签文本
            const firstLabel = edge.getLabels()[0];
            if (firstLabel && firstLabel.attrs && firstLabel.attrs.text) {
              // 确保转换为字符串类型
              edgeLabel = String(firstLabel.attrs.text.text || '');
            }
          }

          return {
            id: edge.id,
            source: edge.getSourceCellId(),
            target: edge.getTargetCellId(),
            sourcePort: edge.getSourcePortId(),
            targetPort: edge.getTargetPortId(),
            // 保存边的标签信息，用于执行条件判断
            label: edgeLabel,
            // 保存边的逻辑表达式，用于执行条件判断
            logic_express: edgeData?.logic_express || ''
          };
        })
      };

      // 开始状态检查
      startStatusCheck(flowId);

      // 执行流程 - 所有验证逻辑已移至后端
      const response = await dataProcessService.executeDataProcessFlow(flow);

      if (response.success) {
        // 直接使用response作为结果，保持类型一致性
        executionState.results = [response];
        executionState.progress = 100;
        executionState.currentStep = '执行完成';
      } else {
        executionState.error = response.message || '流程执行失败';
        executionState.currentStep = '执行失败';
        console.error('流程执行失败:', response.message);
      }

      // 返回API响应给调用者
      return response;
    } catch (error: any) {
      executionState.error = error.message || '执行流程时发生未知错误';
      console.error('执行数据处理流程失败:', error);

      // 返回错误对象，保持与成功响应相同的结构
      return {
        success: false,
        message: error.message || '执行流程时发生未知错误',
        data: null
      };
    } finally {
      // 清除状态检查定时器
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
      }
      modalState.executing = false;
      currentExecutingFlowId = null;
    }
  };
  /**
   * 将流程数据加载到画布
   */
  const loadProcessToCanvas = async (flow: DataProcessFlow) => {
    if (!canvasGraph.value || !flow.nodes) return;

    try {
      // 确保指令已加载完成
      if (instructionCategories.value.length === 0) {
        await loadInstructionList();
        // 等待指令加载完成
        if (instructionCategories.value.length === 0) {
          throw new Error('无法加载指令列表，节点无法创建');
        }
      }

      // 清除现有画布内容
      cleanupCanvas();
      await nextTick();

      // 重新初始化画布
      await initializeCanvas();
      // 再等待一次nextTick确保画布完全就绪
      await nextTick();

      if (!canvasGraph.value) {
        throw new Error('画布初始化失败');
      }

      // 添加节点
      const nodeMap = new Map<string, any>();
      // 先创建所有节点
      for (const nodeData of flow.nodes) {
        // 查找对应的指令信息
        let instruction: Instruction | undefined;
        for (const category of instructionCategories.value) {
          instruction = category.instructions.find(instr => instr.id === nodeData.instructionId);
          if (instruction) break;
        }

        if (!instruction) {
          console.warn(`⚠️ 未找到节点 ${nodeData.id} 对应的指令信息 (ID: ${nodeData.instructionId})`);
          continue;
        }
        if (canvasGraph.value) {
          try {
            // 使用简单的方式创建节点
            const nodeId = nodeData.id; // 直接使用流程中保存的ID

            // 为节点分配序号
            const serialNumber = serialCounter.value++;
            // 将序号和节点id添加到映射字典
            nodeIdToSerialMap.value.set(nodeId, serialNumber);

            const nodeWidth = 120;
            const nodeHeight = 40;
            const adjustedX = nodeData.x - nodeWidth / 2;
            const adjustedY = nodeData.y - nodeHeight / 2;

            // 生成带序号的节点名称
            const nodeLabel = `${serialNumber}-${instruction.name}`;

            // 创建节点 - 优化端口配置
            const node = canvasGraph.value.addNode({
              id: nodeId,
              x: adjustedX,
              y: adjustedY,
              width: nodeWidth,
              height: nodeHeight,
              data: {
                label: nodeLabel,
                instructionId: instruction.id,
                params: nodeData.params || {},
                description: nodeData.description || '', // 确保description属性存在
                input_types: nodeData.input_types || { t: [], e: [] } // 添加输入类型属性
              },
              attrs: {
                body: {
                  fill: '#f6ffed',
                  stroke: '#b7eb8f',
                  rx: 4,
                  ry: 4
                },
                label: {
                  text: nodeLabel,
                  fill: '#333',
                  fontSize: 12,
                  textAnchor: 'middle',
                  textVerticalAnchor: (nodeData.description || '') ? 'bottom' : 'middle',
                },
                // 添加描述信息标签
                description: {
                  text: nodeData.description || '',
                  fill: '#ce6c0bff', // 标准蓝色
                  fontSize: 10,
                  textAnchor: 'middle',
                  textVerticalAnchor: 'middle',
                  y: (nodeData.description || '') ? 6 : 0,
                  visibility: (nodeData.description || '') ? 'visible' : 'hidden'
                }
              },
              markup: [
                {
                  tagName: 'rect',
                  selector: 'body',
                },
                {
                  tagName: 'text',
                  selector: 'label',
                },
                {
                  tagName: 'text',
                  selector: 'description',
                },
              ],
              // 优化端口配置，使连接桩显示正确
              ports: {
                groups: {
                  input: {
                    position: 'left',
                    attrs: {
                      circle: {
                        r: 6,
                        magnet: true,
                        stroke: '#3199FF',
                        strokeWidth: 1,
                        fill: '#fff',
                        style: {
                          visibility: 'visible'
                        }
                      }
                    }
                  },
                  output: {
                    position: 'right',
                    attrs: {
                      circle: {
                        r: 6,
                        magnet: true,
                        stroke: '#3199FF',
                        strokeWidth: 1,
                        fill: '#fff',
                        style: {
                          visibility: 'visible'
                        }
                      }
                    }
                  },
                  top: {
                    position: 'top',
                    attrs: {
                      circle: {
                        r: 6,
                        magnet: true,
                        stroke: '#3199FF',
                        strokeWidth: 1,
                        fill: '#fff',
                        style: {
                          visibility: 'visible'
                        }
                      }
                    }
                  },
                  bottom: {
                    position: 'bottom',
                    attrs: {
                      circle: {
                        r: 6,
                        magnet: true,
                        stroke: '#3199FF',
                        strokeWidth: 1,
                        fill: '#fff',
                        style: {
                          visibility: 'visible'
                        }
                      }
                    }
                  }
                },
                items: [
                  { id: 'input', group: 'input' },
                  { id: 'output', group: 'output' },
                  { id: 'top', group: 'top' },
                  { id: 'bottom', group: 'bottom' }
                ]
              }
            });

            if (node) {
              // 存储节点引用
              nodeMap.set(nodeId, node);

              // 添加连接桩显示控制事件
              addPortVisibilityEvents(node);

              // 确保没有其他工具
              node.removeTools();
            }
          } catch (nodeError) {
            console.error(`❌ 创建节点 ${nodeData.id} 失败:`, nodeError);
          }
        }
      }

      // 再创建所有边
      if (flow.edges && flow.edges.length > 0) {
        for (const edge of flow.edges) {
          if (nodeMap.has(edge.source) && nodeMap.has(edge.target)) {
            try {
              const sourceNode = nodeMap.get(edge.source);
              const targetNode = nodeMap.get(edge.target);

              // 获取节点中心坐标
              const sourceBBox = sourceNode.getBBox();
              const targetBBox = targetNode.getBBox();
              const sourceCenter = { x: sourceBBox.x + sourceBBox.width / 2, y: sourceBBox.y + sourceBBox.height / 2 };
              const targetCenter = { x: targetBBox.x + targetBBox.width / 2, y: targetBBox.y + targetBBox.height / 2 };

              // 根据节点位置动态确定连接桩
              let sourcePortId = edge.sourcePort;
              let targetPortId = edge.targetPort;

              if (!sourcePortId || !targetPortId) {
                // 如果没有提供连接桩，根据节点位置动态计算
                const dx = Math.abs(sourceCenter.x - targetCenter.x);
                const dy = Math.abs(sourceCenter.y - targetCenter.y);

                if (dx > dy) {
                  // 水平方向优先
                  if (sourceCenter.x < targetCenter.x) {
                    // 源在左，目标在右
                    sourcePortId = 'output'; // 源的右侧连接桩
                    targetPortId = 'input';  // 目标的左侧连接桩
                  } else {
                    // 源在右，目标在左
                    sourcePortId = 'input';  // 源的左侧连接桩
                    targetPortId = 'output'; // 目标的右侧连接桩
                  }
                } else {
                  // 垂直方向优先
                  if (sourceCenter.y < targetCenter.y) {
                    // 源在上，目标在下
                    sourcePortId = 'bottom'; // 源的底部连接桩
                    targetPortId = 'top';    // 目标的顶部连接桩
                  } else {
                    // 源在下，目标在上
                    sourcePortId = 'top';    // 源的顶部连接桩
                    targetPortId = 'bottom'; // 目标的底部连接桩
                  }
                }
              }

              // 创建边配置
              const edgeConfig = {
                id: edge.id,
                source: { cell: sourceNode.id, port: sourcePortId },
                target: { cell: targetNode.id, port: targetPortId },
                data: { label: 'label' in edge ? edge.label as string : '' }, // 使用类型保护和断言
                attrs: {
                  line: {
                    stroke: '#3199FF',
                    strokeWidth: 2,
                    strokeDasharray: '0',
                    // 确保箭头方向正确，表示数据流向
                    targetMarker: {
                      name: 'classic',
                      width: 12,
                      height: 12,
                      fill: '#3199FF',
                      stroke: '#3199FF'
                    }
                  }
                },
                router: {
                  name: 'manhattan',
                  args: {
                    padding: 10,
                    // 支持所有方向的连接，确保箭头方向正确
                    startDirections: ['right', 'left', 'top', 'bottom'],
                    endDirections: ['left', 'right', 'bottom', 'top']
                  }
                },
                connector: {
                  name: 'rounded',
                  args: { radius: 15 }
                },
                zIndex: 0
              } as any;

              // 如果边有标签数据，添加标签配置
              const edgeLabel = 'label' in edge ? edge.label as string : '';
              if (edgeLabel) {
                edgeConfig.labels = [
                  {
                    position: 0.5,
                    attrs: {
                      text: {
                        text: edgeLabel,
                        fill: '#333',
                        fontSize: 10,
                        textAnchor: 'middle',
                        textVerticalAnchor: 'middle'
                      },
                      rect: {
                        fill: 'white',
                        stroke: '#ddd',
                        strokeWidth: 1,
                        rx: 4,
                        ry: 4,
                        padding: [4, 8]
                      }
                    }
                  }
                ];
              }

              // 添加边到画布
              canvasGraph.value.addEdge(edgeConfig);
              // 不需要存储创建的边引用
            } catch (edgeError) {
              console.error(`❌ 创建边 ${edge.id} 失败:`, edgeError);
            }
          } else {
            console.warn(`⚠️ 跳过边 ${edge.id}: 源节点 ${edge.source} 或目标节点 ${edge.target} 不存在`);
          }
        }
      }

      // 额外步骤：创建完所有边后，更新所有边的连接桩以确保正确连接
      setTimeout(() => {
        if (canvasGraph.value) {
          const edges = canvasGraph.value.getEdges();
          edges.forEach((edge: any) => {
            try {
              const sourceNode = canvasGraph.value?.getCellById(edge.getSourceCellId());
              const targetNode = canvasGraph.value?.getCellById(edge.getTargetCellId());

              if (sourceNode && targetNode) {
                // 重新计算连接桩
                const sourceBBox = sourceNode.getBBox();
                const targetBBox = targetNode.getBBox();
                const sourceCenter = { x: sourceBBox.x + sourceBBox.width / 2, y: sourceBBox.y + sourceBBox.height / 2 };
                const targetCenter = { x: targetBBox.x + targetBBox.width / 2, y: targetBBox.y + targetBBox.height / 2 };

                let sourcePortId;
                let targetPortId;

                const dx = Math.abs(sourceCenter.x - targetCenter.x);
                const dy = Math.abs(sourceCenter.y - targetCenter.y);

                if (dx > dy) {
                  if (sourceCenter.x < targetCenter.x) {
                    sourcePortId = 'output';
                    targetPortId = 'input';
                  } else {
                    sourcePortId = 'input';
                    targetPortId = 'output';
                  }
                } else {
                  if (sourceCenter.y < targetCenter.y) {
                    sourcePortId = 'bottom';
                    targetPortId = 'top';
                  } else {
                    sourcePortId = 'top';
                    targetPortId = 'bottom';
                  }
                }

                // 更新边的连接桩
                edge.setSource({ cell: sourceNode.id, port: sourcePortId });
                edge.setTarget({ cell: targetNode.id, port: targetPortId });
                edge.setVertices([]);
                // edge.refresh();
              }
            } catch (error) {
              console.error('更新边连接桩失败:', error);
            }
          });
        }
      }, 100);

      // 所有节点和边创建完成后，隐藏所有连接桩并居中显示内容
      if (canvasGraph.value && flow.nodes && flow.nodes.length > 0) {
        // 隐藏所有节点的连接桩
        const nodes = canvasGraph.value.getNodes();
        nodes.forEach((node: any) => {
          const ports = node.getPorts();
          ports.forEach((port: any) => {
            // 使用正确的API设置连接桩透明度为0
            node.portProp(port.id, `attrs/circle/opacity`, 0);
          });
        });

      }
    } catch (error) {
      console.error('❌ 将流程加载到画布失败:', error);
    }
  };

  /**
   * 保存数据处理流程
   */
  const saveDataProcess = async () => {
    if (!canvasGraph.value || modalState.saving) return;

    modalState.saving = true;

    try {
      // 自动保存当前选中节点的参数（如果有）
      saveCurrentNodeParams();
      const nodes = canvasGraph.value.getNodes();
      const edges = canvasGraph.value.getEdges();
      if (nodes.length === 0) {
        throw new Error('画布中没有节点，无法保存流程');
      }

      // 使用数据源ID生成固定的流程ID，确保一个数据源只有一个流程
      const flowId = currentFlowId.value || undefined;
      currentFlowId.value = flowId;

      // 创建流程对象时保留原有信息或使用默认值
      const flow: DataProcessFlow = {
        id: flowId,
        // 使用保存的流程名称和描述（如果有），否则使用默认值
        name: currentFlowInfo.value?.name || `流程_${Date.now()}`,
        description: currentFlowInfo.value?.description || '',
        nodes: nodes.map(node => {
          const nodeData = node.getData() as CanvasNode;
          const position = node.getPosition();

          // 直接使用原始参数名称（不再进行格式转换）
          const convertParams = (params: Record<string, any>): Record<string, any> => {
            // 返回原始参数对象的深拷贝，保留用户定义的参数名称
            return params ? params : {};
          };

          // 处理输入类型：将inputTypes对象转换为所需的格式
          // {t: [paramName1, paramName2], e: [paramName3, paramName4]}
          const inputTypes = nodeData.inputTypes || {};
          const formattedInputTypes: { t: string[], e: string[] } = { t: [], e: [] };

          for (const [paramName, isExpression] of Object.entries(inputTypes)) {
            if (isExpression) {
              formattedInputTypes.e.push(paramName);
            } else {
              formattedInputTypes.t.push(paramName);
            }
          }

          return {
            id: node.id,
            instructionId: nodeData.instructionId,
            x: position.x,
            y: position.y,
            params: convertParams(nodeData.params),
            input_types: formattedInputTypes, // 使用正确的属性名（注意是intput_types，不是input_types）
            description: nodeData.description // 保存节点描述信息
          };
        }),
        edges: edges.map(edge => {
          const edgeData = edge.getData();
          return {
            id: edge.id,
            source: edge.getSourceCellId(),
            target: edge.getTargetCellId(),
            sourcePort: edge.getSourcePortId(),
            targetPort: edge.getTargetPortId(),
            // 保存边的标签信息
            label: edgeData?.label || '',
            // 保存边的逻辑表达式
            logic_express: edgeData?.logic_express || ''
          };
        })
      };

      const response = await dataProcessService.saveDataProcessFlow(flow);

      if (response.success) {
        // 成功提示
        // alert(`流程保存成功！\nID: ${response.data?.id || '未知'}\n消息: ${response.data?.message || ''}`);
      } else {
        throw new Error(response.message || '保存流程失败');
      }
    } catch (error: any) {
      console.error('保存数据处理流程失败:', error);
      // 错误提示
      alert(`保存流程失败！\n错误信息: ${error.message || '未知错误'}`);
    } finally {
      modalState.saving = false;
    }
  };

  /**
   * 重置执行状态
   */
  const resetExecutionState = () => {
    executionState.progress = 0;
    executionState.currentStep = '';
    executionState.results = [];
    executionState.error = null;
  };

  // 切换节点描述信息显示状态
  const toggleNodeDescriptions = () => {
    showNodeDescriptions.value = !showNodeDescriptions.value;
    // 更新所有节点的描述信息显示状态
    if (canvasGraph.value) {
      const nodes = canvasGraph.value.getNodes();
      nodes.forEach(node => {
        const nodeData = node.getData();
        // 确保nodeData中有description属性
        const description = nodeData.description || '';
        if (node.attrs?.description) {
          node.attr('description/visibility', description ? 'visible' : 'hidden');
        }
      });
    }
  };

  // 切换节点提示框显示状态
  const toggleNodeTooltips = () => {
    showNodeTooltips.value = !showNodeTooltips.value;
  };

  /**
   * 切换选择模式（框选/平移）
   * 当切换到框选模式时，启用rubberband功能，禁用panning
   * 当切换到平移模式时，禁用rubberband功能，启用panning
   */
  const toggleSelectionMode = () => {
    isRubberbandMode.value = !isRubberbandMode.value;
    if (canvasGraph.value) {
      // 获取Selection插件实例
      const selection = canvasGraph.value.getPlugin('selection') as Selection;
      if (selection) {
        if (isRubberbandMode.value) {
          // 开启框选，关闭平移
          selection.enableRubberband();
          canvasGraph.value.disablePanning();
        } else {
          // 关闭框选，开启平移
          selection.disableRubberband();
          canvasGraph.value.enablePanning();
        }
      }
    }
  };

  /**
   * 显示节点描述编辑器
   */
  const showNodeDescriptionEditor = (node: Node) => {
    const nodeData = node.getData() as CanvasNode;
    nodeDescriptionEditor.node = node;
    nodeDescriptionEditor.description = nodeData.description || '';
    nodeDescriptionEditor.visible = true;
  };

  /**
   * 保存节点描述信息
   */
  const saveNodeDescription = () => {
    if (!nodeDescriptionEditor.node) return;

    const node = nodeDescriptionEditor.node;
    const nodeData = node.getData() as CanvasNode;
    nodeData.description = nodeDescriptionEditor.description;
    node.setData(nodeData);

    // 更新节点描述显示 - 确保描述信息显示在节点下方
    if (node.attrs?.description) {
      // 确保nodeData中有description属性
      if (!nodeData.description) {
        nodeData.description = '';
      }

      node.attr('label/textVerticalAnchor', (nodeData.description || '') ? 'bottom' : 'middle');
      node.attr('description/text', nodeData.description);
      node.attr('description/fill', '#ce6c0bff');
      node.attr('description/fontSize', 10);
      node.attr('description/textAnchor', 'middle');
      node.attr('description/textVerticalAnchor', 'middle');
      node.attr('description/y', (nodeData.description || '') ? 6 : 0);
      node.attr('description/visibility', nodeData.description ? 'visible' : 'hidden');
    }

    // 隐藏编辑模态框
    nodeDescriptionEditor.visible = false;
  };

  /**
   * 取消节点描述编辑
   */
  const cancelNodeDescription = () => {
    nodeDescriptionEditor.visible = false;
    // 清空编辑状态
    nodeDescriptionEditor.node = null;
    nodeDescriptionEditor.description = '';
  };

  // 终止执行函数，暴露给外部组件使用
  const terminateExecution = async () => {
    return await terminateFlow();
  };

  // ==================== 返回接口 ====================  

  return {
    // 状态
    modalState,
    selectedNode,
    selectedEdge,
    hasSelectedNodes,
    instructionCategories,
    instructionLoading,
    dataSourceInfoCache,
    canvasGraph,
    paramsPanel,
    executionState,
    showNodeDescriptions,
    showNodeTooltips,

    // 画布控制
    resizeCanvas,

    // 节点描述信息控制
    toggleNodeDescriptions,
    toggleNodeTooltips,
    isRubberbandMode,
    toggleSelectionMode,
    // 节点描述编辑器状态
    nodeDescriptionEditor,
    // 节点描述编辑方法
    showNodeDescriptionEditor,
    saveNodeDescription,
    cancelNodeDescription,

    // 计算属性
    isExecuting,

    // 模态框控制
    showDataProcessModal,
    hideDataProcessModal,
    resetDataProcessModal,

    // 指令管理
    loadInstructionList,

    // 画布管理
    initializeCanvas,
    addNodeToCanvas,
    clearCanvas,
    cleanupCanvas,
    deleteNode,
    deleteSelectedNode,
    deleteEdge,
    deleteSelectedEdge,

    // 参数面板
    showParamsPanel,
    showParamsPanelForEdge,
    hideParamsPanel,
    saveNodeParams,
    saveEdgeLabel,
    saveCurrentParams,
    saveCurrentNodeParams,

    // 流程执行
    terminateExecution,

    // 流程执行
    executeProcess,
    saveDataProcess,
    resetExecutionState
  };
}
/**
 * 数据处理指令拖拽组合式函数
 */