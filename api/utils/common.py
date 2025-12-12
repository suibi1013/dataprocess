import hashlib
import base64
import threading

class CommonUtils:
    @staticmethod
    def generate_unique_code(text: str):        
        """
        根据文本生成稳定的标识码（不可逆）。
        
        Args:
            text (str): 字符串文本（可以包含中文）
        
        Returns:
            str: 32位十六进制的MD5标识码
        """
        # 1. 将文本字符串编码为UTF-8字节序列
        # 这确保了中文、英文、特殊字符都能被正确处理
        text_bytes = text.encode('utf-8')
        
        # 2. 创建MD5哈希对象并更新数据
        hash_object = hashlib.md5()
        hash_object.update(text_bytes)
        
        # 3. 获取十六进制表示的哈希值
        unique_code = hash_object.hexdigest()
        
        return unique_code

    def encode_text_to_code(text: str) -> str:
        """
        将文本编码为Base64字符串（可逆）。
        
        Args:
            text (str): 原始文本
        
        Returns:
            str: Base64编码后的字符串
        """
        # 将字符串编码为UTF-8字节，再进行Base64编码
        text_bytes = text.encode('utf-8')
        
        # 使用 URL安全的Base64编码，并去除填充符 '='
        code_bytes = base64.urlsafe_b64encode(text_bytes)
        code = code_bytes.decode('ascii').rstrip('=')  # Base64结果是ASCII字符
        return code

    def decode_code_to_text(code: str) -> str:
        """
        将用于文件名的Base64字符串解码为原始文本。
        
        Args:
            code (str): 经过 encode_text_to_code 编码后的字符串
        
        Returns:
            str: 解码得到的原始文本
        """
        # 计算需要补回多少个 '=' 才能使长度成为4的倍数
        missing_padding = len(code) % 4
        if missing_padding:
            # 补齐到4的倍数
            code += '=' * (4 - missing_padding)
        
        # 使用 URL安全的Base64解码
        text_bytes = base64.urlsafe_b64decode(code)
        
        # 将字节解码为UTF-8字符串
        text = text_bytes.decode('utf-8')
        
        return text


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