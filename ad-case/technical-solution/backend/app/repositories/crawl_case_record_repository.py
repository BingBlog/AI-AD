"""
案例爬取记录数据访问层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import db
import json


class CrawlCaseRecordRepository:
    """案例爬取记录数据访问类"""

    @staticmethod
    async def create_case_record(
        task_id: str, list_page_id: Optional[int], case_id: int,
        case_url: str, case_title: str
    ) -> int:
        """
        创建案例记录
        
        Args:
            task_id: 任务ID
            list_page_id: 列表页记录ID（可选）
            case_id: 案例ID
            case_url: 案例URL
            case_title: 案例标题
            
        Returns:
            记录ID
        """
        query = """
            INSERT INTO crawl_case_records (
                task_id, list_page_id, case_id, case_url, case_title, status
            )
            VALUES ($1, $2, $3, $4, $5, 'pending')
            ON CONFLICT (task_id, case_id) 
            DO UPDATE SET 
                list_page_id = EXCLUDED.list_page_id,
                case_url = EXCLUDED.case_url,
                case_title = EXCLUDED.case_title,
                status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        record_id = await db.fetchval(
            query, task_id, list_page_id, case_id, case_url, case_title
        )
        return record_id

    @staticmethod
    async def update_case_success(
        record_id: int, duration: float, has_detail_data: bool = True
    ):
        """
        更新案例成功记录
        
        Args:
            record_id: 记录ID
            duration: 爬取耗时（秒）
            has_detail_data: 是否成功获取详情页数据
        """
        query = """
            UPDATE crawl_case_records
            SET status = 'success',
                has_detail_data = $1,
                crawled_at = CURRENT_TIMESTAMP,
                duration_seconds = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $3
        """
        
        await db.execute(query, has_detail_data, duration, record_id)

    @staticmethod
    async def update_case_failed(
        record_id: int, error_message: str, error_type: str,
        error_stack: Optional[str], duration: float
    ):
        """
        更新案例失败记录
        
        Args:
            record_id: 记录ID
            error_message: 错误消息
            error_type: 错误类型
            error_stack: 错误堆栈（可选）
            duration: 爬取耗时（秒）
        """
        query = """
            UPDATE crawl_case_records
            SET status = 'failed',
                error_message = $1,
                error_type = $2,
                error_stack = $3,
                crawled_at = CURRENT_TIMESTAMP,
                duration_seconds = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $5
        """
        
        await db.execute(query, error_message, error_type, error_stack, duration, record_id)

    @staticmethod
    async def update_case_validation_failed(
        record_id: int, validation_errors: Dict[str, Any]
    ):
        """
        更新案例验证失败记录
        
        Args:
            record_id: 记录ID
            validation_errors: 验证错误详情（字典）
        """
        validation_errors_json = json.dumps(validation_errors) if validation_errors else None
        
        query = """
            UPDATE crawl_case_records
            SET status = 'validation_failed',
                has_validation_error = TRUE,
                validation_errors = $1::jsonb,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await db.execute(query, validation_errors_json, record_id)

    @staticmethod
    async def update_case_saved(
        record_id: int, batch_file_name: str
    ):
        """
        更新案例保存状态
        
        Args:
            record_id: 记录ID
            batch_file_name: 批次文件名
        """
        query = """
            UPDATE crawl_case_records
            SET saved_to_json = TRUE,
                batch_file_name = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await db.execute(query, batch_file_name, record_id)

    @staticmethod
    async def update_cases_saved_batch(
        record_ids: List[int], batch_file_name: str
    ):
        """
        批量更新案例保存状态
        
        Args:
            record_ids: 记录ID列表
            batch_file_name: 批次文件名
        """
        if not record_ids:
            return
        
        # 使用 IN 子句批量更新
        placeholders = ','.join([f'${i+2}' for i in range(len(record_ids))])
        query = f"""
            UPDATE crawl_case_records
            SET saved_to_json = TRUE,
                batch_file_name = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """
        
        await db.execute(query, batch_file_name, *record_ids)

    @staticmethod
    async def update_case_import_status(
        record_id: int, 
        imported: bool = True, 
        import_status: Optional[str] = None
    ):
        """
        更新案例导入状态
        
        Args:
            record_id: 记录ID
            imported: 是否已导入（默认True）
            import_status: 导入状态，'success' 或 'failed'
        """
        query = """
            UPDATE crawl_case_records
            SET imported = $1,
                import_status = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $3
        """
        
        await db.execute(query, imported, import_status, record_id)

    @staticmethod
    async def update_case_verified(record_id: int, verified: bool = True):
        """
        更新案例验证状态（是否在案例库中存在）
        
        Args:
            record_id: 记录ID
            verified: 是否已验证（默认True）
        """
        query = """
            UPDATE crawl_case_records
            SET verified = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await db.execute(query, verified, record_id)

    @staticmethod
    async def update_case_import_and_verified_by_case_id(
        task_id: str,
        case_id: int,
        imported: bool = True,
        import_status: Optional[str] = None,
        verified: bool = False
    ):
        """
        根据任务ID和案例ID更新导入状态和验证状态
        
        Args:
            task_id: 任务ID
            case_id: 案例ID
            imported: 是否已导入（默认True）
            import_status: 导入状态，'success' 或 'failed'
            verified: 是否已验证（默认False）
        """
        query = """
            UPDATE crawl_case_records
            SET imported = $1,
                import_status = $2,
                verified = $3,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = $4 AND case_id = $5
        """
        
        await db.execute(query, imported, import_status, verified, task_id, case_id)

    @staticmethod
    async def batch_update_import_status_by_case_ids(
        task_id: str,
        case_ids: List[int],
        imported: bool = True,
        import_status: Optional[str] = None
    ):
        """
        批量更新案例导入状态
        
        Args:
            task_id: 任务ID
            case_ids: 案例ID列表
            imported: 是否已导入（默认True）
            import_status: 导入状态，'success' 或 'failed'
        """
        if not case_ids:
            return
        
        placeholders = ','.join([f'${i+4}' for i in range(len(case_ids))])
        query = f"""
            UPDATE crawl_case_records
            SET imported = $1,
                import_status = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = $3 AND case_id IN ({placeholders})
        """
        
        await db.execute(query, imported, import_status, task_id, *case_ids)

    @staticmethod
    async def batch_verify_cases_by_case_ids(
        task_id: str,
        case_ids: List[int],
        verified: bool = True
    ):
        """
        批量验证案例（检查是否在案例库中存在）
        
        Args:
            task_id: 任务ID
            case_ids: 案例ID列表（这些案例已确认在 ad_cases 表中存在）
            verified: 是否已验证（默认True）
        """
        if not case_ids:
            return
        
        placeholders = ','.join([f'${i+3}' for i in range(len(case_ids))])
        query = f"""
            UPDATE crawl_case_records
            SET verified = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = $2 AND case_id IN ({placeholders})
        """
        
        await db.execute(query, verified, task_id, *case_ids)

    @staticmethod
    async def get_failed_cases(task_id: str) -> List[Dict[str, Any]]:
        """
        获取失败的案例
        
        Args:
            task_id: 任务ID
            
        Returns:
            失败的案例记录列表
        """
        query = """
            SELECT id, task_id, list_page_id, case_id, case_url, case_title,
                   status, error_message, error_type, error_stack,
                   crawled_at, duration_seconds, has_detail_data, has_validation_error,
                   validation_errors, saved_to_json, batch_file_name,
                   imported, import_status, verified,
                   retry_count, last_retry_at, created_at, updated_at
            FROM crawl_case_records
            WHERE task_id = $1 AND status IN ('failed', 'validation_failed')
            ORDER BY created_at DESC
        """
        
        rows = await db.fetch(query, task_id)
        return [dict(row) for row in rows]

    @staticmethod
    async def get_cases_by_ids(
        task_id: str, case_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        根据案例ID列表获取案例记录
        
        Args:
            task_id: 任务ID
            case_ids: 案例ID列表
            
        Returns:
            案例记录列表
        """
        if not case_ids:
            return []
        
        placeholders = ','.join([f'${i+2}' for i in range(len(case_ids))])
        query = f"""
            SELECT id, task_id, list_page_id, case_id, case_url, case_title,
                   status, error_message, error_type, error_stack,
                   crawled_at, duration_seconds, has_detail_data, has_validation_error,
                   validation_errors, saved_to_json, batch_file_name,
                   imported, import_status, verified,
                   retry_count, last_retry_at, created_at, updated_at
            FROM crawl_case_records
            WHERE task_id = $1 AND case_id IN ({placeholders})
            ORDER BY created_at DESC
        """
        
        rows = await db.fetch(query, task_id, *case_ids)
        return [dict(row) for row in rows]

    @staticmethod
    async def verify_imports_by_checking_ad_cases(task_id: str) -> Dict[str, Any]:
        """
        验证案例记录的导入状态（检查 case_id 是否在 ad_cases 表中存在）
        
        Args:
            task_id: 任务ID
            
        Returns:
            验证结果统计：{
                'total_checked': 检查的总数,
                'verified_count': 已验证的数量（在 ad_cases 中存在）,
                'unverified_count': 未验证的数量（在 ad_cases 中不存在）
            }
        """
        # 1. 查询任务中所有有 case_id 的记录
        records_query = """
            SELECT DISTINCT case_id 
            FROM crawl_case_records 
            WHERE task_id = $1 AND case_id IS NOT NULL
        """
        records = await db.fetch(records_query, task_id)
        case_ids = [row['case_id'] for row in records if row['case_id']]
        
        if not case_ids:
            return {
                'total_checked': 0,
                'verified_count': 0,
                'unverified_count': 0
            }
        
        # 2. 检查这些 case_id 是否在 ad_cases 表中存在
        placeholders = ','.join([f'${i+1}' for i in range(len(case_ids))])
        existing_query = f"""
            SELECT case_id 
            FROM ad_cases 
            WHERE case_id IN ({placeholders})
        """
        existing_rows = await db.fetch(existing_query, *case_ids)
        existing_case_ids = {row['case_id'] for row in existing_rows}
        
        # 3. 分离已验证和未验证的 case_id
        verified_case_ids = [cid for cid in case_ids if cid in existing_case_ids]
        unverified_case_ids = [cid for cid in case_ids if cid not in existing_case_ids]
        
        # 4. 批量更新验证状态
        if verified_case_ids:
            await CrawlCaseRecordRepository.batch_verify_cases_by_case_ids(
                task_id=task_id,
                case_ids=verified_case_ids,
                verified=True
            )
        
        if unverified_case_ids:
            # 设置未验证的记录为 verified=False
            unverified_placeholders = ','.join([f'${i+3}' for i in range(len(unverified_case_ids))])
            unverified_query = f"""
                UPDATE crawl_case_records
                SET verified = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $2 AND case_id IN ({unverified_placeholders})
            """
            await db.execute(unverified_query, False, task_id, *unverified_case_ids)
        
        return {
            'total_checked': len(case_ids),
            'verified_count': len(verified_case_ids),
            'unverified_count': len(unverified_case_ids)
        }

    @staticmethod
    async def increment_retry_count(record_id: int):
        """
        增加重试次数
        
        Args:
            record_id: 记录ID
        """
        query = """
            UPDATE crawl_case_records
            SET retry_count = retry_count + 1,
                last_retry_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await db.execute(query, record_id)

    @staticmethod
    async def get_case_by_task_and_case_id(
        task_id: str, case_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        根据任务ID和案例ID获取案例记录
        
        Args:
            task_id: 任务ID
            case_id: 案例ID
            
        Returns:
            案例记录，如果不存在则返回None
        """
        query = """
            SELECT id, task_id, list_page_id, case_id, case_url, case_title,
                   status, error_message, error_type, error_stack,
                   crawled_at, duration_seconds, has_detail_data, has_validation_error,
                   validation_errors, saved_to_json, batch_file_name,
                   imported, import_status, verified,
                   retry_count, last_retry_at, created_at, updated_at
            FROM crawl_case_records
            WHERE task_id = $1 AND case_id = $2
        """
        
        row = await db.fetchrow(query, task_id, case_id)
        return dict(row) if row else None

    @staticmethod
    async def list_case_records(
        task_id: str,
        status: Optional[str] = None,
        list_page_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取案例记录列表
        
        Args:
            task_id: 任务ID
            status: 状态筛选（可选）
            list_page_id: 列表页ID筛选（可选）
            page: 页码
            page_size: 每页大小
            
        Returns:
            (案例记录列表, 总记录数)
        """
        where_conditions = ["task_id = $1"]
        params = [task_id]
        param_idx = 2

        if status:
            where_conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if list_page_id is not None:
            where_conditions.append(f"list_page_id = ${param_idx}")
            params.append(list_page_id)
            param_idx += 1

        where_clause = " AND ".join(where_conditions)

        # 查询总数
        count_query = f"SELECT COUNT(*) FROM crawl_case_records WHERE {where_clause}"
        total = await db.fetchval(count_query, *params)

        # 查询列表
        offset = (page - 1) * page_size
        list_query = f"""
            SELECT id, task_id, list_page_id, case_id, case_url, case_title,
                   status, error_message, error_type, error_stack,
                   crawled_at, duration_seconds, has_detail_data, has_validation_error,
                   validation_errors, saved_to_json, batch_file_name,
                   imported, import_status, verified,
                   retry_count, last_retry_at, created_at, updated_at
            FROM crawl_case_records
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.append(page_size)
        params.append(offset)

        rows = await db.fetch(list_query, *params)
        return [dict(row) for row in rows], total
