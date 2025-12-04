"""
日志配置模块

提供统一的日志记录配置和管理
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置类"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        初始化日志配置
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
            max_file_size: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
        """
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper())
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
    
    def setup_logger(self, name: str = "ppt_converter") -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 避免重复配置
        if logger.handlers:
            return logger
        
        logger.setLevel(self.log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器（带轮转）
        log_file = os.path.join(self.log_dir, f"{name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 错误文件处理器
        error_log_file = os.path.join(self.log_dir, f"{name}_error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.addHandler(error_handler)
        
        return logger


class OperationLogger:
    """操作日志记录器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化操作日志记录器
        
        Args:
            logger: 可选的日志记录器实例
        """
        self.logger = logger or LoggerConfig().setup_logger()
    
    def log_operation_start(self, operation: str, **kwargs):
        """记录操作开始"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"🚀 开始操作: {operation} | {context}")
    
    def log_operation_success(self, operation: str, duration: float = None, **kwargs):
        """记录操作成功"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        duration_str = f" | 耗时: {duration:.2f}秒" if duration else ""
        self.logger.info(f"✅ 操作成功: {operation} | {context}{duration_str}")
    
    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """记录操作错误"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.error(f"❌ 操作失败: {operation} | {context} | 错误: {str(error)}", exc_info=True)
    
    def log_operation_warning(self, operation: str, message: str, **kwargs):
        """记录操作警告"""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.warning(f"⚠️ 操作警告: {operation} | {context} | {message}")


def get_logger(name: str = "ppt_converter") -> logging.Logger:
    """
    获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return LoggerConfig().setup_logger(name)


def log_performance(func):
    """
    性能监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        operation_logger = OperationLogger(logger)
        
        # 记录开始
        operation_logger.log_operation_start(
            func.__name__,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录成功
            operation_logger.log_operation_success(
                func.__name__,
                duration=duration,
                result_type=type(result).__name__
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录错误
            operation_logger.log_operation_error(
                func.__name__,
                e,
                duration=duration
            )
            
            raise
    
    return wrapper


# 使用示例（生产环境中已禁用）