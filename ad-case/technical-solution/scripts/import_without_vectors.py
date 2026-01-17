#!/usr/bin/env python3
"""
入库脚本（不生成向量版本）
从JSON文件读取数据，直接入库（不生成向量）
向量可以后续批量生成
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor, Json
from services.pipeline.utils import load_json
from services.pipeline.validator import CaseValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def import_without_vectors(json_file: Path, db_config: dict, skip_existing: bool = True):
    """
    导入数据但不生成向量
    
    Args:
        json_file: JSON文件路径
        db_config: 数据库配置
        skip_existing: 是否跳过已存在的案例
    """
    # 加载JSON文件
    data = load_json(json_file)
    if not data:
        logger.error(f"无法加载JSON文件: {json_file}")
        return
    
    cases = data.get('cases', [])
    if not cases:
        logger.warning(f"JSON文件中没有案例数据: {json_file}")
        return
    
    logger.info(f"JSON文件包含 {len(cases)} 个案例")
    
    # 验证数据
    validator = CaseValidator()
    valid_cases, invalid_cases = validator.validate_batch(cases)
    
    logger.info(f"有效案例: {len(valid_cases)}, 无效案例: {len(invalid_cases)}")
    
    # 过滤已存在的案例
    if skip_existing:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT case_id FROM ad_cases")
        existing_ids = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
        
        new_cases = [c for c in valid_cases if c.get('case_id') not in existing_ids]
        logger.info(f"已存在案例: {len(valid_cases) - len(new_cases)}, 新案例: {len(new_cases)}")
        cases_to_import = new_cases
    else:
        cases_to_import = valid_cases
    
    if not cases_to_import:
        logger.info("没有需要导入的案例")
        return
    
    # 批量入库
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    insert_sql = """
        INSERT INTO ad_cases (
            case_id, source_url, title, description, author, publish_time,
            main_image, images, video_url,
            brand_name, brand_industry, activity_type, location, tags,
            score, score_decimal, favourite,
            company_name, company_logo, agency_name
        ) VALUES (
            %(case_id)s, %(source_url)s, %(title)s, %(description)s, 
            %(author)s, %(publish_time)s,
            %(main_image)s, %(images)s::jsonb, %(video_url)s,
            %(brand_name)s, %(brand_industry)s, %(activity_type)s, 
            %(location)s, %(tags)s::jsonb,
            %(score)s, %(score_decimal)s, %(favourite)s,
            %(company_name)s, %(company_logo)s, %(agency_name)s
        )
        ON CONFLICT (case_id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP
    """
    
    # 准备数据
    insert_data = []
    for case in cases_to_import:
        # 将列表转换为 JSON 字符串（使用 Json 适配器）
        images = case.get('images', [])
        tags = case.get('tags', [])
        
        data = {
            'case_id': case.get('case_id'),
            'source_url': case.get('source_url'),
            'title': case.get('title'),
            'description': case.get('description'),
            'author': case.get('author'),
            'publish_time': case.get('publish_time'),
            'main_image': case.get('main_image'),
            'images': Json(images) if images else Json([]),  # 使用 Json 适配器
            'video_url': case.get('video_url'),
            'brand_name': case.get('brand_name'),
            'brand_industry': case.get('brand_industry'),
            'activity_type': case.get('activity_type'),
            'location': case.get('location'),
            'tags': Json(tags) if tags else Json([]),  # 使用 Json 适配器
            'score': case.get('score'),
            'score_decimal': case.get('score_decimal'),
            'favourite': case.get('favourite', 0),
            'company_name': case.get('company_name'),
            'company_logo': case.get('company_logo'),
            'agency_name': case.get('agency_name')
        }
        insert_data.append(data)
    
    # 批量执行
    try:
        execute_batch(cur, insert_sql, insert_data, page_size=50)
        conn.commit()
        logger.info(f"成功导入 {len(insert_data)} 个案例")
    except Exception as e:
        conn.rollback()
        logger.error(f"批量插入失败: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='从JSON文件导入数据到数据库（不生成向量）')
    
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
        default='',
        help='数据库密码（默认: 空）'
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='不跳过已存在的案例（默认: 跳过）'
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
    
    # 执行导入
    try:
        if args.json_file:
            # 导入单个文件
            json_file = Path(args.json_file)
            if not json_file.exists():
                logger.error(f"JSON文件不存在: {json_file}")
                return 1
            
            import_without_vectors(json_file, db_config, skip_existing=not args.no_skip_existing)
        else:
            # 导入目录中的所有文件
            json_dir = Path(args.json_dir)
            if not json_dir.exists():
                logger.error(f"JSON目录不存在: {json_dir}")
                return 1
            
            json_files = sorted(json_dir.glob(args.pattern))
            
            if not json_files:
                logger.warning(f"目录中没有找到JSON文件: {json_dir}")
                return 1
            
            logger.info(f"找到 {len(json_files)} 个JSON文件")
            
            total_imported = 0
            for i, json_file in enumerate(json_files, 1):
                logger.info(f"\n处理文件 [{i}/{len(json_files)}]: {json_file.name}")
                try:
                    import_without_vectors(json_file, db_config, skip_existing=not args.no_skip_existing)
                    total_imported += 1
                except Exception as e:
                    logger.error(f"导入文件失败 {json_file}: {e}")
                    continue
            
            logger.info(f"\n总共处理了 {total_imported} 个文件")
        
        print("\n" + "=" * 60)
        print("导入完成！")
        print("=" * 60)
        print("注意：本次导入未生成向量，向量可以后续批量生成")
        
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

