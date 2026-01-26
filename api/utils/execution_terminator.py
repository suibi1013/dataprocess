import threading
class ExecutionTerminator:
    """
    执行终止管理器
    用于管理和跟踪各个流程执行的终止状态和执行状态
    """
    # 流程状态常量
    STATUS_IDLE = "idle"           # 空闲状态，未执行
    STATUS_RUNNING = "running"     # 运行中
    STATUS_COMPLETED = "completed" # 执行完成
    STATUS_FAILED = "failed"       # 执行失败
    STATUS_TERMINATED = "terminated" # 被终止
    
    def __init__(self):
        # 存储每个流程的终止标志，键为流程ID，值为终止标志
        self.terminate_flags = {}
        # 存储每个流程的执行状态，键为流程ID，值为状态字符串
        self.flow_status = {}
        # 线程锁，用于保护共享资源
        self._lock = threading.RLock()
    
    def set_terminate_flag(self, flow_id: str):
        """
        设置流程终止标志
        
        Args:
            flow_id: 流程ID
        """
        with self._lock:
            self.terminate_flags[flow_id] = True
    
    def clear_terminate_flag(self, flow_id: str):
        """
        清除流程终止标志
        
        Args:
            flow_id: 流程ID
        """
        with self._lock:
            if flow_id in self.terminate_flags:
                del self.terminate_flags[flow_id]
    
    def should_terminate(self, flow_id: str) -> bool:
        """
        检查流程是否应该终止
        
        Args:
            flow_id: 流程ID
        
        Returns:
            bool: True表示应该终止，False表示继续执行
        """
        with self._lock:
            return self.terminate_flags.get(flow_id, False)
    
    def get_all_terminate_flags(self) -> dict:
        """
        获取所有流程的终止标志
        
        Returns:
            dict: 所有流程的终止标志
        """
        with self._lock:
            return self.terminate_flags.copy()
    
    def set_flow_status(self, flow_id: str, status: str):
        """
        设置流程执行状态
        
        Args:
            flow_id: 流程ID
            status: 执行状态，必须是STATUS_IDLE, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED, STATUS_TERMINATED之一
        """
        with self._lock:
            # 验证状态值的合法性
            valid_statuses = [
                self.STATUS_IDLE,
                self.STATUS_RUNNING,
                self.STATUS_COMPLETED,
                self.STATUS_FAILED,
                self.STATUS_TERMINATED
            ]
            if status not in valid_statuses:
                raise ValueError(f"无效的状态值: {status}，必须是{valid_statuses}之一")
            
            self.flow_status[flow_id] = status
    
    def get_flow_status(self, flow_id: str) -> str:
        """
        获取流程执行状态
        
        Args:
            flow_id: 流程ID
        
        Returns:
            str: 流程执行状态
        """
        with self._lock:
            return self.flow_status.get(flow_id, self.STATUS_IDLE)
    
    def clear_flow_status(self, flow_id: str):
        """
        清除流程执行状态
        
        Args:
            flow_id: 流程ID
        """
        with self._lock:
            if flow_id in self.flow_status:
                del self.flow_status[flow_id]
    
    def get_all_flow_statuses(self) -> dict:
        """
        获取所有流程的执行状态
        
        Returns:
            dict: 所有流程的执行状态
        """
        with self._lock:
            return self.flow_status.copy()
    
    def reset_flow(self, flow_id: str):
        """
        重置流程的终止标志和状态
        
        Args:
            flow_id: 流程ID
        """
        with self._lock:
            self.clear_terminate_flag(flow_id)
            self.set_flow_status(flow_id, self.STATUS_IDLE)


# 创建全局的执行终止管理器实例
execution_terminator = ExecutionTerminator()