"""
任务导入服务层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.repositories.task_import_repository import TaskImportRepository
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.services.import_task_executor import (
    ImportTaskExecutor, register_import_executor, get_import_executor, unregister_import_executor
)
from app.schemas.task_import import (
    ImportStartRequest, ImportStatusResponse, ImportProgress, ImportStats,
    ImportResultResponse, ImportResult, ImportError, ImportHistoryResponse, ImportHistoryItem
)
import asyncio


class TaskImportService:
    """任务导入服务类"""

    def __init__(self):
        self.repo = TaskImportRepository()
        self.task_repo = CrawlTaskRepository()

    async def start_import(self, task_id: str, request: ImportStartRequest) -> Dict[str, Any]:
        """
        启动导入任务

        Returns:
            导入信息（包含 import_id）
        """
        # 检查任务是否存在且已完成
        task_data = await self.task_repo.get_task(task_id)
        if not task_data:
            raise ValueError(f"任务 {task_id} 不存在")

        if task_data["status"] != "completed":
            raise ValueError(f"任务 {task_id} 未完成，无法导入")

        if task_data.get("total_saved", 0) == 0:
            raise ValueError(f"任务 {task_id} 没有已保存的数据")

        # 检查是否已有导入任务在运行
        latest_import = await self.repo.get_latest_import(task_id)
        if latest_import and latest_import["status"] == "running":
            # 验证是否真的有执行器在运行
            import_id = latest_import["import_id"]
            executor = get_import_executor(import_id)
            if executor and executor.is_running:
                raise ValueError(f"任务 {task_id} 已有导入任务在运行")
            else:
                # 没有执行器在运行，更新状态为 failed
                await self.repo.update_import_status(
                    import_id=import_id,
                    status="failed"
                )
                await self.repo.update_import_result(
                    import_id=import_id,
                    error_message="之前的导入任务异常中断，已自动标记为失败"
                )

        # 创建导入记录
        import_id = await self.repo.create_import(
            task_id=task_id,
            import_mode=request.import_mode,
            selected_batches=request.selected_batches,
            skip_existing=request.skip_existing,
            update_existing=request.update_existing,
            generate_vectors=request.generate_vectors,
            skip_invalid=request.skip_invalid,
            batch_size=request.batch_size,
        )

        # 添加创建日志
        await self.task_repo.add_log(
            task_id=task_id,
            level="INFO",
            message=f"开始导入数据到数据库",
            details={"import_id": import_id, "config": request.dict()}
        )

        # 创建并启动导入执行器
        executor = ImportTaskExecutor(task_id, import_id)
        register_import_executor(import_id, executor)

        # 在后台启动导入任务
        asyncio.create_task(executor.execute(
            import_mode=request.import_mode,
            selected_batches=request.selected_batches,
            import_failed_only=request.import_failed_only,
            skip_existing=request.skip_existing,
            update_existing=request.update_existing,
            generate_vectors=request.generate_vectors,
            skip_invalid=request.skip_invalid,
            batch_size=request.batch_size,
            normalize_data=request.normalize_data,
        ))

        return {
            "import_id": import_id,
            "task_id": task_id,
            "status": "running",
            "started_at": datetime.now().isoformat()
        }

    async def get_import_status(self, task_id: str) -> Optional[ImportStatusResponse]:
        """获取导入状态和进度"""
        latest_import = await self.repo.get_latest_import(task_id)
        if not latest_import:
            return None

        import_id = latest_import["import_id"]
        
        # 检查状态为 running 的导入任务是否真的在运行
        if latest_import["status"] == "running":
            executor = get_import_executor(import_id)
            started_at = latest_import.get("started_at")
            
            # 如果没有执行器在运行，且 started_at 为空或超过5分钟，认为任务已失效
            if not executor or (executor and not executor.is_running):
                if not started_at:
                    # started_at 为空，说明任务从未真正启动，更新为 failed
                    await self.repo.update_import_status(
                        import_id=import_id,
                        status="failed"
                    )
                    await self.repo.update_import_result(
                        import_id=import_id,
                        error_message="导入任务启动失败或异常中断"
                    )
                    # 重新获取更新后的状态
                    latest_import = await self.repo.get_import(import_id)
                    if not latest_import:
                        return None
                else:
                    # 检查是否超过5分钟
                    from datetime import timezone
                    started_at_dt = None
                    
                    # 转换 started_at 为 datetime 对象
                    if isinstance(started_at, str):
                        try:
                            started_at_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            started_at_dt = None
                    elif isinstance(started_at, datetime):
                        started_at_dt = started_at
                    
                    if started_at_dt:
                        now = datetime.now(started_at_dt.tzinfo if started_at_dt.tzinfo else timezone.utc)
                        elapsed = (now - started_at_dt).total_seconds()
                        
                        if elapsed > 300:  # 5分钟
                            # 超过5分钟，认为任务已失效
                            await self.repo.update_import_status(
                                import_id=import_id,
                                status="failed"
                            )
                            await self.repo.update_import_result(
                                import_id=import_id,
                                error_message=f"导入任务异常中断（超过{int(elapsed/60)}分钟未更新）"
                            )
                            # 重新获取更新后的状态
                            latest_import = await self.repo.get_import(import_id)
                            if not latest_import:
                                return None

        # 计算进度百分比
        percentage = 0.0
        if latest_import.get("total_cases", 0) > 0:
            imported = latest_import.get("imported_cases", 0)
            total = latest_import["total_cases"]
            percentage = min((imported / total) * 100, 100.0)

        # 计算预计剩余时间
        estimated_time = None
        if latest_import.get("started_at") and latest_import.get("imported_cases", 0) > 0:
            started_at = latest_import["started_at"]
            started_at_dt = None
            
            # 转换 started_at 为 datetime 对象
            if isinstance(started_at, str):
                try:
                    from datetime import timezone
                    started_at_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    started_at_dt = None
            elif isinstance(started_at, datetime):
                started_at_dt = started_at
            
            # 计算预计剩余时间
            if started_at_dt:
                from datetime import timezone
                now = datetime.now(started_at_dt.tzinfo if started_at_dt.tzinfo else timezone.utc)
                elapsed = (now - started_at_dt).total_seconds()
                imported = latest_import.get("imported_cases", 0)
                if imported > 0:
                    avg_time_per_case = elapsed / imported
                    remaining = (latest_import.get("total_cases", 0) - imported)
                    estimated_time = int(remaining * avg_time_per_case)

        progress = ImportProgress(
            total_cases=latest_import.get("total_cases", 0),
            loaded_cases=latest_import.get("loaded_cases", 0),
            valid_cases=latest_import.get("valid_cases", 0),
            invalid_cases=latest_import.get("invalid_cases", 0),
            existing_cases=latest_import.get("existing_cases", 0),
            imported_cases=latest_import.get("imported_cases", 0),
            failed_cases=latest_import.get("failed_cases", 0),
            current_file=latest_import.get("current_file"),
            percentage=percentage,
            estimated_remaining_time=estimated_time
        )

        stats = ImportStats(
            total_loaded=latest_import.get("loaded_cases", 0),
            total_valid=latest_import.get("valid_cases", 0),
            total_invalid=latest_import.get("invalid_cases", 0),
            total_existing=latest_import.get("existing_cases", 0),
            total_imported=latest_import.get("imported_cases", 0),
            total_failed=latest_import.get("failed_cases", 0)
        )

        return ImportStatusResponse(
            import_id=import_id,
            task_id=task_id,
            status=latest_import["status"],
            progress=progress,
            stats=stats,
            started_at=latest_import.get("started_at"),
            updated_at=latest_import.get("updated_at")
        )

    async def cancel_import(self, task_id: str) -> bool:
        """取消导入任务"""
        latest_import = await self.repo.get_latest_import(task_id)
        if not latest_import:
            return False

        if latest_import["status"] != "running":
            return False

        import_id = latest_import["import_id"]

        # 通知执行器取消
        executor = get_import_executor(import_id)
        if executor:
            await executor.cancel()

        # 更新状态
        success = await self.repo.update_import_status(
            import_id=import_id,
            status="cancelled",
            cancelled_at=datetime.now()
        )

        if success:
            await self.task_repo.add_log(
                task_id=task_id,
                level="WARNING",
                message="导入任务已取消"
            )
            unregister_import_executor(import_id)

        return success

    async def get_import_result(self, task_id: str) -> Optional[ImportResultResponse]:
        """获取导入结果"""
        latest_import = await self.repo.get_latest_import(task_id)
        if not latest_import:
            return None

        import_id = latest_import["import_id"]

        # 获取错误列表
        errors_data = await self.repo.get_import_errors(import_id)
        errors = []
        for error_data in errors_data:
            errors.append(ImportError(
                file=error_data.get("file_name"),
                case_id=error_data.get("case_id"),
                error=error_data.get("error_message", "")
            ))

        result = ImportResult(
            total_loaded=latest_import.get("loaded_cases", 0),
            total_valid=latest_import.get("valid_cases", 0),
            total_invalid=latest_import.get("invalid_cases", 0),
            total_existing=latest_import.get("existing_cases", 0),
            total_imported=latest_import.get("imported_cases", 0),
            total_failed=latest_import.get("failed_cases", 0),
            duration_seconds=latest_import.get("duration_seconds"),
            started_at=latest_import.get("started_at"),
            completed_at=latest_import.get("completed_at")
        )

        return ImportResultResponse(
            import_id=import_id,
            task_id=task_id,
            status=latest_import["status"],
            result=result,
            errors=errors
        )

    async def get_import_history(self, task_id: str) -> ImportHistoryResponse:
        """获取导入历史"""
        imports_data = await self.repo.get_task_imports(task_id)

        imports = []
        for import_data in imports_data:
            imports.append(ImportHistoryItem(
                import_id=import_data["import_id"],
                status=import_data["status"],
                total_imported=import_data.get("imported_cases", 0),
                started_at=import_data.get("started_at"),
                completed_at=import_data.get("completed_at")
            ))

        return ImportHistoryResponse(
            imports=imports,
            total=len(imports)
        )
