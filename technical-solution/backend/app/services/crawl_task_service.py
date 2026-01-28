"""
爬取任务服务层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import shutil
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.services.crawl_task_executor import CrawlTaskExecutor, register_executor, get_executor, unregister_executor
from app.schemas.crawl_task import (
    CrawlTaskCreate, CrawlTaskDetail, CrawlTaskListItem,
    CrawlTaskListResponse, CrawlTaskLogsResponse, CrawlTaskLog,
    CrawlTaskProgress, CrawlTaskStats, CrawlTaskTimeline, CrawlTaskConfig
)
from app.config import settings
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
        """获取任务详情
        
        自动从文件计算进度并同步到数据库（如果存在不一致）
        """
        from services.pipeline.utils import calculate_progress_from_files
        
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return None
        
        # 尝试从文件计算实际进度并同步到数据库
        batch_size = task_data.get("batch_size", 30)
        try:
            backend_root = Path(__file__).parent.parent.parent
            task_dir = backend_root / "data" / "json" / task_id
            file_progress = calculate_progress_from_files(task_dir, batch_size)
            
            # 如果文件数据可用且与数据库不一致，更新数据库
            if file_progress['total_crawled'] > 0 or file_progress['batches_saved'] > 0:
                db_completed_pages = task_data.get("completed_pages", 0)
                file_completed_pages = file_progress['completed_pages']
                
                # 如果进度不一致，更新数据库（静默更新，不记录日志）
                if (file_completed_pages != db_completed_pages or 
                    file_progress['total_crawled'] != task_data.get("total_crawled", 0) or
                    file_progress['total_saved'] != task_data.get("total_saved", 0) or
                    file_progress['batches_saved'] != task_data.get("batches_saved", 0)):
                    
                    try:
                        start_page = task_data.get("start_page", 0)
                        current_page = start_page + file_completed_pages
                        
                        await self.repo.update_task_progress(
                            task_id=task_id,
                            completed_pages=file_completed_pages,
                            current_page=current_page,
                            total_crawled=file_progress['total_crawled'],
                            total_saved=file_progress['total_saved'],
                            batches_saved=file_progress['batches_saved']
                        )
                        
                        # 更新 task_data 以便后续使用
                        task_data['completed_pages'] = file_completed_pages
                        task_data['current_page'] = current_page
                        task_data['total_crawled'] = file_progress['total_crawled']
                        task_data['total_saved'] = file_progress['total_saved']
                        task_data['batches_saved'] = file_progress['batches_saved']
                        
                        logger.debug(f"已从文件同步进度到数据库（任务 {task_id}）: {file_completed_pages} 页")
                    except Exception as e:
                        logger.warning(f"同步进度到数据库失败（任务 {task_id}）: {e}")
        except Exception as e:
            # 文件计算失败不影响详情获取，静默处理
            logger.debug(f"从文件计算进度失败（任务 {task_id}）: {e}")
        
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
        """开始执行任务（支持从pending或paused状态开始）"""
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            return False

        current_status = task_data["status"]
        
        # 允许从 pending 或 paused 状态开始
        if current_status not in ["pending", "paused"]:
            return False

        # 如果任务已暂停，先检查是否有执行器
        should_clear_files = False
        if current_status == "paused":
            executor = get_executor(task_id)
            if executor and executor.is_running:
                # 执行器还在运行，尝试恢复
                resume_success = await executor.resume()
                if resume_success:
                    # 恢复成功，更新状态为 running
                    await self.repo.update_task_status(
                        task_id=task_id,
                        status="running"
                    )
                    await self.repo.add_log(
                        task_id=task_id,
                        level="INFO",
                        message="任务已恢复执行"
                    )
                    return True
                # 如果恢复失败，继续执行重新启动逻辑
                should_clear_files = True
            else:
                # 没有执行器或执行器已停止，需要重新启动，清空文件目录
                should_clear_files = True
        
        # 如果需要清空文件目录（从 paused 状态重新启动）
        if should_clear_files:
            try:
                backend_root = Path(__file__).resolve().parent.parent.parent
                task_dir = backend_root / "data" / "json" / task_id
                logger.info(f"从暂停状态重新开始，准备清空任务文件目录: {task_dir} (存在: {task_dir.exists()})")
                if task_dir.exists():
                    deleted_count = 0
                    for item in task_dir.iterdir():
                        try:
                            if item.is_file():
                                item.unlink()
                                deleted_count += 1
                                logger.debug(f"已删除文件: {item.name}")
                            elif item.is_dir():
                                shutil.rmtree(item)
                                deleted_count += 1
                                logger.debug(f"已删除目录: {item.name}")
                        except Exception as e:
                            logger.warning(f"删除 {item.name} 失败: {e}")
                    logger.info(f"已清空任务文件目录: {task_dir} (删除了 {deleted_count} 个项目)")
                    await self.repo.add_log(
                        task_id=task_id,
                        level="INFO",
                        message=f"从暂停状态重新开始，已清空任务文件目录: {task_dir} (删除了 {deleted_count} 个项目)"
                    )
                else:
                    logger.info(f"任务文件目录不存在，无需清空: {task_dir}")
            except Exception as e:
                logger.error(f"清空任务文件目录失败: {e}", exc_info=True)
                await self.repo.add_log(
                    task_id=task_id,
                    level="WARNING",
                    message=f"清空任务文件目录失败: {e}"
                )
        
        # 确定起始页码
        # 如果任务已暂停且需要重新启动，使用起始页码；否则使用当前页码继续
        if current_status == "paused" and should_clear_files:
            # 重新启动，使用起始页码
            start_page = task_data["start_page"]
        elif current_status == "paused":
            # 继续执行，使用当前页码
            current_page = task_data.get("current_page")
            start_page = current_page if current_page is not None else task_data["start_page"]
        else:
            start_page = task_data["start_page"]
        
        # 如果状态是 paused，先重置为 pending
        if current_status == "paused":
            await self.repo.update_task_status(
                task_id=task_id,
                status="pending"
            )
        
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
        # 如果任务正在运行，不允许重新执行（需要先终止）
        if task_data["status"] == "running":
            return False

        # 检查是否已有执行器在运行
        executor = get_executor(task_id)
        if executor and executor.is_running:
            # 先终止现有执行器
            await executor.stop()
            unregister_executor(task_id)
        
        # 如果任务处于暂停状态，先更新状态为 pending
        if task_data["status"] == "paused":
            await self.repo.update_task_status(
                task_id=task_id,
                status="pending"
            )

        # 清空任务对应的文件目录
        try:
            # 获取 backend 根目录（使用绝对路径）
            backend_root = Path(__file__).resolve().parent.parent.parent
            task_dir = backend_root / "data" / "json" / task_id
            logger.info(f"准备清空任务文件目录: {task_dir} (存在: {task_dir.exists()})")
            if task_dir.exists():
                # 删除目录下的所有文件和子目录
                deleted_count = 0
                for item in task_dir.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                            deleted_count += 1
                            logger.debug(f"已删除文件: {item.name}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            deleted_count += 1
                            logger.debug(f"已删除目录: {item.name}")
                    except Exception as e:
                        logger.warning(f"删除 {item.name} 失败: {e}")
                logger.info(f"已清空任务文件目录: {task_dir} (删除了 {deleted_count} 个项目)")
                await self.repo.add_log(
                    task_id=task_id,
                    level="INFO",
                    message=f"已清空任务文件目录: {task_dir} (删除了 {deleted_count} 个项目)"
                )
            else:
                logger.info(f"任务文件目录不存在，无需清空: {task_dir}")
        except Exception as e:
            logger.error(f"清空任务文件目录失败: {e}", exc_info=True)
            await self.repo.add_log(
                task_id=task_id,
                level="WARNING",
                message=f"清空任务文件目录失败: {e}"
            )

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
        # 优先使用文件计算结果来检查进度
        if db_status == "running":
            from services.pipeline.utils import calculate_progress_from_files
            
            # 尝试从文件计算实际进度
            backend_root = Path(__file__).parent.parent.parent
            task_dir = backend_root / "data" / "json" / task_id
            batch_size = task_data.get("batch_size", 30)
            file_progress = calculate_progress_from_files(task_dir, batch_size)
            
            # 优先使用文件计算的进度
            if file_progress['total_crawled'] > 0 or file_progress['batches_saved'] > 0:
                actual_completed_pages = file_progress['completed_pages']
                actual_total_crawled = file_progress['total_crawled']
                actual_total_saved = file_progress['total_saved']
                actual_batches_saved = file_progress['batches_saved']
                
                # 如果文件计算的进度与数据库不一致，更新数据库
                db_completed_pages = task_data.get("completed_pages", 0)
                if actual_completed_pages != db_completed_pages:
                    real_status["warnings"].append(
                        f"进度不一致：数据库显示 {db_completed_pages} 页，文件计算为 {actual_completed_pages} 页"
                    )
                    real_status["recommendations"].append("建议：使用文件计算的进度更新数据库")
                    
                    if auto_fix:
                        try:
                            await self.repo.update_task_progress(
                                task_id=task_id,
                                completed_pages=actual_completed_pages,
                                total_crawled=actual_total_crawled,
                                total_saved=actual_total_saved,
                                batches_saved=actual_batches_saved
                            )
                            await self.repo.add_log(
                                task_id=task_id,
                                level="INFO",
                                message=f"系统自动修复：根据文件计算更新进度为 {actual_completed_pages} 页（已爬取 {actual_total_crawled}，已保存 {actual_total_saved}，批次 {actual_batches_saved}）"
                            )
                            real_status["fixed"] = True
                            task_data["completed_pages"] = actual_completed_pages
                        except Exception as e:
                            real_status["warnings"].append(f"自动修复进度失败: {str(e)}")
                
                completed_pages = actual_completed_pages
            else:
                # 回退到数据库中的进度
                completed_pages = task_data.get("completed_pages", 0)
            
            total_pages = task_data.get("total_pages")
            if total_pages is not None and completed_pages >= total_pages:
                real_status["progress_stalled"] = True
                real_status["warnings"].append(f"已完成所有页数 ({completed_pages}/{total_pages})，但状态未更新为 completed")
                real_status["recommendations"].append("建议：任务应该已完成，可能需要手动更新状态")
                
                # 自动修复：将状态改为已完成
                if auto_fix:
                    try:
                        await self.repo.update_task_status(
                            task_id=task_id,
                            status="completed",
                            completed_at=datetime.now()
                        )
                        await self.repo.add_log(
                            task_id=task_id,
                            level="INFO",
                            message=f"系统自动修复：检测到任务已完成所有页数 ({completed_pages}/{total_pages})，已将任务状态从 running 改为 completed"
                        )
                        real_status["fixed"] = True
                        real_status["db_status"] = "completed"
                        db_status = "completed"
                    except Exception as e:
                        real_status["warnings"].append(f"自动修复失败: {str(e)}")

        # 检查文件系统状态（断点续传文件和批次文件）
        filesystem_info = self._check_filesystem_status(task_id)
        if filesystem_info:
            real_status["filesystem"] = filesystem_info
            # 如果文件系统显示长时间未更新，添加到警告中
            if filesystem_info.get("resume_file_stalled"):
                real_status["progress_stalled"] = True
                hours_diff = filesystem_info.get("resume_file_hours_since_update", 0)
                real_status["warnings"].append(f"断点续传文件已超过 {hours_diff:.2f} 小时未更新，可能已卡住")

        return real_status

    def _check_filesystem_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        检查任务相关的文件系统状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            文件系统状态信息字典，如果检查失败则返回 None
        """
        try:
            # 获取数据目录路径（相对于 backend 目录）
            backend_root = Path(__file__).parent.parent.parent
            data_dir = backend_root / "data"
            task_dir = data_dir / "json" / task_id
            resume_file = task_dir / "crawl_resume.json"
            
            filesystem_info = {
                "resume_file_exists": False,
                "resume_file_stalled": False,
                "resume_file_hours_since_update": None,
                "batch_files_count": 0,
                "last_batch_file_size_mb": None,
                "last_batch_file_mtime": None
            }
            
            # 检查断点续传文件
            if resume_file.exists():
                filesystem_info["resume_file_exists"] = True
                try:
                    with open(resume_file, 'r', encoding='utf-8') as f:
                        resume_data = json.load(f)
                    
                    filesystem_info["resume_file_crawled_ids_count"] = len(resume_data.get('crawled_ids', []))
                    filesystem_info["resume_file_total_count"] = resume_data.get('total_count', 0)
                    last_updated_str = resume_data.get('last_updated')
                    
                    if last_updated_str:
                        try:
                            last_update_time = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                            now = datetime.now(last_update_time.tzinfo if hasattr(last_update_time, 'tzinfo') else None)
                            time_diff = (now - last_update_time).total_seconds()
                            hours_diff = time_diff / 3600
                            filesystem_info["resume_file_hours_since_update"] = hours_diff
                            filesystem_info["resume_file_last_updated"] = last_updated_str
                            
                            # 如果超过1小时未更新，标记为停滞
                            if hours_diff > 1:
                                filesystem_info["resume_file_stalled"] = True
                        except Exception as e:
                            logger.warning(f"无法解析断点续传文件时间: {e}")
                except Exception as e:
                    logger.warning(f"读取断点续传文件失败: {e}")
            
            # 检查批次文件
            if task_dir.exists():
                batch_files = sorted(task_dir.glob("cases_batch_*.json"))
                filesystem_info["batch_files_count"] = len(batch_files)
                
                if batch_files:
                    filesystem_info["first_batch_file"] = batch_files[0].name
                    filesystem_info["last_batch_file"] = batch_files[-1].name
                    
                    # 检查最后一个批次文件
                    last_batch = batch_files[-1]
                    stat = last_batch.stat()
                    filesystem_info["last_batch_file_size_mb"] = round(stat.st_size / (1024 * 1024), 2)
                    filesystem_info["last_batch_file_mtime"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            return filesystem_info
        except Exception as e:
            logger.error(f"检查文件系统状态失败: {e}", exc_info=True)
            return None

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
        
        只要文件中有已保存的数据，就允许导入（不要求任务状态必须是 completed）
        
        Args:
            task_id: 任务ID
            
        Returns:
            导入任务信息（包含 import_id）
        """
        from app.services.task_import_service import TaskImportService
        from app.schemas.task_import import ImportStartRequest
        from services.pipeline.utils import calculate_progress_from_files
        
        # 检查任务是否存在
        task_data = await self.repo.get_task(task_id)
        if not task_data:
            raise ValueError(f"任务 {task_id} 不存在")

        # 检查文件中是否有数据（优先使用文件检查）
        batch_size = task_data.get("batch_size", 30)
        task_dir = Path("data/json") / task_id
        file_progress = calculate_progress_from_files(task_dir, batch_size)
        
        # 如果文件中有数据，允许导入（不要求状态必须是 completed）
        has_file_data = file_progress['total_saved'] > 0 or file_progress['batches_saved'] > 0
        
        if not has_file_data:
            # 如果文件中没有数据，检查数据库中的统计
            db_total_saved = task_data.get("total_saved", 0)
            if db_total_saved == 0:
                raise ValueError(f"任务 {task_id} 没有已保存的数据（文件中也没有找到数据）")
        
        # 如果文件中有数据但数据库状态不是 completed，记录信息
        if has_file_data and task_data["status"] != "completed":
            await self.repo.add_log(
                task_id=task_id,
                level="INFO",
                message=f"任务状态为 {task_data['status']}，但检测到文件中有已保存的数据（{file_progress['total_saved']} 个案例，{file_progress['batches_saved']} 个批次），允许导入"
            )

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
        """转换为详情对象
        
        优先使用文件计算结果来获取准确的进度信息
        """
        from pathlib import Path
        from services.pipeline.utils import calculate_progress_from_files
        
        task_id = task_data.get("task_id")
        batch_size = task_data.get("batch_size", 30)
        status = task_data.get("status", "")
        
        # 尝试从文件计算实际进度
        file_progress = None
        if task_id:
            try:
                backend_root = Path(__file__).parent.parent.parent
                task_dir = backend_root / "data" / "json" / task_id
                file_progress = calculate_progress_from_files(task_dir, batch_size)
                
                # 如果文件数据可用，使用文件计算结果
                if file_progress['total_crawled'] > 0 or file_progress['batches_saved'] > 0:
                    # 更新 task_data 中的进度信息（用于后续计算）
                    task_data['total_crawled'] = file_progress['total_crawled']
                    task_data['total_saved'] = file_progress['total_saved']
                    task_data['batches_saved'] = file_progress['batches_saved']
                    task_data['completed_pages'] = file_progress['completed_pages']
                    # 计算 current_page
                    start_page = task_data.get("start_page", 0)
                    task_data['current_page'] = start_page + file_progress['completed_pages']
            except Exception as e:
                logger.debug(f"从文件计算进度失败（任务 {task_id}）: {e}")
        
        # 计算进度百分比
        percentage = 0.0
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
        """转换为列表项对象
        
        优先使用文件计算结果来获取准确的进度信息
        """
        from pathlib import Path
        from services.pipeline.utils import calculate_progress_from_files
        
        task_id = task_data.get("task_id")
        batch_size = task_data.get("batch_size", 30)
        status = task_data.get("status", "")
        
        # 尝试从文件计算实际进度（列表项只更新关键进度信息，不更新数据库）
        if task_id:
            try:
                backend_root = Path(__file__).parent.parent.parent
                task_dir = backend_root / "data" / "json" / task_id
                file_progress = calculate_progress_from_files(task_dir, batch_size)
                
                # 如果文件数据可用，使用文件计算结果
                if file_progress['total_crawled'] > 0 or file_progress['batches_saved'] > 0:
                    # 更新 task_data 中的进度信息（仅用于显示，不更新数据库）
                    task_data['total_crawled'] = file_progress['total_crawled']
                    task_data['total_saved'] = file_progress['total_saved']
                    task_data['batches_saved'] = file_progress['batches_saved']
                    task_data['completed_pages'] = file_progress['completed_pages']
            except Exception as e:
                # 列表项计算失败不影响显示，静默处理
                logger.debug(f"从文件计算进度失败（任务 {task_id}）: {e}")
        
        # 计算进度百分比
        percentage = 0.0
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
