"""
任务导入数据访问层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import db
import uuid
import json


class TaskImportRepository:
    """任务导入数据访问类"""

    @staticmethod
    async def create_import(
        task_id: str,
        import_mode: str,
        selected_batches: Optional[List[str]],
        skip_existing: bool,
        update_existing: bool,
        generate_vectors: bool,
        skip_invalid: bool,
        batch_size: int,
    ) -> str:
        """
        创建导入记录

        Returns:
            导入ID
        """
        import_id = f"import_{uuid.uuid4().hex[:16]}"

        query = """
            INSERT INTO task_imports (
                import_id, task_id, import_mode, selected_batches,
                skip_existing, update_existing, generate_vectors,
                skip_invalid, batch_size, status
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            ) RETURNING import_id
        """

        selected_batches_json = json.dumps(selected_batches) if selected_batches else None

        await db.execute(
            query,
            import_id, task_id, import_mode, selected_batches_json,
            skip_existing, update_existing, generate_vectors,
            skip_invalid, batch_size, "pending"
        )

        return import_id

    @staticmethod
    async def get_import(import_id: str) -> Optional[Dict[str, Any]]:
        """获取导入记录"""
        query = """
            SELECT * FROM task_imports WHERE import_id = $1
        """
        row = await db.fetchrow(query, import_id)
        if row:
            data = dict(row)
            # 处理 JSONB 字段
            if data.get('selected_batches'):
                if isinstance(data['selected_batches'], str):
                    data['selected_batches'] = json.loads(data['selected_batches'])
            return data
        return None

    @staticmethod
    async def get_task_imports(task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有导入记录"""
        query = """
            SELECT * FROM task_imports
            WHERE task_id = $1
            ORDER BY created_at DESC
        """
        rows = await db.fetch(query, task_id)
        result = []
        for row in rows:
            data = dict(row)
            # 处理 JSONB 字段
            if data.get('selected_batches'):
                if isinstance(data['selected_batches'], str):
                    data['selected_batches'] = json.loads(data['selected_batches'])
            result.append(data)
        return result

    @staticmethod
    async def get_latest_import(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务的最新导入记录"""
        query = """
            SELECT * FROM task_imports
            WHERE task_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await db.fetchrow(query, task_id)
        if row:
            data = dict(row)
            # 处理 JSONB 字段
            if data.get('selected_batches'):
                if isinstance(data['selected_batches'], str):
                    data['selected_batches'] = json.loads(data['selected_batches'])
            return data
        return None

    @staticmethod
    async def update_import_status(
        import_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        cancelled_at: Optional[datetime] = None,
    ) -> bool:
        """更新导入状态"""
        update_fields = []
        params = []

        # Always include status
        update_fields.append("status = $1")
        params.append(status)

        if started_at is not None:
            update_fields.append(f"started_at = ${len(params) + 1}")
            params.append(started_at)
        if completed_at is not None:
            update_fields.append(f"completed_at = ${len(params) + 1}")
            params.append(completed_at)
        if cancelled_at is not None:
            update_fields.append(f"cancelled_at = ${len(params) + 1}")
            params.append(cancelled_at)

        query = f"""
            UPDATE task_imports
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE import_id = ${len(params) + 1}
        """
        params.append(import_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def update_import_progress(
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
        update_fields = []
        params = []

        if total_cases is not None:
            update_fields.append("total_cases = $1")
            params.append(total_cases)
        if loaded_cases is not None:
            update_fields.append(f"loaded_cases = ${len(params) + 1}")
            params.append(loaded_cases)
        if valid_cases is not None:
            update_fields.append(f"valid_cases = ${len(params) + 1}")
            params.append(valid_cases)
        if invalid_cases is not None:
            update_fields.append(f"invalid_cases = ${len(params) + 1}")
            params.append(invalid_cases)
        if existing_cases is not None:
            update_fields.append(f"existing_cases = ${len(params) + 1}")
            params.append(existing_cases)
        if imported_cases is not None:
            update_fields.append(f"imported_cases = ${len(params) + 1}")
            params.append(imported_cases)
        if failed_cases is not None:
            update_fields.append(f"failed_cases = ${len(params) + 1}")
            params.append(failed_cases)
        if current_file is not None:
            update_fields.append(f"current_file = ${len(params) + 1}")
            params.append(current_file)

        if not update_fields:
            return False

        query = f"""
            UPDATE task_imports
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE import_id = ${len(params) + 1}
        """
        params.append(import_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def update_import_result(
        import_id: str,
        duration_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None,
    ) -> bool:
        """更新导入结果"""
        update_fields = []
        params = []

        if duration_seconds is not None:
            update_fields.append("duration_seconds = $1")
            params.append(duration_seconds)
        if error_message is not None:
            update_fields.append(f"error_message = ${len(params) + 1}")
            params.append(error_message)
        if error_stack is not None:
            update_fields.append(f"error_stack = ${len(params) + 1}")
            params.append(error_stack)

        if not update_fields:
            return False

        query = f"""
            UPDATE task_imports
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE import_id = ${len(params) + 1}
        """
        params.append(import_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def add_import_error(
        import_id: str,
        file_name: Optional[str],
        case_id: Optional[int],
        error_type: Optional[str],
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> int:
        """添加导入错误记录"""
        query = """
            INSERT INTO task_import_errors (
                import_id, file_name, case_id, error_type, error_message, error_details
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        error_details_json = json.dumps(error_details) if error_details else None
        result = await db.fetchval(
            query,
            import_id, file_name, case_id, error_type, error_message, error_details_json
        )
        return result

    @staticmethod
    async def get_import_errors(import_id: str) -> List[Dict[str, Any]]:
        """获取导入错误列表"""
        query = """
            SELECT * FROM task_import_errors
            WHERE import_id = $1
            ORDER BY created_at DESC
        """
        rows = await db.fetch(query, import_id)
        result = []
        for row in rows:
            data = dict(row)
            # 处理 JSONB 字段
            if data.get('error_details'):
                if isinstance(data['error_details'], str):
                    data['error_details'] = json.loads(data['error_details'])
            result.append(data)
        return result
