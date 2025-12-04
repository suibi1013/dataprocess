// 验证工具函数

/**
 * 验证规则接口
 */
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  min?: number;
  max?: number;
  custom?: (_value: any) => boolean | string;
}

/**
 * 验证结果接口
 */
export interface ValidationResult {
  valid: boolean;
  message?: string;
}

/**
 * 验证单个字段
 * @param value - 要验证的值
 * @param rules - 验证规则
 * @param fieldName - 字段名称（用于错误消息）
 * @returns 验证结果
 */
export function validateField(value: any, rules: ValidationRule, fieldName: string = '字段'): ValidationResult {
  // 必填验证
  if (rules.required && (value === null || value === undefined || value === '')) {
    return {
      valid: false,
      message: `${fieldName}不能为空`
    };
  }

  // 如果值为空且不是必填，则通过验证
  if (!rules.required && (value === null || value === undefined || value === '')) {
    return { valid: true };
  }

  const stringValue = String(value);

  // 最小长度验证
  if (rules.minLength !== undefined && stringValue.length < rules.minLength) {
    return {
      valid: false,
      message: `${fieldName}长度不能少于${rules.minLength}个字符`
    };
  }

  // 最大长度验证
  if (rules.maxLength !== undefined && stringValue.length > rules.maxLength) {
    return {
      valid: false,
      message: `${fieldName}长度不能超过${rules.maxLength}个字符`
    };
  }

  // 正则表达式验证
  if (rules.pattern && !rules.pattern.test(stringValue)) {
    return {
      valid: false,
      message: `${fieldName}格式不正确`
    };
  }

  // 数值范围验证
  if (typeof value === 'number') {
    if (rules.min !== undefined && value < rules.min) {
      return {
        valid: false,
        message: `${fieldName}不能小于${rules.min}`
      };
    }

    if (rules.max !== undefined && value > rules.max) {
      return {
        valid: false,
        message: `${fieldName}不能大于${rules.max}`
      };
    }
  }

  // 自定义验证
  if (rules.custom) {
    const customResult = rules.custom(value);
    if (typeof customResult === 'string') {
      return {
        valid: false,
        message: customResult
      };
    }
    if (!customResult) {
      return {
        valid: false,
        message: `${fieldName}验证失败`
      };
    }
  }

  return { valid: true };
}

/**
 * 验证表单对象
 * @param data - 表单数据
 * @param rules - 验证规则映射
 * @returns 验证结果映射
 */
export function validateForm(
  data: Record<string, any>,
  rules: Record<string, ValidationRule>
): Record<string, ValidationResult> {
  const results: Record<string, ValidationResult> = {};

  for (const [fieldName, fieldRules] of Object.entries(rules)) {
    const value = data[fieldName];
    results[fieldName] = validateField(value, fieldRules, fieldName);
  }

  return results;
}

/**
 * 检查表单是否有效
 * @param validationResults - 验证结果映射
 * @returns 是否所有字段都有效
 */
export function isFormValid(validationResults: Record<string, ValidationResult>): boolean {
  return Object.values(validationResults).every(result => result.valid);
}

/**
 * 获取表单错误消息
 * @param validationResults - 验证结果映射
 * @returns 错误消息数组
 */
export function getFormErrors(validationResults: Record<string, ValidationResult>): string[] {
  return Object.values(validationResults)
    .filter(result => !result.valid && result.message)
    .map(result => result.message!);
}

/**
 * 验证邮箱地址
 * @param email - 邮箱地址
 * @returns 是否为有效邮箱
 */
export function isValidEmail(email: string): boolean {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailPattern.test(email);
}

/**
 * 验证URL地址
 * @param url - URL地址
 * @returns 是否为有效URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证手机号码（中国大陆）
 * @param phone - 手机号码
 * @returns 是否为有效手机号
 */
export function isValidPhone(phone: string): boolean {
  const phonePattern = /^1[3-9]\d{9}$/;
  return phonePattern.test(phone);
}

/**
 * 验证IP地址
 * @param ip - IP地址
 * @returns 是否为有效IP地址
 */
export function isValidIP(ip: string): boolean {
  const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipPattern.test(ip);
}

/**
 * 验证端口号
 * @param port - 端口号
 * @returns 是否为有效端口号
 */
export function isValidPort(port: number | string): boolean {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port;
  return Number.isInteger(portNum) && portNum >= 1 && portNum <= 65535;
}

/**
 * 验证JSON字符串
 * @param jsonString - JSON字符串
 * @returns 是否为有效JSON
 */
export function isValidJSON(jsonString: string): boolean {
  try {
    JSON.parse(jsonString);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证数据源名称
 * @param name - 数据源名称
 * @returns 验证结果
 */
export function validateDataSourceName(name: string): ValidationResult {
  return validateField(name, {
    required: true,
    minLength: 2,
    maxLength: 50,
    pattern: /^[\u4e00-\u9fa5a-zA-Z0-9_\-\s]+$/
  }, '数据源名称');
}

/**
 * 验证API URL
 * @param url - API URL
 * @returns 验证结果
 */
export function validateApiUrl(url: string): ValidationResult {
  const result = validateField(url, {
    required: true,
    custom: (value) => isValidUrl(value) || 'URL格式不正确'
  }, 'API URL');

  if (!result.valid) return result;

  // 检查是否为HTTP/HTTPS协议
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return {
      valid: false,
      message: 'URL必须以http://或https://开头'
    };
  }

  return { valid: true };
}

/**
 * 验证数据库连接配置
 * @param config - 数据库配置
 * @returns 验证结果映射
 */
export function validateDatabaseConfig(config: any): Record<string, ValidationResult> {
  return validateForm(config, {
    host: {
      required: true,
      custom: (value) => {
        // 可以是IP地址或域名
        return isValidIP(value) || /^[a-zA-Z0-9.-]+$/.test(value) || 'IP地址或域名格式不正确';
      }
    },
    port: {
      required: true,
      custom: (value) => isValidPort(value) || '端口号必须在1-65535之间'
    },
    database: {
      required: true,
      minLength: 1,
      maxLength: 64
    },
    username: {
      required: true,
      minLength: 1,
      maxLength: 32
    },
    password: {
      required: true,
      minLength: 1
    }
  });
}