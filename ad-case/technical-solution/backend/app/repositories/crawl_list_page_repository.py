"""
列表页爬取记录数据访问层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import db


class CrawlListPageRepository:
    """列表页爬取记录数据访问类"""

    @staticmethod
    async def create_list_page_record(
        task_id: str, page_number: int
    ) -> int:
        """
        创建列表页记录
        
        Args:
            task_id: 任务ID
            page_number: 页码
            
        Returns:
            记录ID
        """
        query = """
            INSERT INTO crawl_list_pages (task_id, page_number, status)
            VALUES ($1, $2, 'pending')
            ON CONFLICT (task_id, page_number) 
            DO UPDATE SET status = 'pending', updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        record_id = await db.fetchval(query, task_id, page_number)
        return record_id

    @staticmethod
    async def update_list_page_success(
        record_id: int, items_count: int, duration: float
    ):
        """
        更新列表页成功记录
        
        Args:
            record_id: 记录ID
            items_count: 获取到的案例数量
            duration: 爬取耗时（秒）
        """
        query = """
            UPDATE crawl_list_pages
            SET status = 'success',
                items_count = $1,
                crawled_at = CURRENT_TIMESTAMP,
                duration_seconds = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $3
        """
        
        await db.execute(query, items_count, duration, record_id)

    @staticmethod
    async def update_list_page_failed(
        record_id: int, error_message: str, error_type: str, duration: float
    ):
        """
        更新列表页失败记录
        
        Args:
            record_id: 记录ID
            error_message: 错误消息
            error_type: 错误类型
            duration: 爬取耗时（秒）
        """
        query = """
            UPDATE crawl_list_pages
            SET status = 'failed',
                error_message = $1,
                error_type = $2,
                crawled_at = CURRENT_TIMESTAMP,
                duration_seconds = $3,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $4
        """
        
        await db.execute(query, error_message, error_type, duration, record_id)

    @staticmethod
    async def get_failed_list_pages(task_id: str) -> List[Dict[str, Any]]:
        """
        获取失败的列表页
        
        Args:
            task_id: 任务ID
            
        Returns:
            失败的列表页记录列表
        """
        query = """
            SELECT id, task_id, page_number, status, error_message, error_type,
                   items_count, crawled_at, duration_seconds, retry_count, last_retry_at,
                   created_at, updated_at
            FROM crawl_list_pages
            WHERE task_id = $1 AND status = 'failed'
            ORDER BY page_number ASC
        """
        
        rows = await db.fetch(query, task_id)
        return [dict(row) for row in rows]

    @staticmethod
    async def increment_retry_count(record_id: int):
        """
        增加重试次数
        
        Args:
            record_id: 记录ID
        """
        query = """
            UPDATE crawl_list_pages
            SET retry_count = retry_count + 1,
                last_retry_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await db.execute(query, record_id)

    @staticmethod
    async def get_list_page_by_task_and_page(
        task_id: str, page_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        根据任务ID和页码获取列表页记录
        
        Args:
            task_id: 任务ID
            page_number: 页码
            
        Returns:
            列表页记录，如果不存在则返回None
        """
        query = """
            SELECT id, task_id, page_number, status, error_message, error_type,
                   items_count, crawled_at, duration_seconds, retry_count, last_retry_at,
                   created_at, updated_at
            FROM crawl_list_pages
            WHERE task_id = $1 AND page_number = $2
        """
        
        row = await db.fetchrow(query, task_id, page_number)
        return dict(row) if row else None

    @staticmethod
    async def list_list_pages(
        task_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取列表页记录列表
        
        Args:
            task_id: 任务ID
            status: 状态筛选（可选）
            page: 页码
            page_size: 每页大小
            
        Returns:
            (列表页记录列表, 总记录数)
        """
        where_conditions = ["task_id = $1"]
        params = [task_id]
        param_idx = 2

        if status:
            where_conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_clause = " AND ".join(where_conditions)

        # 查询总数
        count_query = f"SELECT COUNT(*) FROM crawl_list_pages WHERE {where_clause}"
        total = await db.fetchval(count_query, *params)

        # 查询列表
        offset = (page - 1) * page_size
        list_query = f"""
            SELECT id, task_id, page_number, status, error_message, error_type,
                   items_count, crawled_at, duration_seconds, retry_count, last_retry_at,
                   created_at, updated_at
            FROM crawl_list_pages
            WHERE {where_clause}
            ORDER BY page_number ASC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.append(page_size)
        params.append(offset)

        rows = await db.fetch(list_query, *params)
        return [dict(row) for row in rows], total
