// 系统服务 - 处理系统相关的API调用
import { httpClient } from './httpClient';
import type { ApiResponse } from '@/types';

// 备份信息接口
export interface BackupInfo {
  backup_path: string;
  backup_filename: string;
  backup_time: string;
  tables_count: number;
  excluded_tables: string[];
}

// 备份文件列表项接口
export interface BackupFile {
  filename: string;
  file_path: string;
  size: number;
  create_time: string;
  modify_time: string;
}

// 系统服务类
export class SystemService {
  /**
   * 备份数据库
   */
  async backupDatabase(): Promise<ApiResponse<BackupInfo>> {
    return httpClient.post<BackupInfo>('/system/backup');
  }

  /**
   * 还原数据库
   * @param backupFilePath 备份文件路径
   */
  async restoreDatabase(backupFilePath: string): Promise<ApiResponse<void>> {
    return httpClient.post<void>('/system/restore', undefined, {
      params: { backup_file_path: backupFilePath }
    });
  }

  /**
   * 获取备份文件列表
   */
  async getBackupList(): Promise<ApiResponse<BackupFile[]>> {
    return httpClient.get<BackupFile[]>('/system/backups');
  }

  /**
   * 删除备份文件
   * @param backupFilename 备份文件名
   */
  async deleteBackup(backupFilename: string): Promise<ApiResponse<void>> {
    return httpClient.delete<void>(`/system/backup/${backupFilename}`);
  }

  /**
   * 下载备份文件
   * @param backupFilename 备份文件名
   */
  async downloadBackup(backupFilename: string): Promise<void> {
    // 构建下载URL
    const url = `${httpClient.getBaseURL()}/system/backup/download/${backupFilename}`;
    
    // 创建一个隐藏的a标签用于下载
    const link = document.createElement('a');
    link.href = url;
    link.download = backupFilename;
    link.style.display = 'none';
    
    // 添加到DOM并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
  }

  /**
   * 上传备份文件并还原
   * @param file 备份文件
   */
  async uploadAndRestore(file: File): Promise<ApiResponse<void>> {
    // 创建FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', file.name);
    
    return httpClient.upload<void>('/system/restore/upload', formData);
  }
}

// 创建系统服务实例
export const systemService = new SystemService();
