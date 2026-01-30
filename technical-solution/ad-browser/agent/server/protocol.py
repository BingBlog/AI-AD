"""agent.server.protocol

消息协议实现

职责：
- 定义消息协议（第 6 节）
- 实现消息序列化/反序列化
- 实现消息验证
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Union

from agent.exceptions import ValidationException
from agent.models.case_schema import MarketingCase
from agent.models.task_schema import (
    ErrorMessage,
    StartTaskMessage,
    StatusUpdateMessage,
    TaskResultMessage,
)

logger = None


def _get_logger():
    """延迟导入 logger，避免循环依赖"""
    global logger
    if logger is None:
        from agent.utils.logger import get_logger

        logger = get_logger(__name__)
    return logger


# 消息类型联合
Message = Union[StartTaskMessage, StatusUpdateMessage, TaskResultMessage, ErrorMessage]


def parse_message(data: str) -> Message:
    """
    解析消息（从 JSON 字符串）

    Args:
        data: JSON 字符串

    Returns:
        消息对象

    Raises:
        ValidationException: 消息格式错误或类型未知
    """
    log = _get_logger()

    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValidationException(f"消息 JSON 解析失败: {e}", field="data", value=data[:100])

    msg_type = obj.get("type")
    if not msg_type:
        raise ValidationException("消息缺少 type 字段", field="type")

    try:
        if msg_type == "START_TASK":
            return StartTaskMessage(**obj)
        elif msg_type == "STATUS_UPDATE":
            return StatusUpdateMessage(**obj)
        elif msg_type == "TASK_RESULT":
            # TaskResultMessage 的 results 字段需要是 MarketingCase 列表
            # 但序列化后是 dict 列表，需要转换
            results_data = obj.get("results", [])
            if results_data and isinstance(results_data[0], dict):
                # 已经是 dict，直接使用
                return TaskResultMessage(**obj)
            elif results_data and isinstance(results_data[0], MarketingCase):
                # 是 MarketingCase 对象，转换为 dict
                obj["results"] = [case.model_dump() if hasattr(case, "model_dump") else case for case in results_data]
                return TaskResultMessage(**obj)
            else:
                return TaskResultMessage(**obj)
        elif msg_type == "ERROR":
            return ErrorMessage(**obj)
        else:
            raise ValidationException(f"未知的消息类型: {msg_type}", field="type", value=msg_type)
    except Exception as e:
        log.error(f"消息解析失败: {e}, 消息类型: {msg_type}")
        raise ValidationException(f"消息解析失败: {e}", field="message", value=str(obj)[:200])


def serialize_message(message: Message) -> str:
    """
    序列化消息（转换为 JSON 字符串）

    Args:
        message: 消息对象

    Returns:
        JSON 字符串
    """
    if isinstance(message, TaskResultMessage):
        # TaskResultMessage 的 results 可能是 MarketingCase 对象列表
        # 需要转换为 dict
        data = message.model_dump()
        if "results" in data and data["results"]:
            results = []
            for item in data["results"]:
                if isinstance(item, MarketingCase):
                    results.append(item.model_dump())
                elif isinstance(item, dict):
                    results.append(item)
                else:
                    results.append(item)
            data["results"] = results
        return json.dumps(data, ensure_ascii=False)
    else:
        return json.dumps(message.model_dump(), ensure_ascii=False)


def validate_message(message: Message) -> bool:
    """
    验证消息格式

    Args:
        message: 消息对象

    Returns:
        True 表示验证通过

    Raises:
        ValidationException: 验证失败
    """
    if isinstance(message, StartTaskMessage):
        if not message.task_id:
            raise ValidationException("START_TASK 消息缺少 task_id", field="task_id")
        if not message.payload:
            raise ValidationException("START_TASK 消息缺少 payload", field="payload")
    elif isinstance(message, StatusUpdateMessage):
        if not 0 <= message.progress <= 100:
            raise ValidationException(f"进度值超出范围: {message.progress}", field="progress", value=message.progress)
    elif isinstance(message, ErrorMessage):
        if not message.error:
            raise ValidationException("ERROR 消息缺少 error 字段", field="error")

    return True
