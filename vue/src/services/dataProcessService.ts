// 数据流程API服务
// 封装数据处理流程相关的API调用

import { httpClient } from './httpClient';
import { ApiResponse } from '@/types';
import type {
  DataProcessFlow,
  InstructionExecutionResult
} from '@/types/instruction';

/**
 * 数据流程API服务类
 */
export class DataProcessService {
  /**
   * 执行数据处理流程
   */
  async executeDataProcessFlow(flow: DataProcessFlow): Promise<ApiResponse<InstructionExecutionResult[]>> {
    try {
      return await httpClient.post<InstructionExecutionResult[]>('/data-process/execute', flow);
    } catch (error) {
      console.error('执行数据处理流程失败:', error);
      throw error;
    }
  }

  /**
   * 保存数据处理流程
   */
  async saveDataProcessFlow(flow: DataProcessFlow): Promise<ApiResponse<{ id: string; message: string }>> {
    try {
      // 直接使用/data-process/save，因为httpClient已包含/api前缀
      return await httpClient.post<{ id: string; message: string }>('/data-process/save', flow);
    } catch (error) {
      console.error('保存数据处理流程失败:', error);
      throw error;
    }
  }

  /**
   * 获取已保存的数据处理流程列表
   */
  async getSavedDataProcessFlows(): Promise<ApiResponse<DataProcessFlow[]>> {
    try {
      return await httpClient.get<DataProcessFlow[]>('/data-process/list');
    } catch (error) {
      console.error('获取已保存的数据处理流程列表失败:', error);
      throw error;
    }
  }

  /**
   * 根据数据源ID获取流程配置（单个对象）
   */
  async getProcessesByDataSourceId(dataSourceId: string): Promise<ApiResponse<DataProcessFlow | null>> {
    try {
      const response = await httpClient.get<DataProcessFlow>(`/data-process/by-datasource/${dataSourceId}`);
      // 如果返回空对象，转换为null
      if (response.success && response.data) {
        const processData = Object.keys(response.data).length > 0 ? response.data : null;
        return {
          ...response,
          data: processData
        };
      }
      return response;
    } catch (error) {
      console.error('根据数据源ID获取流程配置失败:', error);
      throw error;
    }
  }

  /**
   * 根据流程ID获取流程配置
   */
  async getProcessById(processId: string): Promise<ApiResponse<DataProcessFlow | null>> {
    try {
      const response = await httpClient.get<DataProcessFlow>(`/data-process/${processId}`);
      // 如果返回空对象，转换为null
      if (response.success && response.data) {
        const processData = Object.keys(response.data).length > 0 ? response.data : null;
        return {
          ...response,
          data: processData
        };
      }
      return response;
    } catch (error) {
      console.error('根据流程ID获取流程配置失败:', error);
      throw error;
    }
  }

  /**
   * 删除数据处理流程
   */
  async deleteDataProcessFlow(flowId: string): Promise<ApiResponse<void>> {
    try {
      return await httpClient.delete<void>(`/data-process/flows/${flowId}`);
    } catch (error) {
      console.error(`删除数据处理流程失败 (ID: ${flowId}):`, error);
      throw error;
    }
  }

  /**
   * 根据流程ID执行数据处理流程
   */
  async executeDataProcessFlowById(flowId: string): Promise<ApiResponse<InstructionExecutionResult[]>> {
    try {
      return await httpClient.post<InstructionExecutionResult[]>(`/data-process/execute-by-id/${flowId}`);
    } catch (error) {
      console.error(`根据流程ID执行数据处理流程失败 (ID: ${flowId}):`, error);
      throw error;
    }
  }
  
  /**
   * 获取流程执行历史
   */
  async getExecutionHistory(flowId: string): Promise<ApiResponse<any[]>> {
    try {
      return await httpClient.get<any[]>(`/data-process/execution-history/${flowId}`);
    } catch (error) {
      console.error(`获取流程执行历史失败 (ID: ${flowId}):`, error);
      throw error;
    }
  }

  /**
   * 获取流程执行状态
   */
  async getFlowExecutionStatus(flowId: string): Promise<ApiResponse<any>> {
    try {
      return await httpClient.get<any>(`/data-process/execute/status/${flowId}`);
    } catch (error) {
      console.error(`获取流程执行状态失败 (ID: ${flowId}):`, error);
      throw error;
    }
  }

  /**
   * 终止正在执行的流程
   */
  async terminateDataProcessFlow(flowId: string): Promise<ApiResponse<any>> {
    try {
      return await httpClient.post<any>(`/data-process/execute/terminate`, { flow_id: flowId });
    } catch (error) {
      console.error(`终止流程执行失败 (ID: ${flowId}):`, error);
      throw error;
    }
  }
}

// 导出数据流程服务实例
export const dataProcessService = new DataProcessService();