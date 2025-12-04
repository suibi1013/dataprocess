// 格式化工具函数

import { CellStyle } from '@/types';

/**
 * 构建单元格样式属性字符串
 * @param cellStyle - 单元格样式对象
 * @returns 样式属性字符串
 */
export function buildCellStyleAttribute(cellStyle?: CellStyle): string {
  if (!cellStyle || typeof cellStyle !== 'object') {
    return '';
  }

  const styles: string[] = [];

  // 字体样式
  if (cellStyle.font_size) {
    styles.push(`font-size: ${cellStyle.font_size}px`);
  }
  if (cellStyle.font_color && cellStyle.font_color !== '#000000') {
    styles.push(`color: ${cellStyle.font_color}`);
  }
  if (cellStyle.font_bold) {
    styles.push('font-weight: bold');
  }
  if (cellStyle.font_italic) {
    styles.push('font-style: italic');
  }
  if (cellStyle.font_underline) {
    styles.push('text-decoration: underline');
  }
  if (cellStyle.font_name) {
    styles.push(`font-family: '${cellStyle.font_name}', sans-serif`);
  }

  // 对齐方式
  if (cellStyle.horizontal_align) {
    const alignMap = {
      'left': 'left',
      'center': 'center',
      'right': 'right',
      'justify': 'justify'
    };
    const textAlign = alignMap[cellStyle.horizontal_align] || cellStyle.horizontal_align;
    styles.push(`text-align: ${textAlign}`);
  }
  if (cellStyle.vertical_align) {
    const verticalMap = {
      'top': 'top',
      'center': 'middle',
      'bottom': 'bottom'
    };
    const verticalAlign = verticalMap[cellStyle.vertical_align] || cellStyle.vertical_align;
    styles.push(`vertical-align: ${verticalAlign}`);
  }

  // 背景色
  if (cellStyle.background_color && cellStyle.background_color !== '#000000') {
    styles.push(`background-color: ${cellStyle.background_color}`);
  }

  // 边框
  if (cellStyle.border_top) {
    styles.push(`border-top: 1px solid ${cellStyle.border_top}`);
  }
  if (cellStyle.border_bottom) {
    styles.push(`border-bottom: 1px solid ${cellStyle.border_bottom}`);
  }
  if (cellStyle.border_left) {
    styles.push(`border-left: 1px solid ${cellStyle.border_left}`);
  }
  if (cellStyle.border_right) {
    styles.push(`border-right: 1px solid ${cellStyle.border_right}`);
  }

  // 单元格尺寸
  if (cellStyle.width) {
    styles.push(`width: ${cellStyle.width}px`);
  }
  if (cellStyle.height) {
    styles.push(`height: ${cellStyle.height}px`);
  }

  return styles.length > 0 ? ` style="${styles.join('; ')}"` : '';
}

/**
 * 获取数据源类型标签
 * @param type - 数据源类型
 * @returns 类型标签
 */
export function getDataSourceTypeLabel(type: string): string {
  const typeMap: Record<string, string> = {
    'excel': 'Excel文件',
    'api': 'API接口',
    'database': '数据库'
  };
  return typeMap[type] || type;
}

/**
 * 获取数据源配置信息描述
 * @param dataSource - 数据源对象
 * @returns 配置信息描述
 */
export function getDataSourceConfigInfo(dataSource: any): string {
  if (!dataSource || !dataSource.config) {
    return '无配置信息';
  }

  const { type, config } = dataSource;

  switch (type) {
    case 'excel':
      if (config.files && config.files.length > 0) {
        return `${config.files.length}个文件`;
      }
      return 'Excel文件';
    
    case 'api':
      return config.url || 'API接口';
    
    case 'database':
      if (config.host && config.database) {
        return `${config.host}:${config.port || 3306}/${config.database}`;
      }
      return '数据库连接';
    
    default:
      return '未知配置';
  }
}

/**
 * 格式化数字
 * @param num - 数字
 * @param decimals - 小数位数
 * @param thousandsSeparator - 千位分隔符
 * @returns 格式化后的数字字符串
 */
export function formatNumber(
  num: number,
  decimals: number = 2,
  thousandsSeparator: string = ','
): string {
  if (isNaN(num)) return '0';
  
  const fixed = num.toFixed(decimals);
  const parts = fixed.split('.');
  
  // 添加千位分隔符
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
  
  return parts.join('.');
}

/**
 * 格式化百分比
 * @param value - 数值（0-1之间）
 * @param decimals - 小数位数
 * @returns 百分比字符串
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  if (isNaN(value)) return '0%';
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 截断文本
 * @param text - 原始文本
 * @param maxLength - 最大长度
 * @param suffix - 后缀（默认为'...'）
 * @returns 截断后的文本
 */
export function truncateText(text: string, maxLength: number, suffix: string = '...'): string {
  if (!text || text.length <= maxLength) {
    return text || '';
  }
  
  return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * 首字母大写
 * @param str - 字符串
 * @returns 首字母大写的字符串
 */
export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * 驼峰命名转换为短横线命名
 * @param str - 驼峰命名字符串
 * @returns 短横线命名字符串
 */
export function camelToKebab(str: string): string {
  return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
}

/**
 * 短横线命名转换为驼峰命名
 * @param str - 短横线命名字符串
 * @returns 驼峰命名字符串
 */
export function kebabToCamel(str: string): string {
  return str.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
}

/**
 * 格式化JSON字符串（美化）
 * @param obj - 要格式化的对象
 * @param indent - 缩进空格数
 * @returns 格式化后的JSON字符串
 */
export function formatJSON(obj: any, indent: number = 2): string {
  try {
    return JSON.stringify(obj, null, indent);
  } catch (error) {
    console.error('JSON格式化失败:', error);
    return String(obj);
  }
}

/**
 * 格式化错误消息
 * @param error - 错误对象
 * @returns 格式化后的错误消息
 */
export function formatErrorMessage(error: any): string {
  if (!error) return '未知错误';
  
  if (typeof error === 'string') {
    return error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  if (error.error) {
    return error.error;
  }
  
  return JSON.stringify(error);
}

/**
 * 格式化状态标签
 * @param status - 状态值
 * @returns 状态标签对象
 */
export function formatStatusLabel(status: string): { text: string; type: string; color: string } {
  const statusMap: Record<string, { text: string; type: string; color: string }> = {
    'active': { text: '活跃', type: 'success', color: '#52c41a' },
    'inactive': { text: '未激活', type: 'default', color: '#d9d9d9' },
    'error': { text: '错误', type: 'danger', color: '#ff4d4f' },
    'pending': { text: '待处理', type: 'warning', color: '#faad14' },
    'processing': { text: '处理中', type: 'info', color: '#1890ff' },
    'completed': { text: '已完成', type: 'success', color: '#52c41a' },
    'failed': { text: '失败', type: 'danger', color: '#ff4d4f' }
  };
  
  return statusMap[status] || { text: status, type: 'default', color: '#d9d9d9' };
}