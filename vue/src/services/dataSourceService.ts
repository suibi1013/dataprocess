// 数据源API服务
// 封装数据源相关的API调用

import { httpClient } from './httpClient';
import {
  ApiResponse,
  DataSourceApiService,
  DataSourceType,
  FormErrors,
} from '@/types';
import type {
  DataSource,
  CreateDataSourceRequest,
  DataSourcePreview,
  DataSourceListParams
} from '@/types/dataSource';

/**
 * 数据源API服务类
 */
export class DataSourceService implements DataSourceApiService {
  private readonly basePath = '/datasource';

  /**
   * 获取数据源列表
   */
  async getDataSources(params?: DataSourceListParams): Promise<ApiResponse<DataSource[]>> {
    try {
      // 修正API路径，移除重复的/api前缀
      return await httpClient.get<DataSource[]>('/datasources', params);
    } catch (error) {
      console.error('获取数据源列表失败:', error);
      throw error;
    }
  }

  /**
   * 创建数据源
   */
  async createDataSource(data: CreateDataSourceRequest): Promise<ApiResponse<DataSource>> {
    try {
      // 直接调用POST /datasource接口创建数据源
      // 对于Excel类型，handleFileChange中已上传文件并更新了config.files
      return await httpClient.post<DataSource>(this.basePath, data);
    } catch (error) {
      console.error('创建数据源失败:', error);
      throw error;
    }
  }

  // Excel类型数据源的文件信息已在表单提交前处理，直接通过POST /datasource接口创建

  /**
   * 获取数据源详情
   */
  async getDataSource(id: string): Promise<ApiResponse<DataSource>> {
    try {
      return await httpClient.get<DataSource>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`获取数据源详情失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 更新数据源
   */
  async updateDataSource(id: string, data: Partial<DataSource>): Promise<ApiResponse<DataSource>> {
    try {
      return await httpClient.put<DataSource>(`${this.basePath}/${id}`, data);
    } catch (error) {
      console.error(`更新数据源失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 删除数据源
   */
  async deleteDataSource(id: string): Promise<ApiResponse<void>> {
    try {
      return await httpClient.delete<void>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`删除数据源失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 预览数据源数据
   */
  async previewDataSource(id: string): Promise<ApiResponse<DataSourcePreview>> {
    try {
      // 调用正确的API端点：/api/datasource/{data_source_id}/data
      const response = await httpClient.get<DataSourcePreview>(`${this.basePath}/${id}/data`);
      
      return response;
    } catch (error) {
      console.error(`预览数据源数据失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 测试数据源连接
   */
  async testDataSourceConnection(config: any): Promise<ApiResponse<{ success: boolean; message: string }>> {
    try {
      return await httpClient.post<{ success: boolean; message: string }>(
        `${this.basePath}/test-connection`,
        { config }
      );
    } catch (error) {
      console.error('测试数据源连接失败:', error);
      throw error;
    }
  }

  /**
   * 获取数据源统计信息
   */
  async getDataSourceStats(): Promise<ApiResponse<{ total: number; byType: Record<string, number> }>> {
    try {
      return await httpClient.get<{ total: number; byType: Record<string, number> }>(`${this.basePath}/stats`);
    } catch (error) {
      console.error('获取数据源统计信息失败:', error);
      throw error;
    }
  }

  /**
   * 验证数据源表单数据
   */
  validateDataSourceForm(name: string, type: DataSourceType | '', config: any): FormErrors {
    const errors: FormErrors = {};

    // 验证名称
    if (!name || name.trim().length === 0) {
      errors.name = '数据源名称不能为空';
    } else if (name.trim().length > 50) {
      errors.name = '数据源名称不能超过50个字符';
    }

    // 验证类型
    if (!type) {
      errors.type = '请选择数据源类型';
    }

    // 根据类型验证配置
    if (type && config) {
      const configErrors = this.validateDataSourceConfig(type, config);
      if (configErrors) {
        errors.config = configErrors;
      }
    }

    return errors;
  }

  /**
   * 验证数据源配置
   */
  private validateDataSourceConfig(type: DataSourceType, config: any): string | undefined {
    switch (type) {
      case 'excel':
        if (!config.files || config.files.length === 0) {
          return '请选择Excel文件';
        }
        // 验证文件类型
        for (const file of config.files) {
          if (!file.name.match(/\.(xlsx|xls)$/i)) {
            return '只支持.xlsx和.xls格式的Excel文件';
          }
          // 验证文件大小（10MB限制）
          if (file.size > 10 * 1024 * 1024) {
            return '文件大小不能超过10MB';
          }
        }
        break;

      case 'api':
        if (!config.url || config.url.trim().length === 0) {
          return 'API URL不能为空';
        }
        // 验证URL格式
        try {
          new URL(config.url);
        } catch {
          return '请输入有效的URL地址';
        }
        if (!config.method) {
          return '请选择请求方法';
        }
        break;

      case 'database':
        if (!config.type) {
          return '请选择数据库类型';
        }
        if (!config.host || config.host.trim().length === 0) {
          return '主机地址不能为空';
        }
        if (!config.port || config.port <= 0 || config.port > 65535) {
          return '请输入有效的端口号(1-65535)';
        }
        if (!config.database || config.database.trim().length === 0) {
          return '数据库名不能为空';
        }
        if (!config.username || config.username.trim().length === 0) {
          return '用户名不能为空';
        }
        break;

      default:
        return '不支持的数据源类型';
    }

    return undefined;
  }

  /**
   * 获取数据源类型的显示标签
   */
  getDataSourceTypeLabel(type: DataSourceType): string {
    const labels: Record<DataSourceType, string> = {
      excel: 'Excel文件',
      api: 'API接口',
      database: '数据库'
    };
    return labels[type] || type;
  }

  /**
   * 获取数据源配置信息摘要
   */
  getDataSourceConfigSummary(dataSource: DataSource): string {
    switch (dataSource.type) {
      case 'excel':
        // 处理新格式（config对象包含files数组）
        if ('files' in dataSource.config) {
          const fileCount = dataSource.config.files?.length || 0;
          return `${fileCount}个Excel文件`;
        }
        // 处理旧格式（config是文件数组）
        else if (Array.isArray(dataSource.config)) {
          return `${dataSource.config.length}个Excel文件`;
        }
        return 'Excel文件';

      case 'api':
        if ('url' in dataSource.config) {
          return dataSource.config.url || 'API接口';
        }
        return 'API接口';

      case 'database':
        if ('host' in dataSource.config && 'database' in dataSource.config) {
          return `${dataSource.config.host}/${dataSource.config.database}`;
        }
        return '数据库连接';

      default:
        return '未知类型';
    }
  }
}

// 导出数据源服务实例
export const dataSourceService = new DataSourceService();