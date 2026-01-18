"""
数据导入任务执行器
集成现有的 ImportStage，实现任务数据导入、进度更新和任务控制
"""
import asyncio
import logging
import threading
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

# 添加 backend 目录到路径，以便导入 services 模块
backend_root = Path(__file__).parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from services.pipeline.import_stage import ImportStage
from app.repositories.task_import_repository import TaskImportRepository
from app.services.import_task_executor_sync_db import ImportSyncDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class ImportTaskExecutor:
    """数据导入任务执行器"""

    def __init__(self, task_id: str, import_id: str):
        """
        初始化导入任务执行器

        Args:
            task_id: 任务ID
            import_id: 导入ID
        """
        self.task_id = task_id
        self.import_id = import_id
        self.repo = TaskImportRepository()
        self.import_stage: Optional[ImportStage] = None
        self.is_running = False
        self.is_cancelled = False
        self.progress_callback: Optional[Callable] = None

    async def execute(
        self,
        import_mode: str,
        selected_batches: Optional[List[str]],
        skip_existing: bool,
        update_existing: bool,
        generate_vectors: bool,
        skip_invalid: bool,
        batch_size: int,
    ):
        """
        执行导入任务（异步方法，在后台线程中运行）

        Args:
            import_mode: 导入模式（"full" 或 "selective"）
            selected_batches: 选择的批次文件列表（仅当 import_mode="selective" 时使用）
            skip_existing: 是否跳过已存在的案例
            update_existing: 是否更新已存在的案例
            generate_vectors: 是否生成向量
            skip_invalid: 是否跳过无效数据
            batch_size: 批量导入大小
        """
        # 在后台线程中执行同步代码
        import concurrent.futures
        loop = asyncio.get_event_loop()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                self._execute_sync,
                import_mode,
                selected_batches,
                skip_existing,
                update_existing,
                generate_vectors,
                skip_invalid,
                batch_size,
            )

    def _execute_sync(
        self,
        import_mode: str,
        selected_batches: Optional[List[str]],
        skip_existing: bool,
        update_existing: bool,
        generate_vectors: bool,
        skip_invalid: bool,
        batch_size: int,
    ):
        """
        同步执行导入任务（在后台线程中运行）
        """
        try:
            self.is_running = True
            self.is_cancelled = False

            # 添加开始日志
            self._add_log("INFO", f"开始导入任务数据: {self.task_id}")

            # 更新状态为 running
            ImportSyncDatabase.update_import_status(
                import_id=self.import_id,
                status="running",
                started_at=datetime.now()
            )

            # 准备数据库配置
            db_config = {
                'host': settings.DB_HOST,
                'port': settings.DB_PORT,
                'database': settings.DB_NAME,
                'user': settings.DB_USER,
                'password': settings.DB_PASSWORD,
            }

            # 创建 ImportStage 实例
            # 注意：当前 ImportStage 总是生成向量，如果 generate_vectors=False，后续可以优化
            model_name = 'BAAI/bge-large-zh-v1.5'
            self.import_stage = ImportStage(
                db_config=db_config,
                model_name=model_name,
                batch_size=batch_size,
                skip_existing=skip_existing and not update_existing,
                skip_invalid=skip_invalid
            )

            # 获取任务数据目录
            task_data_dir = Path("data/json") / self.task_id
            if not task_data_dir.exists():
                raise FileNotFoundError(f"任务数据目录不存在: {task_data_dir}")

            # 根据导入模式选择文件
            if import_mode == "selective" and selected_batches:
                # 选择性导入：只导入指定的批次文件
                json_files = []
                for batch_file in selected_batches:
                    file_path = task_data_dir / batch_file
                    if file_path.exists():
                        json_files.append(file_path)
                    else:
                        self._add_log("WARNING", f"文件不存在，跳过: {batch_file}")
                        ImportSyncDatabase.add_import_error(
                            import_id=self.import_id,
                            file_name=batch_file,
                            case_id=None,
                            error_type="file_not_found",
                            error_message=f"文件不存在: {batch_file}"
                        )
            else:
                # 完整导入：导入所有批次文件
                json_files = sorted(task_data_dir.glob("cases_batch_*.json"))

            if not json_files:
                raise ValueError("没有找到要导入的JSON文件")

            # 计算总案例数（用于进度显示）
            total_cases = 0
            for json_file in json_files:
                try:
                    from services.pipeline.utils import load_json
                    data = load_json(json_file)
                    if data and 'cases' in data:
                        total_cases += len(data['cases'])
                except Exception as e:
                    logger.warning(f"无法读取文件 {json_file} 的案例数: {e}")

            # 更新总案例数
            ImportSyncDatabase.update_import_progress(
                import_id=self.import_id,
                total_cases=total_cases
            )

            # 遍历文件，导入数据
            total_loaded = 0
            total_valid = 0
            total_invalid = 0
            total_existing = 0
            total_imported = 0
            total_failed = 0
            
            # 收集所有导入成功的案例ID
            all_imported_case_ids = []

            for json_file in json_files:
                # 检查是否取消
                if self.is_cancelled:
                    self._add_log("WARNING", "导入任务被取消")
                    ImportSyncDatabase.update_import_status(
                        import_id=self.import_id,
                        status="cancelled",
                        cancelled_at=datetime.now()
                    )
                    return

                # 更新当前文件
                ImportSyncDatabase.update_import_progress(
                    import_id=self.import_id,
                    current_file=json_file.name
                )
                self._add_log("INFO", f"开始导入文件: {json_file.name}")

                try:
                    # 导入文件
                    stats = self.import_stage.import_from_json(json_file)

                    # 累计统计
                    total_loaded += stats.get('total_loaded', 0)
                    total_valid += stats.get('total_valid', 0)
                    total_invalid += stats.get('total_invalid', 0)
                    total_existing += stats.get('total_existing', 0)
                    total_imported += stats.get('total_imported', 0)
                    total_failed += stats.get('total_failed', 0)
                    
                    # 收集导入成功的案例ID
                    imported_case_ids = stats.get('imported_case_ids', [])
                    if imported_case_ids:
                        all_imported_case_ids.extend(imported_case_ids)

                    # 更新进度
                    ImportSyncDatabase.update_import_progress(
                        import_id=self.import_id,
                        loaded_cases=total_loaded,
                        valid_cases=total_valid,
                        invalid_cases=total_invalid,
                        existing_cases=total_existing,
                        imported_cases=total_imported,
                        failed_cases=total_failed
                    )

                    self._add_log("INFO", f"文件导入完成: {json_file.name}, 导入 {stats.get('total_imported', 0)} 个案例")

                except Exception as e:
                    logger.error(f"导入文件失败 {json_file.name}: {e}", exc_info=True)
                    error_message = str(e)
                    import traceback
                    error_stack = traceback.format_exc()

                    ImportSyncDatabase.add_import_error(
                        import_id=self.import_id,
                        file_name=json_file.name,
                        case_id=None,
                        error_type="import_error",
                        error_message=error_message,
                        error_details={"error_stack": error_stack}
                    )
                    total_failed += 1

            # 更新最终结果
            # 从数据库获取开始时间
            conn = ImportSyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT started_at FROM task_imports WHERE import_id = %s", (self.import_id,))
                row = cur.fetchone()
                start_time = row[0] if row else datetime.now()
                cur.close()
            finally:
                conn.close()
            
            end_time = datetime.now()
            if isinstance(start_time, datetime):
                duration = (end_time - start_time).total_seconds()
            else:
                duration = 0

            ImportSyncDatabase.update_import_result(
                import_id=self.import_id,
                duration_seconds=int(duration)
            )

            # 更新状态为完成
            ImportSyncDatabase.update_import_status(
                import_id=self.import_id,
                status="completed",
                completed_at=end_time
            )

            # 更新 crawl_case_records 表中的导入状态
            try:
                # 在异步上下文中执行（因为 repository 是异步的）
                async def update_import_status():
                    from app.repositories.crawl_case_record_repository import CrawlCaseRecordRepository
                    from app.database import db
                    
                    if all_imported_case_ids:
                        # 批量更新导入成功的案例
                        await CrawlCaseRecordRepository.batch_update_import_status_by_case_ids(
                            task_id=self.task_id,
                            case_ids=all_imported_case_ids,
                            imported=True,
                            import_status='success'
                        )
                        
                        # 验证这些案例是否在 ad_cases 表中存在（已验证）
                        await CrawlCaseRecordRepository.batch_verify_cases_by_case_ids(
                            task_id=self.task_id,
                            case_ids=all_imported_case_ids,
                            verified=True
                        )
                        
                        logger.info(f"已更新 {len(all_imported_case_ids)} 个案例的导入状态和验证状态")
                    
                    # 验证所有案例记录是否在 ad_cases 表中存在（包括已存在的案例）
                    # 查询任务的所有案例记录的 case_id
                    records_query = """
                        SELECT DISTINCT case_id 
                        FROM crawl_case_records 
                        WHERE task_id = $1 AND case_id IS NOT NULL
                    """
                    records = await db.fetch(records_query, self.task_id)
                    all_case_ids = [row['case_id'] for row in records if row['case_id']]
                    
                    if all_case_ids:
                        # 查询 ad_cases 表中存在的 case_id
                        existing_query = """
                            SELECT case_id 
                            FROM ad_cases 
                            WHERE case_id = ANY($1)
                        """
                        existing_rows = await db.fetch(existing_query, all_case_ids)
                        existing_case_ids = [row['case_id'] for row in existing_rows]
                        
                        # 批量更新验证状态（标记所有在 ad_cases 表中存在的案例）
                        if existing_case_ids:
                            await CrawlCaseRecordRepository.batch_verify_cases_by_case_ids(
                                task_id=self.task_id,
                                case_ids=existing_case_ids,
                                verified=True
                            )
                            logger.info(f"已验证 {len(existing_case_ids)} 个案例在案例库中存在")
                
                # 在新的事件循环中执行异步代码
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(update_import_status())
                except RuntimeError:
                    # 如果没有事件循环，创建一个新的
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(update_import_status())
                    loop.close()
                    
            except Exception as e:
                logger.error(f"更新导入状态失败: {e}", exc_info=True)
                self._add_log("WARNING", f"更新导入状态失败: {str(e)}")

            self._add_log("INFO", f"导入任务完成: 总导入 {total_imported} 个案例，失败 {total_failed} 个")

        except Exception as e:
            logger.error(f"导入任务执行失败: {e}", exc_info=True)
            error_message = str(e)
            import traceback
            error_stack = traceback.format_exc()

            ImportSyncDatabase.update_import_result(
                import_id=self.import_id,
                error_message=error_message,
                error_stack=error_stack
            )
            ImportSyncDatabase.update_import_status(
                import_id=self.import_id,
                status="failed"
            )
            self._add_log("ERROR", f"导入任务执行失败: {error_message}")

        finally:
            self.is_running = False

    async def cancel(self):
        """取消导入任务"""
        self.is_cancelled = True
        self._add_log("WARNING", "导入任务取消请求已发送")
        return True

    def _add_log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """添加日志到数据库（同步方法，在后台线程中调用）"""
        try:
            ImportSyncDatabase.add_log(
                task_id=self.task_id,
                level=level,
                message=message,
                details=details
            )
        except Exception as e:
            logger.error(f"添加日志失败: {e}")


# 全局导入执行器字典（存储正在运行的导入任务）
_running_import_executors: Dict[str, ImportTaskExecutor] = {}


def get_import_executor(import_id: str) -> Optional[ImportTaskExecutor]:
    """获取导入执行器"""
    return _running_import_executors.get(import_id)


def register_import_executor(import_id: str, executor: ImportTaskExecutor):
    """注册导入执行器"""
    _running_import_executors[import_id] = executor


def unregister_import_executor(import_id: str):
    """注销导入执行器"""
    _running_import_executors.pop(import_id, None)
