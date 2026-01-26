"""
检索服务层
"""
import logging
from typing import Optional, List, Dict, Any
from app.repositories.case_repository import CaseRepository
from app.schemas.case import SearchRequest, SearchResponse, CaseSearchResult, Facets, FacetItem
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class SearchService:
    """检索服务类"""
    
    def __init__(self):
        self.case_repo = CaseRepository()
        self.vector_service = VectorService()
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        执行检索
        
        Args:
            request: 检索请求参数
            
        Returns:
            检索响应
        """
        # 根据检索类型选择检索方法
        if request.search_type == "keyword":
            return await self._search_keyword(request)
        elif request.search_type == "semantic":
            return await self._search_semantic(request)
        elif request.search_type == "hybrid":
            return await self._search_hybrid(request)
        else:
            # 默认使用关键词检索
            return await self._search_keyword(request)
    
    async def _search_keyword(self, request: SearchRequest) -> SearchResponse:
        """关键词检索"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"SearchRequest received - brand_industry: {request.brand_industry}, type: {type(request.brand_industry)}")
        
        # 构建筛选条件
        filters = {
            "brand_name": request.brand_name,
            "brand_industry": request.brand_industry,
            "activity_type": request.activity_type,
            "location": request.location,
            "tags": request.tags,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "min_score": request.min_score,
        }
        logger.info(f"Filters built - brand_industry: {filters.get('brand_industry')}, type: {type(filters.get('brand_industry'))}")
        
        # 允许在没有查询关键词时也执行查询（返回所有数据或根据筛选条件）
        # 这样可以支持浏览所有案例的功能
        
        # 执行检索（query 可以为 None，此时只根据筛选条件查询）
        results, total = await self.case_repo.search_keyword(
            query=request.query,
            filters=filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            page_size=request.page_size
        )
        
        # 转换为响应模型
        case_results = []
        for result in results:
            case_result = CaseSearchResult(
                case_id=result["case_id"],
                title=result["title"],
                description=result.get("description"),
                source_url=result["source_url"],
                main_image=result.get("main_image"),
                images=result.get("images", []),
                video_url=result.get("video_url"),
                brand_name=result.get("brand_name"),
                brand_industry=result.get("brand_industry"),
                activity_type=result.get("activity_type"),
                location=result.get("location"),
                tags=result.get("tags", []),
                score=result.get("score"),
                score_decimal=result.get("score_decimal"),
                favourite=result.get("favourite", 0),
                publish_time=result.get("publish_time"),
                author=result.get("author"),
                company_name=result.get("company_name"),
                company_logo=result.get("company_logo"),
                agency_name=result.get("agency_name"),
                similarity=None,  # 关键词检索没有相似度
                highlight=None,  # 高亮功能待实现
            )
            case_results.append(case_result)
        
        # 计算总页数
        total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 0
        
        # 构建响应
        response = SearchResponse(
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            results=case_results,
            facets=None  # 分面统计待实现
        )
        
        return response
    
    async def _search_semantic(self, request: SearchRequest) -> SearchResponse:
        """语义检索"""
        # 验证语义查询文本
        if not request.semantic_query or not request.semantic_query.strip():
            raise ValueError("语义检索查询文本不能为空")
        
        # 将查询文本编码为向量
        query_vector = await self.vector_service.encode_query(request.semantic_query)
        
        # 构建筛选条件
        filters = {
            "brand_name": request.brand_name,
            "brand_industry": request.brand_industry,
            "activity_type": request.activity_type,
            "location": request.location,
            "tags": request.tags,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "min_score": request.min_score,
        }
        
        # 执行语义检索
        min_similarity = request.min_similarity or 0.5
        results, total = await self.case_repo.search_semantic(
            query_vector=query_vector,
            filters=filters,
            min_similarity=min_similarity,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            page_size=request.page_size
        )
        
        # 转换为响应模型
        case_results = []
        for result in results:
            case_result = CaseSearchResult(
                case_id=result["case_id"],
                title=result["title"],
                description=result.get("description"),
                source_url=result["source_url"],
                main_image=result.get("main_image"),
                images=result.get("images", []),
                video_url=result.get("video_url"),
                brand_name=result.get("brand_name"),
                brand_industry=result.get("brand_industry"),
                activity_type=result.get("activity_type"),
                location=result.get("location"),
                tags=result.get("tags", []),
                score=result.get("score"),
                score_decimal=result.get("score_decimal"),
                favourite=result.get("favourite", 0),
                publish_time=result.get("publish_time"),
                author=result.get("author"),
                company_name=result.get("company_name"),
                company_logo=result.get("company_logo"),
                agency_name=result.get("agency_name"),
                similarity=float(result.get("similarity", 0.0)),  # 语义检索包含相似度
                highlight=None,  # 高亮功能待实现
            )
            case_results.append(case_result)
        
        # 计算总页数
        total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 0
        
        # 构建响应
        response = SearchResponse(
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            results=case_results,
            facets=None  # 分面统计待实现
        )
        
        return response
    
    async def _search_hybrid(self, request: SearchRequest) -> SearchResponse:
        """混合检索（关键词 + 语义）"""
        # 混合检索需要同时有 query 和 semantic_query
        if not request.query and not request.semantic_query:
            raise ValueError("混合检索需要提供关键词或语义查询文本")
        
        # 如果只有关键词，降级为关键词检索
        if not request.semantic_query:
            logger.warning("混合检索缺少语义查询文本，降级为关键词检索")
            return await self._search_keyword(request)
        
        # 如果只有语义查询，降级为语义检索
        if not request.query:
            logger.warning("混合检索缺少关键词，降级为语义检索")
            return await self._search_semantic(request)
        
        # 混合检索：使用语义检索结果，对包含关键词的结果进行加权提升
        # 默认权重：关键词 40%，语义 60%
        keyword_weight = 0.4
        semantic_weight = 0.6
        
        # 使用语义检索获取结果
        semantic_request = SearchRequest(
            query=None,
            semantic_query=request.semantic_query,
            search_type="semantic",
            brand_name=request.brand_name,
            brand_industry=request.brand_industry,
            activity_type=request.activity_type,
            location=request.location,
            tags=request.tags,
            start_date=request.start_date,
            end_date=request.end_date,
            min_score=request.min_score,
            sort_by="relevance",
            sort_order="desc",
            page=1,
            page_size=min(request.page_size * 3, 100),  # 获取更多结果以便混合排序
            min_similarity=request.min_similarity,
        )
        
        semantic_response = await self._search_semantic(semantic_request)
        
        # 对结果进行关键词匹配和加权融合
        query_lower = request.query.lower()
        hybrid_results = []
        
        for case in semantic_response.results:
            similarity = case.similarity or 0.0
            
            # 计算关键词匹配得分（简单匹配）
            keyword_score = 0.0
            title = (case.title or "").lower()
            description = (case.description or "").lower()
            brand_name = (case.brand_name or "").lower()
            
            if query_lower in title:
                keyword_score = 1.0  # 标题完全匹配
            elif query_lower in brand_name:
                keyword_score = 0.8  # 品牌名匹配
            elif query_lower in description:
                keyword_score = 0.5  # 描述匹配
            elif any(query_lower in word for word in title.split()):
                keyword_score = 0.6  # 标题部分匹配
            
            # 加权融合得分
            final_score = keyword_score * keyword_weight + similarity * semantic_weight
            
            # 创建新结果对象（保留原数据，更新相似度为最终得分）
            hybrid_case = CaseSearchResult(
                **case.dict(exclude={'similarity'}),
                similarity=final_score
            )
            hybrid_results.append((hybrid_case, final_score))
        
        # 按最终得分排序
        hybrid_results.sort(key=lambda x: x[1], reverse=True)
        
        # 分页
        total = len(hybrid_results)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        paginated_results = [case for case, _ in hybrid_results[start:end]]
        
        # 计算总页数
        total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 0
        
        # 构建响应
        response = SearchResponse(
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            results=paginated_results,
            facets=None
        )
        
        return response