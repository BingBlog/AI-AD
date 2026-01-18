"""
爬取任务相关路由
"""
from fastapi import APIRouter, Query, HTTPException, Path
from typing import Optional
from app.schemas.crawl_task import (
    CrawlTaskCreate, CrawlTaskDetail, CrawlTaskListResponse,
    CrawlTaskLogsResponse, CrawlListPageRecordsResponse, CrawlCaseRecordsResponse
)
from app.schemas.response import BaseResponse
from app.services.crawl_task_service import CrawlTaskService
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.repositories.crawl_list_page_repository import CrawlListPageRepository
from app.repositories.crawl_case_record_repository import CrawlCaseRecordRepository

router = APIRouter(prefix="/api/v1/crawl-tasks", tags=["爬取任务"])

# 创建服务实例
task_service = CrawlTaskService()


@router.get("/last-page", response_model=BaseResponse[dict])
async def get_last_crawled_page(
    data_source: str = Query("adquan", description="数据源")
):
    """
    获取上一次爬取到的页数
    """
    try:
        last_page = await CrawlTaskRepository.get_last_crawled_page(data_source)
        return BaseResponse(
            code=200,
            message="success",
            data={"last_page": last_page, "suggested_start_page": (last_page + 1) if last_page is not None else 0}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上一次爬取页数失败: {str(e)}")


@router.post("", response_model=BaseResponse[dict])
async def create_task(request: CrawlTaskCreate):
    """
    创建爬取任务
    """
    try:
        result = await task_service.create_task(request)
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("", response_model=BaseResponse[CrawlTaskListResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选"),
    data_source: Optional[str] = Query(None, description="数据源筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（任务名称或描述）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大 100"),
    sort_by: str = Query("created_at", description="排序字段：created_at, started_at, status, progress"),
    sort_order: str = Query("desc", description="排序顺序：asc, desc"),
):
    """
    获取任务列表
    """
    try:
        result = await task_service.list_tasks(
            status=status,
            data_source=data_source,
            keyword=keyword,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/{task_id}", response_model=BaseResponse[CrawlTaskDetail])
async def get_task_detail(
    task_id: str = Path(..., description="任务ID")
):
    """
    获取任务详情
    """
    try:
        task = await task_service.get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        return BaseResponse(
            code=200,
            message="success",
            data=task
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/{task_id}/start", response_model=BaseResponse[dict])
async def start_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    开始执行任务
    """
    try:
        success = await task_service.start_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法开始执行（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "running"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始任务失败: {str(e)}")


@router.post("/{task_id}/pause", response_model=BaseResponse[dict])
async def pause_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    暂停任务
    """
    try:
        success = await task_service.pause_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法暂停（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "paused"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.post("/{task_id}/resume", response_model=BaseResponse[dict])
async def resume_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    恢复任务
    """
    try:
        success = await task_service.resume_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法恢复（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "running"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")


@router.post("/{task_id}/cancel", response_model=BaseResponse[dict])
async def cancel_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    取消任务
    """
    try:
        success = await task_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法取消（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "cancelled"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/{task_id}/terminate", response_model=BaseResponse[dict])
async def terminate_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    终止任务
    """
    try:
        success = await task_service.terminate_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法终止（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "terminated"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"终止任务失败: {str(e)}")


@router.post("/{task_id}/retry", response_model=BaseResponse[dict])
async def retry_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    重试任务
    """
    try:
        success = await task_service.retry_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法重试（可能状态不正确）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "status": "pending"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.get("/{task_id}/logs", response_model=BaseResponse[CrawlTaskLogsResponse])
async def get_task_logs(
    task_id: str = Path(..., description="任务ID"),
    level: Optional[str] = Query(None, description="日志级别筛选：INFO, WARNING, ERROR"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量，最大 200"),
):
    """
    获取任务日志
    """
    try:
        result = await task_service.get_logs(
            task_id=task_id,
            level=level,
            page=page,
            page_size=page_size
        )
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务日志失败: {str(e)}")


@router.delete("/{task_id}", response_model=BaseResponse[dict])
async def delete_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    删除任务（仅限已完成、已失败、已取消的任务）
    """
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法删除（可能状态不正确或不存在）")
        
        return BaseResponse(
            code=200,
            message="success",
            data={"task_id": task_id, "deleted": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


@router.get("/{task_id}/list-pages", response_model=BaseResponse[CrawlListPageRecordsResponse])
async def get_task_list_pages(
    task_id: str = Path(..., description="任务ID"),
    status: Optional[str] = Query(None, description="状态筛选：success, failed, skipped, pending"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量，最大 200"),
):
    """
    获取任务的列表页记录
    """
    try:
        records, total = await CrawlListPageRepository.list_list_pages(
            task_id=task_id,
            status=status,
            page=page,
            page_size=page_size
        )
        return BaseResponse(
            code=200,
            message="success",
            data=CrawlListPageRecordsResponse(
                records=records,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表页记录失败: {str(e)}")


@router.get("/{task_id}/cases", response_model=BaseResponse[CrawlCaseRecordsResponse])
async def get_task_case_records(
    task_id: str = Path(..., description="任务ID"),
    status: Optional[str] = Query(None, description="状态筛选：success, failed, skipped, validation_failed, pending"),
    list_page_id: Optional[int] = Query(None, description="列表页ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量，最大 200"),
):
    """
    获取任务的案例记录
    """
    try:
        records, total = await CrawlCaseRecordRepository.list_case_records(
            task_id=task_id,
            status=status,
            list_page_id=list_page_id,
            page=page,
            page_size=page_size
        )
        return BaseResponse(
            code=200,
            message="success",
            data=CrawlCaseRecordsResponse(
                records=records,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取案例记录失败: {str(e)}")
