"""
案例相关路由
"""
import logging
from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List
from datetime import date
from app.schemas.case import SearchRequest, SearchResponse, FilterOptionsResponse
from app.schemas.response import BaseResponse
from app.services.search_service import SearchService
from app.repositories.case_repository import CaseRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["案例"])

# 延迟加载服务实例（避免启动时加载模型）
_search_service: Optional[SearchService] = None

def get_search_service() -> SearchService:
    """获取搜索服务实例（延迟加载）"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service


@router.get("/search", response_model=BaseResponse[SearchResponse])
async def search_cases(
    request: Request,
    query: Optional[str] = Query(None, description="检索关键词（用于关键词检索）"),
    semantic_query: Optional[str] = Query(None, description="语义检索查询文本"),
    search_type: str = Query("keyword", description="检索类型：keyword（关键词）、semantic（语义）、hybrid（混合）"),
    brand_name: Optional[List[str]] = Query(None, description="品牌名称（支持多选，传入多个值）"),
    brand_industry: Optional[List[str]] = Query(None, description="品牌行业（支持多选，传入多个值）"),
    activity_type: Optional[List[str]] = Query(None, description="活动类型（支持多选，传入多个值）"),
    location: Optional[List[str]] = Query(None, description="活动地点（支持多选，传入多个值）"),
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
        # 处理 brand_industry[] 格式的参数（FastAPI不支持[]格式，需要手动处理）
        # 如果brand_industry为None，尝试从请求参数中获取brand_industry[]格式的参数
        if brand_industry is None:
            query_params = request.query_params
            # 检查是否有brand_industry[]参数
            brand_industry_list = []
            for key, value in query_params.multi_items():
                if key == 'brand_industry[]':
                    brand_industry_list.append(value)
            if brand_industry_list:
                brand_industry = brand_industry_list
                logger.info(f"Found brand_industry[] parameters: {brand_industry}")
        
        # 同样处理其他数组参数
        if brand_name is None:
            brand_name_list = []
            for key, value in request.query_params.multi_items():
                if key == 'brand_name[]':
                    brand_name_list.append(value)
            if brand_name_list:
                brand_name = brand_name_list
        
        if activity_type is None:
            activity_type_list = []
            for key, value in request.query_params.multi_items():
                if key == 'activity_type[]':
                    activity_type_list.append(value)
            if activity_type_list:
                activity_type = activity_type_list
        
        if location is None:
            location_list = []
            for key, value in request.query_params.multi_items():
                if key == 'location[]':
                    location_list.append(value)
            if location_list:
                location = location_list
        
        logger.info(f"Final brand_industry: {brand_industry}, type: {type(brand_industry)}")
        
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
        
        logger.info(f"SearchRequest built - brand_industry: {request.brand_industry}, type: {type(request.brand_industry)}")
        
        # 执行检索（延迟加载服务，避免启动时加载模型）
        result = await get_search_service().search(request)
        
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/filter-options", response_model=BaseResponse[FilterOptionsResponse])
async def get_filter_options(
    field: str = Query(..., description="字段名：brand_name, brand_industry, activity_type, location"),
    keyword: Optional[str] = Query(None, description="搜索关键词（可选）"),
    limit: int = Query(20, ge=1, le=1000, description="返回数量限制，默认20，最大1000"),
):
    """
    获取筛选字段的可选项
    
    支持字段：
    - brand_name: 品牌名称
    - brand_industry: 品牌行业
    - activity_type: 活动类型
    - location: 活动地点
    """
    # 验证字段名
    valid_fields = ['brand_name', 'brand_industry', 'activity_type', 'location']
    if field not in valid_fields:
        raise HTTPException(status_code=400, detail=f"无效的字段名，支持的字段：{', '.join(valid_fields)}")
    
    try:
        case_repo = CaseRepository()
        options = await case_repo.get_filter_options(field, keyword, limit)
        
        # 转换为响应格式
        result = FilterOptionsResponse(
            field=field,
            options=options
        )
        
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选选项失败: {str(e)}")


@router.get("/{case_id}", response_model=BaseResponse[dict])
async def get_case_detail(case_id: int):
    """
    获取案例详情
    
    Args:
        case_id: 案例ID
    """
    case_repo = CaseRepository()
    case = await case_repo.get_by_id(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail=f"案例 {case_id} 不存在")
    
    return BaseResponse(
        code=200,
        message="success",
        data=case
    )


@router.get("/{case_id}/similar", response_model=BaseResponse[dict])
async def get_similar_cases(
    case_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量，默认10，最大50"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="最小相似度，默认0.6"),
):
    """
    获取相似案例推荐（基于向量相似度）
    
    Args:
        case_id: 目标案例ID
        limit: 返回数量
        min_similarity: 最小相似度
    """
    try:
        case_repo = CaseRepository()
        similar_cases = await case_repo.get_similar_cases(
            case_id=case_id,
            limit=limit,
            min_similarity=min_similarity
        )
        
        return BaseResponse(
            code=200,
            message="success",
            data={
                "case_id": case_id,
                "similar_cases": similar_cases
            }
        )
    except Exception as e:
        logger.error(f"获取相似案例失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相似案例失败: {str(e)}")
