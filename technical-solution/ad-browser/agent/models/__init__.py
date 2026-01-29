"""数据模型模块"""

from .case_schema import MarketingCase
from .task_schema import (
    ErrorMessage,
    StartTaskMessage,
    StartTaskPayload,
    StatusUpdateMessage,
    TaskRequest,
    TaskResultMessage,
    TaskStatus,
)

__all__ = [
    "MarketingCase",
    "TaskRequest",
    "TaskStatus",
    "StartTaskPayload",
    "StartTaskMessage",
    "StatusUpdateMessage",
    "TaskResultMessage",
    "ErrorMessage",
]
