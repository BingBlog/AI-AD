"""
案例数据访问层
"""
from typing import Optional, List, Dict, Any
from datetime import date
from app.database import db


class CaseRepository:
    """案例数据访问类"""
    
    @staticmethod
    async def search_keyword(
        query: Optional[str],
        filters: Dict[str, Any],
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict], int]:
        """
        关键词检索
        
        Args:
            query: 检索关键词
            filters: 筛选条件字典
            sort_by: 排序字段
            sort_order: 排序顺序
            page: 页码
            page_size: 每页数量
            
        Returns:
            (结果列表, 总记录数)
        """
        # 构建 WHERE 条件
        where_conditions = []
        params = []
        
        # 关键词检索条件（使用全文检索）
        if query:
            # 使用 PostgreSQL 的 to_tsquery 进行全文检索
            # 注意：如果没有安装中文分词插件，使用 'simple' 配置
            where_conditions.append(
                "combined_tsvector @@ plainto_tsquery('simple', $1)"
            )
            params.append(query)
        
        # 筛选条件
        param_idx = len(params) + 1
        
        if filters.get("brand_name"):
            where_conditions.append(f"brand_name ILIKE ${param_idx}")
            params.append(f"%{filters['brand_name']}%")
            param_idx += 1
        
        if filters.get("brand_industry"):
            where_conditions.append(f"brand_industry = ${param_idx}")
            params.append(filters["brand_industry"])
            param_idx += 1
        
        if filters.get("activity_type"):
            where_conditions.append(f"activity_type = ${param_idx}")
            params.append(filters["activity_type"])
            param_idx += 1
        
        if filters.get("location"):
            where_conditions.append(f"location = ${param_idx}")
            params.append(filters["location"])
            param_idx += 1
        
        if filters.get("tags"):
            # JSONB 数组包含查询
            tags = filters["tags"]
            for tag in tags:
                where_conditions.append(f"tags @> ${param_idx}::jsonb")
                params.append(f'["{tag}"]')
                param_idx += 1
        
        if filters.get("start_date"):
            where_conditions.append(f"publish_time >= ${param_idx}")
            params.append(filters["start_date"])
            param_idx += 1
        
        if filters.get("end_date"):
            where_conditions.append(f"publish_time <= ${param_idx}")
            params.append(filters["end_date"])
            param_idx += 1
        
        if filters.get("min_score"):
            # min_score 是 1-5 的整数，需要同时检查 score 和 score_decimal
            # score_decimal 是 10 分制，需要转换为 5 分制进行比较
            # 例如：min_score=4 对应 score>=4 或 score_decimal>=8.0
            min_score_decimal = filters["min_score"] * 2.0  # 转换为10分制
            where_conditions.append(
                f"(score >= ${param_idx} OR CAST(score_decimal AS NUMERIC) >= ${param_idx + 1})"
            )
            params.append(filters["min_score"])
            params.append(min_score_decimal)
            param_idx += 2
        
        # 构建 WHERE 子句
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 构建排序子句
        if sort_by == "relevance" and query:
            # 相关性排序（使用 ts_rank）
            order_by_clause = f"ORDER BY ts_rank(combined_tsvector, plainto_tsquery('simple', $1)) DESC"
        elif sort_by == "time":
            order_by_clause = f"ORDER BY publish_time {sort_order.upper()}"
        elif sort_by == "score":
            # 使用 score_decimal 进行排序（10分制），如果不存在则使用 score（5分制）
            # 将 score_decimal 转换为数值类型进行排序
            order_by_clause = f"ORDER BY CAST(score_decimal AS NUMERIC) {sort_order.upper()} NULLS LAST, score {sort_order.upper()} NULLS LAST"
        elif sort_by == "favourite":
            order_by_clause = f"ORDER BY favourite {sort_order.upper()}"
        elif sort_by == "relevance" and not query:
            # 没有查询关键词时，相关性排序改为按时间倒序
            order_by_clause = "ORDER BY publish_time DESC"
        else:
            # 默认按时间倒序
            order_by_clause = "ORDER BY publish_time DESC"
        
        # 计算总数
        count_query = f"""
            SELECT COUNT(*) 
            FROM ad_cases 
            WHERE {where_clause}
        """
        total = await db.fetchval(count_query, *params)
        
        # 构建查询语句
        offset = (page - 1) * page_size
        limit_idx = len(params) + 1
        offset_idx = limit_idx + 1
        
        # 如果没有查询条件，使用默认排序（按时间倒序）
        if not query and sort_by == "relevance":
            order_by_clause = "ORDER BY publish_time DESC"
        
        select_query = f"""
            SELECT 
                case_id,
                title,
                description,
                source_url,
                main_image,
                images,
                video_url,
                brand_name,
                brand_industry,
                activity_type,
                location,
                tags,
                score,
                score_decimal,
                favourite,
                publish_time,
                author,
                company_name,
                company_logo,
                agency_name
            FROM ad_cases
            WHERE {where_clause}
            {order_by_clause}
            LIMIT ${limit_idx} OFFSET ${offset_idx}
        """
        params.extend([page_size, offset])
        
        # 执行查询
        rows = await db.fetch(select_query, *params)
        
        # 转换为字典列表
        results = []
        for row in rows:
            result = dict(row)
            # 处理 JSONB 字段
            if result.get("images"):
                result["images"] = result["images"] if isinstance(result["images"], list) else []
            if result.get("tags"):
                result["tags"] = result["tags"] if isinstance(result["tags"], list) else []
            results.append(result)
        
        return results, total
    
    @staticmethod
    async def get_by_id(case_id: int) -> Optional[Dict]:
        """根据 ID 获取案例详情"""
        query = """
            SELECT 
                case_id,
                title,
                description,
                source_url,
                main_image,
                images,
                video_url,
                brand_name,
                brand_industry,
                activity_type,
                location,
                tags,
                score,
                score_decimal,
                favourite,
                publish_time,
                author,
                company_name,
                company_logo,
                agency_name,
                created_at,
                updated_at
            FROM ad_cases
            WHERE case_id = $1
        """
        row = await db.fetchrow(query, case_id)
        
        if not row:
            return None
        
        result = dict(row)
        # 处理 JSONB 字段
        if result.get("images"):
            result["images"] = result["images"] if isinstance(result["images"], list) else []
        if result.get("tags"):
            result["tags"] = result["tags"] if isinstance(result["tags"], list) else []
        
        return result
