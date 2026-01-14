"""
API 响应 Schema
"""
from typing import Optional, Generic, TypeVar, List, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(description="错误消息")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(description="状态码")
    message: str = Field(description="错误消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    errors: Optional[List[ErrorDetail]] = Field(default=None, description="错误详情列表")
