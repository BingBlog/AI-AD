#!/usr/bin/env python3
"""
更新现有案例的向量字段
从 JSON 文件重新生成向量并更新到数据库
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.import_stage import ImportStage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='更新现有案例的向量字段')
    parser.add_argument('--db-name', default='ad_case_db', help='数据库名称')
    parser.add_argument('--db-user', default='bing', help='数据库用户')
    parser.add_argument('--db-password', default='', help='数据库密码')
    parser.add_argument('--db-host', default='localhost', help='数据库主机')
    parser.add_argument('--db-port', type=int, default=5432, help='数据库端口')
    parser.add_argument('--json-dir', default='data/json', help='JSON 文件目录')
    parser.add_argument('--batch-size', type=int, default=50, help='批次大小')
    
    args = parser.parse_args()
    
    # 配置数据库连接
    db_config = {
        'dbname': args.db_name,
        'user': args.db_user,
        'password': args.db_password,
        'host': args.db_host,
        'port': args.db_port
    }
    
    # 创建导入阶段实例
    import_stage = ImportStage(
        db_config=db_config,
        json_dir=args.json_dir,
        batch_size=args.batch_size
    )
    
    # 运行导入（会自动生成向量并更新）
    try:
        import_stage.run()
        logger.info("向量更新完成！")
    except Exception as e:
        logger.error(f"向量更新失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
