#!/usr/bin/env python3
"""
爬取脚本
执行爬取任务，将数据保存到JSON文件
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pipeline.crawl_stage import CrawlStage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='爬取广告门案例数据')
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/json',
        help='JSON文件输出目录（默认: data/json）'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='每批保存的案例数量（默认: 100）'
    )
    
    parser.add_argument(
        '--start-page',
        type=int,
        default=0,
        help='起始页码（默认: 0）'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='最大页数（默认: 100）'
    )
    
    parser.add_argument(
        '--case-type',
        type=int,
        default=3,
        help='案例类型：0=全部, 3=精选案例（默认: 3）'
    )
    
    parser.add_argument(
        '--search-value',
        type=str,
        default='',
        help='搜索关键词（默认: 空）'
    )
    
    parser.add_argument(
        '--resume-file',
        type=str,
        default=None,
        help='断点续传文件路径（默认: output_dir/crawl_resume.json）'
    )
    
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='禁用断点续传'
    )
    
    parser.add_argument(
        '--delay-min',
        type=float,
        default=2.0,
        help='最小延迟时间（秒，默认: 2.0）'
    )
    
    parser.add_argument(
        '--delay-max',
        type=float,
        default=5.0,
        help='最大延迟时间（秒，默认: 5.0）'
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 断点续传文件
    resume_file = None
    if args.resume_file:
        resume_file = Path(args.resume_file)
    elif not args.no_resume:
        resume_file = output_dir / 'crawl_resume.json'
    
    # 创建爬取阶段
    crawl_stage = CrawlStage(
        output_dir=output_dir,
        batch_size=args.batch_size,
        resume_file=resume_file,
        delay_range=(args.delay_min, args.delay_max),
        enable_resume=not args.no_resume
    )
    
    # 执行爬取
    try:
        stats = crawl_stage.crawl(
            start_page=args.start_page,
            max_pages=args.max_pages,
            case_type=args.case_type,
            search_value=args.search_value,
            skip_existing=not args.no_resume
        )
        
        print("\n" + "=" * 60)
        print("爬取完成！")
        print("=" * 60)
        print(f"总爬取数: {stats['total_crawled']}")
        print(f"总保存数: {stats['total_saved']}")
        print(f"总失败数: {stats['total_failed']}")
        print(f"保存批次数: {stats['batches_saved']}")
        print(f"总耗时: {stats.get('duration_seconds', 0):.2f} 秒")
        print(f"输出目录: {stats.get('output_dir', output_dir)}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断爬取")
        return 1
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

