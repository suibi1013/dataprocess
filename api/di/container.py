from typing import Dict, Type, TypeVar, Callable, Any
from abc import ABC, abstractmethod
import inspect
import threading

T = TypeVar('T')

class DIContainer:
    """依赖注入容器，支持单例、瞬态和会话模式"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}  # 单例实例
        self._singletons: Dict[str, Any] = {}  # 单例类型
        self._factories: Dict[str, Callable] = {}  # 工厂方法
        self._transients: Dict[str, Type] = {}  # 瞬态类型
        self._session_services: Dict[str, Type] = {}  # 会话模式类型
        self._session_instances = threading.local()  # 线程本地存储，用于会话实例
    
    def register_singleton(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """注册单例服务
        
        单例模式：整个应用生命周期内只有一个实例
        适用场景：仓储层、数据库连接池等
        """
        key = self._get_service_key(interface)
        if implementation is None:
            implementation = interface
        self._singletons[key] = implementation
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """注册瞬态服务
        
        瞬态模式：每次请求都会创建一个新实例
        适用场景：轻量级、无状态的服务
        """
        key = self._get_service_key(interface)
        if implementation is None:
            implementation = interface
        self._transients[key] = implementation
        return self
    
    def register_session(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """注册会话服务
        
        会话模式：每个线程（HTTP请求）创建一个实例，线程内共享
        适用场景：服务层、应用层等需要线程隔离的场景
        """
        key = self._get_service_key(interface)
        if implementation is None:
            implementation = interface
        self._session_services[key] = implementation
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """注册工厂方法
        
        工厂模式：通过工厂方法创建实例
        适用场景：复杂初始化逻辑的服务
        """
        key = self._get_service_key(interface)
        self._factories[key] = factory
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """注册实例
        
        直接注册实例：容器直接返回注册的实例
        适用场景：外部创建的实例，如配置对象
        """
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
            if key not in self._services:
                instance = self._create_instance(self._singletons[key])
                self._services[key] = instance
            return self._services[key]
        
        # 检查工厂方法
        if key in self._factories:
            return self._factories[key]()
        
        # 检查会话模式
        if key in self._session_services:
            return self._resolve_session_service(key)
        
        # 检查瞬态
        if key in self._transients:
            return self._create_instance(self._transients[key])
        
        # 尝试直接创建
        try:
            return self._create_instance(interface)
        except Exception as e:
            raise ValueError(f"无法解析服务 {interface.__name__}: {str(e)}")
    
    def _resolve_session_service(self, key: str) -> Any:
        """解析会话服务
        
        从线程本地存储中获取会话实例，如果不存在则创建
        """
        try:
            # 初始化线程本地存储
            if not hasattr(self._session_instances, 'instances'):
                self._session_instances.instances = {}
            
            # 如果会话中已有实例，直接返回
            if key in self._session_instances.instances:
                return self._session_instances.instances[key]
            
            # 创建新实例
            instance = self._create_instance(self._session_services[key])
            # 保存到会话实例存储中
            self._session_instances.instances[key] = instance
            return instance
        except Exception as e:
            raise ValueError(f"解析会话服务 {key} 失败: {str(e)}")
    
    def cleanup_session(self) -> None:
        """清理会话实例
        
        调用时机：HTTP请求结束时
        """
        if hasattr(self._session_instances, 'instances'):
            # 清空线程本地存储
            self._session_instances.instances.clear()
    
    def _create_instance(self, cls: Type[T]) -> T:
        """创建实例，自动注入依赖"""
        # 获取构造函数参数
        sig = inspect.signature(cls.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                try:
                    # 递归解析依赖
                    params[param_name] = self.resolve(param.annotation)
                except Exception as e:
                    raise ValueError(f"无法解析参数 {param_name} 的依赖 {param.annotation.__name__} 在类 {cls.__name__} 中: {str(e)}")
            elif param.default != inspect.Parameter.empty:
                # 使用默认值
                params[param_name] = param.default
            else:
                raise ValueError(f"无法解析参数 {param_name} 在类 {cls.__name__} 中，没有类型注解且没有默认值")
        
        try:
            return cls(**params)
        except Exception as e:
            raise ValueError(f"创建类 {cls.__name__} 实例失败: {str(e)}")
    
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