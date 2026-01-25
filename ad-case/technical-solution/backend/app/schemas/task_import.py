"""
任务导入相关的 Schema 定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ImportConfig(BaseModel):
    """导入配置"""
    import_mode: str = Field(default="full", description="导入模式：full（完整导入）或 selective（选择批次导入）")
    selected_batches: Optional[List[str]] = Field(default=None, description="选择的批次文件列表（仅当 import_mode='selective' 时使用）")
    skip_existing: bool = Field(default=True, description="是否跳过已存在的案例")
    update_existing: bool = Field(default=False, description="是否更新已存在的案例")
    generate_vectors: bool = Field(default=True, description="是否生成向量")
    skip_invalid: bool = Field(default=True, description="是否跳过无效数据")
    batch_size: int = Field(default=50, ge=1, description="批量导入大小")


class ImportStartRequest(BaseModel):
    """启动导入请求"""
    import_mode: str = Field(default="full", description="导入模式")
    selected_batches: Optional[List[str]] = Field(default=None, description="选择的批次文件列表")
    import_failed_only: bool = Field(default=False, description="仅导入未导入成功的案例（默认 False）")
    skip_existing: bool = Field(default=False, description="是否跳过已存在的案例（默认 False，显示所有错误）")
    update_existing: bool = Field(default=False, description="是否更新已存在的案例")
    generate_vectors: bool = Field(default=True, description="是否生成向量")
    skip_invalid: bool = Field(default=False, description="是否跳过无效数据（默认 False，显示所有错误）")
    batch_size: int = Field(default=50, ge=1, description="批量导入大小")
    normalize_data: bool = Field(default=True, description="是否规范化数据（将非法值转为默认值或NULL，默认 True）")


class ImportProgress(BaseModel):
    """导入进度信息"""
    total_cases: int = Field(default=0, description="总案例数")
    loaded_cases: int = Field(default=0, description="已加载案例数")
    valid_cases: int = Field(default=0, description="有效案例数")
    invalid_cases: int = Field(default=0, description="无效案例数")
    existing_cases: int = Field(default=0, description="已存在案例数")
    imported_cases: int = Field(default=0, description="已导入案例数")
    failed_cases: int = Field(default=0, description="失败案例数")
    current_file: Optional[str] = Field(default=None, description="当前处理的文件")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="完成百分比")
    estimated_remaining_time: Optional[int] = Field(default=None, description="预计剩余时间（秒）")


class ImportStats(BaseModel):
    """导入统计信息"""
    total_loaded: int = Field(default=0, description="总加载数")
    total_valid: int = Field(default=0, description="总有效数")
    total_invalid: int = Field(default=0, description="总无效数")
    total_existing: int = Field(default=0, description="总已存在数")
    total_imported: int = Field(default=0, description="总导入数")
    total_failed: int = Field(default=0, description="总失败数")


class ImportStatusResponse(BaseModel):
    """导入状态响应"""
    import_id: str = Field(..., description="导入ID")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="导入状态")
    progress: ImportProgress = Field(..., description="进度信息")
    stats: ImportStats = Field(..., description="统计信息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class ImportResult(BaseModel):
    """导入结果"""
    total_loaded: int = Field(default=0, description="总加载数")
    total_valid: int = Field(default=0, description="总有效数")
    total_invalid: int = Field(default=0, description="总无效数")
    total_existing: int = Field(default=0, description="总已存在数")
    total_imported: int = Field(default=0, description="总导入数")
    total_failed: int = Field(default=0, description="总失败数")
    duration_seconds: Optional[int] = Field(default=None, description="耗时（秒）")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class ImportError(BaseModel):
    """导入错误信息"""
    file: Optional[str] = Field(default=None, description="文件名")
    case_id: Optional[int] = Field(default=None, description="案例ID")
    error: str = Field(..., description="错误信息")


class ImportResultResponse(BaseModel):
    """导入结果响应"""
    import_id: str = Field(..., description="导入ID")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="导入状态")
    result: ImportResult = Field(..., description="导入结果")
    errors: List[ImportError] = Field(default_factory=list, description="错误列表")


class ImportHistoryItem(BaseModel):
    """导入历史项"""
    import_id: str = Field(..., description="导入ID")
    status: str = Field(..., description="导入状态")
    total_imported: int = Field(default=0, description="导入案例数")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class ImportHistoryResponse(BaseModel):
    """导入历史响应"""
    imports: List[ImportHistoryItem] = Field(default_factory=list, description="导入历史列表")
    total: int = Field(default=0, description="总数")
