"""
列表页爬取记录数据模型

定义列表页爬取记录表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json


@dataclass
class CrawlListPage:
    """
    列表页爬取记录数据模型
    
    对应数据库表: crawl_list_pages
    
    状态枚举:
    - pending: 等待中
    - success: 成功
    - failed: 失败
    - skipped: 跳过
    """
    # 主键
    id: Optional[int] = None  # 数据库自增主键
    
    # 关联
    task_id: Optional[str] = None  # 任务ID，外键关联 crawl_tasks(task_id)
    page_number: Optional[int] = None  # 页码（从0开始）
    
    # 爬取状态
    status: str = 'pending'  # 状态，CHECK约束: success, failed, skipped, pending
    error_message: Optional[str] = None  # 错误消息
    error_type: Optional[str] = None  # 错误类型: network_error, parse_error, api_error, timeout_error
    
    # 爬取结果
    items_count: int = 0  # 获取到的案例数量
    crawled_at: Optional[datetime] = None  # 爬取时间
    duration_seconds: Optional[float] = None  # 爬取耗时（秒）
    
    # 重试信息
    retry_count: int = 0  # 重试次数
    last_retry_at: Optional[datetime] = None  # 最后重试时间
    
    # 元数据
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    updated_at: Optional[datetime] = None  # 更新时间，自动更新
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlListPage':
        """
        从字典创建 CrawlListPage 实例
        
        Args:
            data: 包含列表页记录数据的字典（通常来自数据库查询结果）
            
        Returns:
            CrawlListPage 实例
        """
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            page_number=data.get('page_number'),
            status=data.get('status', 'pending'),
            error_message=data.get('error_message'),
            error_type=data.get('error_type'),
            items_count=data.get('items_count', 0),
            crawled_at=data.get('crawled_at'),
            duration_seconds=data.get('duration_seconds'),
            retry_count=data.get('retry_count', 0),
            last_retry_at=data.get('last_retry_at'),
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
            'task_id': self.task_id,
            'page_number': self.page_number,
            'status': self.status,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'items_count': self.items_count,
            'crawled_at': self.crawled_at,
            'duration_seconds': self.duration_seconds,
            'retry_count': self.retry_count,
            'last_retry_at': self.last_retry_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data
