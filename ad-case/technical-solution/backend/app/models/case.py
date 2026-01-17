"""
广告案例数据模型

定义 ad_cases 表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
这些 Model 类主要用于：
1. 提供类型提示
2. 文档化数据库表结构
3. 字段验证规则说明
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date, datetime


@dataclass
class Case:
    """
    广告案例数据模型
    
    对应数据库表: ad_cases
    """
    # 主键和标识
    id: Optional[int] = None  # 数据库自增主键
    case_id: Optional[int] = None  # 原始案例ID（来自爬虫），唯一索引
    
    # 基础信息
    source_url: Optional[str] = None  # 案例来源URL，必填
    title: Optional[str] = None  # 案例标题，必填，最大500字符
    description: Optional[str] = None  # 详细描述（长文本）
    author: Optional[str] = None  # 作者，最大100字符
    publish_time: Optional[date] = None  # 发布时间
    
    # 媒体资源
    main_image: Optional[str] = None  # 主图URL
    images: List[str] = field(default_factory=list)  # 图片URL数组，JSONB类型
    video_url: Optional[str] = None  # 视频URL
    
    # 分类信息
    brand_name: Optional[str] = None  # 品牌名称，最大200字符
    brand_industry: Optional[str] = None  # 品牌行业，最大100字符
    activity_type: Optional[str] = None  # 活动类型，最大100字符
    location: Optional[str] = None  # 活动地点，最大100字符
    tags: List[str] = field(default_factory=list)  # 标签数组，JSONB类型
    
    # 评分与互动
    score: Optional[int] = None  # 评分（1-5），CHECK约束
    score_decimal: Optional[str] = None  # 评分小数（如"9.5"），最大10字符
    favourite: int = 0  # 收藏数，默认0
    
    # 公司信息
    company_name: Optional[str] = None  # 公司名称，最大200字符
    company_logo: Optional[str] = None  # 公司Logo URL
    agency_name: Optional[str] = None  # 广告公司名称，最大200字符
    
    # 向量字段（用于语义检索）
    # 注意：使用 BGE-large-zh，1024维
    title_vector: Optional[List[float]] = None  # 标题向量，vector(1024)
    description_vector: Optional[List[float]] = None  # 描述向量，vector(1024)
    combined_vector: Optional[List[float]] = None  # 标题+描述组合向量，vector(1024)
    
    # 全文检索字段（用于关键词检索）
    # 注意：这些字段由数据库触发器自动更新
    title_tsvector: Optional[str] = None  # 标题全文检索向量，tsvector类型
    description_tsvector: Optional[str] = None  # 描述全文检索向量，tsvector类型
    combined_tsvector: Optional[str] = None  # 标题+描述组合全文检索向量，tsvector类型
    
    # 元数据
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    updated_at: Optional[datetime] = None  # 更新时间，自动更新
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Case':
        """
        从字典创建 Case 实例
        
        Args:
            data: 包含案例数据的字典（通常来自数据库查询结果）
            
        Returns:
            Case 实例
        """
        # 处理 JSONB 字段
        images = data.get('images', [])
        if isinstance(images, str):
            import json
            images = json.loads(images) if images else []
        elif images is None:
            images = []
        
        tags = data.get('tags', [])
        if isinstance(tags, str):
            import json
            tags = json.loads(tags) if tags else []
        elif tags is None:
            tags = []
        
        return cls(
            id=data.get('id'),
            case_id=data.get('case_id'),
            source_url=data.get('source_url'),
            title=data.get('title'),
            description=data.get('description'),
            author=data.get('author'),
            publish_time=data.get('publish_time'),
            main_image=data.get('main_image'),
            images=images,
            video_url=data.get('video_url'),
            brand_name=data.get('brand_name'),
            brand_industry=data.get('brand_industry'),
            activity_type=data.get('activity_type'),
            location=data.get('location'),
            tags=tags,
            score=data.get('score'),
            score_decimal=data.get('score_decimal'),
            favourite=data.get('favourite', 0),
            company_name=data.get('company_name'),
            company_logo=data.get('company_logo'),
            agency_name=data.get('agency_name'),
            title_vector=data.get('title_vector'),
            description_vector=data.get('description_vector'),
            combined_vector=data.get('combined_vector'),
            title_tsvector=data.get('title_tsvector'),
            description_tsvector=data.get('description_tsvector'),
            combined_tsvector=data.get('combined_tsvector'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )
    
    def to_dict(self, exclude_none: bool = False) -> dict:
        """
        转换为字典
        
        Args:
            exclude_none: 是否排除 None 值
            
        Returns:
            字典
        """
        data = {
            'id': self.id,
            'case_id': self.case_id,
            'source_url': self.source_url,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'publish_time': self.publish_time,
            'main_image': self.main_image,
            'images': self.images,
            'video_url': self.video_url,
            'brand_name': self.brand_name,
            'brand_industry': self.brand_industry,
            'activity_type': self.activity_type,
            'location': self.location,
            'tags': self.tags,
            'score': self.score,
            'score_decimal': self.score_decimal,
            'favourite': self.favourite,
            'company_name': self.company_name,
            'company_logo': self.company_logo,
            'agency_name': self.agency_name,
            'title_vector': self.title_vector,
            'description_vector': self.description_vector,
            'combined_vector': self.combined_vector,
            'title_tsvector': self.title_tsvector,
            'description_tsvector': self.description_tsvector,
            'combined_tsvector': self.combined_tsvector,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data
