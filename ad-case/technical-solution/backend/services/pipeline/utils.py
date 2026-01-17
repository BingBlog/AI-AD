#!/usr/bin/env python3
"""
工具函数
提供数据管道中使用的通用工具函数
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def save_json(data: Any, file_path: Path, indent: int = 2, ensure_ascii: bool = False) -> bool:
    """
    保存数据到JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: JSON缩进
        ensure_ascii: 是否确保ASCII编码
        
    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        
        logger.info(f"JSON文件已保存: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"保存JSON文件失败 {file_path}: {e}")
        return False


def load_json(file_path: Path) -> Optional[Any]:
    """
    从JSON文件加载数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的数据，失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON文件已加载: {file_path}")
        return data
        
    except FileNotFoundError:
        logger.warning(f"JSON文件不存在: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败 {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"加载JSON文件失败 {file_path}: {e}")
        return None


def save_resume_file(resume_file: Path, crawled_ids: Set[int]) -> bool:
    """
    保存断点续传文件
    
    Args:
        resume_file: 断点续传文件路径
        crawled_ids: 已爬取的case_id集合
        
    Returns:
        是否保存成功
    """
    try:
        resume_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'crawled_ids': sorted(list(crawled_ids)),
            'total_count': len(crawled_ids),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(resume_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"断点续传文件已更新: {resume_file}, 已爬取 {len(crawled_ids)} 个案例")
        return True
        
    except Exception as e:
        logger.error(f"保存断点续传文件失败 {resume_file}: {e}")
        return False


def load_resume_file(resume_file: Path) -> Set[int]:
    """
    加载断点续传文件
    
    Args:
        resume_file: 断点续传文件路径
        
    Returns:
        已爬取的case_id集合
    """
    if not resume_file.exists():
        logger.info(f"断点续传文件不存在，从头开始: {resume_file}")
        return set()
    
    try:
        data = load_json(resume_file)
        if data and 'crawled_ids' in data:
            crawled_ids = set(data['crawled_ids'])
            logger.info(f"加载断点续传文件: {resume_file}, 已爬取 {len(crawled_ids)} 个案例")
            return crawled_ids
        else:
            logger.warning(f"断点续传文件格式错误: {resume_file}")
            return set()
            
    except Exception as e:
        logger.error(f"加载断点续传文件失败 {resume_file}: {e}")
        return set()


def get_saved_case_ids_from_json(output_dir) -> Set[int]:
    """
    从JSON文件中获取已保存的case_id集合
    
    Args:
        output_dir: JSON文件输出目录（可以是Path对象或字符串）
        
    Returns:
        已保存的case_id集合
    """
    saved_ids = set()
    output_dir = Path(output_dir)
    
    # 查找所有批次文件
    batch_files = sorted(output_dir.glob('cases_batch_*.json'))
    
    for batch_file in batch_files:
        try:
            data = load_json(batch_file)
            if data and 'cases' in data:
                for case in data['cases']:
                    case_id = case.get('case_id')
                    if case_id:
                        saved_ids.add(case_id)
        except Exception as e:
            logger.error(f"读取批次文件失败 {batch_file}: {e}")
    
    logger.info(f"从JSON文件加载已保存的case_id: {len(saved_ids)} 个")
    return saved_ids


def validate_crawled_ids_saved(crawled_ids: Set[int], saved_ids: Set[int]) -> Dict[str, Any]:
    """
    验证已爬取的ID是否都被保存
    
    Args:
        crawled_ids: 已爬取的case_id集合
        saved_ids: 已保存的case_id集合
        
    Returns:
        验证结果字典，包含：
        - missing_ids: 未保存的ID列表
        - missing_count: 未保存的数量
        - all_saved: 是否全部保存
    """
    missing_ids = sorted(list(crawled_ids - saved_ids))
    missing_count = len(missing_ids)
    all_saved = missing_count == 0
    
    return {
        'missing_ids': missing_ids,
        'missing_count': missing_count,
        'all_saved': all_saved,
        'crawled_count': len(crawled_ids),
        'saved_count': len(saved_ids)
    }


def get_existing_case_ids(db_connection) -> Set[int]:
    """
    从数据库获取已存在的case_id集合
    
    Args:
        db_connection: 数据库连接对象
        
    Returns:
        已存在的case_id集合
    """
    try:
        cursor = db_connection.cursor()
        cursor.execute("SELECT case_id FROM ad_cases")
        existing_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        
        logger.info(f"从数据库加载已存在的case_id: {len(existing_ids)} 个")
        return existing_ids
        
    except Exception as e:
        logger.error(f"获取已存在的case_id失败: {e}")
        return set()


def format_batch_filename(batch_num: int, prefix: str = 'cases_batch') -> str:
    """
    格式化批次文件名
    
    Args:
        batch_num: 批次号
        prefix: 文件名前缀
        
    Returns:
        文件名
    """
    return f"{prefix}_{batch_num:04d}.json"


def get_next_batch_number(output_dir: Path, prefix: str = 'cases_batch') -> int:
    """
    获取下一个批次号
    
    Args:
        output_dir: 输出目录
        prefix: 文件名前缀
        
    Returns:
        下一个批次号
    """
    if not output_dir.exists():
        return 0
    
    # 查找所有批次文件
    batch_files = list(output_dir.glob(f"{prefix}_*.json"))
    
    if not batch_files:
        return 0
    
    # 提取批次号
    batch_numbers = []
    for file in batch_files:
        try:
            # 从文件名中提取批次号
            # 格式: cases_batch_0001.json
            name = file.stem  # cases_batch_0001
            num_str = name.split('_')[-1]  # 0001
            batch_numbers.append(int(num_str))
        except (ValueError, IndexError):
            continue
    
    if not batch_numbers:
        return 0
    
    return max(batch_numbers) + 1


def merge_case_data(list_item: Dict[str, Any], detail_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并列表页数据和详情页数据
    
    Args:
        list_item: 列表页数据
        detail_data: 详情页数据
        
    Returns:
        合并后的数据
    """
    merged = {
        # 列表页数据（优先级高）
        'case_id': list_item.get('id') or detail_data.get('case_id'),
        'score': list_item.get('score') or detail_data.get('score'),
        'score_decimal': list_item.get('score_decimal') or detail_data.get('score_decimal'),
        'favourite': list_item.get('favourite') or detail_data.get('favourite', 0),
        'company_name': list_item.get('company_name') or detail_data.get('company_name'),
        'company_logo': list_item.get('company_logo') or detail_data.get('company_logo'),
        'thumb': list_item.get('thumb') or detail_data.get('thumb'),
        
        # 详情页数据
        'source_url': detail_data.get('source_url'),
        'title': detail_data.get('title'),
        'description': detail_data.get('description'),
        'main_image': detail_data.get('main_image'),
        'images': detail_data.get('images', []),
        'video_url': detail_data.get('video_url'),
        'author': detail_data.get('author'),
        'publish_time': detail_data.get('publish_time'),
        'brand_name': detail_data.get('brand_name'),
        'brand_industry': detail_data.get('brand_industry'),
        'activity_type': detail_data.get('activity_type'),
        'location': detail_data.get('location'),
        'tags': detail_data.get('tags', []),
        'agency_name': detail_data.get('agency_name'),
    }
    
    # 移除None值
    merged = {k: v for k, v in merged.items() if v is not None}
    
    return merged

