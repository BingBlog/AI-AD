"""
爬取任务服务层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.services.crawl_task_executor import CrawlTaskExecutor, register_executor, get_executor, unregister_executor
from app.schemas.crawl_task import (
    CrawlTaskCreate, CrawlTaskDetail, CrawlTaskListItem,
    CrawlTaskListResponse, CrawlTaskLogsResponse, CrawlTaskLog,
    CrawlTaskProgress, CrawlTaskStats, CrawlTaskTimeline, CrawlTaskConfig
)
import asyncio


class CrawlTaskService:
    """爬取任务服务类"""

    def __init__(self):
        self.repo = CrawlTaskRepository()

    async def create_task(self, request: CrawlTaskCreate, created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        创建任务

        Returns:
            任务信息（包含 task_id）
        """
        # 如果 start_page 为空，自动设置为上一次爬取到的页数
        start_page = request.start_page
        if start_page is None:
            last_page = await CrawlTaskRepository.get_last_crawled_page(request.data_source)
            start_page = (last_page + 1) if last_page is not None else 0
        
        # 验证 end_page 必须大于等于 start_page
        if request.end_page < start_page:
            raise ValueError(f"结束页码 ({request.end_page}) 必须大于等于起始页码 ({start_page})")
        
        task_id = await self.repo.create_task(
            name=request.name,
            data_source=request.data_source,
            description=request.description,
            start_page=start_page,
            end_page=request.end_page,
            case_type=request.case_type,
            search_value=request.search_value,
            batch_size=request.batch_size,
            delay_min=request.delay_min,
            delay_max=request.delay_max,
            enable_resume=request.enable_resume,
            created_by=created_by
        )

        # 计算总页数
        total_pages = None
        if request.end_page is not None:
            total_pages = request.end_page - request.start_page + 1

        # 更新总页数
        if total_pages:
            from app.database import db
            await db.execute(
                "UPDATE crawl_tasks SET total_pages = $1 WHERE task_id = $2",
                total_pages, task_id
            )

        # 添加创建日志
        await self.repo.add_log(
            task_id=task_id,
            level="INFO",
            message=f"任务已创建: {request.name}",
            details={"config": request.dict()}
        )

        # 如果立即执行，启动任务
        if request.execute_immediately:
            await self.start_task(task_id)

        return {
            "task_id": task_id,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

    async def _update_field(self, task_id: str, field: str, value: Any):
        """更新单个字段（内部方法）"""
        query = f"UPDATE crawl_tasks SET {field} = $1, updated_at = CURRENT_TIMESTAMP WHERE task_id = $2"
        from app.database import db
        await db.execute(query, value, task_id)

    async def get_task_detail(self, task_id: str) -> Optional[CrawlTaskDetail]:
        """获取任务详情"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return None

        return self._convert_to_detail(task_data)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        data_source: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> CrawlTaskListResponse:
        """获取任务列表"""
        tasks_data, total = await self.repo.list_tasks(
            status=status,
            data_source=data_source,
            keyword=keyword,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        tasks = [self._convert_to_list_item(task_data) for task_data in tasks_data]

        return CrawlTaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size
        )

    async def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        if task_data["status"] != "pending":
            return False

        # 使用任务创建时的起始页码
        start_page = task_data["start_page"]
        return await self.start_task_from_page(task_id, start_page)
    
    async def start_task_from_page(self, task_id: str, start_page: int) -> bool:
        """从指定页码开始执行任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        # 检查是否已有执行器在运行
        executor = get_executor(task_id)
        if executor and executor.is_running:
            return False

        # 更新状态为 running
        success = await self.repo.update_task_status(
            task_id=task_id,
            status="running",
            started_at=datetime.now()
        )

        if success:
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message=f"任务开始执行（从第 {start_page} 页开始）"
            )

            # 创建并启动任务执行器
            executor = CrawlTaskExecutor(task_id)
            register_executor(task_id, executor)

            # 在后台启动任务
            asyncio.create_task(executor.execute(
                name=task_data["name"],
                data_source=task_data["data_source"],
                start_page=start_page,
                end_page=task_data.get("end_page"),
                case_type=task_data.get("case_type"),
                search_value=task_data.get("search_value"),
                batch_size=task_data.get("batch_size", 30),
                delay_min=task_data.get("delay_min", 2.0),
                delay_max=task_data.get("delay_max", 5.0),
                enable_resume=task_data.get("enable_resume", True)
            ))

        return success

    async def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        if task_data["status"] != "running":
            return False

        # 通知执行器暂停
        executor = get_executor(task_id)
        if executor:
            await executor.pause()

        success = await self.repo.update_task_status(
            task_id=task_id,
            status="paused",
            paused_at=datetime.now()
        )

        if success:
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message="任务已暂停"
            )

        return success

    async def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        # 检查任务状态
        current_status = task_data["status"]
        
        # 如果任务不是 paused 状态，检查是否可以恢复
        if current_status != "paused":
            # 如果任务已经失败或完成，不允许恢复
            if current_status in ["failed", "completed", "terminated", "cancelled"]:
                return False
            # 如果任务正在运行，不需要恢复
            if current_status == "running":
                return False

        # 通知执行器恢复
        executor = get_executor(task_id)
        if executor and executor.is_running:
            # 执行器存在且正在运行，尝试恢复
            resume_success = await executor.resume()
            if not resume_success:
                # 如果执行器无法恢复（可能已经完成），重新启动
                # 获取当前应该继续的页码
                current_page = task_data.get("current_page")
                resume_start_page = current_page if current_page is not None else task_data["start_page"]
                await self.repo.update_task_status(
                    task_id=task_id,
                    status="pending"
                )
                return await self.start_task_from_page(task_id, resume_start_page)
        else:
            # 如果没有执行器或执行器已停止，重新启动任务
            # 获取当前应该继续的页码（使用 current_page，如果没有则使用 start_page）
            current_page = task_data.get("current_page")
            resume_start_page = current_page if current_page is not None else task_data["start_page"]
            
            # 先将状态重置为 pending，然后启动
            await self.repo.update_task_status(
                task_id=task_id,
                status="pending"
            )
            return await self.start_task_from_page(task_id, resume_start_page)

        success = await self.repo.update_task_status(
            task_id=task_id,
            status="running"
        )

        if success:
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message="任务已恢复"
            )

        return success

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        if task_data["status"] not in ["pending", "paused"]:
            return False

        success = await self.repo.update_task_status(
            task_id=task_id,
            status="cancelled"
        )

        if success:
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message="任务已取消"
            )

        return success

    async def terminate_task(self, task_id: str) -> bool:
        """终止任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        if task_data["status"] != "running":
            return False

        # 通知执行器终止
        executor = get_executor(task_id)
        if executor:
            await executor.stop()

        success = await self.repo.update_task_status(
            task_id=task_id,
            status="terminated"
        )

        if success:
            await self.repo.add_log(
                task_id=task_id,
                level="WARNING",
                message="任务已终止"
            )
            unregister_executor(task_id)

        return success

    async def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        # 允许重试失败、已完成但有失败案例、或已终止的任务
        if task_data["status"] not in ["failed", "completed", "terminated"]:
            return False

        # 如果是已完成的任务，检查是否有失败的案例需要重试
        if task_data["status"] == "completed":
            total_failed = task_data.get("total_failed", 0)
            if total_failed == 0:
                await self.repo.add_log(
                    task_id=task_id,
                    level="INFO",
                    message="任务已完成且无失败案例，无需重试"
                )
                return False

        # 重置状态和错误信息
        success = await self.repo.update_task_status(
            task_id=task_id,
            status="pending"
        )

        if success:
            await self.repo.update_task_error(task_id=task_id, error_message=None, error_stack=None)
            
            # 清除统计信息，准备重新开始
            await self.repo.update_task_progress(
                task_id=task_id,
                completed_pages=0,
                current_page=task_data.get("start_page", 0),
                total_crawled=0,
                total_saved=0,
                total_failed=0,
                batches_saved=0
            )
            
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message="任务已重置，准备重试（将重新爬取失败的案例）"
            )
            # 自动开始执行
            await self.start_task(task_id)

        return success

    async def get_logs(
        self,
        task_id: str,
        level: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> CrawlTaskLogsResponse:
        """获取任务日志"""
        logs_data, total = await self.repo.get_logs(
            task_id=task_id,
            level=level,
            page=page,
            page_size=page_size
        )

        logs = []
        for log_data in logs_data:
            import json
            details = json.loads(log_data["details"]) if log_data.get("details") else None
            logs.append(CrawlTaskLog(
                id=log_data["id"],
                level=log_data["level"],
                message=log_data["message"],
                details=details,
                created_at=log_data["created_at"]
            ))

        return CrawlTaskLogsResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size
        )

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return await self.repo.delete_task(task_id)

    def _convert_to_detail(self, task_data: Dict[str, Any]) -> CrawlTaskDetail:
        """转换为详情对象"""
        # 计算进度百分比
        percentage = 0.0
        status = task_data.get("status", "")
        
        # 如果任务已完成，百分比应该是 100%
        if status == "completed":
            percentage = 100.0
        elif task_data.get("total_pages"):
            completed = task_data.get("completed_pages", 0)
            total = task_data["total_pages"]
            if total > 0:
                percentage = min((completed / total) * 100, 100.0)

        # 计算预计剩余时间
        estimated_time = None
        if task_data.get("started_at") and task_data.get("completed_pages", 0) > 0:
            started_at = task_data["started_at"]
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed = (datetime.now(started_at.tzinfo) - started_at).total_seconds()
            completed = task_data.get("completed_pages", 0)
            if completed > 0:
                avg_time_per_page = elapsed / completed
                remaining = (task_data.get("total_pages", 0) - completed)
                estimated_time = int(remaining * avg_time_per_page)

        # 计算成功率
        success_rate = 0.0
        total_crawled = task_data.get("total_crawled", 0)
        if total_crawled > 0:
            total_saved = task_data.get("total_saved", 0)
            # 确保成功率不超过 1.0，处理数据不一致或浮点数精度问题
            success_rate = min(total_saved / total_crawled, 1.0)

        progress = CrawlTaskProgress(
            total_pages=task_data.get("total_pages"),
            completed_pages=task_data.get("completed_pages", 0),
            current_page=task_data.get("current_page"),
            percentage=percentage,
            estimated_remaining_time=estimated_time
        )

        stats = CrawlTaskStats(
            total_crawled=task_data.get("total_crawled", 0),
            total_saved=task_data.get("total_saved", 0),
            total_failed=task_data.get("total_failed", 0),
            batches_saved=task_data.get("batches_saved", 0),
            success_rate=success_rate,
            avg_speed=task_data.get("avg_speed"),
            avg_delay=task_data.get("avg_delay"),
            error_rate=task_data.get("error_rate")
        )

        timeline = CrawlTaskTimeline(
            created_at=task_data["created_at"],
            started_at=task_data.get("started_at"),
            paused_at=task_data.get("paused_at"),
            completed_at=task_data.get("completed_at")
        )

        config = CrawlTaskConfig(
            start_page=task_data["start_page"],
            end_page=task_data.get("end_page"),
            case_type=task_data.get("case_type"),
            search_value=task_data.get("search_value"),
            batch_size=task_data.get("batch_size", 100),
            delay_min=task_data.get("delay_min", 2.0),
            delay_max=task_data.get("delay_max", 5.0),
            enable_resume=task_data.get("enable_resume", True)
        )

        return CrawlTaskDetail(
            task_id=task_data["task_id"],
            name=task_data["name"],
            data_source=task_data["data_source"],
            description=task_data.get("description"),
            status=task_data["status"],
            config=config,
            progress=progress,
            stats=stats,
            timeline=timeline,
            error_message=task_data.get("error_message"),
            error_stack=task_data.get("error_stack")
        )

    def _convert_to_list_item(self, task_data: Dict[str, Any]) -> CrawlTaskListItem:
        """转换为列表项对象"""
        # 计算进度百分比
        percentage = 0.0
        if task_data.get("total_pages"):
            completed = task_data.get("completed_pages", 0)
            percentage = (completed / task_data["total_pages"]) * 100

        progress = CrawlTaskProgress(
            total_pages=task_data.get("total_pages"),
            completed_pages=task_data.get("completed_pages", 0),
            current_page=task_data.get("current_page"),
            percentage=percentage
        )

        # 计算成功率
        success_rate = 0.0
        total_crawled = task_data.get("total_crawled", 0)
        if total_crawled > 0:
            total_saved = task_data.get("total_saved", 0)
            # 确保成功率不超过 1.0，处理数据不一致或浮点数精度问题
            success_rate = min(total_saved / total_crawled, 1.0)

        stats = CrawlTaskStats(
            total_crawled=task_data.get("total_crawled", 0),
            total_saved=task_data.get("total_saved", 0),
            total_failed=task_data.get("total_failed", 0),
            batches_saved=task_data.get("batches_saved", 0),
            success_rate=success_rate,
            avg_speed=task_data.get("avg_speed"),
            avg_delay=task_data.get("avg_delay"),
            error_rate=task_data.get("error_rate")
        )

        return CrawlTaskListItem(
            task_id=task_data["task_id"],
            name=task_data["name"],
            data_source=task_data["data_source"],
            status=task_data["status"],
            progress=progress,
            stats=stats,
            created_at=task_data["created_at"],
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )
