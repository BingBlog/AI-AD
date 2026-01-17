"""
爬取任务数据访问层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import db
import uuid


class CrawlTaskRepository:
    """爬取任务数据访问类"""

    @staticmethod
    async def create_task(
        name: str,
        data_source: str,
        description: Optional[str],
        start_page: int,
        end_page: Optional[int],
        case_type: Optional[int],
        search_value: Optional[str],
        batch_size: int,
        delay_min: float,
        delay_max: float,
        enable_resume: bool,
        created_by: Optional[str] = None
    ) -> str:
        """
        创建任务

        Returns:
            任务ID
        """
        task_id = f"task_{uuid.uuid4().hex[:16]}"
        
        query = """
            INSERT INTO crawl_tasks (
                task_id, name, data_source, description,
                start_page, end_page, case_type, search_value,
                batch_size, delay_min, delay_max, enable_resume,
                status, created_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            ) RETURNING task_id
        """
        
        await db.execute(
            query,
            task_id, name, data_source, description,
            start_page, end_page, case_type, search_value,
            batch_size, delay_min, delay_max, enable_resume,
            'pending', created_by
        )
        
        return task_id

    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        query = """
            SELECT 
                task_id, name, data_source, description,
                start_page, end_page, case_type, search_value,
                batch_size, delay_min, delay_max, enable_resume,
                status, created_at, started_at, completed_at, paused_at,
                total_pages, completed_pages, current_page,
                total_crawled, total_saved, total_failed, batches_saved,
                avg_speed, avg_delay, error_rate,
                error_message, error_stack, created_by, updated_at
            FROM crawl_tasks
            WHERE task_id = $1
        """
        
        row = await db.fetchrow(query, task_id)
        if not row:
            return None
        
        return dict(row)

    @staticmethod
    async def list_tasks(
        status: Optional[str] = None,
        data_source: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取任务列表

        Returns:
            (任务列表, 总记录数)
        """
        # 构建 WHERE 条件
        where_conditions = []
        params = []
        param_idx = 1

        if status:
            where_conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if data_source:
            where_conditions.append(f"data_source = ${param_idx}")
            params.append(data_source)
            param_idx += 1

        if keyword:
            where_conditions.append(f"(name ILIKE ${param_idx} OR description ILIKE ${param_idx})")
            params.append(f"%{keyword}%")
            param_idx += 1

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 排序字段映射
        sort_field_map = {
            "created_at": "created_at",
            "started_at": "started_at",
            "status": "status",
            "progress": "completed_pages"
        }
        sort_field = sort_field_map.get(sort_by, "created_at")
        sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

        # 查询总数
        count_query = f"SELECT COUNT(*) FROM crawl_tasks WHERE {where_clause}"
        total = await db.fetchval(count_query, *params)

        # 查询列表
        offset = (page - 1) * page_size
        list_query = f"""
            SELECT 
                task_id, name, data_source, status,
                created_at, started_at, completed_at,
                total_pages, completed_pages, current_page,
                total_crawled, total_saved, total_failed, batches_saved,
                avg_speed, avg_delay, error_rate
            FROM crawl_tasks
            WHERE {where_clause}
            ORDER BY {sort_field} {sort_dir}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.append(page_size)
        params.append(offset)

        rows = await db.fetch(list_query, *params)
        return [dict(row) for row in rows], total

    @staticmethod
    async def update_task_status(
        task_id: str,
        status: str,
        **kwargs
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            **kwargs: 其他要更新的字段（如 started_at, completed_at 等）
        """
        update_fields = ["status = $1"]
        params = [status]
        param_idx = 2

        # 根据状态设置时间字段
        if status == "running" and "started_at" not in kwargs:
            update_fields.append(f"started_at = ${param_idx}")
            params.append(datetime.now())
            param_idx += 1
        elif status == "completed" and "completed_at" not in kwargs:
            update_fields.append(f"completed_at = ${param_idx}")
            params.append(datetime.now())
            param_idx += 1
        elif status == "paused" and "paused_at" not in kwargs:
            update_fields.append(f"paused_at = ${param_idx}")
            params.append(datetime.now())
            param_idx += 1

        # 添加其他更新字段
        for key, value in kwargs.items():
            if value is not None:
                update_fields.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1

        query = f"""
            UPDATE crawl_tasks
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ${param_idx}
        """
        params.append(task_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def update_task_progress(
        task_id: str,
        completed_pages: Optional[int] = None,
        current_page: Optional[int] = None,
        total_crawled: Optional[int] = None,
        total_saved: Optional[int] = None,
        total_failed: Optional[int] = None,
        batches_saved: Optional[int] = None
    ) -> bool:
        """更新任务进度"""
        update_fields = []
        params = []
        param_idx = 1

        if completed_pages is not None:
            update_fields.append(f"completed_pages = ${param_idx}")
            params.append(completed_pages)
            param_idx += 1

        if current_page is not None:
            update_fields.append(f"current_page = ${param_idx}")
            params.append(current_page)
            param_idx += 1

        if total_crawled is not None:
            update_fields.append(f"total_crawled = ${param_idx}")
            params.append(total_crawled)
            param_idx += 1

        if total_saved is not None:
            update_fields.append(f"total_saved = ${param_idx}")
            params.append(total_saved)
            param_idx += 1

        if total_failed is not None:
            update_fields.append(f"total_failed = ${param_idx}")
            params.append(total_failed)
            param_idx += 1

        if batches_saved is not None:
            update_fields.append(f"batches_saved = ${param_idx}")
            params.append(batches_saved)
            param_idx += 1

        if not update_fields:
            return False

        query = f"""
            UPDATE crawl_tasks
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ${param_idx}
        """
        params.append(task_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def update_task_stats(
        task_id: str,
        avg_speed: Optional[float] = None,
        avg_delay: Optional[float] = None,
        error_rate: Optional[float] = None
    ) -> bool:
        """更新任务统计信息"""
        update_fields = []
        params = []
        param_idx = 1

        if avg_speed is not None:
            update_fields.append(f"avg_speed = ${param_idx}")
            params.append(avg_speed)
            param_idx += 1

        if avg_delay is not None:
            update_fields.append(f"avg_delay = ${param_idx}")
            params.append(avg_delay)
            param_idx += 1

        if error_rate is not None:
            update_fields.append(f"error_rate = ${param_idx}")
            params.append(error_rate)
            param_idx += 1

        if not update_fields:
            return False

        query = f"""
            UPDATE crawl_tasks
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ${param_idx}
        """
        params.append(task_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def update_task_error(
        task_id: str,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None
    ) -> bool:
        """更新任务错误信息"""
        update_fields = []
        params = []
        param_idx = 1

        if error_message is not None:
            update_fields.append(f"error_message = ${param_idx}")
            params.append(error_message)
            param_idx += 1

        if error_stack is not None:
            update_fields.append(f"error_stack = ${param_idx}")
            params.append(error_stack)
            param_idx += 1

        if not update_fields:
            return False

        query = f"""
            UPDATE crawl_tasks
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ${param_idx}
        """
        params.append(task_id)

        result = await db.execute(query, *params)
        return result == "UPDATE 1"

    @staticmethod
    async def add_log(
        task_id: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        添加任务日志

        Returns:
            日志ID
        """
        import json
        details_json = json.dumps(details) if details else None

        query = """
            INSERT INTO crawl_task_logs (task_id, level, message, details)
            VALUES ($1, $2, $3, $4::jsonb)
            RETURNING id
        """
        
        log_id = await db.fetchval(query, task_id, level, message, details_json)
        return log_id

    @staticmethod
    async def get_logs(
        task_id: str,
        level: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取任务日志

        Returns:
            (日志列表, 总记录数)
        """
        where_conditions = ["task_id = $1"]
        params = [task_id]
        param_idx = 2

        if level:
            where_conditions.append(f"level = ${param_idx}")
            params.append(level)
            param_idx += 1

        where_clause = " AND ".join(where_conditions)

        # 查询总数
        count_query = f"SELECT COUNT(*) FROM crawl_task_logs WHERE {where_clause}"
        total = await db.fetchval(count_query, *params)

        # 查询列表
        offset = (page - 1) * page_size
        list_query = f"""
            SELECT id, level, message, details, created_at
            FROM crawl_task_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.append(page_size)
        params.append(offset)

        rows = await db.fetch(list_query, *params)
        return [dict(row) for row in rows], total

    @staticmethod
    async def get_last_crawled_page(data_source: str = "adquan") -> Optional[int]:
        """
        获取上一次爬取到的页数
        
        Args:
            data_source: 数据源，默认为 "adquan"
            
        Returns:
            上一次爬取到的页数，如果没有则返回 None
        """
        # 查询已完成或已终止的任务，获取最大的 end_page 或 current_page
        query = """
            SELECT COALESCE(MAX(end_page), MAX(current_page), 0) as last_page
            FROM crawl_tasks
            WHERE data_source = $1
            AND status IN ('completed', 'terminated')
            AND (end_page IS NOT NULL OR current_page IS NOT NULL)
        """
        
        result = await db.fetchval(query, data_source)
        return result if result is not None else None

    @staticmethod
    async def delete_task(task_id: str) -> bool:
        """删除任务（仅限已完成、已失败、已取消的任务）"""
        query = """
            DELETE FROM crawl_tasks
            WHERE task_id = $1
            AND status IN ('completed', 'failed', 'cancelled')
        """
        
        result = await db.execute(query, task_id)
        return result == "DELETE 1"
