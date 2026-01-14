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

logger = logging.getLogger(__name__)


class CSRFTokenManager:
    """CSRF Token管理器类"""
    
    def __init__(self, base_url: str = 'https://m.adquan.com/creative', session: Optional[requests.Session] = None):
        """
        初始化CSRF Token管理器
        
        Args:
            base_url: 基础URL，用于获取Token的HTML页面
            session: requests.Session实例，如果为None则创建新的
        """
        self.base_url = base_url
        self.session = session or requests.Session()
        self._token: Optional[str] = None
        self._token_fetch_time: Optional[float] = None
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
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
        
        # 获取新Token
        self._fetch_token()
        
        if not self._token:
            raise ValueError("无法从HTML页面提取CSRF Token")
        
        return self._token
    
    def _fetch_token(self) -> None:
        """
        从HTML页面获取CSRF Token
        内部方法，不对外暴露
        """
        try:
            logger.info(f"正在访问 {self.base_url} 获取CSRF Token...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 从meta标签提取Token
            csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})
            
            if csrf_meta and csrf_meta.get('content'):
                self._token = csrf_meta.get('content')
                self._token_fetch_time = time.time()
                logger.info(f"成功获取CSRF Token: {self._token[:20]}...")
            else:
                logger.error("在HTML页面中未找到CSRF Token meta标签")
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


