"""
案例相关路由
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import date
from app.schemas.case import SearchRequest, SearchResponse
from app.schemas.response import BaseResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1/cases", tags=["案例"])

# 创建服务实例
search_service = SearchService()


@router.get("/search", response_model=BaseResponse[SearchResponse])
async def search_cases(
    query: Optional[str] = Query(None, description="检索关键词（用于关键词检索）"),
    semantic_query: Optional[str] = Query(None, description="语义检索查询文本"),
    search_type: str = Query("keyword", description="检索类型：keyword（关键词）、semantic（语义）、hybrid（混合）"),
    brand_name: Optional[str] = Query(None, description="品牌名称"),
    brand_industry: Optional[str] = Query(None, description="品牌行业"),
    activity_type: Optional[str] = Query(None, description="活动类型"),
    location: Optional[str] = Query(None, description="活动地点"),
    tags: Optional[List[str]] = Query(None, description="标签列表（多个标签为 AND 关系）"),
    start_date: Optional[date] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[date] = Query(None, description="结束日期（YYYY-MM-DD）"),
    min_score: Optional[int] = Query(None, ge=1, le=5, description="最低评分（1-5）"),
    sort_by: str = Query("relevance", description="排序字段：relevance（相关性）、time（时间）、score（评分）、favourite（收藏数）"),
    sort_order: str = Query("desc", description="排序顺序：asc（升序）、desc（降序）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大 100"),
    min_similarity: Optional[float] = Query(0.5, ge=0.0, le=1.0, description="最小相似度（仅语义检索，0-1）"),
):
    """
    案例检索接口
    
    支持关键词检索、语义检索和混合检索（当前仅支持关键词检索）
    """
    try:
        # 构建请求对象
        request = SearchRequest(
            query=query,
            semantic_query=semantic_query,
            search_type=search_type,
            brand_name=brand_name,
            brand_industry=brand_industry,
            activity_type=activity_type,
            location=location,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            min_similarity=min_similarity,
        )
        
        # 执行检索
        result = await search_service.search(request)
        
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/{case_id}", response_model=BaseResponse[dict])
async def get_case_detail(case_id: int):
    """
    获取案例详情
    
    Args:
        case_id: 案例ID
    """
    from app.repositories.case_repository import CaseRepository
    
    case_repo = CaseRepository()
    case = await case_repo.get_by_id(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail=f"案例 {case_id} 不存在")
    
    return BaseResponse(
        code=200,
        message="success",
        data=case
    )
