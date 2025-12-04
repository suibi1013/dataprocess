from typing import Dict, Type, TypeVar, Callable, Any
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')

class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._transients: Dict[str, Type] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """注册单例服务"""
        key = self._get_service_key(interface)
        if implementation is None:
            implementation = interface
        self._singletons[key] = implementation
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """注册瞬态服务"""
        key = self._get_service_key(interface)
        if implementation is None:
            implementation = interface
        self._transients[key] = implementation
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """注册工厂方法"""
        key = self._get_service_key(interface)
        self._factories[key] = factory
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """注册实例"""
        key = self._get_service_key(interface)
        self._services[key] = instance
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析服务"""
        key = self._get_service_key(interface)
        
        # 检查是否已有实例
        if key in self._services:
            return self._services[key]
        
        # 检查单例
        if key in self._singletons:
            instance = self._create_instance(self._singletons[key])
            self._services[key] = instance
            return instance
        
        # 检查工厂方法
        if key in self._factories:
            return self._factories[key]()
        
        # 检查瞬态
        if key in self._transients:
            return self._create_instance(self._transients[key])
        
        # 尝试直接创建
        try:
            return self._create_instance(interface)
        except Exception as e:
            raise ValueError(f"无法解析服务 {interface.__name__}: {str(e)}")
    
    def _create_instance(self, cls: Type[T]) -> T:
        """创建实例，自动注入依赖"""
        # 获取构造函数参数
        sig = inspect.signature(cls.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                # 递归解析依赖
                params[param_name] = self.resolve(param.annotation)
            elif param.default != inspect.Parameter.empty:
                # 使用默认值
                params[param_name] = param.default
            else:
                raise ValueError(f"无法解析参数 {param_name} 在类 {cls.__name__} 中")
        
        return cls(**params)
    
    def _get_service_key(self, interface: Type) -> str:
        """获取服务键"""
        return f"{interface.__module__}.{interface.__name__}"

# 全局容器实例
container = DIContainer()

def get_container() -> DIContainer:
    """获取全局容器"""
    return container

def inject(interface: Type[T]) -> T:
    """依赖注入装饰器函数"""
    return container.resolve(interface)