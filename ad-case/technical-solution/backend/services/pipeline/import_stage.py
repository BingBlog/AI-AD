#!/usr/bin/env python3
"""
入库阶段
负责从JSON文件读取数据，生成向量，并批量入库
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
from FlagEmbedding import FlagModel
import numpy as np

from .utils import load_json, get_existing_case_ids
from .validator import CaseValidator

logger = logging.getLogger(__name__)


class ImportStage:
    """入库阶段类"""
    
    def __init__(
        self,
        db_config: Dict[str, Any],
        model_name: str = 'BAAI/bge-large-zh-v1.5',
        batch_size: int = 50,
        skip_existing: bool = True,
        skip_invalid: bool = True
    ):
        """
        初始化入库阶段
        
        Args:
            db_config: 数据库配置字典
                {
                    'host': 'localhost',
                    'database': 'ad_case_db',
                    'user': 'postgres',
                    'password': 'password',
                    'port': 5432
                }
            model_name: 嵌入模型名称
            batch_size: 批量入库大小
            skip_existing: 是否跳过已存在的案例
            skip_invalid: 是否跳过无效的案例
        """
        self.db_config = db_config
        self.batch_size = batch_size
        self.skip_existing = skip_existing
        self.skip_invalid = skip_invalid
        
        # 初始化嵌入模型
        logger.info(f"加载嵌入模型: {model_name}")
        self.model = FlagModel(
            model_name,
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
        )
        logger.info("嵌入模型加载完成")
        
        # 初始化验证器
        self.validator = CaseValidator()
        
        # 统计信息
        self.stats = {
            'total_loaded': 0,
            'total_valid': 0,
            'total_invalid': 0,
            'total_existing': 0,
            'total_imported': 0,
            'total_failed': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 已存在的case_id集合（延迟加载）
        self.existing_ids: Optional[Set[int]] = None
    
    def import_from_json(self, json_file: Path) -> Dict[str, Any]:
        """
        从JSON文件导入数据
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            导入统计信息
        """
        logger.info("=" * 60)
        logger.info(f"开始导入JSON文件: {json_file}")
        logger.info("=" * 60)
        
        self.stats['start_time'] = datetime.now()
        
        # 加载JSON文件
        data = load_json(json_file)
        if not data:
            logger.error(f"无法加载JSON文件: {json_file}")
            return self.stats
        
        cases = data.get('cases', [])
        if not cases:
            logger.warning(f"JSON文件中没有案例数据: {json_file}")
            return self.stats
        
        logger.info(f"JSON文件包含 {len(cases)} 个案例")
        self.stats['total_loaded'] = len(cases)
        
        # 验证数据
        valid_cases, invalid_cases = self.validator.validate_batch(cases)
        self.stats['total_valid'] = len(valid_cases)
        self.stats['total_invalid'] = len(invalid_cases)
        
        if invalid_cases:
            logger.warning(f"发现 {len(invalid_cases)} 个无效案例")
            if self.skip_invalid:
                logger.info("将跳过无效案例")
            else:
                logger.warning("将尝试导入无效案例（可能失败）")
        
        # 过滤已存在的案例（但仍然需要更新向量）
        self._load_existing_ids()
        new_cases = [c for c in valid_cases if c.get('case_id') not in self.existing_ids]
        existing_cases = [c for c in valid_cases if c.get('case_id') in self.existing_ids]
        
        self.stats['total_existing'] = len(existing_cases)
        logger.info(f"已存在案例: {len(existing_cases)}, 新案例: {len(new_cases)}")
        
        # 即使案例已存在，也导入以更新向量字段
        if self.skip_existing:
            cases_to_import = new_cases
        else:
            # 导入所有案例（包括已存在的，用于更新向量）
            cases_to_import = valid_cases if self.skip_invalid else cases
        
        if not cases_to_import:
            logger.info("没有需要导入的案例")
            return self.stats
        
        # 批量生成向量并入库
        try:
            self._batch_import(cases_to_import)
        except Exception as e:
            logger.error(f"批量导入失败: {e}")
            raise
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("=" * 60)
        logger.info("导入完成")
        logger.info("=" * 60)
        logger.info(f"总加载数: {self.stats['total_loaded']}")
        logger.info(f"有效数: {self.stats['total_valid']}")
        logger.info(f"无效数: {self.stats['total_invalid']}")
        logger.info(f"已存在数: {self.stats['total_existing']}")
        logger.info(f"成功导入数: {self.stats['total_imported']}")
        logger.info(f"失败数: {self.stats['total_failed']}")
        logger.info(f"总耗时: {duration:.2f} 秒")
        
        return {
            **self.stats,
            'duration_seconds': duration
        }
    
    def import_from_directory(self, json_dir: Path, pattern: str = 'cases_batch_*.json') -> Dict[str, Any]:
        """
        从目录中的所有JSON文件导入数据
        
        Args:
            json_dir: JSON文件目录
            pattern: 文件匹配模式
            
        Returns:
            导入统计信息
        """
        json_dir = Path(json_dir)
        json_files = sorted(json_dir.glob(pattern))
        
        if not json_files:
            logger.warning(f"目录中没有找到JSON文件: {json_dir}")
            return self.stats
        
        logger.info(f"找到 {len(json_files)} 个JSON文件")
        
        total_stats = self.stats.copy()
        
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"\n处理文件 [{i}/{len(json_files)}]: {json_file.name}")
            
            try:
                file_stats = self.import_from_json(json_file)
                
                # 累计统计
                for key in ['total_loaded', 'total_valid', 'total_invalid', 
                           'total_existing', 'total_imported', 'total_failed']:
                    total_stats[key] += file_stats.get(key, 0)
                    
            except Exception as e:
                logger.error(f"导入文件失败 {json_file}: {e}")
                continue
        
        return total_stats
    
    def _load_existing_ids(self):
        """加载已存在的case_id集合"""
        if self.existing_ids is not None:
            return
        
        try:
            conn = self._get_connection()
            self.existing_ids = get_existing_case_ids(conn)
            conn.close()
        except Exception as e:
            logger.error(f"加载已存在的case_id失败: {e}")
            self.existing_ids = set()
    
    def _batch_import(self, cases: List[Dict[str, Any]]):
        """
        批量导入案例
        
        Args:
            cases: 案例列表
        """
        # 批量生成向量
        logger.info("开始生成向量...")
        cases_with_vectors = self._generate_vectors_batch(cases)
        logger.info(f"向量生成完成: {len(cases_with_vectors)} 个案例")
        
        # 批量入库
        logger.info("开始批量入库...")
        conn = self._get_connection()
        
        try:
            for i in range(0, len(cases_with_vectors), self.batch_size):
                batch = cases_with_vectors[i:i + self.batch_size]
                self._insert_batch(conn, batch)
                logger.info(f"已入库批次: {i // self.batch_size + 1} / {(len(cases_with_vectors) + self.batch_size - 1) // self.batch_size}")
            
            conn.commit()
            logger.info("批量入库完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"批量入库失败: {e}")
            raise
        finally:
            conn.close()
    
    def _generate_vectors_batch(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量生成向量
        
        Args:
            cases: 案例列表
            
        Returns:
            包含向量的案例列表
        """
        cases_with_vectors = []
        
        for case in cases:
            try:
                # 生成组合向量（标题+描述）
                title = case.get('title', '').strip()
                description = case.get('description', '').strip()
                combined_text = f"{title} {description}".strip()
                
                if combined_text:
                    # FlagEmbedding 的 encode 方法不支持 normalize 参数
                    # 向量默认已经归一化
                    vector = self.model.encode(combined_text)
                    # 手动归一化向量
                    import numpy as np
                    vector_norm = vector / np.linalg.norm(vector)
                    case['combined_vector'] = vector_norm.tolist()
                else:
                    logger.warning(f"案例 {case.get('case_id')} 没有文本内容，跳过向量生成")
                    case['combined_vector'] = None
                
                cases_with_vectors.append(case)
                
            except Exception as e:
                logger.error(f"生成向量失败 [case_id={case.get('case_id')}]: {e}")
                case['vector_error'] = str(e)
                case['combined_vector'] = None
                cases_with_vectors.append(case)
        
        return cases_with_vectors
    
    def _insert_batch(self, conn, batch: List[Dict[str, Any]]):
        """
        批量插入数据库
        
        Args:
            conn: 数据库连接
            batch: 批次数据
        """
        insert_sql = """
            INSERT INTO ad_cases (
                case_id, source_url, title, description, author, publish_time,
                main_image, images, video_url,
                brand_name, brand_industry, activity_type, location, tags,
                score, score_decimal, favourite,
                company_name, company_logo, agency_name,
                combined_vector
            ) VALUES (
                %(case_id)s, %(source_url)s, %(title)s, %(description)s, 
                %(author)s, %(publish_time)s,
                %(main_image)s, %(images)s::jsonb, %(video_url)s,
                %(brand_name)s, %(brand_industry)s, %(activity_type)s, 
                %(location)s, %(tags)s::jsonb,
                %(score)s, %(score_decimal)s, %(favourite)s,
                %(company_name)s, %(company_logo)s, %(agency_name)s,
                %(combined_vector)s::vector(1024)
            )
            ON CONFLICT (case_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                combined_vector = EXCLUDED.combined_vector,
                updated_at = CURRENT_TIMESTAMP
        """
        
        # 准备数据
        import json
        insert_data = []
        for case in batch:
            # 检查向量是否存在
            if case.get('combined_vector') is None:
                logger.warning(f"案例 {case.get('case_id')} 没有向量，跳过")
                self.stats['total_failed'] += 1
                continue
            
            data = {
                'case_id': case.get('case_id'),
                'source_url': case.get('source_url'),
                'title': case.get('title'),
                'description': case.get('description'),
                'author': case.get('author'),
                'publish_time': case.get('publish_time'),
                'main_image': case.get('main_image'),
                'images': json.dumps(case.get('images', []), ensure_ascii=False),  # 转换为 JSON 字符串
                'video_url': case.get('video_url'),
                'brand_name': case.get('brand_name'),
                'brand_industry': case.get('brand_industry'),
                'activity_type': case.get('activity_type'),
                'location': case.get('location'),
                'tags': json.dumps(case.get('tags', []), ensure_ascii=False),  # 转换为 JSON 字符串
                'score': case.get('score'),
                'score_decimal': case.get('score_decimal'),
                'favourite': case.get('favourite', 0),
                'company_name': case.get('company_name'),
                'company_logo': case.get('company_logo'),
                'agency_name': case.get('agency_name'),
                'combined_vector': case.get('combined_vector')  # 向量列表
            }
            insert_data.append(data)
        
        if not insert_data:
            return
        
        # 批量执行
        cur = conn.cursor()
        try:
            execute_batch(cur, insert_sql, insert_data, page_size=self.batch_size)
            self.stats['total_imported'] += len(insert_data)
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            raise
        finally:
            cur.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(**self.db_config)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'database': 'ad_case_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    # 创建入库阶段
    import_stage = ImportStage(
        db_config=db_config,
        batch_size=10  # 测试用小批次
    )
    
    # 从JSON文件导入
    json_file = Path('data/json/cases_batch_0001.json')
    
    if json_file.exists():
        try:
            stats = import_stage.import_from_json(json_file)
            
            print("\n导入统计:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"JSON文件不存在: {json_file}")

