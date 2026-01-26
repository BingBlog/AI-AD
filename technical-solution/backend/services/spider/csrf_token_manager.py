#!/usr/bin/env python3
"""
CSRF Token管理器
负责从广告门网站获取和管理CSRF Token
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional
import time
import base64
import json
import binascii
from .proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class CSRFTokenManager:
    """CSRF Token管理器类"""
    
    def __init__(self, base_url: str = 'https://www.adquan.com/case_library/index', 
                 session: Optional[requests.Session] = None,
                 proxy_manager: Optional[ProxyManager] = None):
        """
        初始化CSRF Token管理器
        
        Args:
            base_url: 基础URL，用于获取Token的HTML页面
            session: requests.Session实例，如果为None则创建新的
            proxy_manager: 代理管理器实例（可选）
        """
        self.base_url = base_url
        self._session = session or requests.Session()
        self._token: Optional[str] = None
        self._token_fetch_time: Optional[float] = None
        self.proxy_manager = proxy_manager
        
        # 设置默认请求头（桌面端浏览器）
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        获取CSRF Token
        
        Args:
            force_refresh: 是否强制刷新Token
            
        Returns:
            CSRF Token字符串
            
        Raises:
            ValueError: 如果无法获取Token
        """
        # 如果已有Token且不强制刷新，直接返回
        if self._token and not force_refresh:
            return self._token
        
        # 优先从 Cookie 中提取 XSRF-TOKEN
        cookie_token = self._extract_csrf_from_cookie()
        if cookie_token:
            self._token = cookie_token
            self._token_fetch_time = time.time()
            logger.info(f"从 Cookie 中成功提取 CSRF Token: {cookie_token[:20]}...")
            return cookie_token
        
        # 如果 Cookie 中没有，则从 HTML 页面获取
        self._fetch_token()
        
        if not self._token:
            raise ValueError("无法获取CSRF Token")
        
        return self._token
    
    def _extract_csrf_from_cookie(self) -> Optional[str]:
        """
        从 Cookie 中提取并解析 XSRF-TOKEN
        
        Returns:
            CSRF Token 字符串，如果提取失败则返回 None
        """
        try:
            # 从 session.cookies 中获取 XSRF-TOKEN
            xsrf_token = None
            for cookie in self._session.cookies:
                if cookie.name == 'XSRF-TOKEN':
                    xsrf_token = cookie.value
                    break
            
            if not xsrf_token:
                logger.debug("Cookie 中未找到 XSRF-TOKEN，将尝试从 HTML 页面获取")
                return None
            
            # Laravel 的 XSRF-TOKEN 可能是 base64 编码的 JSON
            # 格式: {"iv":"...","value":"...","mac":"..."}
            # 需要解码并提取实际的 token 值
            try:
                # URL 解码（Laravel 使用 URL-safe base64）
                # 补全 padding
                padding = 4 - len(xsrf_token) % 4
                if padding != 4:
                    xsrf_token += '=' * padding
                
                decoded = base64.urlsafe_b64decode(xsrf_token)
                token_data = json.loads(decoded.decode('utf-8'))
                
                # 提取实际的 token 值
                actual_token = token_data.get('value', '')
                
                if actual_token:
                    logger.debug(f"成功从 Cookie 中解析 CSRF Token")
                    return actual_token
                else:
                    logger.warning("XSRF-TOKEN 中未找到 value 字段")
                    # 如果解析失败，尝试直接使用原始值（某些情况下可能直接是 token）
                    return xsrf_token
                    
            except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.debug(f"解析 XSRF-TOKEN 失败: {e}，尝试直接使用原始值")
                # 如果解析失败，尝试直接使用原始值（某些情况下可能直接是 token）
                return xsrf_token
                
        except Exception as e:
            logger.warning(f"提取 CSRF Token 时发生错误: {e}")
            return None
    
    def _fetch_token(self) -> None:
        """
        从HTML页面获取CSRF Token
        内部方法，不对外暴露
        """
        try:
            logger.info(f"正在访问 {self.base_url} 获取CSRF Token...")
            try:
                response = self._session.get(self.base_url, timeout=30)
                response.raise_for_status()
                
                # 记录成功的请求
                if self.proxy_manager:
                    self.proxy_manager.record_request(success=True)
            except Exception as e:
                # 记录失败的请求并处理错误
                if self.proxy_manager:
                    self.proxy_manager.handle_error(e)
                raise
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 从meta标签提取Token
            csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})
            
            if csrf_meta and csrf_meta.get('content'):
                self._token = csrf_meta.get('content')
                self._token_fetch_time = time.time()
                logger.info(f"从 HTML 页面成功获取CSRF Token: {self._token[:20]}...")
            else:
                logger.warning("在HTML页面中未找到CSRF Token meta标签，尝试从 Cookie 中提取")
                # 尝试从 Cookie 中提取（可能在访问页面后 Cookie 已更新）
                cookie_token = self._extract_csrf_from_cookie()
                if cookie_token:
                    self._token = cookie_token
                    self._token_fetch_time = time.time()
                    logger.info(f"从 Cookie 中成功获取CSRF Token: {cookie_token[:20]}...")
                else:
                    logger.error("无法从 HTML 页面或 Cookie 中获取 CSRF Token")
                    self._token = None
                    self._token_fetch_time = None
                
        except requests.RequestException as e:
            logger.error(f"请求HTML页面失败: {e}")
            self._token = None
            self._token_fetch_time = None
            raise
        except Exception as e:
            logger.error(f"提取CSRF Token时发生错误: {e}")
            self._token = None
            self._token_fetch_time = None
            raise
    
    def refresh_token(self) -> str:
        """
        强制刷新CSRF Token
        
        Returns:
            新的CSRF Token字符串
        """
        logger.info("强制刷新CSRF Token...")
        return self.get_token(force_refresh=True)
    
    def get_token_for_header(self) -> dict:
        """
        获取用于HTTP请求头的Token字典
        
        Returns:
            包含X-CSRF-TOKEN的字典，可直接用于requests的headers参数
        """
        token = self.get_token()
        return {'X-CSRF-TOKEN': token}
    
    def is_token_valid(self) -> bool:
        """
        检查当前Token是否有效（是否存在）
        
        Returns:
            True如果Token存在，False否则
        """
        return self._token is not None and len(self._token) > 0
    
    def get_token_age(self) -> Optional[float]:
        """
        获取Token的年龄（秒）
        
        Returns:
            Token年龄（秒），如果Token不存在则返回None
        """
        if self._token_fetch_time is None:
            return None
        return time.time() - self._token_fetch_time
    
    def handle_token_error(self, response: requests.Response) -> bool:
        """
        处理Token相关的错误响应
        如果检测到Token失效（401/403），自动刷新Token
        
        Args:
            response: HTTP响应对象
            
        Returns:
            True如果检测到Token错误并已刷新，False否则
        """
        # 检查是否是Token相关的错误
        if response.status_code in (401, 403):
            logger.warning(f"检测到HTTP {response.status_code}错误，可能是CSRF Token失效，尝试刷新...")
            try:
                self.refresh_token()
                return True
            except Exception as e:
                logger.error(f"刷新Token失败: {e}")
                return False
        
        # 检查响应内容中是否包含Token错误信息
        try:
            if hasattr(response, 'text') and response.text:
                error_indicators = ['csrf', 'token', 'unauthorized', 'forbidden']
                response_lower = response.text.lower()
                if any(indicator in response_lower for indicator in error_indicators):
                    logger.warning("响应内容中可能包含Token错误信息，尝试刷新Token...")
                    try:
                        self.refresh_token()
                        return True
                    except Exception as e:
                        logger.error(f"刷新Token失败: {e}")
                        return False
        except Exception:
            pass
        
        return False
    
    @property
    def token(self) -> Optional[str]:
        """
        Token属性，只读访问
        
        Returns:
            当前Token值，如果不存在则返回None
        """
        return self._token
    
    @property
    def session(self) -> requests.Session:
        """
        Session属性，用于访问底层的requests.Session
        
        Returns:
            requests.Session实例
        """
        return self._session
    
    @session.setter
    def session(self, value: requests.Session):
        """设置Session"""
        self._session = value


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("CSRF Token管理器测试")
    print("=" * 60)
    
    try:
        # 创建Token管理器
        token_manager = CSRFTokenManager()
        
        # 获取Token
        token = token_manager.get_token()
        print(f"\n✓ 成功获取Token: {token}")
        print(f"  Token长度: {len(token)} 字符")
        print(f"  Token是否有效: {token_manager.is_token_valid()}")
        
        # 获取用于请求头的格式
        headers = token_manager.get_token_for_header()
        print(f"\n✓ 请求头格式: {headers}")
        
        # 测试Token年龄
        age = token_manager.get_token_age()
        if age is not None:
            print(f"\n✓ Token年龄: {age:.2f} 秒")
        
        # 测试刷新Token
        print("\n测试刷新Token...")
        new_token = token_manager.refresh_token()
        print(f"✓ 刷新后的Token: {new_token}")
        print(f"  是否相同: {token == new_token}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


