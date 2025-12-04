// 文件工具函数

/**
 * 格式化文件大小
 * @param bytes - 文件大小（字节）
 * @param decimals - 小数位数，默认为2
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * 获取文件扩展名
 * @param filename - 文件名
 * @returns 文件扩展名（不包含点号）
 */
export function getFileExtension(filename: string): string {
  if (!filename) return '';
  
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === filename.length - 1) {
    return '';
  }
  
  return filename.substring(lastDotIndex + 1).toLowerCase();
}

/**
 * 获取文件名（不包含扩展名）
 * @param filename - 完整文件名
 * @returns 不包含扩展名的文件名
 */
export function getFileNameWithoutExtension(filename: string): string {
  if (!filename) return '';
  
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1) {
    return filename;
  }
  
  return filename.substring(0, lastDotIndex);
}

/**
 * 验证文件类型
 * @param file - 文件对象
 * @param allowedTypes - 允许的文件类型数组
 * @returns 是否为允许的文件类型
 */
export function validateFileType(file: File, allowedTypes: string[]): boolean {
  if (!file || !allowedTypes || allowedTypes.length === 0) {
    return false;
  }
  
  const fileExtension = getFileExtension(file.name);
  return allowedTypes.includes(fileExtension);
}

/**
 * 验证文件大小
 * @param file - 文件对象
 * @param maxSizeInMB - 最大文件大小（MB）
 * @returns 是否符合大小限制
 */
export function validateFileSize(file: File, maxSizeInMB: number): boolean {
  if (!file) return false;
  
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
}

/**
 * 读取文件内容为文本
 * @param file - 文件对象
 * @returns Promise<string> 文件内容
 */
export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      resolve(event.target?.result as string || '');
    };
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };
    
    reader.readAsText(file);
  });
}

/**
 * 读取文件内容为Base64
 * @param file - 文件对象
 * @returns Promise<string> Base64编码的文件内容
 */
export function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      const result = event.target?.result as string || '';
      // 移除data:xxx;base64,前缀
      const base64 = result.split(',')[1] || result;
      resolve(base64);
    };
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };
    
    reader.readAsDataURL(file);
  });
}

/**
 * 下载文件
 * @param data - 文件数据（Blob、ArrayBuffer或字符串）
 * @param filename - 文件名
 * @param mimeType - MIME类型
 */
export function downloadFile(data: Blob | ArrayBuffer | string, filename: string, mimeType?: string): void {
  let blob: Blob;
  
  if (data instanceof Blob) {
    blob = data;
  } else if (data instanceof ArrayBuffer) {
    blob = new Blob([data], { type: mimeType || 'application/octet-stream' });
  } else {
    blob = new Blob([data], { type: mimeType || 'text/plain' });
  }
  
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // 清理URL对象
  URL.revokeObjectURL(url);
}

/**
 * 将文件名转换为安全的ID
 * @param filename - 文件名
 * @returns 安全的ID字符串
 */
export function sanitizeFilenameForId(filename: string): string {
  if (!filename) return '';
  
  return filename
    .replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_') // 替换特殊字符为下划线
    .replace(/_+/g, '_') // 合并多个下划线
    .replace(/^_|_$/g, ''); // 移除首尾下划线
}

/**
 * 检查是否为Excel文件
 * @param filename - 文件名
 * @returns 是否为Excel文件
 */
export function isExcelFile(filename: string): boolean {
  const excelExtensions = ['xlsx', 'xls', 'xlsm', 'xlsb'];
  const extension = getFileExtension(filename);
  return excelExtensions.includes(extension);
}

/**
 * 检查是否为图片文件
 * @param filename - 文件名
 * @returns 是否为图片文件
 */
export function isImageFile(filename: string): boolean {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
  const extension = getFileExtension(filename);
  return imageExtensions.includes(extension);
}