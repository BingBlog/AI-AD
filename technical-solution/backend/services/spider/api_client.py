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
from .list_page_html_parser import ListPageHTMLParser
from .proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class AdquanAPIClient:
    """广告门API客户端类"""
    
    def __init__(self, base_url: str = 'https://www.adquan.com/case_library/index', 
                 delay_range: tuple = (1, 3), max_retries: int = 3,
                 proxy_manager: Optional[ProxyManager] = None):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            delay_range: 请求延迟范围（秒），用于控制请求频率
            max_retries: 最大重试次数
            proxy_manager: 代理管理器实例（可选）
        """
        self.base_url = base_url
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.proxy_manager = proxy_manager
        
        # 创建Session
        self.session = requests.Session()
        
        # 创建CSRF Token管理器（先获取Token，此时使用HTML请求的headers）
        self.token_manager = CSRFTokenManager(base_url=base_url, session=self.session, proxy_manager=proxy_manager)
        
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
        api_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.adquan.com/case_library/index',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
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
    
    def _map_params(self, page: int, case_type: int = 1, **kwargs) -> Dict[str, Any]:
        """
        将旧参数格式映射到新参数格式
        
        Args:
            page: 页码（从 0 开始）
            case_type: 案例类型（兼容旧参数，映射到 typeclass）
            **kwargs: 其他参数（industry, typeclass, area, year, filter, keyword）
        
        Returns:
            新接口所需的参数字典
        """
        return {
            'page': page,
            'industry': kwargs.get('industry', 0),
            'typeclass': kwargs.get('typeclass', case_type),  # 兼容旧参数
            'area': kwargs.get('area', ''),
            'year': kwargs.get('year', 0),
            'filter': kwargs.get('filter', 0),
            'keyword': kwargs.get('keyword', ''),
        }
    
    def get_creative_list(self, page: int = 0, case_type: int = 1, retry_count: int = 0, **kwargs) -> Dict[str, Any]:
        """
        获取创意案例列表
        
        Args:
            page: 页码（从0开始）
            case_type: 案例类型（默认为1，兼容旧参数）
            retry_count: 当前重试次数（内部使用）
            **kwargs: 其他参数（industry, typeclass, area, year, filter, keyword）
            
        Returns:
            API返回的JSON数据字典，格式与旧接口保持一致
            
        Raises:
            requests.RequestException: 请求失败
            ValueError: 响应数据格式错误
            
        Note:
            **新接口**：返回的 data 字段是 HTML 字符串，需要解析后转换为原有格式。
        """
        # 准备请求参数（新接口格式）
        params = self._map_params(page, case_type, **kwargs)
        
        # 获取CSRF Token并添加到Headers
        # 如果Token获取失败，尝试刷新
        try:
            token_headers = self.token_manager.get_token_for_header()
        except ValueError:
            logger.warning("Token获取失败，尝试刷新...")
            token_headers = self.token_manager.get_token_for_header()  # 会触发刷新
        
        headers = {**self.session.headers, **token_headers}
        
        try:
            # 构建完整的请求URL（用于日志和调试）
            from urllib.parse import urlencode
            full_url = f"{self.base_url}?{urlencode(params)}"
            
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"API请求详情:")
            logger.info(f"  - 完整URL: {full_url}")
            logger.info(f"  - 基础URL: {self.base_url}")
            logger.info(f"  - 页码（内部）: {page} (API使用: {page + 1})")
            logger.info(f"  - 案例类型: {case_type}")
            logger.info(f"  - 请求参数: {params}")
            logger.info(f"  - 请求方法: GET")
            logger.info(f"  - 超时设置: 30 秒")
            logger.info(f"  - 重试次数: {retry_count}/{self.max_retries}")
            logger.info(f"  - 请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # 记录关键headers（不记录完整headers避免泄露敏感信息）
            logger.info(f"  - 关键Headers:")
            logger.info(f"    * User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
            logger.info(f"    * X-CSRF-TOKEN: {headers.get('X-CSRF-TOKEN', 'N/A')[:20]}...")
            logger.info(f"    * X-Requested-With: {headers.get('X-Requested-With', 'N/A')}")
            logger.info(f"    * Referer: {headers.get('Referer', 'N/A')}")
            
            # 发送请求
            request_start_time = time.time()
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                request_duration = time.time() - request_start_time
                
                # 记录成功的请求
                if self.proxy_manager:
                    self.proxy_manager.record_request(success=True)
            except Exception as e:
                request_duration = time.time() - request_start_time
                # 记录失败的请求并处理错误
                if self.proxy_manager:
                    self.proxy_manager.handle_error(e)
                raise
            
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
                        return self.get_creative_list(page, case_type, retry_count + 1, **kwargs)
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
            
            # 新接口：data 字段是 HTML 字符串，需要解析
            if isinstance(data, dict) and 'data' in data:
                html_content = data.get('data', '')
                
                if not html_content:
                    logger.warning(f"⚠️ API 返回的 data 字段为空")
                    return {
                        'code': 0,
                        'message': '请求成功',
                        'data': {
                            'items': [],
                            'page': page,
                        }
                    }
                
                # 检查 data 是字符串（HTML）还是字典（旧格式）
                if isinstance(html_content, str):
                    # 新接口：解析 HTML 字符串
                    logger.info(f"  - 检测到 HTML 格式响应，开始解析...")
                    logger.info(f"  - HTML 内容长度: {len(html_content)} 字符")
                    # 记录HTML内容的前500字符用于诊断
                    html_preview = html_content[:500] if len(html_content) > 500 else html_content
                    logger.info(f"  - HTML 内容预览（前500字符）: {html_preview}")
                    
                    try:
                        parser = ListPageHTMLParser(base_url='https://www.adquan.com')
                        items = parser.parse_html(html_content)
                        logger.info(f"  - HTML 解析完成，提取到 {len(items)} 个案例")
                        
                        # 如果解析结果为空，记录更详细的诊断信息和完整HTML
                        if not items:
                            logger.warning(f"⚠️ HTML 解析结果为空，可能的原因：")
                            logger.warning(f"   1. HTML 结构已变化，未找到 article_1 元素")
                            logger.warning(f"   2. HTML 内容不完整或格式错误")
                            logger.warning(f"   3. 该页确实没有数据")
                            # 检查HTML中是否包含 article_1
                            if 'article_1' not in html_content:
                                logger.warning(f"   - 诊断: HTML中未找到 'article_1' 字符串")
                            else:
                                logger.warning(f"   - 诊断: HTML中包含 'article_1' 字符串，但解析失败")
                            # 记录HTML中的关键元素
                            if '<div' in html_content:
                                div_count = html_content.count('<div')
                                logger.warning(f"   - HTML中包含 {div_count} 个 <div> 标签")
                            
                            # 记录完整HTML内容用于排查问题
                            logger.warning("=" * 80)
                            logger.warning("解析结果为空时的完整HTML内容（用于排查问题）:")
                            logger.warning("=" * 80)
                            html_len = len(html_content)
                            if html_len > 10000:
                                logger.warning(f"HTML内容长度: {html_len} 字符（超过10000，仅显示前后各5000字符）")
                                logger.warning("【HTML前5000字符】:")
                                logger.warning(html_content[:5000])
                                logger.warning("【HTML后5000字符】:")
                                logger.warning(html_content[-5000:])
                            else:
                                logger.warning(f"HTML内容长度: {html_len} 字符")
                                logger.warning(html_content)
                            logger.warning("=" * 80)
                        
                        # 转换为旧格式（保持向后兼容）
                        result = {
                            'code': 0,
                            'message': '请求成功',
                            'data': {
                                'items': items,
                                'page': page,
                            }
                        }
                        
                        logger.info(f"✓ API请求成功完成")
                        logger.info(f"  - 页码: {page}")
                        logger.info(f"  - 案例数量: {len(items)}")
                        
                        return result
                    except Exception as e:
                        logger.error(f"✗ HTML 解析失败: {e}")
                        logger.error(f"  - HTML 内容长度: {len(html_content)} 字符")
                        logger.error("=" * 80)
                        logger.error("解析异常时的完整HTML内容（用于排查问题）:")
                        logger.error("=" * 80)
                        html_len = len(html_content)
                        if html_len > 10000:
                            logger.error(f"HTML内容长度: {html_len} 字符（超过10000，仅显示前后各5000字符）")
                            logger.error("【HTML前5000字符】:")
                            logger.error(html_content[:5000])
                            logger.error("【HTML后5000字符】:")
                            logger.error(html_content[-5000:])
                        else:
                            logger.error(f"HTML内容长度: {html_len} 字符")
                            logger.error(html_content)
                        logger.error("=" * 80)
                        import traceback
                        logger.error(f"异常堆栈:\n{traceback.format_exc()}")
                        raise ValueError(f"HTML 解析失败: {e}")
                elif isinstance(html_content, dict):
                    # 旧接口格式（向后兼容）
                    logger.info(f"  - 检测到 JSON 格式响应（旧接口格式）")
                    items_count = len(html_content.get('items', []))
                    logger.info(f"  - items数量: {items_count}")
                    return data
                else:
                    logger.warning(f"  - 'data' 字段类型: {type(html_content).__name__}（期望字符串或字典）")
                    return data
            else:
                logger.warning(f"  - 响应中未找到 'data' 字段")
                return data
            
        except requests.RequestException as e:
            logger.error(f"✗ HTTP请求异常")
            logger.error(f"  异常类型: {type(e).__name__}")
            logger.error(f"  异常消息: {str(e)}")
            
            # 处理代理错误
            if self.proxy_manager:
                self.proxy_manager.handle_error(e)
            
            # 如果是网络错误且未达到最大重试次数，进行重试
            if retry_count < self.max_retries:
                logger.info(f"准备重试请求（第{retry_count + 1}次，最多{self.max_retries}次）...")
                self._wait()
                return self.get_creative_list(page, case_type, retry_count + 1, **kwargs)
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

