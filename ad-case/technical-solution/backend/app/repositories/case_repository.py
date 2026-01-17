"""
案例数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import date
from app.database import db

logger = logging.getLogger(__name__)


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
        
        # 关键词检索条件（使用 ILIKE 进行模糊匹配，支持中文）
        if query:
            # 使用 ILIKE 在多个字段中搜索，支持中文
            # 搜索字段：title, description, brand_name
            query_param = f"%{query}%"
            where_conditions.append(
                "(title ILIKE $1 OR description ILIKE $1 OR brand_name ILIKE $1)"
            )
            params.append(query_param)
        
        # 筛选条件
        param_idx = len(params) + 1
        
        if filters.get("brand_name"):
            brand_name_value = filters["brand_name"]
            if isinstance(brand_name_value, list) and len(brand_name_value) > 0:
                # 多选：使用 IN 或 ILIKE ANY
                placeholders = ", ".join([f"${param_idx + i}" for i in range(len(brand_name_value))])
                where_conditions.append(f"brand_name ILIKE ANY(ARRAY[{placeholders}])")
                params.extend([f"%{v}%" for v in brand_name_value])
                param_idx += len(brand_name_value)
            elif isinstance(brand_name_value, str):
                # 单选：模糊匹配
                where_conditions.append(f"brand_name ILIKE ${param_idx}")
                params.append(f"%{brand_name_value}%")
                param_idx += 1
        
        if filters.get("brand_industry"):
            brand_industry_value = filters["brand_industry"]
            logger.debug(f"brand_industry filter value: {brand_industry_value}, type: {type(brand_industry_value)}")
            if isinstance(brand_industry_value, list) and len(brand_industry_value) > 0:
                # 多选：处理可能包含顿号的值，拆分成多个值
                expanded_values = []
                for v in brand_industry_value:
                    # 如果值包含顿号，拆分成多个值
                    if '、' in v or ',' in v:
                        # 支持中文顿号和英文逗号
                        parts = v.replace(',', '、').split('、')
                        expanded_values.extend([p.strip() for p in parts if p.strip()])
                    else:
                        expanded_values.append(v.strip())
                
                # 去重
                expanded_values = list(set(expanded_values))
                logger.debug(f"brand_industry expanded values: {expanded_values}")
                
                if expanded_values:
                    # 使用多个 ILIKE OR 条件进行模糊匹配，支持部分匹配
                    # 构建 OR 条件：brand_industry ILIKE $X OR brand_industry ILIKE $Y OR ...
                    or_conditions = []
                    for i, v in enumerate(expanded_values):
                        or_conditions.append(f"brand_industry ILIKE ${param_idx + i}")
                        params.append(f"%{v}%")
                    where_conditions.append(f"({' OR '.join(or_conditions)})")
                    logger.debug(f"brand_industry SQL condition: ({' OR '.join(or_conditions)})")
                    logger.debug(f"brand_industry params: {[f'%{v}%' for v in expanded_values]}")
                    param_idx += len(expanded_values)
            elif isinstance(brand_industry_value, str):
                # 单选：模糊匹配
                where_conditions.append(f"brand_industry ILIKE ${param_idx}")
                params.append(f"%{brand_industry_value}%")
                param_idx += 1
        
        if filters.get("activity_type"):
            activity_type_value = filters["activity_type"]
            if isinstance(activity_type_value, list) and len(activity_type_value) > 0:
                # 多选：处理可能包含顿号的值，拆分成多个值
                expanded_values = []
                for v in activity_type_value:
                    # 如果值包含顿号，拆分成多个值
                    if '、' in v or ',' in v:
                        # 支持中文顿号和英文逗号
                        parts = v.replace(',', '、').split('、')
                        expanded_values.extend([p.strip() for p in parts if p.strip()])
                    else:
                        expanded_values.append(v.strip())
                
                # 去重
                expanded_values = list(set(expanded_values))
                
                if expanded_values:
                    # 使用多个 ILIKE OR 条件进行模糊匹配，支持部分匹配
                    or_conditions = []
                    for i, v in enumerate(expanded_values):
                        or_conditions.append(f"activity_type ILIKE ${param_idx + i}")
                        params.append(f"%{v}%")
                    where_conditions.append(f"({' OR '.join(or_conditions)})")
                    param_idx += len(expanded_values)
            elif isinstance(activity_type_value, str):
                # 单选：模糊匹配
                where_conditions.append(f"activity_type ILIKE ${param_idx}")
                params.append(f"%{activity_type_value}%")
                param_idx += 1
        
        if filters.get("location"):
            location_value = filters["location"]
            if isinstance(location_value, list) and len(location_value) > 0:
                # 多选：处理可能包含顿号的值，拆分成多个值
                expanded_values = []
                for v in location_value:
                    # 如果值包含顿号，拆分成多个值
                    if '、' in v or ',' in v:
                        # 支持中文顿号和英文逗号
                        parts = v.replace(',', '、').split('、')
                        expanded_values.extend([p.strip() for p in parts if p.strip()])
                    else:
                        expanded_values.append(v.strip())
                
                # 去重
                expanded_values = list(set(expanded_values))
                
                if expanded_values:
                    # 使用多个 ILIKE OR 条件进行模糊匹配，支持部分匹配
                    or_conditions = []
                    for i, v in enumerate(expanded_values):
                        or_conditions.append(f"location ILIKE ${param_idx + i}")
                        params.append(f"%{v}%")
                    where_conditions.append(f"({' OR '.join(or_conditions)})")
                    param_idx += len(expanded_values)
            elif isinstance(location_value, str):
                # 单选：模糊匹配
                where_conditions.append(f"location ILIKE ${param_idx}")
                params.append(f"%{location_value}%")
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
        logger.debug(f"WHERE clause: {where_clause}")
        logger.debug(f"Params: {params}")
        
        # 构建排序子句
        if sort_by == "relevance" and query:
            # 相关性排序（使用字段匹配优先级：title > brand_name > description）
            # 使用 CASE WHEN 来设置匹配优先级
            # 注意：query 参数已经在 WHERE 条件中使用 $1，这里可以复用同一个参数
            order_by_clause = """ORDER BY 
                CASE 
                    WHEN title ILIKE $1 THEN 1
                    WHEN brand_name ILIKE $1 THEN 2
                    WHEN description ILIKE $1 THEN 3
                    ELSE 4
                END ASC,
                publish_time DESC"""
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
        logger.debug(f"Count query: {count_query}")
        logger.debug(f"Count query params: {params}")
        total = await db.fetchval(count_query, *params)
        logger.debug(f"Total count: {total}")
        
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
        logger.debug(f"Select query: {select_query}")
        logger.debug(f"Select query params: {params}")
        
        # 执行查询
        rows = await db.fetch(select_query, *params)
        logger.debug(f"Query returned {len(rows)} rows")
        
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
    
    @staticmethod
    async def get_filter_options(
        field: str,
        keyword: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取筛选字段的可选项
        
        Args:
            field: 字段名（brand_name, brand_industry, activity_type, location）
            keyword: 搜索关键词（可选）
            limit: 返回数量限制
            
        Returns:
            选项列表，每个选项包含 value 和 count
        """
        # 验证字段名
        valid_fields = ['brand_name', 'brand_industry', 'activity_type', 'location']
        if field not in valid_fields:
            return []
        
        # 构建查询条件
        where_conditions = [f"{field} IS NOT NULL"]
        params = []
        
        # 如果有搜索关键词，添加模糊匹配条件
        if keyword:
            where_conditions.append(f"{field} ILIKE ${len(params) + 1}")
            params.append(f"%{keyword}%")
        
        where_clause = " AND ".join(where_conditions)
        
        # 构建查询：获取不重复的值和对应的数量
        query = f"""
            SELECT 
                {field} as value,
                COUNT(*) as count
            FROM ad_cases
            WHERE {where_clause}
            GROUP BY {field}
            ORDER BY count DESC, {field} ASC
            LIMIT ${len(params) + 1}
        """
        params.append(limit)
        
        # 执行查询
        rows = await db.fetch(query, *params)
        
        # 转换为字典列表
        results = []
        for row in rows:
            if row['value']:  # 排除空值
                results.append({
                    'value': row['value'],
                    'count': row['count']
                })
        
        return results