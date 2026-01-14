#!/usr/bin/env python3
"""
爬取阶段
负责爬取案例数据并保存到JSON文件
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from spider.api_client import AdquanAPIClient
from spider.detail_parser import DetailPageParser
from .utils import (
    save_json, save_resume_file, load_resume_file,
    format_batch_filename, get_next_batch_number, merge_case_data
)
from .validator import CaseValidator

logger = logging.getLogger(__name__)


class CrawlStage:
    """爬取阶段类"""
    
    def __init__(
        self,
        output_dir: Path,
        batch_size: int = 100,
        resume_file: Optional[Path] = None,
        delay_range: tuple = (2, 5),
        enable_resume: bool = True
    ):
        """
        初始化爬取阶段
        
        Args:
            output_dir: JSON文件输出目录
            batch_size: 每批保存的案例数量
            resume_file: 断点续传文件路径
            delay_range: 请求延迟范围（秒）
            enable_resume: 是否启用断点续传
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_size = batch_size
        self.delay_range = delay_range
        self.enable_resume = enable_resume
        
        # 断点续传文件
        if resume_file:
            self.resume_file = Path(resume_file)
        else:
            self.resume_file = self.output_dir / 'crawl_resume.json'
        
        # 已爬取的case_id集合
        self.crawled_ids: Set[int] = set()
        if self.enable_resume:
            self.crawled_ids = load_resume_file(self.resume_file)
        
        # 初始化组件
        self.api_client = AdquanAPIClient()
        self.detail_parser = DetailPageParser(session=self.api_client.session)
        self.validator = CaseValidator()
        
        # 统计信息
        self.stats = {
            'total_crawled': 0,
            'total_saved': 0,
            'total_failed': 0,
            'batches_saved': 0,
            'start_time': None,
            'end_time': None
        }
    
    def crawl(
        self,
        start_page: int = 0,
        max_pages: int = 100,
        case_type: int = 3,
        search_value: str = '',
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        执行爬取任务
        
        Args:
            start_page: 起始页码
            max_pages: 最大页数
            case_type: 案例类型
            search_value: 搜索关键词
            skip_existing: 是否跳过已爬取的案例
            
        Returns:
            爬取统计信息
        """
        logger.info("=" * 60)
        logger.info("开始爬取阶段")
        logger.info("=" * 60)
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"批次大小: {self.batch_size}")
        logger.info(f"已爬取案例数: {len(self.crawled_ids)}")
        logger.info(f"起始页: {start_page}, 最大页数: {max_pages}")
        
        self.stats['start_time'] = datetime.now()
        
        try:
            # 获取列表页数据
            logger.info("开始获取列表页数据...")
            list_items = self.api_client.get_creative_list_paginated(
                start_page=start_page,
                max_pages=max_pages,
                case_type=case_type,
                search_value=search_value
            )
            
            logger.info(f"获取到 {len(list_items)} 个案例列表项")
            
            # 当前批次数据
            current_batch: List[Dict[str, Any]] = []
            batch_num = get_next_batch_number(self.output_dir)
            
            # 遍历每个案例
            for i, item in enumerate(list_items, 1):
                case_id = item.get('id')
                case_url = item.get('url')
                case_title = item.get('title', '未知标题')
                
                # 检查是否已爬取
                if skip_existing and case_id and case_id in self.crawled_ids:
                    logger.debug(f"[{i}/{len(list_items)}] 跳过已爬取: {case_title} (case_id={case_id})")
                    continue
                
                if not case_url:
                    logger.warning(f"[{i}/{len(list_items)}] 跳过：没有URL")
                    self.stats['total_failed'] += 1
                    continue
                
                logger.info(f"[{i}/{len(list_items)}] 爬取: {case_title}")
                logger.debug(f"  URL: {case_url}")
                
                try:
                    # 解析详情页
                    detail_data = self.detail_parser.parse(case_url)
                    
                    # 合并数据
                    case_data = merge_case_data(item, detail_data)
                    
                    # 验证数据
                    is_valid, error = self.validator.validate_case(case_data)
                    if not is_valid:
                        logger.warning(f"  数据验证失败: {error}")
                        case_data['validation_error'] = error
                    
                    # 添加到批次
                    current_batch.append(case_data)
                    self.crawled_ids.add(case_id)
                    self.stats['total_crawled'] += 1
                    
                    logger.info(f"  ✓ 爬取成功")
                    logger.debug(f"    标题: {case_data.get('title')}")
                    logger.debug(f"    描述长度: {len(case_data.get('description', ''))} 字符")
                    
                    # 达到批次大小，保存JSON
                    if len(current_batch) >= self.batch_size:
                        self._save_batch(current_batch, batch_num)
                        current_batch = []
                        batch_num += 1
                    
                    # 更新断点续传文件
                    if self.enable_resume and i % 10 == 0:  # 每10个案例更新一次
                        save_resume_file(self.resume_file, self.crawled_ids)
                    
                    # 请求延迟
                    if i < len(list_items):
                        delay = self._get_delay()
                        time.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"  ✗ 爬取失败: {e}")
                    self.stats['total_failed'] += 1
                    
                    # 保存失败信息
                    failed_case = {
                        'case_id': case_id,
                        'url': case_url,
                        'title': case_title,
                        'error': str(e),
                        'crawl_time': datetime.now().isoformat()
                    }
                    current_batch.append(failed_case)
                    
                    continue
            
            # 保存剩余批次
            if current_batch:
                self._save_batch(current_batch, batch_num)
            
            # 最终更新断点续传文件
            if self.enable_resume:
                save_resume_file(self.resume_file, self.crawled_ids)
            
            self.stats['end_time'] = datetime.now()
            
            # 计算耗时
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info("=" * 60)
            logger.info("爬取阶段完成")
            logger.info("=" * 60)
            logger.info(f"总爬取数: {self.stats['total_crawled']}")
            logger.info(f"总保存数: {self.stats['total_saved']}")
            logger.info(f"总失败数: {self.stats['total_failed']}")
            logger.info(f"保存批次数: {self.stats['batches_saved']}")
            logger.info(f"总耗时: {duration:.2f} 秒")
            
            return {
                **self.stats,
                'duration_seconds': duration,
                'output_dir': str(self.output_dir),
                'batches': self.stats['batches_saved']
            }
            
        except Exception as e:
            logger.error(f"爬取阶段失败: {e}")
            raise
    
    def _save_batch(self, batch: List[Dict[str, Any]], batch_num: int) -> bool:
        """
        保存批次数据到JSON文件
        
        Args:
            batch: 批次数据
            batch_num: 批次号
            
        Returns:
            是否保存成功
        """
        filename = format_batch_filename(batch_num)
        file_path = self.output_dir / filename
        
        # 准备输出数据
        output_data = {
            'batch_num': batch_num,
            'batch_size': len(batch),
            'created_at': datetime.now().isoformat(),
            'cases': batch
        }
        
        # 保存JSON
        if save_json(output_data, file_path):
            self.stats['total_saved'] += len(batch)
            self.stats['batches_saved'] += 1
            logger.info(f"批次 {batch_num} 已保存: {file_path} ({len(batch)} 个案例)")
            return True
        else:
            logger.error(f"批次 {batch_num} 保存失败: {file_path}")
            return False
    
    def _get_delay(self) -> float:
        """获取随机延迟时间"""
        import random
        return random.uniform(*self.delay_range)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建输出目录
    output_dir = Path('data/json')
    
    # 创建爬取阶段
    crawl_stage = CrawlStage(
        output_dir=output_dir,
        batch_size=10,  # 测试用小批次
        delay_range=(1, 2)  # 测试用短延迟
    )
    
    # 执行爬取（只爬取1页作为测试）
    try:
        stats = crawl_stage.crawl(
            start_page=0,
            max_pages=1,
            case_type=3
        )
        
        print("\n爬取统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

