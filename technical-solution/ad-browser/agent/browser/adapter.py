"""agent.browser.adapter

Browser-Use Adapter

职责：
- 封装 browser-use 原始调用
- 固定并管理 Prompt（不暴露自由 Prompt）
- 提供动作级 API
- 标准化返回结果（第 10 节）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from agent.config import settings
from agent.exceptions import BrowserAdapterException
from agent.utils.logger import get_logger

from .actions import BrowserActions

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

    def __init__(self, runner: Optional[Runner] = None):
        self._runner = runner

    def _build_task(self, action_instruction: str) -> str:
        return f"{EXECUTION_PREAMBLE}\n\n{action_instruction}".strip()

    async def _default_runner(self, task: str) -> Any:
        """默认 runner：使用 browser_use.Agent 执行 task。"""
        try:
            from browser_use import Agent  # type: ignore
        except Exception as e:  # pragma: no cover
            raise BrowserAdapterException(f"无法导入 browser_use.Agent: {e}", action="init")

        # 兼容两种集成方式：优先 ChatDeepSeek，否则回退到 langchain_openai.ChatOpenAI
        llm = None
        try:
            from browser_use.llm import ChatDeepSeek  # type: ignore

            llm = ChatDeepSeek(
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                api_key=settings.deepseek_api_key,
            )
        except Exception:
            try:
                from langchain_openai import ChatOpenAI  # type: ignore

                llm = ChatOpenAI(
                    model=settings.deepseek_model,
                    base_url=settings.deepseek_base_url,
                    api_key=settings.deepseek_api_key,
                    temperature=0,
                )
            except Exception as e:  # pragma: no cover
                raise BrowserAdapterException(f"LLM 初始化失败（ChatDeepSeek/ChatOpenAI 均不可用）: {e}", action="init")

        agent = Agent(task=task, llm=llm, use_vision=False)
        # 兼容不同版本：run 可能是 async
        run_fn = getattr(agent, "run", None)
        if run_fn is None:
            raise BrowserAdapterException("browser_use.Agent 缺少 run()", action="init")
        result = run_fn()
        if hasattr(result, "__await__"):
            return await result
        return result

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
        return await self._run_action(f"Open the page: {url}", action_name="open_page", url=url)

    async def search(self, query: str) -> Dict[str, Any]:
        return await self._run_action(
            f"Search for: {query}. Use the site's search box if present.",
            action_name="search",
        )

    async def scroll(self, times: int = 1) -> Dict[str, Any]:
        times = max(1, int(times))
        return await self._run_action(f"Scroll down {times} times.", action_name="scroll")

    async def open_item(self, index: int) -> Dict[str, Any]:
        # index 是 0-based（文档里是 open_item(index)）
        idx = max(0, int(index))
        return await self._run_action(f"Open the item at index {idx}.", action_name="open_item")

    async def extract(self, rule: str) -> Dict[str, Any]:
        # 注意：这里只表达“提取规则”，不暴露自由 Prompt
        return await self._run_action(f"Extract content following this rule: {rule}", action_name="extract")
