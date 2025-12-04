// 日期工具函数

/**
 * 格式化日期字符串
 * @param dateString - 日期字符串
 * @param format - 格式化模式，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDate(dateString: string, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString; // 如果无法解析，返回原字符串
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  } catch (error) {
    console.error('日期格式化失败:', error);
    return dateString;
  }
}

/**
 * 获取相对时间描述
 * @param dateString - 日期字符串
 * @returns 相对时间描述，如 "2小时前"
 */
export function getRelativeTime(dateString: string): string {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    if (diffMs < 0) return '未来时间';
    
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSeconds < 60) {
      return '刚刚';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return formatDate(dateString, 'YYYY-MM-DD');
    }
  } catch (error) {
    console.error('相对时间计算失败:', error);
    return dateString;
  }
}

/**
 * 检查日期是否有效
 * @param dateString - 日期字符串
 * @returns 是否为有效日期
 */
export function isValidDate(dateString: string): boolean {
  if (!dateString) return false;
  
  try {
    const date = new Date(dateString);
    return !isNaN(date.getTime());
  } catch {
    return false;
  }
}

/**
 * 获取当前时间戳
 * @returns 当前时间戳（毫秒）
 */
export function getCurrentTimestamp(): number {
  return Date.now();
}

/**
 * 将时间戳转换为日期字符串
 * @param timestamp - 时间戳（毫秒）
 * @param format - 格式化模式
 * @returns 格式化后的日期字符串
 */
export function timestampToDate(timestamp: number, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  return formatDate(new Date(timestamp).toISOString(), format);
}