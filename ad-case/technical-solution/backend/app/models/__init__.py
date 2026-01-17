"""
数据模型模块

定义数据库表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
"""
from app.models.case import Case
from app.models.crawl_task import CrawlTask, CrawlTaskLog, CrawlTaskStatusHistory

__all__ = [
    'Case',
    'CrawlTask',
    'CrawlTaskLog',
    'CrawlTaskStatusHistory',
]