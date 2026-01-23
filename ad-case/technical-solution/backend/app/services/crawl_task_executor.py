"""
爬取任务执行器
集成现有的 CrawlStage，实现任务执行、进度更新和任务控制
"""
import asyncio
import logging
import threading
import time
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime

# 添加 backend 目录到路径，以便导入 services 模块
backend_root = Path(__file__).parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from services.pipeline.crawl_stage import CrawlStage
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.services.crawl_task_executor_sync_db import SyncDatabase

logger = logging.getLogger(__name__)


class CrawlTaskExecutor:
    """爬取任务执行器"""

    def __init__(self, task_id: str):
        """
        初始化任务执行器

        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self.repo = CrawlTaskRepository()
        self.crawl_stage: Optional[CrawlStage] = None
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.execution_thread: Optional[threading.Thread] = None
        self.progress_callback: Optional[Callable] = None

    async def execute(
        self,
        name: str,
        data_source: str,
        start_page: int,
        end_page: Optional[int],
        case_type: Optional[int],
        search_value: Optional[str],
        batch_size: int,
        delay_min: float,
        delay_max: float,
        enable_resume: bool,
    ):
        """
        执行任务（异步方法，在后台线程中运行）

        Args:
            name: 任务名称
            data_source: 数据源
            start_page: 起始页码
            end_page: 结束页码
            case_type: 案例类型
            search_value: 搜索关键词
            batch_size: 批次大小
            delay_min: 最小延迟
            delay_max: 最大延迟
            enable_resume: 是否启用断点续传
        """
        # 在后台线程中执行同步代码
        import concurrent.futures
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                self._execute_sync,
                name,
                data_source,
                start_page,
                end_page,
                case_type,
                search_value,
                batch_size,
                delay_min,
                delay_max,
                enable_resume,
            )

    def _execute_sync(
        self,
        name: str,
        data_source: str,
        start_page: int,
        end_page: Optional[int],
        case_type: Optional[int],
        search_value: Optional[str],
        batch_size: int,
        delay_min: float,
        delay_max: float,
        enable_resume: bool,
    ):
        """
        同步执行任务（在后台线程中运行）
        """
        try:
            self.is_running = True
            self.is_paused = False
            self.should_stop = False

            # 添加开始日志和详细配置信息
            self._add_log("INFO", f"任务开始执行: {name}")
            self._add_log("INFO", f"任务配置详情:")
            self._add_log("INFO", f"  - 数据源: {data_source}")
            self._add_log("INFO", f"  - 起始页码: {start_page}")
            self._add_log("INFO", f"  - 结束页码: {end_page if end_page is not None else '无限制'}")
            self._add_log("INFO", f"  - 案例类型: {case_type if case_type is not None else '默认(3)'}")
            self._add_log("INFO", f"  - 搜索关键词: {search_value if search_value else '无'}")
            self._add_log("INFO", f"  - 批次大小: {batch_size}")
            self._add_log("INFO", f"  - 延迟范围: {delay_min} - {delay_max} 秒")
            self._add_log("INFO", f"  - 断点续传: {'启用' if enable_resume else '禁用'}")

            # 计算总页数
            max_pages = None
            if end_page is not None:
                max_pages = end_page - start_page + 1
                self._add_log("INFO", f"  - 计划爬取页数: {max_pages} 页")

            # 更新总页数
            if max_pages:
                self._update_total_pages(max_pages)
                SyncDatabase.update_task_progress(
                    task_id=self.task_id,
                    completed_pages=0,
                    current_page=start_page,
                    total_crawled=0,
                    total_saved=0,
                    total_failed=0,
                    batches_saved=0
                )

            # 准备输出目录（使用任务ID作为子目录）
            output_dir = Path("data/json") / self.task_id
            resume_file = output_dir / "crawl_resume.json" if enable_resume else None
            self._add_log("INFO", f"输出目录: {output_dir.absolute()}")
            if enable_resume:
                self._add_log("INFO", f"断点续传文件: {resume_file.absolute()}")

            # 创建进度回调函数
            def progress_callback() -> bool:
                """
                进度回调函数，每10个案例调用一次
                返回 True 表示继续执行，False 表示需要暂停
                """
                # 检查是否应该停止（停止优先级高于暂停）
                if self.should_stop:
                    # 停止任务，抛出异常以中断爬取循环
                    raise KeyboardInterrupt("任务被终止")
                
                # 检查是否暂停
                if self.is_paused:
                    return False
                
                # 更新进度
                self._update_progress_periodically_sync()
                
                return True
            
            # 创建 CrawlStage 实例
            self._add_log("INFO", "正在初始化爬取组件...")
            self.crawl_stage = CrawlStage(
                output_dir=output_dir,
                batch_size=batch_size,
                resume_file=resume_file,
                delay_range=(delay_min, delay_max),
                enable_resume=enable_resume,
                progress_callback=progress_callback,
                task_id=self.task_id  # 传递 task_id 用于记录列表页状态
            )
            self._add_log("INFO", "爬取组件初始化完成")

            # 创建自定义日志处理器，将日志同时记录到数据库
            class DatabaseLogHandler(logging.Handler):
                def __init__(self, executor):
                    super().__init__()
                    self.executor = executor

                def emit(self, record):
                    try:
                        level = record.levelname
                        message = self.format(record)
                        # 只记录 INFO、WARNING、ERROR 级别的日志
                        if level in ['INFO', 'WARNING', 'ERROR']:
                            asyncio.run(self.executor._add_log(level, message))
                    except Exception:
                        pass  # 避免日志记录失败影响主流程

            # 添加数据库日志处理器到 pipeline logger 和 spider logger
            # 注意：需要获取正确的 logger 名称（使用实际的模块路径）
            # 由于代码在 backend 目录下，logger 名称应该是 services.pipeline.crawl_stage
            pipeline_logger = logging.getLogger('services.pipeline.crawl_stage')
            api_client_logger = logging.getLogger('services.spider.api_client')
            
            db_handler = DatabaseLogHandler(self)
            db_handler.setFormatter(logging.Formatter('%(message)s'))
            db_handler.setLevel(logging.INFO)
            
            # 添加到所有相关的 logger
            pipeline_logger.addHandler(db_handler)
            api_client_logger.addHandler(db_handler)
            
            # 同时添加到父级 logger 以确保捕获所有日志
            services_logger = logging.getLogger('services')
            services_logger.addHandler(db_handler)
            services_logger.setLevel(logging.INFO)
            
            # 确保 propagate 为 True，让日志向上传播
            pipeline_logger.propagate = True
            api_client_logger.propagate = True
            
            self._add_log("INFO", f"日志处理器已添加:")
            self._add_log("INFO", f"  - pipeline logger: {pipeline_logger.name} (level: {pipeline_logger.level})")
            self._add_log("INFO", f"  - api_client logger: {api_client_logger.name} (level: {api_client_logger.level})")
            self._add_log("INFO", f"  - services logger: {services_logger.name} (level: {services_logger.level})")

            try:
                # 执行爬取（在循环中定期更新进度）
                self._add_log("INFO", f"开始执行爬取任务，从第 {start_page} 页开始")
                if max_pages:
                    self._add_log("INFO", f"计划爬取 {max_pages} 页（到第 {end_page} 页）")
                else:
                    self._add_log("INFO", "将爬取到最后一页（无页数限制）")
                
                # 确保日志处理器已添加（再次确认）
                self._add_log("INFO", "准备开始爬取，日志记录已启用")
                
                stats = self._crawl_with_progress_update(
                    start_page=start_page,
                    max_pages=max_pages,
                    case_type=case_type or 3,
                    search_value=search_value or '',
                    skip_existing=enable_resume
                )
                
                self._add_log("INFO", f"爬取阶段完成，统计信息:")
                self._add_log("INFO", f"  - 总爬取数: {stats.get('total_crawled', 0)}")
                self._add_log("INFO", f"  - 成功数: {stats.get('total_saved', 0)}")
                self._add_log("INFO", f"  - 失败数: {stats.get('total_failed', 0)}")
                self._add_log("INFO", f"  - 保存批次数: {stats.get('batches_saved', 0)}")
                if stats.get('duration_seconds'):
                    self._add_log("INFO", f"  - 耗时: {stats.get('duration_seconds', 0):.2f} 秒")
            except KeyboardInterrupt:
                # 任务被终止
                self._add_log("WARNING", "任务被终止")
                self._update_task_status_sync("terminated")
                return
            finally:
                # 移除日志处理器
                try:
                    pipeline_logger.removeHandler(db_handler)
                    api_client_logger.removeHandler(db_handler)
                    services_logger.removeHandler(db_handler)
                except Exception as e:
                    logger.warning(f"移除日志处理器失败: {e}")

            # 检查是否被停止
            if self.should_stop:
                self._add_log("WARNING", "任务被终止")
                self._update_task_status_sync("terminated")
                return

            # 更新最终统计（同步方法）
            self._update_final_stats_sync(stats)

            # 验证所有已爬取的ID是否都被保存（如果启用了断点续传）
            if enable_resume and self.crawl_stage and self.crawl_stage.crawled_ids:
                from services.pipeline.utils import get_saved_case_ids_from_json, validate_crawled_ids_saved
                
                output_dir = Path("data/json") / self.task_id
                saved_ids = get_saved_case_ids_from_json(output_dir)
                validation_result = validate_crawled_ids_saved(self.crawl_stage.crawled_ids, saved_ids)
                
                if not validation_result['all_saved']:
                    missing_count = validation_result['missing_count']
                    missing_ids = validation_result['missing_ids']
                    
                    # 更新失败统计
                    stats['total_failed'] += missing_count
                    
                    # 记录警告日志
                    self._add_log("WARNING", f"发现 {missing_count} 个已爬取但未保存的案例ID，已计入失败统计")
                    if len(missing_ids) <= 20:
                        self._add_log("WARNING", f"未保存的ID列表: {missing_ids}")
                    else:
                        self._add_log("WARNING", f"未保存的ID列表（前20个）: {missing_ids[:20]}...")
                    
                    # 更新最终统计（包含验证后的失败数）
                    self._update_final_stats_sync(stats)
                else:
                    self._add_log("INFO", f"验证通过：所有 {validation_result['crawled_count']} 个已爬取的案例都已保存")

            # 确保 total_crawled 至少等于 total_saved + total_failed
            if stats.get('total_crawled', 0) == 0:
                # 如果 total_crawled 为 0，但总保存数和失败数不为 0，则重新计算
                total_processed = stats.get('total_saved', 0) + stats.get('total_failed', 0)
                if total_processed > 0:
                    stats['total_crawled'] = total_processed
                    logger.warning(f"检测到 total_crawled 为 0，已重新计算为 {total_processed}")

            # 再次更新最终统计（包含修复后的 total_crawled）
            self._update_final_stats_sync(stats)

            # 检查是否真的爬取到了数据
            total_crawled = stats.get('total_crawled', 0)
            total_saved = stats.get('total_saved', 0)
            total_failed = stats.get('total_failed', 0)
            total_processed = total_crawled + total_saved + total_failed
            
            # 如果没有爬取到任何数据，标记为失败
            if total_processed == 0:
                error_message = "任务执行完成，但未爬取到任何数据。可能原因：1) 列表页返回空数据；2) 所有案例都已跳过；3) 网络或API问题导致无法获取数据"
                self._add_log("ERROR", error_message)
                self._update_task_error_sync(error_message, "")
                success = self._update_task_status_sync("failed")
                
                if not success:
                    logger.error(f"更新任务状态为 failed 失败，任务ID: {self.task_id}")
                else:
                    logger.warning(f"任务 {self.task_id} 未爬取到任何数据，已标记为 failed")
            else:
                # 同步案例记录到数据库（从JSON文件）
                try:
                    self._sync_case_records_from_json()
                except Exception as e:
                    logger.error(f"同步案例记录到数据库失败: {e}", exc_info=True)
                    self._add_log("WARNING", f"同步案例记录到数据库失败: {str(e)}")

                # 更新任务状态为完成（在更新统计之后）
                success = self._update_task_status_sync("completed", completed_at=datetime.now())
                
                if not success:
                    logger.error(f"更新任务状态为 completed 失败，任务ID: {self.task_id}")
                    # 即使状态更新失败，也要注销执行器
                else:
                    logger.info(f"任务 {self.task_id} 状态已更新为 completed")
            
            # 注销执行器
            try:
                unregister_executor(self.task_id)
            except Exception as e:
                logger.error(f"注销执行器失败: {e}")

            self._add_log("INFO", f"任务执行完成: 总爬取 {stats.get('total_crawled', 0)} 个，成功 {stats.get('total_saved', 0)} 个，失败 {stats.get('total_failed', 0)} 个")

        except Exception as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            error_message = str(e)
            import traceback
            error_stack = traceback.format_exc()

            self._update_task_error_sync(error_message, error_stack)
            self._update_task_status_sync("failed")
            self._add_log("ERROR", f"任务执行失败: {error_message}")

        finally:
            self.is_running = False
            self.is_paused = False
            # 确保执行器被注销
            try:
                unregister_executor(self.task_id)
            except Exception as e:
                logger.error(f"注销执行器失败: {e}")

    async def pause(self):
        """暂停任务"""
        if not self.is_running:
            return False

        self.is_paused = True
        self._add_log("INFO", "任务暂停请求已发送")
        return True

    async def resume(self):
        """恢复任务"""
        if not self.is_paused:
            return False

        self.is_paused = False
        self._add_log("INFO", "任务恢复请求已发送")
        return True

    async def stop(self):
        """停止任务"""
        self.should_stop = True
        self.is_paused = False
        self._add_log("WARNING", "任务终止请求已发送")
        return True

    def _add_log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """添加日志到数据库（同步方法，在后台线程中调用）"""
        try:
            SyncDatabase.add_log(
                task_id=self.task_id,
                level=level,
                message=message,
                details=details
            )
        except Exception as e:
            logger.error(f"添加日志失败: {e}")

    def _update_total_pages(self, total_pages: int):
        """更新总页数（同步方法，在后台线程中调用）"""
        try:
            SyncDatabase.update_total_pages(self.task_id, total_pages)
        except Exception as e:
            logger.error(f"更新总页数失败: {e}")

    async def _update_progress(
        self,
        completed_pages: int,
        current_page: int,
        total_crawled: int,
        total_saved: int,
        total_failed: int,
        batches_saved: int
    ):
        """更新进度"""
        await self.repo.update_task_progress(
            task_id=self.task_id,
            completed_pages=completed_pages,
            current_page=current_page,
            total_crawled=total_crawled,
            total_saved=total_saved,
            total_failed=total_failed,
            batches_saved=batches_saved
        )

    def _crawl_with_progress_update(
        self,
        start_page: int,
        max_pages: Optional[int],
        case_type: int,
        search_value: str,
        skip_existing: bool
    ) -> Dict[str, Any]:
        """
        执行爬取并定期更新进度
        
        进度更新通过 CrawlStage 的 progress_callback 实现，每10个案例更新一次
        """
        # 执行爬取（进度更新已通过回调机制实现）
        stats = self.crawl_stage.crawl(
            start_page=start_page,
            max_pages=max_pages,
            case_type=case_type,
            search_value=search_value,
            skip_existing=skip_existing
        )
        
        # 最终更新进度
        self._update_progress_periodically_sync()
        
        return stats

    def _update_progress_periodically_sync(self):
        """定期更新进度（同步方法，在后台线程中调用）"""
        if not self.crawl_stage:
            return
        
        stats = self.crawl_stage.stats
        
        # 获取任务配置以计算当前页
        try:
            task_data = SyncDatabase.get_task(self.task_id)
            if task_data:
                start_page = task_data.get('start_page', 0)
                batch_size = task_data.get('batch_size', 30)
                
                # 每页数量等于 batch_size
                items_per_page = batch_size
                total_processed = stats.get('total_crawled', 0) + stats.get('total_failed', 0)
                completed_pages = total_processed // items_per_page if items_per_page > 0 else 0
                current_page = start_page + completed_pages
                
                SyncDatabase.update_task_progress(
                    task_id=self.task_id,
                    completed_pages=completed_pages,
                    current_page=current_page,
                    total_crawled=stats.get('total_crawled', 0),
                    total_saved=stats.get('total_saved', 0),
                    total_failed=stats.get('total_failed', 0),
                    batches_saved=stats.get('batches_saved', 0)
                )
        except Exception as e:
            logger.error(f"更新进度失败: {e}")

    def _sync_case_records_from_json(self):
        """从JSON文件同步案例记录到数据库（同步方法）"""
        try:
            from services.pipeline.utils import load_json
            import asyncio
            from app.repositories.crawl_case_record_repository import CrawlCaseRecordRepository
            from app.repositories.crawl_list_page_repository import CrawlListPageRepository
            from datetime import datetime
            
            output_dir = Path("data/json") / self.task_id
            if not output_dir.exists():
                logger.warning(f"输出目录不存在: {output_dir}")
                return
            
            # 查找所有批次文件
            batch_files = sorted(output_dir.glob("cases_batch_*.json"))
            if not batch_files:
                logger.info(f"没有找到批次文件，跳过同步案例记录")
                return
            
            logger.info(f"开始同步案例记录，共 {len(batch_files)} 个批次文件")
            
            # 在异步上下文中执行（需要创建新的事件循环，因为这是在同步线程中）
            async def sync_records():
                total_synced = 0
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
                                    task_id=self.task_id,
                                    list_page_id=None,  # 列表页记录ID需要从其他地方获取
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
                                continue
                    except Exception as e:
                        logger.error(f"处理批次文件失败 {batch_file}: {e}")
                        continue
                
                logger.info(f"案例记录同步完成，共同步 {total_synced} 条记录")
                return total_synced
            
            # 在新的事件循环中执行异步代码
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(sync_records())
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(sync_records())
                loop.close()
                
        except Exception as e:
            logger.error(f"同步案例记录失败: {e}", exc_info=True)
            raise

    def _update_task_status_sync(self, status: str, **kwargs) -> bool:
        """更新任务状态（同步方法）"""
        try:
            result = SyncDatabase.update_task_status(
                task_id=self.task_id,
                status=status,
                started_at=kwargs.get('started_at'),
                paused_at=kwargs.get('paused_at'),
                completed_at=kwargs.get('completed_at')
            )
            if not result:
                logger.warning(f"更新任务状态返回 False，任务ID: {self.task_id}, 状态: {status}")
            return result
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}", exc_info=True)
            return False

    def _update_task_error_sync(self, error_message: str, error_stack: str):
        """更新任务错误信息（同步方法）"""
        try:
            SyncDatabase.update_task_error(
                task_id=self.task_id,
                error_message=error_message,
                error_stack=error_stack
            )
        except Exception as e:
            logger.error(f"更新任务错误信息失败: {e}")

    def _update_final_stats_sync(self, stats: Dict[str, Any]):
        """更新最终统计信息（同步方法，在后台线程中调用）"""
        try:
            # 计算平均速度
            duration = stats.get('duration_seconds', 0)
            avg_speed = None
            if duration > 0 and stats.get('total_crawled', 0) > 0:
                avg_speed = (stats['total_crawled'] / duration) * 60  # 案例/分钟

            # 更新统计
            # 计算错误率，确保不超过 1.0
            total_crawled = max(stats.get('total_crawled', 1), 1)
            total_failed = stats.get('total_failed', 0)
            error_rate = min(total_failed / total_crawled, 1.0) if total_crawled > 0 else 0.0
            
            SyncDatabase.update_task_stats(
                task_id=self.task_id,
                avg_speed=avg_speed,
                avg_delay=(self.crawl_stage.delay_range[0] + self.crawl_stage.delay_range[1]) / 2 if self.crawl_stage else None,
                error_rate=error_rate
            )

            # 计算最终完成的页数
            # 获取任务配置以计算 completed_pages
            task_data = SyncDatabase.get_task(self.task_id)
            if task_data:
                batch_size = task_data.get('batch_size', 30)
                items_per_page = batch_size
                total_processed = stats.get('total_crawled', 0) + stats.get('total_failed', 0)
                calculated_completed_pages = total_processed // items_per_page if items_per_page > 0 else 0
                
                # 如果 total_pages 存在，使用 total_pages 作为 completed_pages（任务已完成）
                total_pages = task_data.get('total_pages')
                if total_pages is not None:
                    # 任务完成时，completed_pages 应该等于 total_pages
                    completed_pages = total_pages
                else:
                    completed_pages = calculated_completed_pages
            else:
                completed_pages = 0

            # 更新最终进度
            SyncDatabase.update_task_progress(
                task_id=self.task_id,
                completed_pages=completed_pages,
                current_page=None,
                total_crawled=stats.get('total_crawled', 0),
                total_saved=stats.get('total_saved', 0),
                total_failed=stats.get('total_failed', 0),
                batches_saved=stats.get('batches_saved', 0)
            )
        except Exception as e:
            logger.error(f"更新最终统计信息失败: {e}")


# 全局任务执行器字典（存储正在运行的任务）
_running_executors: Dict[str, CrawlTaskExecutor] = {}


def get_executor(task_id: str) -> Optional[CrawlTaskExecutor]:
    """获取任务执行器"""
    return _running_executors.get(task_id)


def register_executor(task_id: str, executor: CrawlTaskExecutor):
    """注册任务执行器"""
    _running_executors[task_id] = executor


def unregister_executor(task_id: str):
    """注销任务执行器"""
    _running_executors.pop(task_id, None)
