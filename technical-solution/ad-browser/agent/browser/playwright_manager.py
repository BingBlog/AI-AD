"""Playwright 浏览器管理器

职责：
- 统一管理 Playwright 浏览器生命周期
- 提供 page 实例给外部使用
- 确保浏览器会话持续可用
"""

from __future__ import annotations

import asyncio
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class PlaywrightManager:
    """Playwright 浏览器管理器 - 确保 page 生命周期独立于 Agent"""
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._initialized = False
    
    async def initialize(self, headless: bool = False) -> Page:
        """初始化浏览器，返回 page 实例"""
        if self._initialized:
            return self._page
        
        try:
            logger.info("初始化 Playwright 浏览器...")
            self._playwright = await async_playwright().start()
            
            # 创建浏览器（使用 Chrome 而不是 Chromium，以保持登录状态）
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                channel="chrome",  # 使用系统安装的 Chrome 浏览器
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # 创建上下文
            self._context = await self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            # 创建页面
            self._page = await self._context.new_page()
            
            self._initialized = True
            logger.info(f"✅ Playwright 初始化完成，page URL: {self._page.url}")
            return self._page
            
        except Exception as e:
            logger.error(f"Playwright 初始化失败: {e}")
            await self.cleanup()
            raise
    
    @property
    def page(self) -> Optional[Page]:
        """获取当前 page 实例"""
        return self._page
    
    @property
    def browser(self) -> Optional[Browser]:
        """获取浏览器实例"""
        return self._browser
    
    @property
    def context(self) -> Optional[BrowserContext]:
        """获取浏览器上下文"""
        return self._context
    
    async def cleanup(self):
        """清理浏览器资源"""
        logger.info("清理 Playwright 浏览器资源...")
        
        if self._page:
            try:
                await self._page.close()
            except Exception as e:
                logger.debug(f"关闭 page 失败: {e}")
            self._page = None
        
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.debug(f"关闭 context 失败: {e}")
            self._context = None
        
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.debug(f"关闭 browser 失败: {e}")
            self._browser = None
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.debug(f"停止 playwright 失败: {e}")
            self._playwright = None
        
        self._initialized = False
        logger.info("✅ Playwright 资源清理完成")
    
    def __del__(self):
        """析构函数 - 确保资源被清理"""
        if self._initialized:
            # 异步清理需要在事件循环中执行
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.cleanup())
            except Exception:
                pass


# 全局单例
_playwright_manager = PlaywrightManager()


def get_playwright_manager() -> PlaywrightManager:
    """获取全局 Playwright 管理器实例"""
    return _playwright_manager