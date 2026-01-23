#!/usr/bin/env python3
"""
爬取阶段
负责爬取案例数据并保存到JSON文件
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
from datetime import datetime

from ..spider.api_client import AdquanAPIClient
from ..spider.detail_parser import DetailPageParser
from .utils import (
    save_json, save_resume_file, load_resume_file,
    format_batch_filename, get_next_batch_number, merge_case_data,
    get_saved_case_ids_from_json, validate_crawled_ids_saved
)
from .validator import CaseValidator

logger = logging.getLogger(__name__)


class CrawlStage:
    """爬取阶段类"""
    
    def __init__(
        self,
        output_dir: Path,
        batch_size: int = 30,
        resume_file: Optional[Path] = None,
        delay_range: tuple = (2, 5),
        enable_resume: bool = True,
        progress_callback: Optional[Callable[[], bool]] = None,
        task_id: Optional[str] = None
    ):
        """
        初始化爬取阶段
        
        Args:
            output_dir: JSON文件输出目录
            batch_size: 每批保存的案例数量
            resume_file: 断点续传文件路径
            delay_range: 请求延迟范围（秒）
            enable_resume: 是否启用断点续传
            progress_callback: 进度回调函数，每处理一定数量的案例后调用
                               返回 True 表示继续执行，False 表示暂停
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_size = batch_size
        self.delay_range = delay_range
        self.enable_resume = enable_resume
        self.progress_callback = progress_callback
        self.task_id = task_id  # 任务ID，用于记录列表页状态
        
        # 断点续传文件
        if resume_file:
            self.resume_file = Path(resume_file)
        else:
            self.resume_file = self.output_dir / 'crawl_resume.json'
        
        # 已爬取的case_id集合
        self.crawled_ids: Set[int] = set()
        # 已保存的case_id集合（用于验证）
        self.saved_ids: Set[int] = set()
        
        if self.enable_resume:
            self.crawled_ids = load_resume_file(self.resume_file)
            # 加载已保存的ID，用于验证
            try:
                self.saved_ids = get_saved_case_ids_from_json(self.output_dir)
            except Exception as e:
                logger.warning(f"加载已保存的ID失败: {e}，将从头开始验证")
                self.saved_ids = set()
        
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
        max_pages: Optional[int] = 100,
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
            # 流式处理：边获取边处理，不一次性加载所有数据
            logger.info("开始流式获取和处理列表页数据...")
            logger.info(f"列表页获取参数: start_page={start_page}, max_pages={max_pages}, case_type={case_type}, search_value='{search_value}'")
            
            # 当前批次数据
            current_batch: List[Dict[str, Any]] = []
            batch_num = get_next_batch_number(self.output_dir)
            
            # 处理计数器（用于进度更新，包括成功和失败的案例）
            processed_count = 0
            total_list_items = 0  # 累计列表项数量
            
            # 使用生成器逐页获取并处理（流式处理）
            logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info("开始流式处理：将逐页获取并立即处理，不一次性加载所有数据")
            logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            for page_items, page_num in self._get_list_items_streaming(
                start_page=start_page,
                max_pages=max_pages,
                case_type=case_type
            ):
                logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                logger.info(f"收到第 {page_num} 页数据，开始处理...")
                
                if not page_items:
                    logger.info(f"第 {page_num} 页无数据，停止获取")
                    break
                
                total_list_items += len(page_items)
                logger.info(f"第 {page_num} 页获取到 {len(page_items)} 个案例，开始处理...")
                
                # 立即处理这一页的数据
                for i, item in enumerate(page_items, 1):
                    item_index = total_list_items - len(page_items) + i
                    case_id = item.get('id')
                    case_url = item.get('url')
                    case_title = item.get('title', '未知标题')
                    
                    # 检查是否已爬取且已保存
                    if skip_existing and case_id and case_id in self.crawled_ids:
                        # 如果ID在已爬取列表中，检查是否已保存
                        if case_id in self.saved_ids:
                            logger.debug(f"[{item_index}/{total_list_items}] 跳过已爬取且已保存: {case_title} (case_id={case_id})")
                            continue
                        else:
                            # ID已爬取但未保存，需要重新爬取
                            logger.warning(f"[{item_index}/{total_list_items}] 重新爬取未保存的案例: {case_title} (case_id={case_id})")
                            # 从已爬取列表中移除，以便重新爬取
                            self.crawled_ids.discard(case_id)
                    
                    if not case_url:
                        logger.warning(f"[{item_index}/{total_list_items}] 跳过：没有URL")
                        self.stats['total_failed'] += 1
                        processed_count += 1
                        # 检查进度更新
                        if processed_count % 10 == 0:
                            self._check_progress_and_pause()
                        continue
                    
                    logger.info(f"[{item_index}/{total_list_items}] 爬取: {case_title}")
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
                        processed_count += 1
                        
                        # 标记为已保存（将在保存批次后更新）
                        
                        logger.info(f"  ✓ 爬取成功")
                        logger.debug(f"    标题: {case_data.get('title')}")
                        logger.debug(f"    描述长度: {len(case_data.get('description', ''))} 字符")
                        
                        # 达到批次大小，保存JSON
                        if len(current_batch) >= self.batch_size:
                            self._save_batch(current_batch, batch_num)
                            current_batch = []
                            batch_num += 1
                        
                        # 每10个案例更新进度并检查暂停状态
                        if processed_count % 10 == 0:
                            self._check_progress_and_pause()
                        
                        # 请求延迟（每处理一个案例后）
                        delay = self._get_delay()
                        time.sleep(delay)
                            
                    except Exception as e:
                        logger.error(f"  ✗ 爬取失败: {e}")
                        self.stats['total_failed'] += 1
                        processed_count += 1
                        
                        # 保存失败信息
                        failed_case = {
                            'case_id': case_id,
                            'url': case_url,
                            'title': case_title,
                            'error': str(e),
                            'crawl_time': datetime.now().isoformat()
                        }
                        current_batch.append(failed_case)
                        
                        # 每10个案例更新进度并检查暂停状态
                        if processed_count % 10 == 0:
                            self._check_progress_and_pause()
                        
                        continue
            
            # 保存剩余批次
            if current_batch:
                self._save_batch(current_batch, batch_num)
            
            # 验证所有已爬取的ID是否都被保存
            if self.enable_resume and self.crawled_ids:
                saved_ids = get_saved_case_ids_from_json(self.output_dir)
                validation_result = validate_crawled_ids_saved(self.crawled_ids, saved_ids)
                
                if not validation_result['all_saved']:
                    missing_count = validation_result['missing_count']
                    missing_ids = validation_result['missing_ids']
                    logger.warning(f"发现 {missing_count} 个已爬取但未保存的案例ID")
                    logger.debug(f"未保存的ID列表: {missing_ids[:10]}..." if len(missing_ids) > 10 else f"未保存的ID列表: {missing_ids}")
                    
                    # 将未保存的ID计入失败统计
                    self.stats['total_failed'] += missing_count
                    
                    # 为未保存的ID创建失败记录并保存
                    if missing_ids:
                        failed_batch = []
                        for missing_id in missing_ids:
                            failed_case = {
                                'case_id': missing_id,
                                'url': None,
                                'title': f'案例 {missing_id}',
                                'error': '已爬取但未保存到JSON文件',
                                'crawl_time': datetime.now().isoformat(),
                                'validation_error': '数据丢失'
                            }
                            failed_batch.append(failed_case)
                        
                        # 保存失败记录到单独的批次
                        if failed_batch:
                            self._save_batch(failed_batch, batch_num)
                            logger.warning(f"已将 {len(failed_batch)} 个未保存的案例记录为失败")
            
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
    
    def _check_progress_and_pause(self):
        """检查进度并处理暂停逻辑"""
        # 更新断点续传文件
        if self.enable_resume:
            save_resume_file(self.resume_file, self.crawled_ids)
        
        # 调用进度回调（如果设置了）
        if self.progress_callback:
            try:
                should_continue = self.progress_callback()
                if not should_continue:
                    # 回调返回 False，表示需要暂停
                    logger.info("收到暂停信号，等待恢复...")
                    # 等待暂停状态解除
                    while True:
                        try:
                            should_continue = self.progress_callback()
                            if should_continue:
                                logger.info("收到恢复信号，继续执行...")
                                break
                        except KeyboardInterrupt:
                            # 如果回调抛出 KeyboardInterrupt，表示需要停止
                            raise
                        time.sleep(0.5)  # 每0.5秒检查一次
            except KeyboardInterrupt:
                # 如果回调抛出 KeyboardInterrupt，重新抛出以中断爬取
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
            
            # 更新已保存的ID集合
            for case in batch:
                case_id = case.get('case_id')
                if case_id:
                    self.saved_ids.add(case_id)
            
            logger.info(f"批次 {batch_num} 已保存: {file_path} ({len(batch)} 个案例)")
            return True
        else:
            logger.error(f"批次 {batch_num} 保存失败: {file_path}")
            return False
    
    def _get_list_items_streaming(
        self, start_page: int, max_pages: Optional[int], case_type: int = 1
    ):
        """
        流式获取列表页数据（生成器），逐页返回数据并记录状态
        
        Args:
            start_page: 起始页码
            max_pages: 最大页数
            case_type: 案例类型（默认为1）
            
        Yields:
            (items, page_num): 每页的案例列表和页码
        """
        page = start_page
        
        # 如果 task_id 不存在，回退到原来的方法（兼容性）
        if not self.task_id:
            logger.warning("task_id 未设置，使用默认分页方法（不记录列表页状态）")
            # 回退到非流式方法
            all_items = self.api_client.get_creative_list_paginated(start_page, max_pages, case_type=case_type)
            yield all_items, start_page
            return
        
        # 导入同步数据库类
        from app.services.crawl_task_executor_sync_db import SyncDatabase
        
        logger.info(f"开始流式获取案例列表")
        logger.info(f"  - 起始页: {start_page}")
        logger.info(f"  - 最大页数: {max_pages if max_pages is not None else '无限制（爬取到最后一页）'}")
        logger.info(f"  - API客户端已初始化: {self.api_client is not None}")
        
        # 如果 max_pages 为 None，表示爬取到最后一页
        if max_pages is None:
            # 无限循环，直到没有更多数据
            while True:
                page_start_time = time.time()
                logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                logger.info(f"开始获取第 {page} 页数据")
                logger.info(f"请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 创建列表页记录
                SyncDatabase.create_list_page_record(self.task_id, page)
                
                try:
                    # 获取当前页数据
                    logger.info(f"正在请求API: page={page}, case_type={case_type}")
                    data = self.api_client.get_creative_list(page, case_type=case_type)
                    logger.info(f"API请求成功，响应数据类型: {type(data).__name__}")
                    
                    # 解析返回数据
                    if isinstance(data, dict):
                        logger.info(f"响应数据结构检查:")
                        logger.info(f"  - 是否为字典: ✓")
                        logger.info(f"  - 包含 'data' 键: {'✓' if 'data' in data else '✗'}")
                        
                        # 检查数据结构
                        if 'data' in data and isinstance(data['data'], dict):
                            logger.info(f"  - 'data' 是字典: ✓")
                            items = data['data'].get('items', [])
                            logger.info(f"  - 'items' 数量: {len(items)}")
                            
                            # 检查API返回的状态码
                            if 'code' in data:
                                api_code = data.get('code')
                                api_message = data.get('message', '')
                                logger.info(f"  - API状态码: {api_code}")
                                if api_message:
                                    logger.info(f"  - API消息: {api_message}")
                            
                            if not items:
                                logger.warning(f"⚠️ 第 {page} 页返回空数据（items为空）")
                                logger.warning(f"  响应数据键: {list(data.keys())}")
                                if 'data' in data:
                                    logger.warning(f"  data 键: {list(data['data'].keys())}")
                                # 更新为成功状态（0个案例）
                                duration = time.time() - page_start_time
                                SyncDatabase.update_list_page_success(
                                    self.task_id, page, 0, duration
                                )
                                logger.info(f"第 {page} 页处理完成（0个案例），停止获取")
                                break
                            
                            duration = time.time() - page_start_time
                            logger.info(f"✓ 第 {page} 页获取成功:")
                            logger.info(f"  - 本页案例数: {len(items)}")
                            logger.info(f"  - 请求耗时: {duration:.2f} 秒")
                            
                            # 更新为成功状态
                            SyncDatabase.update_list_page_success(
                                self.task_id, page, len(items), duration
                            )
                            
                            # 立即 yield 这一页的数据（流式处理）
                            # 注意：yield 会暂停生成器，等待调用者处理完当前页数据后才会继续
                            logger.info(f"  → 准备 yield 第 {page} 页数据（{len(items)} 个案例）")
                            yield items, page
                            logger.info(f"  ← 第 {page} 页数据处理完成，继续获取下一页")
                            
                            # 等待后再请求下一页（在 yield 之后，确保当前页已处理）
                            # 注意：这个等待会在调用者处理完当前页数据后执行
                            self.api_client._wait()
                            page += 1
                            
                        else:
                            logger.error(f"✗ 第 {page} 页数据格式异常")
                            logger.error(f"  响应数据类型: {type(data).__name__}")
                            logger.error(f"  响应数据键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                            if isinstance(data, dict) and 'data' in data:
                                logger.error(f"  'data' 类型: {type(data['data']).__name__}")
                                if isinstance(data['data'], dict):
                                    logger.error(f"  'data' 键: {list(data['data'].keys())}")
                            logger.error(f"  原始响应数据（前500字符）: {str(data)[:500]}")
                            duration = time.time() - page_start_time
                            error_msg = f"数据格式异常: data字段不是字典或不存在"
                            SyncDatabase.update_list_page_failed(
                                self.task_id, page, 
                                error_msg,
                                'parse_error', duration
                            )
                            break
                    else:
                        logger.error(f"✗ 第 {page} 页返回数据不是字典格式")
                        logger.error(f"  响应数据类型: {type(data).__name__}")
                        logger.error(f"  响应数据内容（前500字符）: {str(data)[:500]}")
                        duration = time.time() - page_start_time
                        SyncDatabase.update_list_page_failed(
                            self.task_id, page,
                            f"返回数据不是字典格式，实际类型: {type(data).__name__}",
                            'parse_error', duration
                        )
                        break
                    
                except Exception as e:
                    logger.error(f"获取第{page}页时发生错误: {e}")
                    duration = time.time() - page_start_time
                    # 确定错误类型
                    error_type = 'network_error'
                    if 'SSL' in str(e) or 'SSLError' in str(type(e).__name__):
                        error_type = 'network_error'
                    elif 'JSON' in str(e) or 'JSONDecodeError' in str(type(e).__name__):
                        error_type = 'parse_error'
                    elif 'timeout' in str(e).lower() or 'Timeout' in str(type(e).__name__):
                        error_type = 'timeout_error'
                    
                    SyncDatabase.update_list_page_failed(
                        self.task_id, page,
                        str(e), error_type, duration
                    )
                    # 停止获取，避免无限循环
                    break
        else:
            # max_pages 不为 None，有页数限制
            while page < start_page + max_pages:
                page_start_time = time.time()
                logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                logger.info(f"开始获取第 {page} 页数据")
                logger.info(f"请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 创建列表页记录
                SyncDatabase.create_list_page_record(self.task_id, page)
                
                try:
                    # 获取当前页数据
                    logger.info(f"正在请求API: page={page}, case_type={case_type}")
                    data = self.api_client.get_creative_list(page, case_type=case_type)
                    logger.info(f"API请求成功，响应数据类型: {type(data).__name__}")
                    
                    # 解析返回数据
                    if isinstance(data, dict):
                        logger.info(f"响应数据结构检查:")
                        logger.info(f"  - 是否为字典: ✓")
                        logger.info(f"  - 包含 'data' 键: {'✓' if 'data' in data else '✗'}")
                        
                        # 检查数据结构
                        if 'data' in data and isinstance(data['data'], dict):
                            logger.info(f"  - 'data' 是字典: ✓")
                            items = data['data'].get('items', [])
                            logger.info(f"  - 'items' 数量: {len(items)}")
                            
                            # 检查API返回的状态码
                            if 'code' in data:
                                api_code = data.get('code')
                                api_message = data.get('message', '')
                                logger.info(f"  - API状态码: {api_code}")
                                if api_message:
                                    logger.info(f"  - API消息: {api_message}")
                            
                            if not items:
                                logger.info(f"第{page}页没有更多数据，停止获取")
                                duration = time.time() - page_start_time
                                SyncDatabase.update_list_page_success(
                                    self.task_id, page, 0, duration
                                )
                                break
                            
                            duration = time.time() - page_start_time
                            logger.info(f"✓ 第 {page} 页获取成功:")
                            logger.info(f"  - 本页案例数: {len(items)}")
                            logger.info(f"  - 请求耗时: {duration:.2f} 秒")
                            
                            # 更新为成功状态
                            SyncDatabase.update_list_page_success(
                                self.task_id, page, len(items), duration
                            )
                            
                            # 立即 yield 这一页的数据（流式处理）
                            # 注意：yield 会暂停生成器，等待调用者处理完当前页数据后才会继续
                            logger.info(f"  → 准备 yield 第 {page} 页数据（{len(items)} 个案例）")
                            yield items, page
                            logger.info(f"  ← 第 {page} 页数据处理完成，继续获取下一页")
                            
                            # 等待后再请求下一页（在 yield 之后，确保当前页已处理）
                            # 注意：这个等待会在调用者处理完当前页数据后执行
                            self.api_client._wait()
                            page += 1
                            
                        else:
                            logger.error(f"✗ 第 {page} 页数据格式异常")
                            logger.error(f"  响应数据类型: {type(data).__name__}")
                            logger.error(f"  响应数据键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                            if isinstance(data, dict) and 'data' in data:
                                logger.error(f"  'data' 类型: {type(data['data']).__name__}")
                                if isinstance(data['data'], dict):
                                    logger.error(f"  'data' 键: {list(data['data'].keys())}")
                            logger.error(f"  原始响应数据（前500字符）: {str(data)[:500]}")
                            duration = time.time() - page_start_time
                            error_msg = f"数据格式异常: data字段不是字典或不存在"
                            SyncDatabase.update_list_page_failed(
                                self.task_id, page, 
                                error_msg,
                                'parse_error', duration
                            )
                            break
                    else:
                        logger.error(f"✗ 第 {page} 页返回数据不是字典格式")
                        logger.error(f"  响应数据类型: {type(data).__name__}")
                        logger.error(f"  响应数据内容（前500字符）: {str(data)[:500]}")
                        duration = time.time() - page_start_time
                        SyncDatabase.update_list_page_failed(
                            self.task_id, page,
                            f"返回数据不是字典格式，实际类型: {type(data).__name__}",
                            'parse_error', duration
                        )
                        break
                    
                except Exception as e:
                    logger.error(f"获取第{page}页时发生错误: {e}")
                    duration = time.time() - page_start_time
                    # 确定错误类型
                    error_type = 'network_error'
                    if 'SSL' in str(e) or 'SSLError' in str(type(e).__name__):
                        error_type = 'network_error'
                    elif 'JSON' in str(e) or 'JSONDecodeError' in str(type(e).__name__):
                        error_type = 'parse_error'
                    elif 'timeout' in str(e).lower() or 'Timeout' in str(type(e).__name__):
                        error_type = 'timeout_error'
                    
                    SyncDatabase.update_list_page_failed(
                        self.task_id, page,
                        str(e), error_type, duration
                    )
                    # 可以选择继续或停止
                    # 这里选择停止，避免无限循环
                    break
    
    def _get_list_items_with_status_recording(
        self, start_page: int, max_pages: Optional[int], case_type: int = 1
    ) -> List[Dict[str, Any]]:
        """
        分页获取列表页数据并记录每一页的状态（已废弃，保留用于兼容性）
        
        注意：此方法会一次性加载所有数据到内存，建议使用 _get_list_items_streaming 方法
        
        Args:
            start_page: 起始页码
            max_pages: 最大页数
            case_type: 案例类型（默认为1）
            
        Returns:
            所有案例的列表
        """
        logger.warning("使用已废弃的方法 _get_list_items_with_status_recording，建议使用流式处理方法")
        all_items = []
        
        # 使用流式方法收集所有数据（向后兼容）
        for items, _ in self._get_list_items_streaming(start_page, max_pages, case_type):
            all_items.extend(items)
        
        return all_items
    
    def _get_delay(self) -> float:
        """获取随机延迟时间"""
        import random
        return random.uniform(*self.delay_range)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
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

