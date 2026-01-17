"""
爬取任务数据模型

定义爬取任务相关表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class CrawlTask:
    """
    爬取任务数据模型
    
    对应数据库表: crawl_tasks
    
    状态枚举:
    - pending: 等待中
    - running: 运行中
    - paused: 已暂停
    - completed: 已完成
    - failed: 已失败
    - cancelled: 已取消
    - terminated: 已终止
    """
    # 主键和标识
    id: Optional[int] = None  # 数据库自增主键
    task_id: Optional[str] = None  # 任务ID，唯一索引，格式: task_{uuid}
    
    # 基本信息
    name: Optional[str] = None  # 任务名称，必填，最大255字符
    data_source: Optional[str] = None  # 数据源，必填，最大64字符（如"adquan"）
    description: Optional[str] = None  # 任务描述
    
    # 任务配置
    start_page: Optional[int] = None  # 起始页码，必填，>= 0
    end_page: Optional[int] = None  # 结束页码，>= start_page
    case_type: Optional[int] = None  # 案例类型
    search_value: Optional[str] = None  # 搜索关键词，最大255字符
    batch_size: int = 100  # 批次大小，默认100，> 0
    delay_min: float = 2.0  # 最小延迟时间（秒），默认2.0，>= 0
    delay_max: float = 5.0  # 最大延迟时间（秒），默认5.0，>= delay_min
    enable_resume: bool = True  # 是否启用断点续传，默认True
    
    # 任务状态
    status: str = 'pending'  # 任务状态，默认pending，CHECK约束
    
    # 时间信息
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    started_at: Optional[datetime] = None  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    paused_at: Optional[datetime] = None  # 暂停时间
    
    # 进度信息
    total_pages: Optional[int] = None  # 总页数
    completed_pages: int = 0  # 已完成页数，默认0
    current_page: Optional[int] = None  # 当前页码
    
    # 统计信息
    total_crawled: int = 0  # 总爬取数，默认0
    total_saved: int = 0  # 总保存数，默认0
    total_failed: int = 0  # 总失败数，默认0
    batches_saved: int = 0  # 已保存批次数，默认0
    
    # 性能指标
    avg_speed: Optional[float] = None  # 平均爬取速度（案例/分钟）
    avg_delay: Optional[float] = None  # 平均请求延迟（秒）
    error_rate: Optional[float] = None  # 错误率，0-1之间
    
    # 错误信息
    error_message: Optional[str] = None  # 错误信息
    error_stack: Optional[str] = None  # 错误堆栈
    
    # 元数据
    created_by: Optional[str] = None  # 创建者，最大64字符
    updated_at: Optional[datetime] = None  # 更新时间，自动更新
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlTask':
        """
        从字典创建 CrawlTask 实例
        
        Args:
            data: 包含任务数据的字典（通常来自数据库查询结果）
            
        Returns:
            CrawlTask 实例
        """
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            name=data.get('name'),
            data_source=data.get('data_source'),
            description=data.get('description'),
            start_page=data.get('start_page'),
            end_page=data.get('end_page'),
            case_type=data.get('case_type'),
            search_value=data.get('search_value'),
            batch_size=data.get('batch_size', 100),
            delay_min=data.get('delay_min', 2.0),
            delay_max=data.get('delay_max', 5.0),
            enable_resume=data.get('enable_resume', True),
            status=data.get('status', 'pending'),
            created_at=data.get('created_at'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            paused_at=data.get('paused_at'),
            total_pages=data.get('total_pages'),
            completed_pages=data.get('completed_pages', 0),
            current_page=data.get('current_page'),
            total_crawled=data.get('total_crawled', 0),
            total_saved=data.get('total_saved', 0),
            total_failed=data.get('total_failed', 0),
            batches_saved=data.get('batches_saved', 0),
            avg_speed=data.get('avg_speed'),
            avg_delay=data.get('avg_delay'),
            error_rate=data.get('error_rate'),
            error_message=data.get('error_message'),
            error_stack=data.get('error_stack'),
            created_by=data.get('created_by'),
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
            'name': self.name,
            'data_source': self.data_source,
            'description': self.description,
            'start_page': self.start_page,
            'end_page': self.end_page,
            'case_type': self.case_type,
            'search_value': self.search_value,
            'batch_size': self.batch_size,
            'delay_min': self.delay_min,
            'delay_max': self.delay_max,
            'enable_resume': self.enable_resume,
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'paused_at': self.paused_at,
            'total_pages': self.total_pages,
            'completed_pages': self.completed_pages,
            'current_page': self.current_page,
            'total_crawled': self.total_crawled,
            'total_saved': self.total_saved,
            'total_failed': self.total_failed,
            'batches_saved': self.batches_saved,
            'avg_speed': self.avg_speed,
            'avg_delay': self.avg_delay,
            'error_rate': self.error_rate,
            'error_message': self.error_message,
            'error_stack': self.error_stack,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data


@dataclass
class CrawlTaskLog:
    """
    爬取任务日志数据模型
    
    对应数据库表: crawl_task_logs
    
    日志级别枚举:
    - INFO: 信息
    - WARNING: 警告
    - ERROR: 错误
    - DEBUG: 调试
    """
    id: Optional[int] = None  # 数据库自增主键
    task_id: Optional[str] = None  # 任务ID，外键关联 crawl_tasks(task_id)
    level: Optional[str] = None  # 日志级别，CHECK约束: INFO, WARNING, ERROR, DEBUG
    message: Optional[str] = None  # 日志消息，必填
    details: Optional[Dict[str, Any]] = None  # 详细信息，JSONB类型
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlTaskLog':
        """
        从字典创建 CrawlTaskLog 实例
        
        Args:
            data: 包含日志数据的字典（通常来自数据库查询结果）
            
        Returns:
            CrawlTaskLog 实例
        """
        # 处理 JSONB 字段
        details = data.get('details')
        if isinstance(details, str):
            details = json.loads(details) if details else None
        elif details is None:
            details = None
        
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            level=data.get('level'),
            message=data.get('message'),
            details=details,
            created_at=data.get('created_at'),
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
            'level': self.level,
            'message': self.message,
            'details': self.details,
            'created_at': self.created_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data


@dataclass
class CrawlTaskStatusHistory:
    """
    爬取任务状态历史数据模型
    
    对应数据库表: crawl_task_status_history
    
    用于记录任务状态变更历史，由数据库触发器自动创建。
    """
    id: Optional[int] = None  # 数据库自增主键
    task_id: Optional[str] = None  # 任务ID，外键关联 crawl_tasks(task_id)
    status: Optional[str] = None  # 新状态，CHECK约束
    previous_status: Optional[str] = None  # 之前的状态
    reason: Optional[str] = None  # 状态变更原因
    created_at: Optional[datetime] = None  # 创建时间，自动设置
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlTaskStatusHistory':
        """
        从字典创建 CrawlTaskStatusHistory 实例
        
        Args:
            data: 包含状态历史数据的字典（通常来自数据库查询结果）
            
        Returns:
            CrawlTaskStatusHistory 实例
        """
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            status=data.get('status'),
            previous_status=data.get('previous_status'),
            reason=data.get('reason'),
            created_at=data.get('created_at'),
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
            'status': self.status,
            'previous_status': self.previous_status,
            'reason': self.reason,
            'created_at': self.created_at,
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        
        return data
