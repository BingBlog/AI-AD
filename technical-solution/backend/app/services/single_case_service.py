#!/usr/bin/env python3
"""
单个案例服务
用于单个案例的验证和导入
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json

from services.pipeline.utils import load_json
from services.pipeline.validator import CaseValidator
from services.pipeline.import_stage import ImportStage
from app.repositories.crawl_case_record_repository import CrawlCaseRecordRepository
from app.config import settings

logger = logging.getLogger(__name__)


class SingleCaseService:
    """单个案例服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.validator = CaseValidator()
    
    async def get_case_data_from_json(
        self, 
        task_id: str, 
        case_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        从JSON文件中获取单个案例的数据
        
        Args:
            task_id: 任务ID
            case_id: 案例ID
            
        Returns:
            案例数据字典，如果不存在则返回None
        """
        # 获取案例记录
        record = await CrawlCaseRecordRepository.get_case_by_task_and_case_id(
            task_id=task_id,
            case_id=case_id
        )
        
        if not record:
            return None
        
        batch_file_name = record.get('batch_file_name')
        if not batch_file_name:
            return None
        
        # 构建JSON文件路径（相对于backend目录）
        # 与其他服务保持一致：使用 "data/json" 相对路径
        backend_root = Path(__file__).parent.parent.parent
        json_dir = backend_root / "data" / "json" / task_id
        json_file = json_dir / batch_file_name
        
        if not json_file.exists():
            logger.error(f"JSON文件不存在: {json_file}")
            return None
        
        # 加载JSON文件
        data = load_json(json_file)
        if not data or 'cases' not in data:
            return None
        
        # 查找对应的案例
        for case in data.get('cases', []):
            if case.get('case_id') == case_id:
                return case
        
        return None
    
    async def validate_single_case(
        self,
        task_id: str,
        case_id: int,
        normalize_data: bool = True
    ) -> Dict[str, Any]:
        """
        验证单个案例数据
        
        Args:
            task_id: 任务ID
            case_id: 案例ID
            normalize_data: 是否规范化数据
            
        Returns:
            验证结果：{
                'is_valid': bool,
                'error_message': Optional[str],
                'formatted_case': Optional[Dict],
                'validation_errors': Optional[Dict]
            }
        """
        # 获取案例数据
        case_data = await self.get_case_data_from_json(task_id, case_id)
        if not case_data:
            return {
                'is_valid': False,
                'error_message': '无法从JSON文件中找到案例数据',
                'formatted_case': None,
                'validation_errors': {
                    'error': '无法从JSON文件中找到案例数据'
                }
            }
        
        # 格式化数据
        if normalize_data:
            formatted_case = self.validator.format_case(case_data, normalize=True)
        else:
            formatted_case = case_data.copy()
        
        # 验证数据
        is_valid, error_message = self.validator.validate_case(formatted_case)
        
        result = {
            'is_valid': is_valid,
            'error_message': error_message,
            'formatted_case': formatted_case if is_valid else None,
            'validation_errors': None
        }
        
        if not is_valid:
            result['validation_errors'] = {
                'validation_error': error_message,
                'error': error_message
            }
        
        return result
    
    async def import_single_case(
        self,
        task_id: str,
        case_id: int,
        normalize_data: bool = True,
        generate_vectors: bool = True
    ) -> Dict[str, Any]:
        """
        导入单个案例到数据库
        
        Args:
            task_id: 任务ID
            case_id: 案例ID
            normalize_data: 是否规范化数据
            generate_vectors: 是否生成向量
            
        Returns:
            导入结果：{
                'success': bool,
                'error_message': Optional[str],
                'imported_case_id': Optional[int]
            }
        """
        # 验证案例数据
        validation_result = await self.validate_single_case(
            task_id=task_id,
            case_id=case_id,
            normalize_data=normalize_data
        )
        
        if not validation_result['is_valid']:
            # 更新验证失败状态
            record = await CrawlCaseRecordRepository.get_case_by_task_and_case_id(
                task_id=task_id,
                case_id=case_id
            )
            if record:
                await CrawlCaseRecordRepository.batch_update_validation_status_by_case_ids(
                    task_id=task_id,
                    case_validation_map={
                        case_id: {
                            'has_validation_error': True,
                            'validation_errors': validation_result['validation_errors'],
                            'status': 'validation_failed'
                        }
                    }
                )
            
            return {
                'success': False,
                'error_message': validation_result['error_message'],
                'imported_case_id': None
            }
        
        formatted_case = validation_result['formatted_case']
        if not formatted_case:
            return {
                'success': False,
                'error_message': '格式化后的案例数据为空',
                'imported_case_id': None
            }
        
        # 创建导入阶段实例
        db_config = {
            'host': settings.DB_HOST,
            'database': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'port': settings.DB_PORT
        }
        
        import_stage = ImportStage(
            db_config=db_config,
            batch_size=1,
            skip_existing=False,
            skip_invalid=False,
            normalize_data=normalize_data
        )
        
        # 生成向量（如果需要）
        if generate_vectors:
            try:
                cases_with_vectors = import_stage._generate_vectors_batch([formatted_case])
                if cases_with_vectors:
                    formatted_case = cases_with_vectors[0]
            except Exception as e:
                logger.error(f"生成向量失败: {e}")
                return {
                    'success': False,
                    'error_message': f'生成向量失败: {str(e)}',
                    'imported_case_id': None
                }
        
        # 导入到数据库
        try:
            imported_case_ids, failed_cases = import_stage._batch_import([formatted_case])
            
            if failed_cases:
                error_message = failed_cases.get(case_id, '导入失败')
                return {
                    'success': False,
                    'error_message': error_message,
                    'imported_case_id': None
                }
            
            if imported_case_ids and case_id in imported_case_ids:
                # 更新导入状态
                await CrawlCaseRecordRepository.batch_update_import_status_by_case_ids(
                    task_id=task_id,
                    case_ids=[case_id],
                    imported=True,
                    import_status='success'
                )
                
                # 验证导入
                await CrawlCaseRecordRepository.batch_verify_cases_by_case_ids(
                    task_id=task_id,
                    case_ids=[case_id],
                    verified=True
                )
                
                return {
                    'success': True,
                    'error_message': None,
                    'imported_case_id': case_id
                }
            else:
                return {
                    'success': False,
                    'error_message': '导入失败：案例ID不在导入成功的列表中',
                    'imported_case_id': None
                }
        except Exception as e:
            logger.error(f"导入案例失败: {e}", exc_info=True)
            return {
                'success': False,
                'error_message': f'导入失败: {str(e)}',
                'imported_case_id': None
            }
