"""
案例相关的 Schema 定义
"""
from typing import Optional, List, Dict, Any, Union
from datetime import date
from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    """案例基础信息"""
    case_id: int = Field(description="案例ID")
    title: str = Field(description="案例标题")
    description: Optional[str] = Field(default=None, description="案例描述")
    source_url: str = Field(description="案例来源URL")
    main_image: Optional[str] = Field(default=None, description="主图URL")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    video_url: Optional[str] = Field(default=None, description="视频URL")
    brand_name: Optional[str] = Field(default=None, description="品牌名称")
    brand_industry: Optional[str] = Field(default=None, description="品牌行业")
    activity_type: Optional[str] = Field(default=None, description="活动类型")
    location: Optional[str] = Field(default=None, description="活动地点")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    score: Optional[int] = Field(default=None, ge=1, le=5, description="评分（1-5）")
    score_decimal: Optional[str] = Field(default=None, description="评分（小数）")
    favourite: int = Field(default=0, description="收藏数")
    publish_time: Optional[date] = Field(default=None, description="发布时间")
    author: Optional[str] = Field(default=None, description="作者")
    company_name: Optional[str] = Field(default=None, description="公司名称")
    company_logo: Optional[str] = Field(default=None, description="公司Logo")
    agency_name: Optional[str] = Field(default=None, description="广告公司名称")


class CaseSearchResult(CaseBase):
    """案例检索结果"""
    similarity: Optional[float] = Field(default=None, description="相似度分数（语义检索）")
    highlight: Optional[Dict[str, str]] = Field(default=None, description="高亮文本")


class SearchRequest(BaseModel):
    """检索请求参数"""
    query: Optional[str] = Field(default=None, description="检索关键词（用于关键词检索）")
    semantic_query: Optional[str] = Field(default=None, description="语义检索查询文本")
    search_type: str = Field(default="keyword", description="检索类型：keyword（关键词）、semantic（语义）、hybrid（混合）")
    
    # 筛选条件（支持字符串或字符串数组，数组表示多选）
    brand_name: Optional[Union[str, List[str]]] = Field(default=None, description="品牌名称（支持多选）")
    brand_industry: Optional[Union[str, List[str]]] = Field(default=None, description="品牌行业（支持多选）")
    activity_type: Optional[Union[str, List[str]]] = Field(default=None, description="活动类型（支持多选）")
    location: Optional[Union[str, List[str]]] = Field(default=None, description="活动地点（支持多选）")
    tags: Optional[List[str]] = Field(default=None, description="标签列表（多个标签为 AND 关系）")
    start_date: Optional[date] = Field(default=None, description="开始日期")
    end_date: Optional[date] = Field(default=None, description="结束日期")
    min_score: Optional[int] = Field(default=None, ge=1, le=5, description="最低评分（1-5）")
    
    # 排序和分页
    sort_by: str = Field(default="relevance", description="排序字段：relevance（相关性）、time（时间）、score（评分）、favourite（收藏数）")
    sort_order: str = Field(default="desc", description="排序顺序：asc（升序）、desc（降序）")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量，最大 100")
    min_similarity: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="最小相似度（仅语义检索，0-1）")


class FacetItem(BaseModel):
    """分面统计项"""
    name: str = Field(description="名称")
    count: int = Field(description="数量")


class Facets(BaseModel):
    """分面统计"""
    brands: List[FacetItem] = Field(default_factory=list, description="品牌统计")
    industries: List[FacetItem] = Field(default_factory=list, description="行业统计")
    activity_types: List[FacetItem] = Field(default_factory=list, description="活动类型统计")
    tags: List[FacetItem] = Field(default_factory=list, description="标签统计")
    locations: List[FacetItem] = Field(default_factory=list, description="地点统计")


class FilterOption(BaseModel):
    """筛选选项"""
    value: str = Field(description="选项值")
    count: int = Field(description="对应的案例数量")


class FilterOptionsResponse(BaseModel):
    """筛选选项响应"""
    field: str = Field(description="字段名")
    options: List[FilterOption] = Field(description="选项列表")


class SearchResponse(BaseModel):
    """检索响应"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")
    results: List[CaseSearchResult] = Field(description="检索结果列表")
    facets: Optional[Facets] = Field(default=None, description="分面统计")
