"""
爬取任务相关的 Schema 定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CrawlTaskConfig(BaseModel):
    """任务配置"""
    start_page: int = Field(ge=0, description="起始页码")
    end_page: Optional[int] = Field(default=None, ge=0, description="结束页码")
    case_type: Optional[int] = Field(default=None, description="案例类型")
    search_value: Optional[str] = Field(default=None, description="搜索关键词")
    batch_size: int = Field(default=30, ge=1, description="批次大小")
    delay_min: float = Field(default=2.0, ge=0, description="最小延迟时间（秒）")
    delay_max: float = Field(default=5.0, ge=0, description="最大延迟时间（秒）")
    enable_resume: bool = Field(default=True, description="是否启用断点续传")


class CrawlTaskCreate(BaseModel):
    """创建任务请求"""
    name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    data_source: str = Field(default="adquan", description="数据源")
    description: Optional[str] = Field(default=None, description="任务描述")
    start_page: Optional[int] = Field(default=None, ge=0, description="起始页码，为空时自动设置为上一次爬取到的页数")
    end_page: int = Field(..., ge=0, description="结束页码（必填）")
    case_type: Optional[int] = Field(default=None, description="案例类型")
    search_value: Optional[str] = Field(default=None, description="搜索关键词")
    batch_size: int = Field(default=30, ge=1, description="批次大小")
    delay_min: float = Field(default=2.0, ge=0, description="最小延迟时间（秒）")
    delay_max: float = Field(default=5.0, ge=0, description="最大延迟时间（秒）")
    enable_resume: bool = Field(default=True, description="是否启用断点续传")
    execute_immediately: bool = Field(default=True, description="是否立即执行")


class CrawlTaskProgress(BaseModel):
    """任务进度信息"""
    total_pages: Optional[int] = Field(default=None, description="总页数")
    completed_pages: int = Field(default=0, description="已完成页数")
    current_page: Optional[int] = Field(default=None, description="当前页码")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="完成百分比")
    estimated_remaining_time: Optional[int] = Field(default=None, description="预计剩余时间（秒）")


class CrawlTaskStats(BaseModel):
    """任务统计信息"""
    total_crawled: int = Field(default=0, description="总爬取数")
    total_saved: int = Field(default=0, description="总保存数")
    total_failed: int = Field(default=0, description="总失败数")
    batches_saved: int = Field(default=0, description="已保存批次数")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="成功率")
    avg_speed: Optional[float] = Field(default=None, description="平均爬取速度（案例/分钟）")
    avg_delay: Optional[float] = Field(default=None, description="平均请求延迟（秒）")
    error_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="错误率")


class CrawlTaskTimeline(BaseModel):
    """任务时间线"""
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    paused_at: Optional[datetime] = Field(default=None, description="暂停时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class CrawlTaskBase(BaseModel):
    """任务基础信息"""
    task_id: str = Field(description="任务ID")
    name: str = Field(description="任务名称")
    data_source: str = Field(description="数据源")
    description: Optional[str] = Field(default=None, description="任务描述")
    status: str = Field(description="任务状态")
    config: CrawlTaskConfig = Field(description="任务配置")
    progress: CrawlTaskProgress = Field(description="进度信息")
    stats: CrawlTaskStats = Field(description="统计信息")
    timeline: CrawlTaskTimeline = Field(description="时间线")


class CrawlTaskListItem(BaseModel):
    """任务列表项"""
    task_id: str = Field(description="任务ID")
    name: str = Field(description="任务名称")
    data_source: str = Field(description="数据源")
    status: str = Field(description="任务状态")
    progress: CrawlTaskProgress = Field(description="进度信息")
    stats: CrawlTaskStats = Field(description="统计信息")
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class CrawlTaskDetail(CrawlTaskBase):
    """任务详情"""
    error_message: Optional[str] = Field(default=None, description="错误信息")
    error_stack: Optional[str] = Field(default=None, description="错误堆栈")


class CrawlTaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[CrawlTaskListItem] = Field(description="任务列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


class CrawlTaskLog(BaseModel):
    """任务日志"""
    id: int = Field(description="日志ID")
    level: str = Field(description="日志级别")
    message: str = Field(description="日志消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")
    created_at: datetime = Field(description="创建时间")


class CrawlTaskLogsResponse(BaseModel):
    """任务日志响应"""
    logs: List[CrawlTaskLog] = Field(description="日志列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


class CrawlTaskUpdate(BaseModel):
    """更新任务请求（仅限等待中或已暂停的任务）"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    start_page: Optional[int] = Field(default=None, ge=0, description="起始页码")
    end_page: Optional[int] = Field(default=None, ge=0, description="结束页码")
    case_type: Optional[int] = Field(default=None, description="案例类型")
    search_value: Optional[str] = Field(default=None, description="搜索关键词")
    batch_size: Optional[int] = Field(default=None, ge=1, description="批次大小")
    delay_min: Optional[float] = Field(default=None, ge=0, description="最小延迟时间（秒）")
    delay_max: Optional[float] = Field(default=None, ge=0, description="最大延迟时间（秒）")
    enable_resume: Optional[bool] = Field(default=None, description="是否启用断点续传")


class CrawlListPageRecord(BaseModel):
    """列表页爬取记录"""
    id: int = Field(description="记录ID")
    task_id: str = Field(description="任务ID")
    page_number: int = Field(description="页码")
    status: str = Field(description="状态")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    items_count: int = Field(default=0, description="获取到的案例数量")
    crawled_at: Optional[datetime] = Field(default=None, description="爬取时间")
    duration_seconds: Optional[float] = Field(default=None, description="爬取耗时（秒）")
    retry_count: int = Field(default=0, description="重试次数")
    last_retry_at: Optional[datetime] = Field(default=None, description="最后重试时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class CrawlListPageRecordsResponse(BaseModel):
    """列表页记录响应"""
    records: List[CrawlListPageRecord] = Field(description="记录列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


class CrawlCaseRecord(BaseModel):
    """案例爬取记录"""
    id: int = Field(description="记录ID")
    task_id: str = Field(description="任务ID")
    list_page_id: Optional[int] = Field(default=None, description="列表页记录ID")
    case_id: Optional[int] = Field(default=None, description="案例ID")
    case_url: Optional[str] = Field(default=None, description="案例URL")
    case_title: Optional[str] = Field(default=None, description="案例标题")
    status: str = Field(description="状态")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    error_stack: Optional[str] = Field(default=None, description="错误堆栈")
    crawled_at: Optional[datetime] = Field(default=None, description="爬取时间")
    duration_seconds: Optional[float] = Field(default=None, description="爬取耗时（秒）")
    has_detail_data: bool = Field(default=False, description="是否成功获取详情页数据")
    has_validation_error: bool = Field(default=False, description="是否有验证错误")
    validation_errors: Optional[Dict[str, Any]] = Field(default=None, description="验证错误详情")
    saved_to_json: bool = Field(default=False, description="是否已保存到JSON文件")
    batch_file_name: Optional[str] = Field(default=None, description="批次文件名")
    imported: bool = Field(default=False, description="已导入：是否已执行过导入动作")
    import_status: Optional[str] = Field(default=None, description="导入状态：success（成功）或 failed（失败）")
    verified: bool = Field(default=False, description="已验证：在案例库中可以匹配到对应的案例")
    retry_count: int = Field(default=0, description="重试次数")
    last_retry_at: Optional[datetime] = Field(default=None, description="最后重试时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class CrawlCaseRecordsResponse(BaseModel):
    """案例记录响应"""
    records: List[CrawlCaseRecord] = Field(description="记录列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
