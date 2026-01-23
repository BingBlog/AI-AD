#!/usr/bin/env python3
"""
广告门API客户端
负责调用广告门网站的API接口获取案例列表数据
"""

import requests
import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from .csrf_token_manager import CSRFTokenManager

logger = logging.getLogger(__name__)


class AdquanAPIClient:
    """广告门API客户端类"""
    
    def __init__(self, base_url: str = 'https://m.adquan.com/creative', 
                 delay_range: tuple = (1, 3), max_retries: int = 3):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            delay_range: 请求延迟范围（秒），用于控制请求频率
            max_retries: 最大重试次数
        """
        self.base_url = base_url
        self.delay_range = delay_range
        self.max_retries = max_retries
        
        # 创建Session
        self.session = requests.Session()
        
        # 创建CSRF Token管理器（先获取Token，此时使用HTML请求的headers）
        self.token_manager = CSRFTokenManager(base_url=base_url, session=self.session)
        
        # 预先获取Token，确保Token可用
        # 这样后续API请求时Token已经准备好
        try:
            self.token_manager.get_token()
        except Exception as e:
            logger.warning(f"初始化时获取Token失败: {e}，将在首次API请求时重试")
        
        # 设置API请求的默认Headers（在获取Token之后）
        self._setup_api_headers()
    
    def _setup_api_headers(self):
        """设置API请求的默认Headers"""
        # 注意：不要覆盖User-Agent和Accept-Language，这些已经在Token管理器中设置
        # 只添加API特有的headers
        api_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Connection': 'keep-alive',
            'Referer': 'https://m.adquan.com/creative',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.session.headers.update(api_headers)
    
    def _get_delay(self) -> float:
        """获取随机延迟时间"""
        import random
        return random.uniform(*self.delay_range)
    
    def _wait(self):
        """等待指定时间，控制请求频率"""
        delay = self._get_delay()
        time.sleep(delay)
    
    def get_creative_list(self, page: int = 0, case_type: int = 1, retry_count: int = 0) -> Dict[str, Any]:
        """
        获取创意案例列表
        
        Args:
            page: 页码（从0开始，但API使用从1开始的页码）
            case_type: 案例类型（默认为1）
            retry_count: 当前重试次数（内部使用）
            
        Returns:
            API返回的JSON数据字典
            
        Raises:
            requests.RequestException: 请求失败
            ValueError: 响应数据格式错误
            
        Note:
            **API限制**：使用 page 和 type 参数查询案例列表。
            API的page参数从1开始，但这里传入的page从0开始，会自动转换为1开始。
        """
        # 准备请求参数 - 包含 page 和 type 参数
        # API的page从1开始，所以需要+1
        params = {
            'page': page + 1,  # API使用从1开始的页码
            'type': case_type,
        }
        
        # 获取CSRF Token并添加到Headers
        # 如果Token获取失败，尝试刷新
        try:
            token_headers = self.token_manager.get_token_for_header()
        except ValueError:
            logger.warning("Token获取失败，尝试刷新...")
            token_headers = self.token_manager.get_token_for_header()  # 会触发刷新
        
        headers = {**self.session.headers, **token_headers}
        
        try:
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"API请求详情:")
            logger.info(f"  - URL: {self.base_url}")
            logger.info(f"  - 页码（内部）: {page} (API使用: {page + 1})")
            logger.info(f"  - 案例类型: {case_type}")
            logger.info(f"  - 请求参数: {params}")
            logger.info(f"  - 超时设置: 30 秒")
            logger.info(f"  - 请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 发送请求
            request_start_time = time.time()
            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=30
            )
            request_duration = time.time() - request_start_time
            
            logger.info(f"API响应详情:")
            logger.info(f"  - HTTP状态码: {response.status_code}")
            logger.info(f"  - 请求耗时: {request_duration:.2f} 秒")
            logger.info(f"  - 响应头 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            logger.info(f"  - 响应大小: {len(response.content)} 字节")
            
            # 检查响应状态
            response.raise_for_status()
            logger.info(f"  - HTTP状态检查: ✓ 通过")
            
            # 检查是否是Token错误
            if response.status_code in (401, 403):
                logger.warning(f"⚠️ 检测到HTTP {response.status_code}，可能是Token失效")
                logger.warning(f"  响应内容（前200字符）: {response.text[:200]}")
                if self.token_manager.handle_token_error(response):
                    # Token已刷新，重试请求
                    if retry_count < self.max_retries:
                        logger.info(f"✓ Token已刷新，准备重试请求（第{retry_count + 1}次，最多{self.max_retries}次）...")
                        self._wait()  # 等待后再重试
                        return self.get_creative_list(page, case_type, retry_count + 1)
                    else:
                        error_msg = f"Token刷新后仍失败，已达到最大重试次数 {self.max_retries}"
                        logger.error(f"✗ {error_msg}")
                        raise requests.RequestException(error_msg)
            
            # 解析JSON响应
            logger.info(f"开始解析JSON响应...")
            try:
                data = response.json()
                logger.info(f"  - JSON解析: ✓ 成功")
                logger.info(f"  - 数据类型: {type(data).__name__}")
                if isinstance(data, dict):
                    logger.info(f"  - 数据键: {list(data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"✗ JSON解析失败")
                logger.error(f"  错误: {e}")
                logger.error(f"  响应内容（前500字符）: {response.text[:500]}")
                logger.error(f"  响应内容（后500字符）: {response.text[-500:]}")
                raise ValueError(f"响应不是有效的JSON格式: {e}")
            
            # 检查API返回的状态码
            if isinstance(data, dict) and 'code' in data:
                api_code = data.get('code')
                api_message = data.get('message', '')
                logger.info(f"  - API状态码: {api_code}")
                if api_message:
                    logger.info(f"  - API消息: {api_message}")
                
                if api_code != 0:
                    error_msg = api_message or '未知错误'
                    logger.error(f"✗ API返回错误")
                    logger.error(f"  - 错误码: {api_code}")
                    logger.error(f"  - 错误消息: {error_msg}")
                    logger.error(f"  - 完整响应数据: {data}")
                    raise ValueError(f"API错误: {error_msg}")
                else:
                    logger.info(f"  - API状态码检查: ✓ 通过")
            
            # 检查数据内容
            if isinstance(data, dict):
                if 'data' in data:
                    data_content = data['data']
                    if isinstance(data_content, dict):
                        items_count = len(data_content.get('items', []))
                        logger.info(f"  - 数据内容检查: ✓")
                        logger.info(f"  - items数量: {items_count}")
                    else:
                        logger.warning(f"  - 'data' 字段类型: {type(data_content).__name__}（期望字典）")
                else:
                    logger.warning(f"  - 响应中未找到 'data' 字段")
            
            logger.info(f"✓ API请求成功完成")
            logger.info(f"  - 页码: {page}")
            logger.info(f"  - 返回数据大小: {len(str(data))} 字符")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"✗ HTTP请求异常")
            logger.error(f"  异常类型: {type(e).__name__}")
            logger.error(f"  异常消息: {str(e)}")
            
            # 如果是网络错误且未达到最大重试次数，进行重试
            if retry_count < self.max_retries:
                logger.info(f"准备重试请求（第{retry_count + 1}次，最多{self.max_retries}次）...")
                self._wait()
                return self.get_creative_list(page, retry_count + 1)
            else:
                logger.error(f"已达到最大重试次数 {self.max_retries}，放弃重试")
                raise
        
        except Exception as e:
            logger.error(f"✗ 获取案例列表时发生未知异常")
            logger.error(f"  异常类型: {type(e).__name__}")
            logger.error(f"  异常消息: {str(e)}")
            import traceback
            logger.error(f"  异常堆栈:\n{traceback.format_exc()}")
            raise
    
    def get_creative_list_paginated(self, start_page: int = 0, max_pages: Optional[int] = 100, case_type: int = 1) -> List[Dict[str, Any]]:
        """
        分页获取所有案例列表
        
        Args:
            start_page: 起始页码
            max_pages: 最大页数，None 表示爬取到最后一页
            case_type: 案例类型（默认为1）
            
        Returns:
            所有案例的列表
            
        Note:
            **API限制**：使用 page 和 type 参数查询案例列表。
        """
        all_items = []
        page = start_page
        
        logger.info(f"开始分页获取案例列表 - 起始页={start_page}, 最大页数={max_pages}, 案例类型={case_type}")
        
        # 如果 max_pages 为 None，表示爬取到最后一页
        if max_pages is None:
            # 无限循环，直到没有更多数据
            while True:
                try:
                    # 获取当前页数据
                    data = self.get_creative_list(page, case_type=case_type)
                    
                    # 解析返回数据
                    if isinstance(data, dict):
                        # 检查数据结构
                        if 'data' in data and isinstance(data['data'], dict):
                            items = data['data'].get('items', [])
                            
                            if not items:
                                logger.info(f"第{page}页没有更多数据，停止获取")
                                break
                            
                            all_items.extend(items)
                            logger.info(f"第{page}页获取到 {len(items)} 个案例，累计 {len(all_items)} 个")
                            
                            # 检查是否还有下一页
                            current_page = data['data'].get('page')
                            if current_page is not None and str(current_page) == "0":
                                # 如果返回的page是"0"，可能表示没有更多数据
                                # 但需要根据实际API行为判断
                                pass
                        else:
                            logger.warning(f"第{page}页返回数据格式异常: {data}")
                            break
                    else:
                        logger.warning(f"第{page}页返回数据不是字典格式")
                        break
                    
                    # 等待后再请求下一页
                    self._wait()
                    page += 1
                    
                except Exception as e:
                    logger.error(f"获取第{page}页时发生错误: {e}")
                    # 可以选择继续或停止
                    # 这里选择停止，避免无限循环
                    break
        else:
            # max_pages 不为 None，有页数限制
            while page < start_page + max_pages:
                try:
                    # 获取当前页数据
                    data = self.get_creative_list(page, case_type=case_type)
                    
                    # 解析返回数据
                    if isinstance(data, dict):
                        # 检查数据结构
                        if 'data' in data and isinstance(data['data'], dict):
                            items = data['data'].get('items', [])
                            
                            if not items:
                                logger.info(f"第{page}页没有更多数据，停止获取")
                                break
                            
                            all_items.extend(items)
                            logger.info(f"第{page}页获取到 {len(items)} 个案例，累计 {len(all_items)} 个")
                            
                            # 检查是否还有下一页
                            current_page = data['data'].get('page')
                            if current_page is not None and str(current_page) == "0":
                                # 如果返回的page是"0"，可能表示没有更多数据
                                # 但需要根据实际API行为判断
                                pass
                        else:
                            logger.warning(f"第{page}页返回数据格式异常: {data}")
                            break
                    else:
                        logger.warning(f"第{page}页返回数据不是字典格式")
                        break
                    
                    # 等待后再请求下一页
                    self._wait()
                    page += 1
                    
                except Exception as e:
                    logger.error(f"获取第{page}页时发生错误: {e}")
                    # 可以选择继续或停止
                    # 这里选择停止，避免无限循环
                    break
        
        logger.info(f"分页获取完成，共获取 {len(all_items)} 个案例")
        return all_items
    
    def parse_case_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单个案例项，提取关键信息
        
        Args:
            item: API返回的案例项字典
            
        Returns:
            解析后的案例信息字典
        """
        parsed = {
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'case_id': item.get('id', ''),
            'thumb': item.get('thumb', ''),
            'score': item.get('score', 0),
            'score_decimal': item.get('score_decimal', '0.0'),
            'favourite': item.get('favourite', 0),
            'company_name': item.get('company_name', ''),
            'company_logo': item.get('company_logo', ''),
            'vip_img': item.get('vip_img', ''),
        }
        
        return parsed


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("广告门API客户端测试")
    print("=" * 60)
    
    try:
        # 创建API客户端
        client = AdquanAPIClient()
        
        # 测试获取第一页数据
        print("\n【测试1】获取第一页案例列表...")
        data = client.get_creative_list(page=0)
        
        print(f"✓ 请求成功")
        print(f"  返回数据类型: {type(data)}")
        
        if isinstance(data, dict):
            print(f"  返回数据键: {list(data.keys())}")
            
            if 'data' in data and isinstance(data['data'], dict):
                items = data['data'].get('items', [])
                print(f"  案例数量: {len(items)}")
                
                if items:
                    print(f"\n  第一个案例信息:")
                    first_item = client.parse_case_item(items[0])
                    for key, value in first_item.items():
                        print(f"    {key}: {value}")
        
        # 测试解析案例项
        if isinstance(data, dict) and 'data' in data:
            items = data['data'].get('items', [])
            if items:
                print(f"\n【测试2】解析案例项...")
                parsed = client.parse_case_item(items[0])
                print(f"✓ 解析成功")
                print(f"  案例标题: {parsed.get('title')}")
                print(f"  案例链接: {parsed.get('url')}")
        
        # 测试分页获取（只获取2页作为测试）
        print(f"\n【测试3】分页获取案例（测试2页）...")
        all_items = client.get_creative_list_paginated(start_page=0, max_pages=2, case_type=1)
        print(f"✓ 分页获取完成")
        print(f"  总共获取: {len(all_items)} 个案例")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

