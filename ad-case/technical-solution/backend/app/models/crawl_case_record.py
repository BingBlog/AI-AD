"""
案例爬取记录数据模型

定义案例爬取记录表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class CrawlCaseRecord:
    """
    案例爬取记录数据模型
    
    对应数据库表: crawl_case_records
    
    状态枚举:
    - pending: 等待中
    - success: 成功
    - failed: 失败
    - skipped: 跳过
    - validation_failed: 验证失败
    """
    # 主键
    id: Optional[int] = None  # 数据库自增主键
    
    # 关联
    task_id: Optional[str] = None  # 任务ID，外键关联 crawl_tasks(task_id)
    list_page_id: Optional[int] = None  # 列表页记录ID，外键关联 crawl_list_pages(id)
    
    # 案例标识
    case_id: Optional[int] = None  # 原始案例ID
    case_url: Optional[str] = None  # 案例URL
    case_title: Optional[str] = None  # 案例标题
    
    # 爬取状态
    status: str = 'pending'  # 状态，CHECK约束: success, failed, skipped, validation_failed, pending
    error_message: Optional[str] = None  # 错误消息
    error_type: Optional[str] = None  # 错误类型: network_error, parse_error, validation_error, timeout_error
    error_stack: Optional[str] = None  # 详细错误堆栈
    
    # 爬取结果
    crawled_at: Optional[datetime] = None  # 爬取时间
    duration_seconds: Optional[float] = None  # 爬取耗时（秒）
    
    # 数据质量
    has_detail_data: bool = False  # 是否成功获取详情页数据
    has_validation_error: bool = False  # 是否有验证错误
    validation_errors: Optional[Dict[str, Any]] = None  # 验证错误详情（JSONB类型）
    
    # 保存状态
    saved_to_json: bool = False  # 是否已保存到JSON文件
    batch_file_name: Optional[str] = None  # 保存到的批次文件名
    
    # 重试信息
    retry_count: int = 0  # 重试次数
    last_retry_at: Optional[datetime] = None  # 最后重试时间
    
    # 元数据
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    updated_at: Optional[datetime] = None  # 更新时间，自动更新
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlCaseRecord':
        """
        从字典创建 CrawlCaseRecord 实例
        
        Args:
            data: 包含案例记录数据的字典（通常来自数据库查询结果）
            
        Returns:
            CrawlCaseRecord 实例
        """
        # 处理 JSONB 字段
        validation_errors = data.get('validation_errors')
        if isinstance(validation_errors, str):
            validation_errors = json.loads(validation_errors) if validation_errors else None
        elif validation_errors is None:
            validation_errors = None
        
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            list_page_id=data.get('list_page_id'),
            case_id=data.get('case_id'),
            case_url=data.get('case_url'),
            case_title=data.get('case_title'),
            status=data.get('status', 'pending'),
            error_message=data.get('error_message'),
            error_type=data.get('error_type'),
            error_stack=data.get('error_stack'),
            crawled_at=data.get('crawled_at'),
            duration_seconds=data.get('duration_seconds'),
            has_detail_data=data.get('has_detail_data', False),
            has_validation_error=data.get('has_validation_error', False),
            validation_errors=validation_errors,
            saved_to_json=data.get('saved_to_json', False),
            batch_file_name=data.get('batch_file_name'),
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
            'list_page_id': self.list_page_id,
            'case_id': self.case_id,
            'case_url': self.case_url,
            'case_title': self.case_title,
            'status': self.status,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'error_stack': self.error_stack,
            'crawled_at': self.crawled_at,
            'duration_seconds': self.duration_seconds,
            'has_detail_data': self.has_detail_data,
            'has_validation_error': self.has_validation_error,
            'validation_errors': self.validation_errors,
            'saved_to_json': self.saved_to_json,
            'batch_file_name': self.batch_file_name,
            'retry_count': self.retry_count,
            'last_retry_at': self.last_retry_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data
