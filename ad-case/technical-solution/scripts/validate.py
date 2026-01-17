#!/usr/bin/env python3
"""
数据验证脚本
验证JSON文件中的数据质量
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pipeline.validator import CaseValidator
from services.pipeline.utils import load_json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='验证JSON文件中的数据质量')
    
    parser.add_argument(
        '--json-file',
        type=str,
        default=None,
        help='JSON文件路径（如果指定，只验证该文件）'
    )
    
    parser.add_argument(
        '--json-dir',
        type=str,
        default='data/json',
        help='JSON文件目录（如果指定--json-file则忽略，默认: data/json）'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='cases_batch_*.json',
        help='文件匹配模式（默认: cases_batch_*.json）'
    )
    
    args = parser.parse_args()
    
    validator = CaseValidator()
    
    # 执行验证
    try:
        if args.json_file:
            # 验证单个文件
            json_file = Path(args.json_file)
            if not json_file.exists():
                logger.error(f"JSON文件不存在: {json_file}")
                return 1
            
            validate_file(json_file, validator)
        else:
            # 验证目录中的所有文件
            json_dir = Path(args.json_dir)
            if not json_dir.exists():
                logger.error(f"JSON目录不存在: {json_dir}")
                return 1
            
            json_files = sorted(json_dir.glob(args.pattern))
            
            if not json_files:
                logger.warning(f"目录中没有找到JSON文件: {json_dir}")
                return 1
            
            logger.info(f"找到 {len(json_files)} 个JSON文件")
            
            total_valid = 0
            total_invalid = 0
            total_cases = 0
            
            for i, json_file in enumerate(json_files, 1):
                logger.info(f"\n处理文件 [{i}/{len(json_files)}]: {json_file.name}")
                file_valid, file_invalid, file_total = validate_file(json_file, validator)
                
                total_valid += file_valid
                total_invalid += file_invalid
                total_cases += file_total
            
            print("\n" + "=" * 60)
            print("总体验证结果")
            print("=" * 60)
            print(f"总案例数: {total_cases}")
            print(f"有效案例: {total_valid}")
            print(f"无效案例: {total_invalid}")
            print(f"有效率: {total_valid / total_cases * 100:.2f}%" if total_cases > 0 else "N/A")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断验证")
        return 1
    except Exception as e:
        logger.error(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_file(json_file: Path, validator: CaseValidator) -> tuple:
    """
    验证单个JSON文件
    
    Returns:
        (valid_count, invalid_count, total_count)
    """
    data = load_json(json_file)
    if not data:
        logger.error(f"无法加载JSON文件: {json_file}")
        return 0, 0, 0
    
    cases = data.get('cases', [])
    if not cases:
        logger.warning(f"JSON文件中没有案例数据: {json_file}")
        return 0, 0, 0
    
    logger.info(f"验证 {len(cases)} 个案例...")
    
    valid_cases, invalid_cases = validator.validate_batch(cases)
    
    # 获取验证摘要
    summary = validator.get_validation_summary(valid_cases, invalid_cases)
    
    print(f"\n文件: {json_file.name}")
    print(f"  总案例数: {summary['total']}")
    print(f"  有效案例: {summary['valid']}")
    print(f"  无效案例: {summary['invalid']}")
    print(f"  有效率: {summary['valid_rate'] * 100:.2f}%")
    
    if invalid_cases:
        print(f"\n  错误类型统计:")
        for error_type, count in summary['error_types'].items():
            print(f"    - {error_type}: {count}")
    
    return len(valid_cases), len(invalid_cases), len(cases)


if __name__ == '__main__':
    sys.exit(main())

