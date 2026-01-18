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
import logging

logger = logging.getLogger(__name__)


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

    async def restart_task(self, task_id: str) -> bool:
        """重新执行任务（从起始页重新开始）"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        # 允许重新执行已完成、失败或终止的任务
        # 不允许重新执行正在运行或暂停的任务
        if task_data["status"] in ["running", "paused"]:
            return False

        # 检查是否已有执行器在运行
        executor = get_executor(task_id)
        if executor and executor.is_running:
            # 先终止现有执行器
            await executor.stop()
            unregister_executor(task_id)

        # 重置状态和错误信息
        success = await self.repo.update_task_status(
            task_id=task_id,
            status="pending"
        )

        if success:
            await self.repo.update_task_error(task_id=task_id, error_message=None, error_stack=None)
            
            # 清除所有统计信息，准备从起始页重新开始
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
                message=f"任务已重置，准备重新执行（将从第 {task_data.get('start_page', 0)} 页开始）"
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

    async def check_real_status(self, task_id: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        检查任务的真实状态
        
        Args:
            task_id: 任务ID
            auto_fix: 是否自动修复（当执行器不存在时，自动将状态改为暂停）
        
        Returns:
            包含真实状态信息的字典
        """
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return {
                "exists": False,
                "message": "任务不存在"
            }

        db_status = task_data.get("status", "")
        real_status = {
            "exists": True,
            "db_status": db_status,
            "executor_exists": False,
            "executor_running": False,
            "executor_paused": False,
            "status_mismatch": False,
            "progress_stalled": False,
            "warnings": [],
            "recommendations": [],
            "fixed": False
        }

        # 检查执行器状态
        executor = get_executor(task_id)
        if executor:
            real_status["executor_exists"] = True
            real_status["executor_running"] = executor.is_running
            real_status["executor_paused"] = executor.is_paused

        # 如果数据库状态是 running，但执行器不存在或不在运行，说明状态不一致
        if db_status == "running":
            if not executor:
                real_status["status_mismatch"] = True
                real_status["warnings"].append("任务状态为 running，但执行器不存在")
                real_status["recommendations"].append("建议：尝试恢复任务或手动更新状态")
                
                # 自动修复：将状态改为暂停
                if auto_fix:
                    try:
                        await self.repo.update_task_status(
                            task_id=task_id,
                            status="paused",
                            paused_at=datetime.now()
                        )
                        await self.repo.add_log(
                            task_id=task_id,
                            level="WARNING",
                            message="系统自动修复：检测到执行器不存在，已将任务状态从 running 改为 paused"
                        )
                        real_status["fixed"] = True
                        real_status["db_status"] = "paused"
                        db_status = "paused"
                    except Exception as e:
                        real_status["warnings"].append(f"自动修复失败: {str(e)}")
            elif not executor.is_running:
                real_status["status_mismatch"] = True
                real_status["warnings"].append("任务状态为 running，但执行器未在运行")
                real_status["recommendations"].append("建议：尝试恢复任务")
                
                # 自动修复：将状态改为暂停
                if auto_fix:
                    try:
                        await self.repo.update_task_status(
                            task_id=task_id,
                            status="paused",
                            paused_at=datetime.now()
                        )
                        await self.repo.add_log(
                            task_id=task_id,
                            level="WARNING",
                            message="系统自动修复：检测到执行器未在运行，已将任务状态从 running 改为 paused"
                        )
                        real_status["fixed"] = True
                        real_status["db_status"] = "paused"
                        db_status = "paused"
                    except Exception as e:
                        real_status["warnings"].append(f"自动修复失败: {str(e)}")
        
        # 检查进度是否停滞（如果任务运行中，但已超过1小时未更新）
        if db_status == "running":
            updated_at = task_data.get("updated_at")
            if updated_at:
                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                now = datetime.now(updated_at.tzinfo if hasattr(updated_at, 'tzinfo') else None)
                time_diff = (now - updated_at).total_seconds()
                hours_diff = time_diff / 3600
                
                if hours_diff > 1:
                    real_status["progress_stalled"] = True
                    real_status["warnings"].append(f"任务已超过 {hours_diff:.2f} 小时未更新，可能已卡住")
                    real_status["recommendations"].append("建议：检查任务日志或尝试恢复任务")

        # 检查是否已完成所有页数但状态未更新
        if db_status == "running":
            completed_pages = task_data.get("completed_pages", 0)
            total_pages = task_data.get("total_pages")
            if total_pages is not None and completed_pages >= total_pages:
                real_status["progress_stalled"] = True
                real_status["warnings"].append(f"已完成所有页数 ({completed_pages}/{total_pages})，但状态未更新为 completed")
                real_status["recommendations"].append("建议：任务应该已完成，可能需要手动更新状态")

        return real_status

    async def sync_case_records_from_json(self, task_id: str) -> Dict[str, Any]:
        """
        从JSON文件同步案例记录到数据库
        
        Args:
            task_id: 任务ID
            
        Returns:
            同步结果
        """
        from pathlib import Path
        from services.pipeline.utils import load_json
        from app.repositories.crawl_case_record_repository import CrawlCaseRecordRepository
        
        output_dir = Path("data/json") / task_id
        if not output_dir.exists():
            return {
                "success": False,
                "message": f"输出目录不存在: {output_dir}"
            }
        
        # 查找所有批次文件
        batch_files = sorted(output_dir.glob("cases_batch_*.json"))
        if not batch_files:
            return {
                "success": False,
                "message": "没有找到批次文件"
            }
        
        total_synced = 0
        total_errors = 0
        
        try:
            for batch_file in batch_files:
                try:
                    data = load_json(batch_file)
                    if not data or 'cases' not in data:
                        continue
                    
                    cases = data['cases']
                    batch_file_name = batch_file.name
                    
                    for case in cases:
                        case_id = case.get('case_id')
                        if not case_id:
                            continue
                        
                        case_url = case.get('url') or case.get('source_url')
                        case_title = case.get('title', '未知标题')
                        
                        # 检查是否有错误信息（表示失败）
                        has_error = 'error' in case or 'validation_error' in case
                        
                        try:
                            # 创建或更新案例记录
                            record_id = await CrawlCaseRecordRepository.create_case_record(
                                task_id=task_id,
                                list_page_id=None,
                                case_id=case_id,
                                case_url=case_url,
                                case_title=case_title
                            )
                            
                            if has_error:
                                # 更新为失败状态
                                error_message = case.get('error') or case.get('validation_error', '未知错误')
                                error_type = 'parse_error' if 'error' in case else 'validation_error'
                                await CrawlCaseRecordRepository.update_case_failed(
                                    record_id=record_id,
                                    error_message=str(error_message),
                                    error_type=error_type,
                                    error_stack=None,
                                    duration=0.0
                                )
                            else:
                                # 更新为成功状态
                                await CrawlCaseRecordRepository.update_case_success(
                                    record_id=record_id,
                                    duration=0.0,
                                    has_detail_data=True
                                )
                            
                            # 更新保存状态
                            await CrawlCaseRecordRepository.update_case_saved(
                                record_id=record_id,
                                batch_file_name=batch_file_name
                            )
                            
                            total_synced += 1
                        except Exception as e:
                            logger.error(f"同步案例记录失败 case_id={case_id}: {e}")
                            total_errors += 1
                            continue
                except Exception as e:
                    logger.error(f"处理批次文件失败 {batch_file}: {e}")
                    total_errors += 1
                    continue
            
            return {
                "success": True,
                "message": f"同步完成：成功 {total_synced} 条，失败 {total_errors} 条",
                "total_synced": total_synced,
                "total_errors": total_errors
            }
        except Exception as e:
            logger.error(f"同步案例记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "total_synced": total_synced,
                "total_errors": total_errors
            }

    async def sync_to_cases_db(self, task_id: str) -> Dict[str, Any]:
        """
        将任务数据同步到 cases 数据库表（启动导入任务）
        
        Args:
            task_id: 任务ID
            
        Returns:
            导入任务信息（包含 import_id）
        """
        from app.services.task_import_service import TaskImportService
        from app.schemas.task_import import ImportStartRequest
        
        # 检查任务是否存在且已完成
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            raise ValueError(f"任务 {task_id} 不存在")

        if task_data["status"] != "completed":
            raise ValueError(f"任务 {task_id} 未完成，无法同步到案例数据库")

        if task_data.get("total_saved", 0) == 0:
            raise ValueError(f"任务 {task_id} 没有已保存的数据")

        # 使用导入服务启动导入任务（使用默认配置）
        import_service = TaskImportService()
        
        # 创建默认的导入请求
        import_request = ImportStartRequest(
            import_mode="full",  # 完整导入所有批次
            skip_existing=True,  # 跳过已存在的案例
            update_existing=False,  # 不更新已存在的案例
            generate_vectors=True,  # 生成向量
            skip_invalid=True,  # 跳过无效数据
            batch_size=50  # 批量大小
        )
        
        try:
            result = await import_service.start_import(task_id, import_request)
            
            # 添加同步日志
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message=f"开始同步数据到案例数据库（导入ID: {result.get('import_id')}）",
                details={"import_id": result.get('import_id'), "config": import_request.dict()}
            )
            
            return result
        except Exception as e:
            logger.error(f"启动同步到案例数据库失败: {e}", exc_info=True)
            raise

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
        status = task_data.get("status", "")
        
        # 如果任务已完成，百分比应该是 100%
        if status == "completed":
            percentage = 100.0
        elif task_data.get("total_pages"):
            completed = task_data.get("completed_pages", 0)
            total = task_data["total_pages"]
            if total > 0:
                # 确保百分比不超过 100.0，处理数据不一致的情况
                percentage = min((completed / total) * 100, 100.0)

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
