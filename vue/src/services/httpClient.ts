// HTTP客户端服务
// 封装axios，提供统一的HTTP请求接口

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '@/types';

// 检测是否在Electron环境中
const isElectron = () => {
  // 检测是否在Electron渲染进程中
  const userAgent = window.navigator.userAgent.toLowerCase();
  return userAgent.includes(' electron/');
};

// 获取基础URL，根据环境自动选择
const getBaseUrl = () => {
  // 开发环境和Electron环境都使用固定的后端服务地址，包含/api前缀
  // 使用127.0.0.1而不是localhost，确保与后端监听地址完全一致
  return isElectron() ? 'http://127.0.0.1:5001/api' : 'http://127.0.0.1:5001/api';
};

// HTTP客户端类
export class HttpClient {
  private instance: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = getBaseUrl()) {
    this.baseURL = baseURL;
    this.instance = axios.create({
      baseURL,
      timeout: 180000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 可以在这里添加认证token等
        return config;
      },
      (error) => {
        console.error('请求拦截器错误:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        console.error('响应拦截器错误:', error);
        return this.handleError(error);
      }
    );
  }

  /**
   * 错误处理
   */
  private handleError(error: any): Promise<never> {
    const apiError: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: '未知错误',
    };

    if (error.response) {
      // 服务器响应了错误状态码
      const { status, data } = error.response;
      apiError.code = `HTTP_${status}`;
      apiError.message = data?.message || data?.error || `HTTP错误 ${status}`;
      apiError.details = data;
    } else if (error.request) {
      // 请求已发出但没有收到响应
      apiError.code = 'NETWORK_ERROR';
      apiError.message = '网络错误，请检查网络连接';
    } else {
      // 其他错误
      apiError.message = error.message || '请求配置错误';
    }

    return Promise.reject(apiError);
  }

  /**
   * GET请求
   */
  async get<T = any>(url: string, params?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.get(url, { params });
    return this.formatResponse<T>(response);
  }

  /**
   * POST请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, data, config);
    return this.formatResponse<T>(response);
  }

  /**
   * PUT请求
   */
  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.put(url, data);
    return this.formatResponse<T>(response);
  }

  /**
   * DELETE请求
   */
  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    const response = await this.instance.delete(url);
    return this.formatResponse<T>(response);
  }

  /**
   * 文件上传
   */
  async upload<T = any>(url: string, formData: FormData): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return this.formatResponse<T>(response);
  }

  /**
   * 格式化响应数据
   */
  private formatResponse<T>(response: AxiosResponse): ApiResponse<T> {
    const { data } = response;
    
    // 如果后端返回的数据已经是标准格式，直接返回
    if (data && typeof data === 'object' && 'success' in data) {
      return data as ApiResponse<T>;
    }
    
    // 否则包装成标准格式
    return {
      success: true,
      data: data as T,
    };
  }

  /**
   * 获取基础URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * 设置基础URL
   */
  setBaseURL(baseURL: string): void {
    this.baseURL = baseURL;
    this.instance.defaults.baseURL = baseURL;
  }
}

// 创建默认的HTTP客户端实例
export const httpClient = new HttpClient();