"""
异常处理框架

定义自定义异常类，提供统一的异常处理机制。
符合第 15 节异常策略：页面异常直接跳过，最多重试 1 次。
"""
from typing import Optional


class AgentException(Exception):
    """Agent 基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码（可选）
            details: 错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """异常的字符串表示"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class StateMachineException(AgentException):
    """状态机异常"""
    
    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        target_state: Optional[str] = None
    ):
        """
        初始化状态机异常
        
        Args:
            message: 错误消息
            current_state: 当前状态
            target_state: 目标状态
        """
        details = {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state
        
        super().__init__(
            message,
            error_code="STATE_MACHINE_ERROR",
            details=details
        )


class BrowserAdapterException(AgentException):
    """Browser Adapter 异常"""
    
    def __init__(
        self,
        message: str,
        action: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        初始化 Browser Adapter 异常
        
        Args:
            message: 错误消息
            action: 执行的操作
            url: 相关 URL
        """
        details = {}
        if action:
            details["action"] = action
        if url:
            details["url"] = url
        
        super().__init__(
            message,
            error_code="BROWSER_ADAPTER_ERROR",
            details=details
        )


class LLMException(AgentException):
    """LLM 调用异常"""
    
    def __init__(
        self,
        message: str,
        task_type: Optional[str] = None,
        retry_count: Optional[int] = None
    ):
        """
        初始化 LLM 异常
        
        Args:
            message: 错误消息
            task_type: 任务类型（相关性判断、提取、洞察）
            retry_count: 重试次数
        """
        details = {}
        if task_type:
            details["task_type"] = task_type
        if retry_count is not None:
            details["retry_count"] = retry_count
        
        super().__init__(
            message,
            error_code="LLM_ERROR",
            details=details
        )


class TaskException(AgentException):
    """任务执行异常"""
    
    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        state: Optional[str] = None
    ):
        """
        初始化任务异常
        
        Args:
            message: 错误消息
            task_id: 任务 ID
            state: 任务状态
        """
        details = {}
        if task_id:
            details["task_id"] = task_id
        if state:
            details["state"] = state
        
        super().__init__(
            message,
            error_code="TASK_ERROR",
            details=details
        )


class ConfigurationException(AgentException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        初始化配置异常
        
        Args:
            message: 错误消息
            config_key: 配置键名
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            details=details
        )


class ValidationException(AgentException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[any] = None
    ):
        """
        初始化验证异常
        
        Args:
            message: 错误消息
            field: 字段名
            value: 字段值
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details=details
        )
