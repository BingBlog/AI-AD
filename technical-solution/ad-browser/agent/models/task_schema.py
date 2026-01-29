"""agent.models.task_schema

任务相关模型。

对应技术文档 `AGET-TECH_MVP.md`：
- 第 6 节 插件 ↔ Agent 通信协议（START_TASK 等）
- 第 5 节 状态机（用于状态回传）
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskRequest(BaseModel):
    """任务请求（Agent 内部表示）"""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="任务 ID")
    platform: str = Field(default="xiaohongshu", description="平台")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    max_items: int = Field(default=10, ge=1, le=10, description="最大详情数（<=10）")


class TaskStatus(BaseModel):
    """任务状态（用于进度回传/内部状态）"""

    model_config = ConfigDict(extra="forbid")

    state: str = Field(..., description="状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度（0-100）")
    message: str = Field(default="", description="状态说明")


# 下面是协议层模型（可复用在后续 WebSocket server/protocol 实现中）
class StartTaskPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    platform: str = Field(default="xiaohongshu")
    keywords: List[str] = Field(default_factory=list)
    max_items: int = Field(default=10, ge=1, le=10)


class StartTaskMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["START_TASK"]
    task_id: str
    payload: StartTaskPayload


class StatusUpdateMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["STATUS_UPDATE"] = "STATUS_UPDATE"
    state: str
    progress: int = Field(ge=0, le=100)
    message: str = ""


class TaskResultMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["TASK_RESULT"] = "TASK_RESULT"
    results: list[dict] = Field(default_factory=list)


class ErrorMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["ERROR"] = "ERROR"
    error: str
    task_id: Optional[str] = None
