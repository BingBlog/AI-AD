"""
任务导入数据模型

定义任务导入相关表的数据结构，用于类型提示和文档说明。
注意：本项目使用 asyncpg 直接操作数据库，不使用 ORM。
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class TaskImport:
    """
    任务导入数据模型

    对应数据库表: task_imports

    状态枚举:
    - pending: 等待中
    - running: 运行中
    - completed: 已完成
    - failed: 已失败
    - cancelled: 已取消
    """
    # 主键和标识
    id: Optional[int] = None
    import_id: Optional[str] = None
    task_id: Optional[str] = None

    # 导入配置
    import_mode: str = "full"
    selected_batches: Optional[List[str]] = None
    skip_existing: bool = True
    update_existing: bool = False
    generate_vectors: bool = True
    skip_invalid: bool = True
    batch_size: int = 50

    # 导入状态
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # 进度信息
    total_cases: int = 0
    loaded_cases: int = 0
    valid_cases: int = 0
    invalid_cases: int = 0
    existing_cases: int = 0
    imported_cases: int = 0
    failed_cases: int = 0
    current_file: Optional[str] = None

    # 结果信息
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskImport':
        """从字典创建 TaskImport 实例"""
        # 处理 JSONB 字段
        selected_batches = data.get('selected_batches')
        if isinstance(selected_batches, str):
            selected_batches = json.loads(selected_batches) if selected_batches else None
        elif selected_batches is None:
            selected_batches = None

        return cls(
            id=data.get('id'),
            import_id=data.get('import_id'),
            task_id=data.get('task_id'),
            import_mode=data.get('import_mode', 'full'),
            selected_batches=selected_batches,
            skip_existing=data.get('skip_existing', True),
            update_existing=data.get('update_existing', False),
            generate_vectors=data.get('generate_vectors', True),
            skip_invalid=data.get('skip_invalid', True),
            batch_size=data.get('batch_size', 50),
            status=data.get('status', 'pending'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            cancelled_at=data.get('cancelled_at'),
            total_cases=data.get('total_cases', 0),
            loaded_cases=data.get('loaded_cases', 0),
            valid_cases=data.get('valid_cases', 0),
            invalid_cases=data.get('invalid_cases', 0),
            existing_cases=data.get('existing_cases', 0),
            imported_cases=data.get('imported_cases', 0),
            failed_cases=data.get('failed_cases', 0),
            current_file=data.get('current_file'),
            duration_seconds=data.get('duration_seconds'),
            error_message=data.get('error_message'),
            error_stack=data.get('error_stack'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

    def to_dict(self, exclude_none: bool = False) -> dict:
        """转换为字典"""
        data = {
            'id': self.id,
            'import_id': self.import_id,
            'task_id': self.task_id,
            'import_mode': self.import_mode,
            'selected_batches': json.dumps(self.selected_batches) if self.selected_batches else None,
            'skip_existing': self.skip_existing,
            'update_existing': self.update_existing,
            'generate_vectors': self.generate_vectors,
            'skip_invalid': self.skip_invalid,
            'batch_size': self.batch_size,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'cancelled_at': self.cancelled_at,
            'total_cases': self.total_cases,
            'loaded_cases': self.loaded_cases,
            'valid_cases': self.valid_cases,
            'invalid_cases': self.invalid_cases,
            'existing_cases': self.existing_cases,
            'imported_cases': self.imported_cases,
            'failed_cases': self.failed_cases,
            'current_file': self.current_file,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
            'error_stack': self.error_stack,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}

        return data


@dataclass
class TaskImportError:
    """
    任务导入错误数据模型

    对应数据库表: task_import_errors
    """
    id: Optional[int] = None
    import_id: Optional[str] = None
    file_name: Optional[str] = None
    case_id: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskImportError':
        """从字典创建 TaskImportError 实例"""
        # 处理 JSONB 字段
        error_details = data.get('error_details')
        if isinstance(error_details, str):
            error_details = json.loads(error_details) if error_details else None
        elif error_details is None:
            error_details = None

        return cls(
            id=data.get('id'),
            import_id=data.get('import_id'),
            file_name=data.get('file_name'),
            case_id=data.get('case_id'),
            error_type=data.get('error_type'),
            error_message=data.get('error_message'),
            error_details=error_details,
            created_at=data.get('created_at'),
        )

    def to_dict(self, exclude_none: bool = False) -> dict:
        """转换为字典"""
        data = {
            'id': self.id,
            'import_id': self.import_id,
            'file_name': self.file_name,
            'case_id': self.case_id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_details': json.dumps(self.error_details) if self.error_details else None,
            'created_at': self.created_at,
        }

        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}

        return data
