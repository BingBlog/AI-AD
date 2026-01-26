#!/usr/bin/env python3
"""
从数据库直接生成向量
为数据库中已有的案例生成向量并更新
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

import psycopg2
from psycopg2.extras import execute_batch
from FlagEmbedding import FlagModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_vectors_from_db(
    db_config: dict,
    batch_size: int = 32,
    model_name: str = 'BAAI/bge-large-zh-v1.5'
):
    """
    从数据库读取案例，生成向量并更新
    
    Args:
        db_config: 数据库配置
        batch_size: 批次大小
        model_name: 模型名称
    """
    # 初始化模型
    logger.info(f"加载嵌入模型: {model_name}")
    model = FlagModel(
        model_name,
        query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
    )
    logger.info("嵌入模型加载完成")
    
    # 连接数据库
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    try:
        # 查询所有需要生成向量的案例
        logger.info("查询需要生成向量的案例...")
        cur.execute("""
            SELECT id, case_id, title, description
            FROM ad_cases
            WHERE combined_vector IS NULL
            AND (title IS NOT NULL OR description IS NOT NULL)
            ORDER BY id
        """)
        
        cases = cur.fetchall()
        total = len(cases)
        logger.info(f"找到 {total} 个需要生成向量的案例")
        
        if total == 0:
            logger.info("所有案例都已生成向量")
            return
        
        # 批量处理
        processed = 0
        failed = 0
        
        for i in range(0, total, batch_size):
            batch = cases[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"处理批次 [{batch_num}/{total_batches}]: {len(batch)} 个案例")
            
            # 准备文本和ID
            texts = []
            case_ids = []
            for case in batch:
                case_id, _, title, description = case
                title = (title or '').strip()
                description = (description or '').strip()
                combined = f"{title} {description}".strip()
                
                if combined:
                    texts.append(combined)
                    case_ids.append(case_id)
                else:
                    logger.warning(f"案例 {case_id} 没有文本内容，跳过")
            
            if not texts:
                logger.warning(f"批次 {batch_num} 没有有效文本，跳过")
                continue
            
            try:
                # 批量编码（FlagEmbedding 不支持 normalize 参数，需要手动归一化）
                vectors = model.encode(texts, batch_size=len(texts))
                
                # 手动归一化向量
                vectors_norm = []
                for vector in vectors:
                    vector_norm = vector / np.linalg.norm(vector)
                    vectors_norm.append(vector_norm)
                
                # 准备更新数据
                update_data = []
                for j, case_id in enumerate(case_ids):
                    vector_list = vectors_norm[j].tolist()
                    update_data.append((vector_list, case_id))
                
                # 批量更新
                update_sql = """
                    UPDATE ad_cases
                    SET combined_vector = %s::vector(1024)
                    WHERE id = %s
                """
                
                execute_batch(cur, update_sql, update_data, page_size=len(update_data))
                conn.commit()
                
                processed += len(update_data)
                logger.info(f"成功更新 {len(update_data)} 个案例的向量")
                
            except Exception as e:
                logger.error(f"批次 {batch_num} 处理失败: {e}")
                conn.rollback()
                failed += len(batch)
                continue
            
            # 显示进度
            progress = (processed / total) * 100
            logger.info(f"进度: {processed}/{total} ({progress:.1f}%)")
        
        logger.info("=" * 60)
        logger.info(f"向量生成完成！")
        logger.info(f"成功: {processed}, 失败: {failed}, 总计: {total}")
        logger.info("=" * 60)
        
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='从数据库生成向量')
    parser.add_argument('--db-name', default='ad_case_db', help='数据库名称')
    parser.add_argument('--db-user', default='bing', help='数据库用户')
    parser.add_argument('--db-password', default='', help='数据库密码')
    parser.add_argument('--db-host', default='localhost', help='数据库主机')
    parser.add_argument('--db-port', type=int, default=5432, help='数据库端口')
    parser.add_argument('--batch-size', type=int, default=32, help='批次大小（默认: 32）')
    parser.add_argument('--model-name', default='BAAI/bge-large-zh-v1.5', help='模型名称')
    
    args = parser.parse_args()
    
    # 配置数据库连接
    db_config = {
        'dbname': args.db_name,
        'user': args.db_user,
        'password': args.db_password,
        'host': args.db_host,
        'port': args.db_port
    }
    
    try:
        generate_vectors_from_db(
            db_config=db_config,
            batch_size=args.batch_size,
            model_name=args.model_name
        )
    except Exception as e:
        logger.error(f"向量生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
