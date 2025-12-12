<template>
  <div class="data-process-page">
    <div class="page-header">
      <h1>数据流程</h1>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showAddProcessModal">
          新增流程
        </el-button>
      </div>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="search-filter">
      <el-input 
        v-model="searchKeyword"
        placeholder="搜索流程名称或描述"
        :prefix-icon="Search"
        @input="debouncedSearch"
        class="search-input"
      />
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-message">{{ error }}</div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>
    
    <!-- 流程列表 -->
    <div v-else-if="processes.length > 0" class="process-content">
      <el-table 
        :data="filteredProcesses" 
        style="width: 100%"
        row-key="id"
        :expand-row-keys="expandedRows"
        @expand-change="handleRowExpand"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <h4>执行记录</h4>
              <div v-if="executionResults[row.id] && executionResults[row.id].length > 0">
                <el-table :data="executionResults[row.id]" style="width: 100%" size="small" row-key="id">
                  <el-table-column prop="executed_at" label="执行时间" min-width="180">
                    <template #default="scope">
                      {{ new Date(scope.row.executed_at).toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="success" label="状态" min-width="100">
                    <template #default="scope">
                      <el-tag :type="scope.row.success ? 'success' : 'danger'">
                        {{ scope.row.success ? '成功' : '失败' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="execution_time" label="执行时长(秒)" min-width="120" />
                  <el-table-column prop="error_message" label="错误消息" min-width="200">
                    <template #default="scope">
                      {{ scope.row.error_message || '-' }}
                    </template>
                  </el-table-column>
                  <el-table-column label="执行结果" min-width="100">
                    <template #default="scope">
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="showExecutionDetails(scope.row)"
                        v-if="scope.row.result_data"
                      >
                        查看
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-else-if="loadingResults[row.id]" class="loading-results">
                <div class="loading-spinner small"></div>
                <span>加载执行结果中...</span>
              </div>
              <div v-else class="no-results">
                暂无执行结果
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="流程名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column prop="updated_at" label="修改时间" min-width="180" />
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              @click="configureProcess(scope.row)"
              style="margin-right: 5px"
            >
              配置
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              @click="editProcess(scope.row)"
              style="margin-right: 5px"
            >
              编辑
            </el-button>
            <el-button 
              :type="executingFlows.has(scope.row.id) ? 'danger' : 'info'" 
              size="small" 
              @click="executeProcessById(scope.row.id)"
              style="margin-right: 5px"
            >
              <template v-if="executingFlows.has(scope.row.id)">
                <el-icon><Loading /></el-icon>
                终止
              </template>
              <template v-else>
                执行
              </template>
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteProcess(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <i class="icon-document-text"></i>
      </div>
      <p>暂无流程数据</p>
      <el-button type="primary" @click="showAddProcessModal">
        新增流程
      </el-button>
    </div>
    
    <!-- 新增/编辑流程对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="500px"
      :before-close="handleDialogClose"
    >
      <el-form :model="formData" :rules="rules" ref="formRef">
        <el-form-item label="流程名称" prop="name">
          <el-input 
            v-model="formData.name" 
            placeholder="请输入流程名称"
            :disabled="isSubmitting"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            placeholder="请输入流程描述"
            :disabled="isSubmitting"
            rows="4"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialogClose" :disabled="isSubmitting">
          取消
        </el-button>
        <el-button 
          type="primary" 
          @click="submitForm"
          :loading="isSubmitting"
        >
          {{ isSubmitting ? '提交中...' : '确定' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 流程配置模态框 -->
    <DataProcessModal
      :visible="modalState.visible"
      :data-source="{ id: '', name: '', type: '' }"
    />
    
    <!-- 执行结果详情对话框 -->
    <el-dialog 
      v-model="dialogDetailVisible" 
      title="执行结果详情" 
      width="800px"
      id="executionResultDialog"
      :before-close="closeDetailDialog"
    >
      <el-tabs v-if="currentExecutionResult && currentExecutionResult.result_data" v-model="activeTab">
        <el-tab-pane label="最终结果" name="finalResult">
          <div v-if="currentExecutionResult.result_data.final_result" class="execution-detail-content">
            <!-- 根据数据类型选择显示方式 -->
            <template v-if="typeof currentExecutionResult.result_data.final_result === 'object'">
              <div class="json-container">
                <!-- 手动添加复制按钮 -->
                <el-button 
                  type="primary" 
                  size="small" 
                  class="manual-copy-btn"
                  @click="copyToClipboard(JSON.stringify(currentExecutionResult.result_data.final_result, null, 2))"
                >
                  复制
                </el-button>
                <vue-json-pretty 
                  :data="currentExecutionResult.result_data.final_result" 
                  :deep="3" 
                  :show-length="true" 
                  :show-line-number="true"
                  :highlight-hover="true"
                  :selectable="true"
                  copyable
                  highlight-key
                />
              </div>
            </template>
            <template v-else>
              <!-- 对于非对象类型，显示可点击的URL -->
              <pre v-html="textToHtmlWithLinks(String(currentExecutionResult.result_data.final_result))"></pre>
            </template>
          </div>
          <div v-else class="empty-detail">暂无最终结果</div>
        </el-tab-pane>
        <el-tab-pane label="过程数据" name="processResults">
          <div v-if="currentExecutionResult.result_data.process_results" class="execution-detail-content">
            <!-- 根据数据类型选择显示方式 -->
            <template v-if="typeof currentExecutionResult.result_data.process_results === 'object'">
              <div class="json-container">
                <!-- 手动添加复制按钮 -->
                <el-button 
                  type="primary" 
                  size="small" 
                  class="manual-copy-btn"
                  @click="copyToClipboard(JSON.stringify(currentExecutionResult.result_data.process_results, null, 2))"
                >
                  复制
                </el-button>
                <vue-json-pretty 
                  :data="currentExecutionResult.result_data.process_results" 
                  :deep="3" 
                  :show-length="true" 
                  :show-line-number="true"
                  :highlight-hover="true"
                  :selectable="true"
                  copyable
                  highlight-key
                />
              </div>
            </template>
            <template v-else>
              <!-- 对于非对象类型，显示可点击的URL -->
              <pre v-html="textToHtmlWithLinks(String(currentExecutionResult.result_data.process_results))"></pre>
            </template>
          </div>
          <div v-else class="empty-detail">暂无过程数据</div>
        </el-tab-pane>
        <el-tab-pane label="执行顺序" name="executionOrder">
          <div v-if="currentExecutionResult.result_data.execution_order && currentExecutionResult.result_data.execution_order.length > 0" class="execution-detail-content">
            <ul class="execution-order-list">
              <li v-for="(node, index) in currentExecutionResult.result_data.execution_order" :key="index">
                <span>{{ index + 1 }}. </span>
                <span v-html="textToHtmlWithLinks(String(node))"></span>
              </li>
            </ul>
          </div>
          <div v-else class="empty-detail">暂无执行顺序信息</div>
        </el-tab-pane>
      </el-tabs>
      <div v-else class="empty-detail">暂无执行结果数据</div>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Loading } from '@element-plus/icons-vue'
import { dataProcessService } from '../services/dataProcessService'
import { useDataProcess } from '../composables/useDataProcess'
import { httpClient } from '../services/httpClient'
import DataProcessModal from '../components/DataProcess/DataProcessModal.vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

interface Process {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

interface ExecutionResult {
  id: string
  flow_id: string
  flow_name: string
  success: boolean
  error_message: string | null
  execution_time: number
  executed_at: string
  result_data: {
    final_result?: any
    process_results?: any
    execution_order?: string[]
  }
}

// DataProcessFlow接口的简化版本
interface DataProcessFlow {
  id: string
  name: string
  description?: string
  nodes?: any[]
  edges?: any[]
  createdAt?: string
  updatedAt?: string
}

export default defineComponent({
  name: 'DataProcess',
  components: {
    DataProcessModal,
    VueJsonPretty
  },
  setup() {
      // 使用数据处理组合式函数
      // modalState is used for controlling DataProcessModal visibility
      const { showDataProcessModal, modalState } = useDataProcess();
      
      // 响应式数据
      const processes = ref<Process[]>([])
      const searchKeyword = ref('')
      const loading = ref(false)
      const error = ref('')
      const dialogVisible = ref(false)
      const currentProcessId = ref<string | null>(null)
      const isSubmitting = ref(false)
      const formRef = ref()
      const executingProcessId = ref<string | null>(null)
      // 新增用于展开行和执行结果的状态
      const expandedRows = ref<string[]>([])
      const executionResults = ref<Record<string, ExecutionResult[]>>({})
      const loadingResults = ref<Record<string, boolean>>({})
      // 执行结果详情相关状态
      const activeTab = ref('finalResult')
      
      // 执行状态跟踪
      const flowExecutionStatus = ref<Record<string, string>>({})
      // 状态检查定时器
      const statusCheckIntervals = ref<Record<string, number>>({})
      // 正在执行的流程ID列表
      const executingFlows = ref<Set<string>>(new Set())
      // 终止按钮加载状态
      const terminatingFlowId = ref<string | null>(null)
    
    // 复制到剪贴板功能
    const copyToClipboard = (text: string) => {
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('复制成功')
      }).catch(() => {
        ElMessage.error('复制失败，请手动复制')
      })
    }
    
    // 将文本中的URL转换为可点击的链接
    const textToHtmlWithLinks = (text: string) => {
      if (!text) return '';
      
      // 匹配URL的正则表达式
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      
      // 将URL替换为可点击的链接
      return text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: #409eff; text-decoration: underline;">$1</a>');
    }
    // 表单数据
    const formData = reactive({
      name: '',
      description: ''
    })
    
    // 表单验证规则
    const rules = reactive({
      name: [
        { required: true, message: '请输入流程名称', trigger: 'blur' },
        { min: 1, max: 50, message: '流程名称长度在 1 到 50 个字符', trigger: 'blur' }
      ],
      description: [
        { max: 200, message: '流程描述长度不超过 200 个字符', trigger: 'blur' }
      ]
    })
    
    // 计算属性
    const dialogTitle = computed(() => {
      return currentProcessId.value ? '编辑流程' : '新增流程'
    })
    
    const filteredProcesses = computed(() => {
      if (!searchKeyword.value.trim()) {
        return processes.value
      }
      
      const keyword = searchKeyword.value.toLowerCase()
      return processes.value.filter(process => 
        process.name.toLowerCase().includes(keyword) ||
        process.description.toLowerCase().includes(keyword)
      )
    })
    
    // 加载流程列表
    const loadProcessList = async () => {
      loading.value = true
      error.value = ''
      
      try {
        // 调用流程接口获取数据
        const response = await dataProcessService.getSavedDataProcessFlows()
        
        if (response.success && response.data) {
          // 确保返回的数据格式与Process接口匹配
          processes.value = response.data.map(flow => ({
            id: flow.id || '',
            name: flow.name,
            description: flow.description || '', // 直接使用description
            created_at: flow.createdAt || new Date().toLocaleString(),
            updated_at: flow.updatedAt || new Date().toLocaleString()
          }))
        } else {
          error.value = response.message || '加载失败'
        }
      } catch (err: any) {
        error.value = '加载流程列表失败：' + (err.message || '未知错误')
        console.error('加载流程列表失败:', err)
      } finally {
        loading.value = false
      }
    }
    
    // 防抖搜索
    const debouncedSearch = () => {
      // 实际项目中可以添加防抖逻辑
    }
    
    // 显示新增流程对话框
    const showAddProcessModal = () => {
      currentProcessId.value = null
      resetForm()
      dialogVisible.value = true
    }
    
    // 流程配置
    const configureProcess = async (process: Process) => {
      try {
        // 使用数据处理组合式函数打开配置模态框
        await showDataProcessModal(process.id);
        
        // 加载流程配置
        const response = await dataProcessService.getProcessById(process.id);
        if (!response.success || !response.data) {          
          ElMessage.warning('未找到流程配置数据');
        }
      } catch (error) {
        console.error('配置流程失败:', error);
        ElMessage.error('打开流程配置失败');
      }
    }
    
    // 关闭执行结果详情对话框
    const closeDetailDialog = () => {
      dialogDetailVisible.value = false
      currentExecutionResult.value = null
    }
    
    // 编辑流程
    const editProcess = (process: Process) => {
      currentProcessId.value = process.id
      formData.name = process.name
      formData.description = process.description
      dialogVisible.value = true
    }
    
    // 删除流程
    const deleteProcess = async (id: string) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这个流程吗？',
          '警告',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 调用服务层删除接口
        const response = await dataProcessService.deleteDataProcessFlow(id)
        
        if (response.success) {
          processes.value = processes.value.filter(p => p.id !== id)
          ElMessage.success('删除成功')
        } else {
          ElMessage.error(response.message || '删除失败')
        }
      } catch (err: any) {
        if (err.name !== 'CanceledError') {
          ElMessage.error('删除失败：' + (err.message || '未知错误'))
        }
        // 用户取消删除操作不显示错误
      }
    }
    
    // 根据流程ID执行流程或终止流程
    // eslint-disable-next-line no-unused-vars, @typescript-eslint/no-unused-vars
    const executeProcessById = async (flowId: string) => {
      // 如果流程正在执行，则终止执行
      if (executingFlows.value.has(flowId)) {
        await terminateFlow(flowId)
        return
      }
      
      try {
        executingProcessId.value = flowId
        // 立即添加到正在执行列表，确保按钮状态正确
        executingFlows.value.add(flowId)
        flowExecutionStatus.value[flowId] = 'running'
        
        // 开始定期检查状态（在调用executeDataProcessFlowById之前）
        startStatusCheck(flowId)
        
        // 调用服务层执行接口
        const response = await dataProcessService.executeDataProcessFlowById(flowId)
        
        if (response.success) {
          ElMessage.success('流程执行成功')          
        } else {
          ElMessage.error(`执行失败: ${response.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('执行流程失败:', error)
        ElMessage.error('执行流程时发生错误')
        // 清理状态
        executingFlows.value.delete(flowId)
        delete flowExecutionStatus.value[flowId]
        // 清理定时器
        if (statusCheckIntervals.value[flowId]) {
          clearInterval(statusCheckIntervals.value[flowId])
          delete statusCheckIntervals.value[flowId]
        }
      } finally {
        executingProcessId.value = null
      }
    }
    
    // 定期检查流程执行状态
    const startStatusCheck = (flowId: string) => {
      // 清除之前的定时器
      if (statusCheckIntervals.value[flowId]) {
        clearInterval(statusCheckIntervals.value[flowId])
        delete statusCheckIntervals.value[flowId]
      }
      
      // 每隔3秒检查一次状态
      const intervalId = window.setInterval(async () => {
        try {
          const statusResponse = await dataProcessService.getFlowExecutionStatus(flowId)
          if (statusResponse.success) {
            const status = statusResponse.data.status
            flowExecutionStatus.value[flowId] = status
            
            // 如果状态不是running，清除定时器并更新状态
            if (status !== 'running') {
              executingFlows.value.delete(flowId)
              clearInterval(statusCheckIntervals.value[flowId])
              delete statusCheckIntervals.value[flowId]
              
              // 根据最终状态显示提示
              if (status === 'completed') {
                ElMessage.success(`流程 ${flowId} 执行完成`)
              } else if (status === 'failed') {
                ElMessage.error(`流程 ${flowId} 执行失败`)
              } else if (status === 'terminated') {
                ElMessage.info(`流程 ${flowId} 已终止`)
              }
            }
          }
        } catch (error) {
          console.error(`获取流程 ${flowId} 状态失败:`, error)
        }
      }, 3000)
      
      statusCheckIntervals.value[flowId] = intervalId as unknown as number
    }
    
    // 终止流程执行
    const terminateFlow = async (flowId: string) => {
      try {
        terminatingFlowId.value = flowId
        
        // 调用服务层终止接口
        const response = await dataProcessService.terminateDataProcessFlow(flowId)
        
        if (response.success) {
          ElMessage.success('流程终止请求已发送')
          // 立即更新UI状态，提供更好的用户体验
          executingFlows.value.delete(flowId)
          delete flowExecutionStatus.value[flowId]
          // 清理定时器
          if (statusCheckIntervals.value[flowId]) {
            clearInterval(statusCheckIntervals.value[flowId])
            delete statusCheckIntervals.value[flowId]
          }
        } else {
          ElMessage.error(`终止失败: ${response.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('终止流程失败:', error)
        ElMessage.error('终止流程时发生错误')
      } finally {
        terminatingFlowId.value = null
      }
    }
    
    // 重置表单
    const resetForm = () => {
      formData.name = ''
      formData.description = ''
      if (formRef.value) {
        formRef.value.resetFields()
      }
    }
    
    // 处理对话框关闭
    const handleDialogClose = () => {
      dialogVisible.value = false
      resetForm()
    }
    
    // 提交表单
    const submitForm = async () => {
      if (!formRef.value) return
      
      try {
        await formRef.value.validate()
        isSubmitting.value = true
        
        let result
        
        if (currentProcessId.value) {
          // 编辑流程：调用基本信息保存接口
          const basicInfo = {
            id: currentProcessId.value,
            name: formData.name,
            description: formData.description
          }
          
          result = await httpClient.post('/data-process/save-basic-info', basicInfo)
        } else {
          // 新增流程：仍然调用完整保存接口，但只提供基本信息
          const flowData: DataProcessFlow = {
            id: '',
            name: formData.name,
            description: formData.description,
            nodes: [], // 新增流程时初始化为空数组
            edges: [] // 新增流程时初始化为空数组
          }
          
          result = await httpClient.post('/data-process/save', flowData)
        }
        
        if (result.success) {
          // 重新加载流程列表以获取最新数据
          await loadProcessList()
          ElMessage.success(currentProcessId.value ? '编辑成功' : '新增成功')
          dialogVisible.value = false
          resetForm()
        } else {
          ElMessage.error(result.message || '操作失败')
        }
      } catch (err: any) {
        if (err.name !== 'CanceledError') {
          ElMessage.error('操作失败：' + (err.message || '未知错误'))
        }
      } finally {
        isSubmitting.value = false
      }
    }
    
    // 执行结果详情对话框
    const dialogDetailVisible = ref(false)
    const currentExecutionResult = ref<ExecutionResult | null>(null)
    
    // 显示执行结果详情
    const showExecutionDetails = (result: ExecutionResult) => {
      currentExecutionResult.value = result
      dialogDetailVisible.value = true
    }
    
    // 获取流程执行结果
    const fetchExecutionResults = async (processId: string) => {
      try {
        loadingResults.value[processId] = true
        // 调用真实API接口获取执行结果
        const response = await dataProcessService.getExecutionHistory(processId)
        
        if (response.success && response.data) {
          // 数据已经符合ExecutionResult接口格式，直接赋值
          executionResults.value[processId] = response.data
        } else {
          executionResults.value[processId] = []
        }
      } catch (err) {
        console.error('获取执行结果失败:', err)
        executionResults.value[processId] = []
      } finally {
        loadingResults.value[processId] = false
      }
    }
    
    // 处理行展开事件
    const handleRowExpand = (row: Process, expanded: boolean[]) => {
      if (expanded && expanded.length > 0) {
        // 行展开时获取执行结果
        expandedRows.value = [row.id]
        fetchExecutionResults(row.id)
      } else {
        // 行收起时清空展开行
        expandedRows.value = []
      }
    }
    
    // 生命周期钩子
    onMounted(() => {
      loadProcessList()
    })
    
    // 组件卸载前清理定时器
    onBeforeUnmount(() => {
      // 清理所有状态检查定时器
      Object.values(statusCheckIntervals.value).forEach(intervalId => {
        clearInterval(intervalId)
      })
      statusCheckIntervals.value = {}
      executingFlows.value.clear()
    })
    
    return {
        processes,
        searchKeyword,
        loading,
        error,
        dialogVisible,
        dialogTitle,
        formData,
        rules,
        formRef,
        isSubmitting,
        filteredProcesses,
        Search,
        Plus,
        Loading,
        debouncedSearch,
        showAddProcessModal,
        configureProcess,
        editProcess,
        deleteProcess,
        executeProcessById,
        executingProcessId,
        handleDialogClose,
        submitForm,
        modalState,
        // 新增导出项
        expandedRows,
        executionResults,
        loadingResults,
        handleRowExpand,
        dialogDetailVisible,
        currentExecutionResult,
        showExecutionDetails,
        closeDetailDialog,
        activeTab,
        copyToClipboard,
        textToHtmlWithLinks,
        // 执行状态相关导出
        executingFlows,
        flowExecutionStatus,
        terminatingFlowId
      }
  }
})
</script>

<style scoped>
.data-process-page {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.page-header h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-filter {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

/* 执行结果详情对话框样式 - 使用深度选择器 */
:deep(#executionResultDialog .el-dialog__body) {
  max-height: 600px;
  overflow-y: auto;
}

.execution-detail-content {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 16px;
  margin-top: 10px;
}

/* VueJsonPretty样式调整 */
.execution-detail-content :deep(.vue-json-pretty) {
  font-family: Monaco, Menlo, 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

/* 空状态样式 */
.empty-detail {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.search-input {
  width: 300px;
}

.error-message {
  padding: 10px 15px;
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  color: #f56c6c;
  margin-bottom: 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.process-content {
  margin-bottom: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  color: #dcdfe6;
}

.empty-state p {
  margin-bottom: 20px;
}

/* 展开行内容样式 */
.expand-content {
  padding: 20px;
  background-color: #fafafa;
  border-radius: 4px;
}

.expand-content h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}

.loading-results {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 执行结果详情样式 */
.execution-detail-content {
  height: 100%;
  overflow: auto;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}
  
  /* VueJsonPretty组件样式调整 */
  .execution-detail-content {
    position: relative;
  }
  
  .vjsonp-container {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
    overflow-wrap: break-word;
    padding: 10px;
  }
  
  /* 确保行号和内容正确显示 */
  .vjsonp-line {
    display: flex;
    align-items: flex-start;
  }
  
  .vjsonp-line-number {
    color: #909399;
    margin-right: 10px;
    min-width: 24px;
    text-align: right;
  }
  
  .vjsonp-tree {
    flex: 1;
  }
  
  /* 复制按钮样式 - 确保可见 */
  .vjsonp-copy-button {
    position: absolute !important;
    top: 15px !important;
    right: 15px !important;
    background-color: #409eff !important;
    color: white !important;
    border: none !important;
    padding: 4px 8px !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    cursor: pointer !important;
    z-index: 100 !important;
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
  }
  
  /* 手动添加的复制按钮样式 */
  .json-container {
    position: relative;
    width: 100%;
  }
  
  .manual-copy-btn {
    position: absolute !important;
    top: 10px !important;
    right: 10px !important;
    z-index: 200 !important;
    font-size: 12px !important;
    padding: 4px 12px !important;
  }
  
  .vjsonp-copy-button:hover {
    background-color: #66b1ff !important;
  }
  
  /* 确保展开/折叠按钮可见 */
  .vjsonp-expand-icon {
    margin-right: 5px !important;
    cursor: pointer !important;
    color: #606266 !important;
  }
  
  /* 增强语法高亮效果 */
  .vjsonp-key {
    color: #336699 !important;
    font-weight: bold;
  }
  
  .vjsonp-string {
    color: #e66170 !important;
  }
  
  .vjsonp-number {
    color: #2584cd !important;
  }
  
  .vjsonp-boolean {
    color: #ff8c00 !important;
  }
  
  .vjsonp-null {
    color: #808080 !important;
  }

.execution-detail-content pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.execution-order-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.execution-order-list li {
  padding: 8px 12px;
  margin-bottom: 4px;
  background-color: #fff;
  border-left: 3px solid #409eff;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.empty-detail {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.loading-spinner.small {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  border-width: 2px;
}

.no-results {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .process-management-page {
    padding: 15px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .search-filter {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
}
/* 固定高度对话框样式 - 使用深度选择器 */
  :deep(#executionResultDialog) {
    display: flex;
    flex-direction: column;
    height: var(--el-dialog-height);
  }
    
  :deep(#executionResultDialog .el-tabs) {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  :deep(#executionResultDialog .el-tabs__content) {
    height: 400px;
    overflow-y: auto;
    padding-bottom: 0;
  }
  
  :deep(#executionResultDialog .el-tab-pane) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  </style>