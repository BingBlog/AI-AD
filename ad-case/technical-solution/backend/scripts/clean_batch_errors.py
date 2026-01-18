#!/usr/bin/env python3
"""
清理批次文件中的错误数据
移除不属于本任务的错误案例
"""
import json
import sys
from pathlib import Path
from typing import Set, Dict, Any, List

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from services.pipeline.utils import load_json, save_json


def clean_batch_file(batch_file: Path, crawled_ids: Set[int], dry_run: bool = True, remove_all_errors: bool = False) -> Dict[str, Any]:
    """
    清理批次文件中的错误数据
    
    Args:
        batch_file: 批次文件路径
        crawled_ids: 属于本任务的已爬取ID集合
        dry_run: 是否只是预览，不实际修改文件
        
    Returns:
        清理结果统计
    """
    data = load_json(batch_file)
    if not data or 'cases' not in data:
        return {
            'file': str(batch_file),
            'error': 'Invalid batch file format'
        }
    
    original_cases = data['cases']
    cleaned_cases = []
    removed_count = 0
    error_count = 0
    
    for case in original_cases:
        case_id = case.get('case_id')
        
        # 检查是否是错误案例
        has_error = 'error' in case or 'validation_error' in case
        
        # 检查是否属于本任务
        belongs_to_task = case_id in crawled_ids if case_id else False
        
        # 保留条件：有效案例 OR 属于本任务的错误案例（用于重试，除非指定移除所有错误）
        if not has_error:
            # 有效案例，保留
            cleaned_cases.append(case)
        elif belongs_to_task and not remove_all_errors:
            # 属于本任务的错误案例，保留（可以重试）
            cleaned_cases.append(case)
            error_count += 1
        else:
            # 不属于本任务的错误案例，或指定移除所有错误时，移除
            removed_count += 1
    
    result = {
        'file': str(batch_file),
        'original_count': len(original_cases),
        'cleaned_count': len(cleaned_cases),
        'removed_count': removed_count,
        'error_count': error_count,
        'valid_count': len(cleaned_cases) - error_count
    }
    
    if not dry_run and removed_count > 0:
        # 更新批次文件
        data['cases'] = cleaned_cases
        data['batch_size'] = len(cleaned_cases)
        save_json(data, batch_file)
        result['saved'] = True
    else:
        result['saved'] = False
    
    return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理批次文件中的错误数据')
    parser.add_argument('task_id', help='任务ID')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--batch-file', help='只清理指定的批次文件')
    parser.add_argument('--remove-all-errors', action='store_true', help='移除所有错误记录（包括属于本任务的）')
    
    args = parser.parse_args()
    
    task_id = args.task_id
    task_dir = Path('data/json') / task_id
    
    if not task_dir.exists():
        print(f"错误: 任务目录不存在: {task_dir}")
        return 1
    
    # 读取 resume 文件获取 crawled_ids
    resume_file = task_dir / 'crawl_resume.json'
    if not resume_file.exists():
        print(f"错误: Resume文件不存在: {resume_file}")
        return 1
    
    resume_data = load_json(resume_file)
    crawled_ids = set(resume_data.get('crawled_ids', []))
    
    print("=" * 60)
    print(f"清理批次文件中的错误数据")
    print("=" * 60)
    print(f"任务ID: {task_id}")
    print(f"已爬取ID数: {len(crawled_ids)}")
    print(f"模式: {'预览（不修改文件）' if args.dry_run else '实际清理'}")
    print()
    
    # 获取要清理的批次文件
    if args.batch_file:
        batch_files = [Path(args.batch_file)]
    else:
        batch_files = sorted(task_dir.glob('cases_batch_*.json'))
    
    if not batch_files:
        print("没有找到批次文件")
        return 0
    
    total_removed = 0
    total_original = 0
    total_cleaned = 0
    
    for batch_file in batch_files:
        result = clean_batch_file(batch_file, crawled_ids, dry_run=args.dry_run, remove_all_errors=args.remove_all_errors)
        
        if 'error' in result:
            print(f"✗ {batch_file.name}: {result['error']}")
            continue
        
        print(f"{batch_file.name}:")
        print(f"  原始案例数: {result['original_count']}")
        print(f"  清理后案例数: {result['cleaned_count']} (有效: {result['valid_count']}, 错误: {result['error_count']})")
        print(f"  移除案例数: {result['removed_count']}")
        if result['saved']:
            print(f"  ✓ 文件已更新")
        print()
        
        total_original += result['original_count']
        total_cleaned += result['cleaned_count']
        total_removed += result['removed_count']
    
    print("=" * 60)
    print("总计:")
    print(f"  原始案例数: {total_original}")
    print(f"  清理后案例数: {total_cleaned}")
    print(f"  移除案例数: {total_removed}")
    
    if args.dry_run:
        print("\n提示: 使用 --no-dry-run 参数实际执行清理")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
