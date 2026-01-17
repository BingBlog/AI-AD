"""
同步数据库操作辅助类
用于在后台线程中执行数据库操作，避免连接池耗尽
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class SyncDatabase:
    """同步数据库操作类（用于后台线程）"""

    @staticmethod
    def _get_connection():
        """获取数据库连接"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )

    @staticmethod
    def add_log(
        task_id: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加任务日志"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                details_json = json.dumps(details) if details else None
                cur.execute(
                    """
                    INSERT INTO crawl_task_logs (task_id, level, message, details)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (task_id, level, message, details_json)
                )
                log_id = cur.fetchone()[0]
                conn.commit()
                return log_id
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"添加日志失败: {e}")
            return 0

    @staticmethod
    def update_task_progress(
        task_id: str,
        completed_pages: Optional[int] = None,
        current_page: Optional[int] = None,
        total_crawled: Optional[int] = None,
        total_saved: Optional[int] = None,
        total_failed: Optional[int] = None,
        batches_saved: Optional[int] = None
    ) -> bool:
        """更新任务进度"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = []
                params = []

                if completed_pages is not None:
                    update_fields.append("completed_pages = %s")
                    params.append(completed_pages)

                if current_page is not None:
                    update_fields.append("current_page = %s")
                    params.append(current_page)

                if total_crawled is not None:
                    update_fields.append("total_crawled = %s")
                    params.append(total_crawled)

                if total_saved is not None:
                    update_fields.append("total_saved = %s")
                    params.append(total_saved)

                if total_failed is not None:
                    update_fields.append("total_failed = %s")
                    params.append(total_failed)

                if batches_saved is not None:
                    update_fields.append("batches_saved = %s")
                    params.append(batches_saved)

                if not update_fields:
                    return False

                query = f"""
                    UPDATE crawl_tasks
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                """
                params.append(task_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return False

    @staticmethod
    def update_task_status(
        task_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        paused_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """更新任务状态"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = ["status = %s"]
                params = [status]

                if started_at is not None:
                    update_fields.append("started_at = %s")
                    params.append(started_at)

                if paused_at is not None:
                    update_fields.append("paused_at = %s")
                    params.append(paused_at)

                if completed_at is not None:
                    update_fields.append("completed_at = %s")
                    params.append(completed_at)

                query = f"""
                    UPDATE crawl_tasks
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                """
                params.append(task_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    @staticmethod
    def update_task_error(
        task_id: str,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None
    ) -> bool:
        """更新任务错误信息"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = []
                params = []

                if error_message is not None:
                    update_fields.append("error_message = %s")
                    params.append(error_message)

                if error_stack is not None:
                    update_fields.append("error_stack = %s")
                    params.append(error_stack)

                if not update_fields:
                    return False

                query = f"""
                    UPDATE crawl_tasks
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                """
                params.append(task_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新任务错误信息失败: {e}")
            return False

    @staticmethod
    def update_task_stats(
        task_id: str,
        avg_speed: Optional[float] = None,
        avg_delay: Optional[float] = None,
        error_rate: Optional[float] = None
    ) -> bool:
        """更新任务统计信息"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = []
                params = []

                if avg_speed is not None:
                    update_fields.append("avg_speed = %s")
                    params.append(avg_speed)

                if avg_delay is not None:
                    update_fields.append("avg_delay = %s")
                    params.append(avg_delay)

                if error_rate is not None:
                    update_fields.append("error_rate = %s")
                    params.append(error_rate)

                if not update_fields:
                    return False

                query = f"""
                    UPDATE crawl_tasks
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                """
                params.append(task_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新任务统计信息失败: {e}")
            return False

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute(
                    """
                    SELECT * FROM crawl_tasks WHERE task_id = %s
                    """,
                    (task_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None

    @staticmethod
    def update_total_pages(task_id: str, total_pages: int) -> bool:
        """更新总页数"""
        try:
            conn = SyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE crawl_tasks SET total_pages = %s WHERE task_id = %s
                    """,
                    (total_pages, task_id)
                )
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新总页数失败: {e}")
            return False
