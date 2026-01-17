#!/usr/bin/env python3
"""
入库脚本
从JSON文件读取数据，生成向量，并批量入库
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pipeline.import_stage import ImportStage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='从JSON文件导入数据到数据库')
    
    parser.add_argument(
        '--json-file',
        type=str,
        default=None,
        help='JSON文件路径（如果指定，只导入该文件）'
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
    
    parser.add_argument(
        '--db-host',
        type=str,
        default='localhost',
        help='数据库主机（默认: localhost）'
    )
    
    parser.add_argument(
        '--db-port',
        type=int,
        default=5432,
        help='数据库端口（默认: 5432）'
    )
    
    parser.add_argument(
        '--db-name',
        type=str,
        required=True,
        help='数据库名称（必需）'
    )
    
    parser.add_argument(
        '--db-user',
        type=str,
        required=True,
        help='数据库用户（必需）'
    )
    
    parser.add_argument(
        '--db-password',
        type=str,
        required=True,
        help='数据库密码（必需）'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='批量入库大小（默认: 50）'
    )
    
    parser.add_argument(
        '--model-name',
        type=str,
        default='BAAI/bge-large-zh-v1.5',
        help='嵌入模型名称（默认: BAAI/bge-large-zh-v1.5）'
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='不跳过已存在的案例（默认: 跳过）'
    )
    
    parser.add_argument(
        '--no-skip-invalid',
        action='store_true',
        help='不跳过无效的案例（默认: 跳过）'
    )
    
    args = parser.parse_args()
    
    # 数据库配置
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    # 创建入库阶段
    import_stage = ImportStage(
        db_config=db_config,
        model_name=args.model_name,
        batch_size=args.batch_size,
        skip_existing=not args.no_skip_existing,
        skip_invalid=not args.no_skip_invalid
    )
    
    # 执行导入
    try:
        if args.json_file:
            # 导入单个文件
            json_file = Path(args.json_file)
            if not json_file.exists():
                logger.error(f"JSON文件不存在: {json_file}")
                return 1
            
            stats = import_stage.import_from_json(json_file)
        else:
            # 导入目录中的所有文件
            json_dir = Path(args.json_dir)
            if not json_dir.exists():
                logger.error(f"JSON目录不存在: {json_dir}")
                return 1
            
            stats = import_stage.import_from_directory(json_dir, args.pattern)
        
        print("\n" + "=" * 60)
        print("导入完成！")
        print("=" * 60)
        print(f"总加载数: {stats['total_loaded']}")
        print(f"有效数: {stats['total_valid']}")
        print(f"无效数: {stats['total_invalid']}")
        print(f"已存在数: {stats['total_existing']}")
        print(f"成功导入数: {stats['total_imported']}")
        print(f"失败数: {stats['total_failed']}")
        print(f"总耗时: {stats.get('duration_seconds', 0):.2f} 秒")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断导入")
        return 1
    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

