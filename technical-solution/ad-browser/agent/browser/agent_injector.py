"""
Agent 注入器

职责：
- 创建 browser-use Agent，但使用外部提供的 page
- 确保 Agent 不管理浏览器生命周期
- 提供 Agent 执行后的 page 状态检查
"""

from __future__ import annotations

from typing import Any, Optional

from agent.config import settings
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class AgentInjector:
    """Agent 注入器：使用外部 page 创建 Agent"""
    
    def __init__(self):
        self._agent = None
        self._llm = None
    
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
                    raise Exception(f"LLM 初始化失败（ChatDeepSeek/ChatOpenAI 均不可用）: {e}")
        return self._llm
    
    async def create_agent_with_page(self, page, task: str) -> Any:
        """
        创建 Agent，但使用外部提供的 page
        
        Args:
            page: Playwright Page 实例
            task: 任务描述
            
        Returns:
            Agent 实例
        """
        try:
            from browser_use import Agent  # type: ignore
        except Exception as e:  # pragma: no cover
            raise Exception(f"无法导入 browser_use.Agent: {e}")
        
        # 获取 LLM
        llm = self._get_llm()
        
        # 创建 Agent，但使用外部 page
        # 注意：这里需要 browser-use 支持注入 page
        # 如果 browser-use 不支持，我们需要采用其他方法
        
        try:
            # 尝试直接创建 Agent 并设置 page
            agent = Agent(task=task, llm=llm, use_vision=False)
            
            # 关键：尝试将外部 page 注入到 Agent 中
            # 这需要 browser-use 的内部支持
            if hasattr(agent, 'page'):
                agent.page = page
                logger.info("成功将外部 page 注入 Agent")
            elif hasattr(agent, 'browser_context') and hasattr(agent.browser_context, 'page'):
                agent.browser_context.page = page
                logger.info("成功将外部 page 注入 Agent 的 browser_context")
            else:
                logger.warning("无法将外部 page 注入 Agent，可能需要使用其他方法")
            
            self._agent = agent
            return agent
            
        except Exception as e:
            logger.error(f"创建 Agent 失败: {e}")
            raise
    
    async def execute_task(self, agent, task: str) -> Any:
        """
        执行 Agent 任务，但保持 page 可用
        
        Args:
            agent: Agent 实例
            task: 任务描述
            
        Returns:
            执行结果
        """
        try:
            # 设置新的任务
            agent.task = task
            
            # 执行 Agent
            run_fn = getattr(agent, "run", None)
            if run_fn is None:
                raise Exception("browser_use.Agent 缺少 run()")
            
            result = run_fn()
            
            # 等待任务完成
            if hasattr(result, "__await__"):
                result = await result
            
            return result
            
        except Exception as e:
            logger.error(f"Agent 任务执行失败: {e}")
            raise
    
    def get_agent(self) -> Optional[Any]:
        """获取当前 Agent 实例"""
        return self._agent