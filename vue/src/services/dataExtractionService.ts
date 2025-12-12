import type { 
  ApiResponse, 
  DataSourceDetails, 
  InstructionResult 
} from '@/types/dataExtraction';
import { httpClient } from './httpClient';

/**
 * 数据源服务类
 * 负责与后端API的交互
 */
export class DataSourceService {
  // 使用httpClient，不再需要硬编码API_BASE

  /**
   * 获取数据源详细信息
   * @param dataSourceId 数据源ID
   * @param limit 数据限制数量
   * @returns 数据源详细信息
   */
  async getDataSourceDetails(
    dataSourceId: string, 
    limit: number = 1
  ): Promise<ApiResponse<DataSourceDetails>> {    
    try {
      return await httpClient.get(`/datasource/${dataSourceId}/data?limit=${limit}`);
    } catch (error) {
      console.error('获取数据源详细信息失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '网络请求失败'
      };
    }
  }

  /**
   * 获取数据源完整数据（用于预览）
   * @param dataSourceId 数据源ID
   * @returns 数据源完整数据
   */
  async getDataSourceData(
    dataSourceId: string
  ): Promise<ApiResponse<DataSourceDetails>> {
    try {
      return await httpClient.get(`/datasource/${dataSourceId}/data`);
    } catch (error) {
      console.error('获取数据源数据失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '网络请求失败'
      };
    }
  }

  /**
   * 执行指令
   * @param instructionId 指令ID
   * @param params 指令参数
   * @param intputTypes 输入类型配置，t表示文本，e表示表达式
   * @returns 执行结果
   */
  async executeInstruction(
    instructionId: string, 
    params: Record<string, any> = {},
    intputTypes: { t: string[]; e: string[] } = { t: [], e: [] }
  ): Promise<InstructionResult> {
    try {
      const result = await httpClient.post('/instruction/execute', {
        instruction_id: instructionId,
        script_params: params,
        input_types: intputTypes
      });
      
      return result;
    } catch (error) {
      console.error('指令执行失败:', error);
      throw error;
    }
  }

  /**
   * 获取数据源列表
   * @returns 数据源列表
   */
  async getDataSourceList(): Promise<ApiResponse<any[]>> {
    try {
      return await httpClient.get('/datasources');
    } catch (error) {
      console.error('获取数据源列表失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '网络请求失败'
      };
    }
  }

  /**
   * 通过文件路径和工作表名获取数据源数据
   * @param filePath 文件路径
   * @param sheetName 工作表名
   * @param limit 数据限制数量
   * @returns 数据源详细信息
   */
  async getDataSourceDataByFilePath(
    filePath: string, 
    sheetName: string, 
    limit: number = 1
  ): Promise<ApiResponse<DataSourceDetails>> {
    try {
      // 构建查询参数
      const params = new URLSearchParams({
        file_path: filePath,
        sheet_name: sheetName,
        limit: limit.toString()
      });
      
      return await httpClient.get(`/datasource/file-data?${params}`);
    } catch (error) {
      console.error('通过文件路径获取数据源数据失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '网络请求失败'
      };
    }
  }

  /**
   * 解析数据源路径
   * @param sourceDataPath 源数据路径 (格式: "数据源ID:工作表名")
   * @returns 解析后的数据源ID和工作表名
   */
  parseDataSourcePath(sourceDataPath: string): {
    dataSourceId: string;
    sheetName: string;
  } {
    const parts = sourceDataPath.split(':');
    return {
      dataSourceId: parts[0] || '',
      sheetName: parts[1] || ''
    };
  }

  /**
   * 构建数据源路径
   * @param dataSourceId 数据源ID
   * @param sheetName 工作表名
   * @returns 完整的数据源路径
   */
  buildSourceDataPath(dataSourceId: string, sheetName: string): string {
    return `${dataSourceId}:${sheetName}`;
  }
}

// 创建单例实例
export const dataSourceService = new DataSourceService();