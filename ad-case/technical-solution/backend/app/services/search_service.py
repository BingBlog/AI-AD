"""
检索服务层
"""
from typing import Optional, List, Dict, Any
from app.repositories.case_repository import CaseRepository
from app.schemas.case import SearchRequest, SearchResponse, CaseSearchResult, Facets, FacetItem


class SearchService:
    """检索服务类"""
    
    def __init__(self):
        self.case_repo = CaseRepository()
    
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
            # 语义检索（待实现）
            raise NotImplementedError("语义检索功能待实现")
        elif request.search_type == "hybrid":
            # 混合检索（待实现）
            raise NotImplementedError("混合检索功能待实现")
        else:
            # 默认使用关键词检索
            return await self._search_keyword(request)
    
    async def _search_keyword(self, request: SearchRequest) -> SearchResponse:
        """关键词检索"""
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
