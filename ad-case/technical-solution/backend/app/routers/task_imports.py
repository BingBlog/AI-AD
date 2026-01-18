"""
任务导入相关路由
"""
from fastapi import APIRouter, HTTPException, Path
from pathlib import Path as PathLib
from typing import List
from app.schemas.task_import import (
    ImportStartRequest, ImportStatusResponse, ImportResultResponse, ImportHistoryResponse
)
from app.schemas.response import BaseResponse
from app.services.task_import_service import TaskImportService

router = APIRouter(prefix="/api/v1/crawl-tasks/{task_id}/import", tags=["任务导入"])

# 创建服务实例
import_service = TaskImportService()


@router.post("", response_model=BaseResponse[dict])
async def start_import(
    task_id: str = Path(..., description="任务ID"),
    request: ImportStartRequest = ImportStartRequest(),
):
    """
    启动导入任务
    """

    try:
        result = await import_service.start_import(task_id, request)
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动导入失败: {str(e)}")


@router.get("/status", response_model=BaseResponse[ImportStatusResponse])
async def get_import_status(
    task_id: str = Path(..., description="任务ID")
):
    """
    获取导入状态和进度
    """
    try:
        result = await import_service.get_import_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="未找到导入记录")
        
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导入状态失败: {str(e)}")


@router.post("/cancel", response_model=BaseResponse[dict])
async def cancel_import(
    task_id: str = Path(..., description="任务ID")
):
    """
    取消导入任务
    """
    try:
        success = await import_service.cancel_import(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="导入任务无法取消（可能状态不正确或不存在）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "cancelled"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消导入失败: {str(e)}")


@router.get("/result", response_model=BaseResponse[ImportResultResponse])
async def get_import_result(
    task_id: str = Path(..., description="任务ID")
):
    """
    获取导入结果
    """
    try:
        result = await import_service.get_import_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="未找到导入记录")
        
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导入结果失败: {str(e)}")


@router.get("/history", response_model=BaseResponse[ImportHistoryResponse])
async def get_import_history(
    task_id: str = Path(..., description="任务ID")
):
    """
    获取导入历史
    """
    try:
        result = await import_service.get_import_history(task_id)
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导入历史失败: {str(e)}")


@router.get("/batch-files", response_model=BaseResponse[List[str]])
async def get_batch_files(
    task_id: str = Path(..., description="任务ID")
):
    """
    获取任务的批次文件列表
    """
    try:
        # 获取任务数据目录
        task_data_dir = PathLib("data/json") / task_id
        if not task_data_dir.exists():
            return BaseResponse(
                code=200,
                message="success",
                data=[]
            )
        
        # 查找所有批次文件
        batch_files = sorted(task_data_dir.glob("cases_batch_*.json"))
        file_names = [f.name for f in batch_files]
        
        return BaseResponse(
            code=200,
            message="success",
            data=file_names
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批次文件列表失败: {str(e)}")
