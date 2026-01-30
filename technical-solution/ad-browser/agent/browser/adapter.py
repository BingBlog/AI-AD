"""agent.browser.adapter

Browser-Use Adapter

职责：
- 封装 browser-use 原始调用
- 固定并管理 Prompt（不暴露自由 Prompt）
- 提供动作级 API
- 标准化返回结果（第 10 节）
"""

from __future__ import annotations

import asyncio
import inspect
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from playwright.async_api import Page
from agent.config import settings
from agent.exceptions import BrowserAdapterException
from agent.utils.logger import get_logger

from .actions import BrowserActions

# Playwright 相关导入
try:
    from playwright.async_api import Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = BrowserContext = Page = Any

logger = get_logger(__name__)


EXECUTION_PREAMBLE = """\
Perform only the requested action.
Do not explain.
Do not add extra steps.
"""


@dataclass
class BrowserUseResult:
    success: bool
    meta: Dict[str, Any]
    content: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "meta": self.meta,
            "content": self.content,
            "error": self.error,
        }


Runner = Callable[[str], Awaitable[Any]]


class BrowserAdapter(BrowserActions):
    """Browser-Use Adapter（可注入 runner，便于测试）"""

    def __init__(self, runner: Optional[Runner] = None, page: Optional[Page] = None):
        self._runner = runner
        self._agent = None  # 共享的 Agent 实例
        self._llm = None  # 共享的 LLM 实例
        self._page = page  # Playwright Page 实例（外部注入）
        self._browser = None  # Playwright Browser 实例
        self._context = None  # Playwright BrowserContext 实例
        self._own_browser = False  # 标记是否由我们自己创建 browser

    def _build_task(self, action_instruction: str) -> str:
        return f"{EXECUTION_PREAMBLE}\n\n{action_instruction}".strip()

    def _get_llm(self):
        """获取或创建 LLM 实例（单例）"""
        if self._llm is None:
            try:
                from browser_use.llm import ChatDeepSeek  # type: ignore
                self._llm = ChatDeepSeek(
                    base_url=settings.deepseek_base_url,
                    model=settings.deepseek_model,
                    api_key=settings.deepseek_api_key,
                )
            except Exception:
                try:
                    from langchain_openai import ChatOpenAI  # type: ignore
                    self._llm = ChatOpenAI(
                        model=settings.deepseek_model,
                        base_url=settings.deepseek_base_url,
                        api_key=settings.deepseek_api_key,
                        temperature=0,
                    )
                except Exception as e:  # pragma: no cover
                    raise BrowserAdapterException(f"LLM 初始化失败（ChatDeepSeek/ChatOpenAI 均不可用）: {e}", action="init")
        return self._llm

    async def _ensure_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """
        确保有可用的浏览器会话
        
        Returns:
            (browser, context, page) 三元组
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserAdapterException("Playwright 未安装", action="init")
        
        # 如果已经有 page，直接返回
        if self._page and self._context and self._browser:
            return self._browser, self._context, self._page
        
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise BrowserAdapterException(f"无法导入 playwright: {e}", action="init")
        
        # 创建新的浏览器会话（使用 Chrome 而不是 Chromium，以保持登录状态）
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # 需要可视化处理登录
            channel="chrome",  # 使用系统安装的 Chrome 浏览器
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # 保存引用
        self._browser = browser
        self._context = context
        self._page = page
        self._own_browser = True
        
        logger.info("✅ 创建新的浏览器会话")
        return browser, context, page

    async def _create_agent_with_page(self, task: str, page: Page) -> Any:
        """
        创建 browser-use Agent，使用现有的 page
        
        ⚠️ 重要：browser-use Agent 可能不支持直接注入 page
        ⚠️ 如果注入失败，我们使用 Playwright 直接执行操作，不使用 Agent
        
        Args:
            task: 任务描述
            page: 现有的 Playwright Page 实例
            
        Returns:
            Agent 实例（如果成功）或 None（如果不需要 Agent）
        """
        try:
            from browser_use import Agent  # type: ignore
        except Exception as e:  # pragma: no cover
            raise BrowserAdapterException(f"无法导入 browser_use.Agent: {e}", action="init")
        
        llm = self._get_llm()
        
        # 尝试多种方式创建 Agent 并注入 page
        # 方法 1: 尝试使用 page 参数（如果 Agent 支持）
        try:
            agent = Agent(task=task, llm=llm, use_vision=False, page=page)
            logger.info("✅ 使用 page 参数创建 Agent")
            return agent
        except (TypeError, ValueError) as e:
            logger.debug(f"Agent 不支持 page 参数: {e}")
        
        # 方法 2: 创建 Agent 后尝试注入 page
        try:
            agent = Agent(task=task, llm=llm, use_vision=False)
            
            # 尝试直接设置 page
            if hasattr(agent, 'page'):
                agent.page = page
                logger.info("✅ 直接注入 page 到 Agent.page")
                return agent
            
            # 尝试注入到 browser_context
            if hasattr(agent, 'browser_context') and agent.browser_context:
                if hasattr(agent.browser_context, 'page'):
                    agent.browser_context.page = page
                    logger.info("✅ 注入 page 到 Agent.browser_context.page")
                    return agent
                elif hasattr(agent.browser_context, 'pages'):
                    # 尝试添加到 pages 列表
                    try:
                        agent.browser_context.pages.append(page)
                        logger.info("✅ 添加 page 到 Agent.browser_context.pages")
                        return agent
                    except Exception:
                        pass
            
            # 如果所有注入方式都失败，返回 None
            # 调用者应该使用 Playwright 直接操作
            logger.warning("⚠️ 无法将 page 注入 Agent，将使用 Playwright 直接操作")
            return None
            
        except Exception as e:
            logger.error(f"创建 Agent 失败: {e}")
            return None

    async def _default_runner(self, task: str) -> Any:
        """
        默认 runner：使用 browser_use.Agent 执行 task。
        
        ⚠️ 重要：现在使用 Playwright 主导模式
        ⚠️ 先确保有 page，再尝试创建 Agent 执行任务
        ⚠️ 如果 Agent 无法注入 page，回退到 Playwright 直接操作
        """
        # 确保有可用的浏览器会话
        browser, context, page = await self._ensure_browser()
        
        # 尝试创建 Agent 并注入 page
        agent = await self._create_agent_with_page(task, page)
        
        if agent is None:
            # Agent 无法注入 page，使用 Playwright 直接执行
            logger.info("⚠️ Agent 无法使用我们的 page，使用 Playwright 直接执行任务")
            return await self._execute_with_playwright(task, page)
        
        # 保存 Agent 引用（用于调试）
        self._agent = agent
        
        try:
            # 执行任务
            run_fn = getattr(agent, "run", None)
            if run_fn is None:
                raise BrowserAdapterException("browser_use.Agent 缺少 run()", action="init")
            result = run_fn()
            
            # 等待任务完成（如果是异步的）
            if hasattr(result, "__await__"):
                result = await result
            
            # 注意：不再尝试从 Agent 获取 page，因为我们自己管理 page
            logger.info("✅ Agent 任务完成，page 仍然可用")
            
            return result
        except Exception as e:
            logger.warning(f"Agent 执行失败，回退到 Playwright: {e}")
            # 回退到 Playwright 直接操作
            return await self._execute_with_playwright(task, page)
    
    async def _execute_with_playwright(self, task: str, page: Page) -> str:
        """
        使用 Playwright 直接执行任务（不使用 Agent）
        
        Args:
            task: 任务描述
            page: Playwright Page 实例
            
        Returns:
            执行结果
        """
        # 简单解析任务类型
        task_lower = task.lower()
        
        if "open the page:" in task_lower or "open page:" in task_lower:
            # 提取 URL
            url_match = re.search(r'(?:open the page:|open page:)\s*(https?://[^\s]+)', task, re.IGNORECASE)
            if url_match:
                url = url_match.group(1)
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=5000)
                return f"成功打开页面: {url}"
        
        # 其他任务类型暂时返回提示
        logger.warning(f"Playwright 直接执行不支持的任务类型: {task[:50]}")
        return f"任务已接收: {task[:100]}"
    
    async def _try_save_page(self, agent):
        """
        尝试从 Agent 获取并保存 page 实例
        
        ⚠️ 关键：这是唯一一次获取 page 的机会
        ⚠️ 后续所有操作必须使用这个 page，不能创建新的 Agent
        """
        try:
            logger.info(f"尝试保存 page 实例，agent 类型: {type(agent)}")
            
            # 方法 1：直接通过 browser_context 获取（最直接的方法）
            if hasattr(agent, "browser_context") and agent.browser_context:
                logger.info(f"agent.browser_context 类型: {type(agent.browser_context)}")
                
                # 检查 browser_context 是否有 get_page 方法
                if hasattr(agent.browser_context, "get_page"):
                    try:
                        page_fn = agent.browser_context.get_page
                        # 正确检查协程函数：使用 inspect.iscoroutinefunction
                        if inspect.iscoroutinefunction(page_fn):
                            page = await page_fn()
                        elif inspect.iscoroutine(page_fn):
                            # 如果已经是协程对象，直接 await
                            page = await page_fn
                        else:
                            page = page_fn()
                        if page:
                            self._page = page
                            try:
                                current_url = page.url
                            except:
                                current_url = 'N/A'
                            logger.info(f"✅ 已保存 page 实例（从 browser_context.get_page()），当前 URL: {current_url}")
                            return
                    except Exception as e:
                        logger.debug(f"browser_context.get_page() 失败: {e}")
                
                # 检查 browser_context.pages
                if hasattr(agent.browser_context, "pages"):
                    pages = agent.browser_context.pages
                    logger.info(f"browser_context.pages 类型: {type(pages)}, 数量: {len(pages) if pages else 0}")
                    if pages and len(pages) > 0:
                        self._page = pages[-1]
                        try:
                            current_url = self._page.url
                        except:
                            current_url = 'N/A'
                        logger.info(f"✅ 已保存 page 实例（从 browser_context.pages），当前 URL: {current_url}")
                        return
                
                # 检查 browser_context 是否有 playwright_context
                if hasattr(agent.browser_context, "playwright_context"):
                    playwright_context = agent.browser_context.playwright_context
                    if playwright_context and hasattr(playwright_context, "pages"):
                        pages = playwright_context.pages
                        logger.info(f"playwright_context.pages 数量: {len(pages) if pages else 0}")
                        if pages and len(pages) > 0:
                            self._page = pages[-1]
                            try:
                                current_url = self._page.url
                            except:
                                current_url = 'N/A'
                            logger.info(f"✅ 已保存 page 实例（从 playwright_context.pages），当前 URL: {current_url}")
                            return
            
            # 方法 2：通过 browser 获取
            if hasattr(agent, "browser") and agent.browser:
                logger.info(f"agent.browser 类型: {type(agent.browser)}")
                
                # 检查 browser 是否有 get_playwright_browser 方法
                if hasattr(agent.browser, "get_playwright_browser"):
                    try:
                        playwright_browser_fn = agent.browser.get_playwright_browser
                        # 正确检查协程函数：使用 inspect.iscoroutinefunction
                        # 如果检查失败，尝试直接 await（更安全的备用方案）
                        try:
                            if inspect.iscoroutinefunction(playwright_browser_fn):
                                playwright_browser = await playwright_browser_fn()
                            elif inspect.iscoroutine(playwright_browser_fn):
                                # 如果已经是协程对象，直接 await
                                playwright_browser = await playwright_browser_fn
                            else:
                                playwright_browser = playwright_browser_fn()
                        except TypeError:
                            # 如果 inspect 检查失败，尝试直接 await
                            try:
                                playwright_browser = await playwright_browser_fn()
                            except TypeError:
                                # 如果不是协程，直接调用
                                playwright_browser = playwright_browser_fn()
                        
                        if playwright_browser and hasattr(playwright_browser, "contexts"):
                            contexts = playwright_browser.contexts
                            logger.info(f"playwright_browser.contexts 数量: {len(contexts) if contexts else 0}")
                            if contexts and len(contexts) > 0:
                                last_context = contexts[-1]
                                if hasattr(last_context, "pages"):
                                    pages = last_context.pages
                                    logger.info(f"context.pages 数量: {len(pages) if pages else 0}")
                                    if pages and len(pages) > 0:
                                        self._page = pages[-1]
                                        try:
                                            current_url = self._page.url
                                        except:
                                            current_url = 'N/A'
                                        logger.info(f"✅ 已保存 page 实例（从 playwright_browser.contexts），当前 URL: {current_url}")
                                        return
                    except Exception as e:
                        logger.debug(f"get_playwright_browser() 失败: {e}")
                
                # 检查 browser.playwright_browser 属性
                if hasattr(agent.browser, "playwright_browser") and agent.browser.playwright_browser:
                    try:
                        playwright_browser = agent.browser.playwright_browser
                        if hasattr(playwright_browser, "contexts"):
                            contexts = playwright_browser.contexts
                            if contexts and len(contexts) > 0:
                                last_context = contexts[-1]
                                if hasattr(last_context, "pages"):
                                    pages = last_context.pages
                                    if pages and len(pages) > 0:
                                        self._page = pages[-1]
                                        try:
                                            current_url = self._page.url
                                        except:
                                            current_url = 'N/A'
                                        logger.info(f"✅ 已保存 page 实例（从 playwright_browser 属性），当前 URL: {current_url}")
                                        return
                    except Exception as e:
                        logger.debug(f"playwright_browser 属性访问失败: {e}")
            
            # 方法 3：直接检查 agent.page
            if hasattr(agent, "page") and agent.page:
                self._page = agent.page
                try:
                    current_url = self._page.url
                except:
                    current_url = 'N/A'
                logger.info(f"✅ 已保存 page 实例（从 agent.page），当前 URL: {current_url}")
                return
            
            logger.warning("❌ 无法从 Agent 获取 page 实例")
            # 输出 agent 的所有属性以便调试
            logger.debug(f"agent 属性: {[attr for attr in dir(agent) if not attr.startswith('_')][:20]}")
        except Exception as e:
            logger.error(f"无法从 Agent 获取 page: {e}", exc_info=True)

    def _standardize(
        self,
        *,
        raw: Any,
        url: str = "",
        title: str = "",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        # browser_use 结果结构不稳定，这里统一将其字符串化放到 text
        text = "" if raw is None else (raw if isinstance(raw, str) else str(raw))
        return BrowserUseResult(
            success=error is None,
            meta={"url": url, "title": title},
            content={"text": text},
            error=error,
        ).to_dict()

    async def _run_action(self, action: str, *, action_name: str, url: str = "") -> Dict[str, Any]:
        task = self._build_task(action)
        runner = self._runner or self._default_runner
        try:
            raw = await runner(task)
            return self._standardize(raw=raw, url=url)
        except Exception as e:
            raise BrowserAdapterException(str(e), action=action_name, url=url)

    async def open_page(self, url: str) -> Dict[str, Any]:
        """
        打开页面（Playwright 主导模式）
        
        Args:
            url: 要打开的 URL
            
        Returns:
            操作结果
        """
        try:
            # 确保有可用的浏览器会话
            browser, context, page = await self._ensure_browser()
            
            # 使用 Playwright 直接打开页面
            logger.info(f"使用 Playwright 打开页面: {url}")
            # 使用更宽松的等待策略，避免超时
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except Exception as goto_error:
                # 如果 domcontentloaded 超时，尝试使用 commit 或更宽松的条件
                logger.warning(f"domcontentloaded 超时，尝试使用更宽松的等待策略: {goto_error}")
                try:
                    await page.goto(url, wait_until='commit', timeout=30000)
                except Exception:
                    # 如果还是失败，至少尝试导航（不等待）
                    await page.goto(url, wait_until='load', timeout=30000)
            
            # 等待页面加载（使用更宽松的条件）
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except Exception:
                # 如果 networkidle 超时，尝试 domcontentloaded
                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=5000)
                except Exception:
                    # 如果还是超时，至少等待一小段时间
                    await asyncio.sleep(2)
            
            # 检测是否需要登录
            login_required = await self.check_login_required()
            if login_required:
                logger.info("检测到需要登录，等待用户扫码登录...")
                await self.wait_for_login()
                logger.info("用户登录完成，继续执行任务")
            
            return self._standardize(
                raw=f"成功打开页面: {url}",
                url=page.url,
                title=await page.title()
            )
            
        except Exception as e:
            logger.error(f"打开页面失败: {e}")
            raise BrowserAdapterException(f"打开页面失败: {e}", action="open_page", url=url)
    
    async def check_login_required(self) -> bool:
        """
        检测页面是否需要登录
        
        Returns:
            True 如果需要登录，False 如果已登录或不需要登录
        """
        if self._page is None:
            return False
        
        try:
            # 等待页面加载
            await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
            
            # 小红书登录检测：检查是否有登录弹窗、二维码或登录按钮
            login_indicators = [
                # 登录弹窗
                '.login-container',
                '.login-box',
                '.login-modal',
                '[class*="login"]',
                # 二维码登录
                '.qrcode',
                '.qr-code',
                '[class*="qrcode"]',
                # 登录按钮
                'button:has-text("登录")',
                'a:has-text("登录")',
                # 小红书特定的登录元素
                '.reds-icon-close',  # 登录弹窗的关闭按钮
            ]
            
            for selector in login_indicators:
                try:
                    element = await self._page.query_selector(selector)
                    if element:
                        # 检查元素是否可见
                        is_visible = await element.is_visible()
                        if is_visible:
                            logger.info(f"检测到登录元素: {selector}")
                            return True
                except Exception:
                    continue
            
            # 检查页面 URL 是否包含登录相关路径
            current_url = self._page.url
            if any(keyword in current_url.lower() for keyword in ['login', 'signin', 'auth']):
                logger.info(f"检测到登录相关 URL: {current_url}")
                return True
            
            # 检查页面文本中是否包含登录提示
            try:
                body_text = await self._page.inner_text("body")
                login_keywords = ['请登录', '扫码登录', '立即登录', '登录后查看']
                if any(keyword in body_text for keyword in login_keywords):
                    logger.info("检测到登录提示文本")
                    return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            logger.warning(f"检测登录状态时出错: {e}")
            return False
    
    async def wait_for_login(self, timeout: int = 300) -> None:
        """
        等待用户完成登录
        
        Args:
            timeout: 超时时间（秒），默认 5 分钟
        """
        if self._page is None:
            raise BrowserAdapterException("Page 实例不存在", action="wait_for_login")
        
        logger.info(f"等待用户登录，超时时间: {timeout} 秒")
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查是否已登录（登录元素消失）
            login_required = await self.check_login_required()
            if not login_required:
                logger.info("检测到用户已登录")
                # 等待页面稳定
                await asyncio.sleep(2)
                return
            
            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise BrowserAdapterException(
                    f"等待登录超时（{timeout} 秒），请稍后重试",
                    action="wait_for_login"
                )
            
            # 等待一段时间后再次检查
            await asyncio.sleep(2)

    async def search(self, query: str) -> Dict[str, Any]:
        """
        搜索关键词（使用 Playwright 直接操作，保持浏览器上下文）
        
        ⚠️ 重要：不能使用 browser-use Agent，必须使用 Playwright API
        """
        # #region debug log
        import json
        import time
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "hypothesisId": "C",
                    "location": "adapter.py:587",
                    "message": "search() method called",
                    "data": {
                        "query": query,
                        "pageExists": self._page is not None,
                        "currentUrl": self._page.url if self._page else "N/A"
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        if self._page is None:
            raise BrowserAdapterException(
                "Page 实例不存在，请先调用 open_page() 打开页面",
                action="search"
            )
        
        # 直接使用 Playwright 搜索
        result = await self._search_with_playwright(query)
        
        # #region debug log
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "hypothesisId": "C",
                    "location": "adapter.py:610",
                    "message": "search() method completed",
                    "data": {
                        "resultSuccess": result.get("success"),
                        "resultError": result.get("error"),
                        "currentUrl": self._page.url if self._page else "N/A"
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        return result
    
    async def _get_page_from_agent(self):
        """从 Agent 获取 Playwright Page 实例"""
        if self._agent is None:
            return None
        try:
            # browser-use Agent 可能有 browser 或 page 属性
            if hasattr(self._agent, "browser") and hasattr(self._agent.browser, "pages"):
                pages = self._agent.browser.pages
                if pages:
                    return pages[-1]  # 返回最后一个页面
            if hasattr(self._agent, "page"):
                return self._agent.page
            if hasattr(self._agent, "context") and hasattr(self._agent.context, "pages"):
                pages = self._agent.context.pages
                if pages:
                    return pages[-1]
        except Exception as e:
            logger.debug(f"无法从 Agent 获取 page: {e}")
        return None
    
    async def _search_with_playwright(self, query: str) -> Dict[str, Any]:
        """使用 Playwright 直接搜索"""
        # #region debug log
        import json
        import time
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "hypothesisId": "C",
                    "location": "adapter.py:625",
                    "message": "_search_with_playwright() started",
                    "data": {
                        "query": query,
                        "currentUrl": self._page.url if self._page else "N/A"
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        try:
            # 等待页面加载（使用更宽松的条件，避免超时）
            try:
                await self._page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                # 如果 networkidle 超时，尝试 domcontentloaded（更宽松）
                try:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    # 如果还是超时，至少等待一小段时间让页面稳定
                    await asyncio.sleep(1)
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "adapter.py:650",
                        "message": "Starting to find search input",
                        "data": {
                            "currentUrl": self._page.url if self._page else "N/A"
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 尝试多种方式找到搜索框
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="搜索"]',
                'input[placeholder*="Search"]',
                'input[class*="search"]',
                'input[id*="search"]',
                'input[name*="search"]',
                '.search-input input',
                '#search-input',
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self._page.wait_for_selector(selector, timeout=2000, state="visible")
                    if search_input:
                        # #region debug log
                        try:
                            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "run3",
                                    "hypothesisId": "C",
                                    "location": "adapter.py:670",
                                    "message": "Found search input",
                                    "data": {
                                        "selector": selector
                                    },
                                    "timestamp": int(time.time() * 1000)
                                }) + '\n')
                        except Exception:
                            pass
                        # #endregion
                        break
                except Exception:
                    continue
            
            if not search_input:
                # 如果找不到搜索框，回退到 Agent
                logger.warning("未找到搜索框，回退到 Agent")
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run3",
                            "hypothesisId": "C",
                            "location": "adapter.py:680",
                            "message": "Search input not found, falling back to Agent",
                            "data": {},
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                return await self._run_action(
                    f"On the current page, find and use the search box to search for: {query}.",
                    action_name="search",
                )
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "adapter.py:690",
                        "message": "Filling search input",
                        "data": {
                            "query": query,
                            "currentUrl": self._page.url
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 清空并输入搜索关键词
            await search_input.fill("")
            await search_input.fill(query)
            
            # 尝试多种方式触发搜索
            # 方法1: 按Enter键
            await search_input.press("Enter")
            await asyncio.sleep(1)  # 等待一下看是否有反应
            
            # 检查URL是否改变（小红书搜索结果URL格式：/search_result?keyword=...）
            await asyncio.sleep(1)  # 等待一下让页面响应
            current_url = self._page.url
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "adapter.py:710",
                        "message": "After pressing Enter",
                        "data": {
                            "currentUrl": current_url,
                            "urlChanged": "search_result" in current_url
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            # 如果URL没有改变到搜索结果页，尝试点击搜索按钮或直接导航
            if "search_result" not in current_url:
                logger.info("按Enter后URL未改变，尝试点击搜索按钮")
                # 尝试找到搜索按钮
                search_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("搜索")',
                    'button:has-text("Search")',
                    '.search-button',
                    '.search-btn',
                    '[class*="search-button"]',
                    '[class*="search-btn"]',
                ]
                
                for btn_selector in search_button_selectors:
                    try:
                        search_button = await self._page.wait_for_selector(btn_selector, timeout=1000, state="visible")
                        if search_button:
                            await search_button.click()
                            await asyncio.sleep(1)
                            current_url = self._page.url
                            # #region debug log
                            try:
                                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({
                                        "sessionId": "debug-session",
                                        "runId": "run3",
                                        "hypothesisId": "C",
                                        "location": "adapter.py:735",
                                        "message": "After clicking search button",
                                        "data": {
                                            "buttonSelector": btn_selector,
                                            "currentUrl": current_url
                                        },
                                        "timestamp": int(time.time() * 1000)
                                    }) + '\n')
                            except Exception:
                                pass
                            # #endregion
                            break
                    except Exception:
                        continue
            
            # 如果仍然没有跳转到搜索结果页，尝试直接导航到搜索结果URL
            final_url = self._page.url
            if "search_result" not in final_url:
                logger.warning("搜索框方式未成功跳转，尝试直接导航到搜索结果页")
                # 构造搜索结果URL（小红书格式）
                encoded_keyword = urllib.parse.quote(query, safe='')
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_explore_feed"
                
                # #region debug log
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run3",
                            "hypothesisId": "C",
                            "location": "adapter.py:760",
                            "message": "Direct navigation to search result URL",
                            "data": {
                                "searchUrl": search_url,
                                "currentUrl": final_url
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                
                await self._page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)  # 等待页面加载
            
            # 等待搜索结果加载（使用更宽松的条件）
            try:
                # 等待URL包含 search_result
                await self._page.wait_for_function(
                    "window.location.href.includes('search_result')",
                    timeout=5000
                )
            except Exception:
                # 如果URL检查超时，至少等待页面稳定
                try:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    await asyncio.sleep(2)
            
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "adapter.py:705",
                        "message": "Search completed",
                        "data": {
                            "currentUrl": self._page.url if self._page else "N/A"
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            return self._standardize(raw=f"搜索完成: {query}")
            
        except Exception as e:
            logger.error(f"Playwright 搜索失败: {e}", exc_info=True)
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "adapter.py:715",
                        "message": "Search failed with exception",
                        "data": {
                            "error": str(e),
                            "errorType": type(e).__name__
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            raise BrowserAdapterException(str(e), action="search")

    async def scroll(self, times: int = 1) -> Dict[str, Any]:
        """
        滚动页面（使用 Playwright 直接操作）
        
        ⚠️ 重要：不能使用 browser-use Agent，必须使用 Playwright API
        """
        if self._page is None:
            raise BrowserAdapterException(
                "Page 实例不存在，请先调用 open_page() 打开页面",
                action="scroll"
            )
        
        times = max(1, int(times))
        try:
            for _ in range(times):
                await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.5)  # 等待滚动完成
            
            return self._standardize(raw=f"已滚动 {times} 次")
        except Exception as e:
            raise BrowserAdapterException(str(e), action="scroll")

    async def open_item(self, index: int) -> Dict[str, Any]:
        # index 是 0-based（文档里是 open_item(index)）
        idx = max(0, int(index))
        return await self._run_action(f"Open the item at index {idx}.", action_name="open_item")

    async def extract(self, rule: str) -> Dict[str, Any]:
        """
        提取内容（使用 Playwright 直接操作）
        
        ⚠️ 重要：不能使用 browser-use Agent，必须使用 Playwright API
        """
        if self._page is None:
            raise BrowserAdapterException(
                "Page 实例不存在，请先调用 open_page() 打开页面",
                action="extract"
            )
        
        # 使用 Playwright 提取页面内容
        try:
            # 等待页面加载完成（特别是动态内容）
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass  # 如果超时，继续执行
            
            # 等待一小段时间让动态内容加载
            await asyncio.sleep(1)
            
            # 获取页面 HTML
            html = await self._page.content()
            # 获取页面文本
            text = await self._page.inner_text("body")
            
            # 返回提取的内容（这里简化处理，实际可以根据 rule 进行更复杂的提取）
            return self._standardize(
                raw=text,
                url=self._page.url,
                title=await self._page.title()
            )
        except Exception as e:
            raise BrowserAdapterException(str(e), action="extract")
