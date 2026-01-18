"""
导入任务执行器的同步数据库操作辅助类
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


class ImportSyncDatabase:
    """导入同步数据库操作类（用于后台线程）"""

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
    def update_import_progress(
        import_id: str,
        total_cases: Optional[int] = None,
        loaded_cases: Optional[int] = None,
        valid_cases: Optional[int] = None,
        invalid_cases: Optional[int] = None,
        existing_cases: Optional[int] = None,
        imported_cases: Optional[int] = None,
        failed_cases: Optional[int] = None,
        current_file: Optional[str] = None,
    ) -> bool:
        """更新导入进度"""
        try:
            conn = ImportSyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = []
                params = []

                if total_cases is not None:
                    update_fields.append("total_cases = %s")
                    params.append(total_cases)
                if loaded_cases is not None:
                    update_fields.append("loaded_cases = %s")
                    params.append(loaded_cases)
                if valid_cases is not None:
                    update_fields.append("valid_cases = %s")
                    params.append(valid_cases)
                if invalid_cases is not None:
                    update_fields.append("invalid_cases = %s")
                    params.append(invalid_cases)
                if existing_cases is not None:
                    update_fields.append("existing_cases = %s")
                    params.append(existing_cases)
                if imported_cases is not None:
                    update_fields.append("imported_cases = %s")
                    params.append(imported_cases)
                if failed_cases is not None:
                    update_fields.append("failed_cases = %s")
                    params.append(failed_cases)
                if current_file is not None:
                    update_fields.append("current_file = %s")
                    params.append(current_file)

                if not update_fields:
                    return False

                query = f"""
                    UPDATE task_imports
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE import_id = %s
                """
                params.append(import_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新导入进度失败: {e}")
            return False

    @staticmethod
    def update_import_status(
        import_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        cancelled_at: Optional[datetime] = None,
    ) -> bool:
        """更新导入状态"""
        try:
            conn = ImportSyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = ["status = %s"]
                params = [status]

                if started_at is not None:
                    update_fields.append("started_at = %s")
                    params.append(started_at)
                if completed_at is not None:
                    update_fields.append("completed_at = %s")
                    params.append(completed_at)
                if cancelled_at is not None:
                    update_fields.append("cancelled_at = %s")
                    params.append(cancelled_at)

                query = f"""
                    UPDATE task_imports
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE import_id = %s
                """
                params.append(import_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新导入状态失败: {e}")
            return False

    @staticmethod
    def update_import_result(
        import_id: str,
        duration_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None,
    ) -> bool:
        """更新导入结果"""
        try:
            conn = ImportSyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                update_fields = []
                params = []

                if duration_seconds is not None:
                    update_fields.append("duration_seconds = %s")
                    params.append(duration_seconds)
                if error_message is not None:
                    update_fields.append("error_message = %s")
                    params.append(error_message)
                if error_stack is not None:
                    update_fields.append("error_stack = %s")
                    params.append(error_stack)

                if not update_fields:
                    return False

                query = f"""
                    UPDATE task_imports
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE import_id = %s
                """
                params.append(import_id)

                cur.execute(query, params)
                conn.commit()
                return cur.rowcount == 1
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"更新导入结果失败: {e}")
            return False

    @staticmethod
    def add_import_error(
        import_id: str,
        file_name: Optional[str],
        case_id: Optional[int],
        error_type: Optional[str],
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> int:
        """添加导入错误记录"""
        try:
            conn = ImportSyncDatabase._get_connection()
            try:
                cur = conn.cursor()
                error_details_json = json.dumps(error_details) if error_details else None
                cur.execute(
                    """
                    INSERT INTO task_import_errors (
                        import_id, file_name, case_id, error_type, error_message, error_details
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (import_id, file_name, case_id, error_type, error_message, error_details_json)
                )
                log_id = cur.fetchone()[0]
                conn.commit()
                return log_id
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            logger.error(f"添加导入错误失败: {e}")
            return 0

    @staticmethod
    def add_log(
        task_id: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加任务日志（复用爬取任务的日志表）"""
        try:
            conn = ImportSyncDatabase._get_connection()
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
