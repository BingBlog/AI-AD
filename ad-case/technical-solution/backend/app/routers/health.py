"""
健康检查路由
"""
from fastapi import APIRouter
from app.schemas.response import BaseResponse
from typing import Dict

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("", response_model=BaseResponse[Dict[str, str]])
async def health_check():
    """健康检查接口"""
    return BaseResponse(
        code=200,
        message="success",
        data={"status": "healthy", "service": "ad-case-api"}
    )
