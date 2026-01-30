"""agent.controller.task_controller

任务控制器

职责：
- 整合状态机、Browser Adapter、LLM Client
- 实现完整任务执行流程（第 13 节）
- 处理错误和重试
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

from agent.browser.adapter import BrowserAdapter
from agent.config import settings
from agent.controller.state_machine import State, StateMachine
from agent.exceptions import TaskException
from agent.extractor.detail_parser import DetailParser
from agent.extractor.list_parser import ListParser
from agent.llm.client import LLMClient
from agent.models.case_schema import MarketingCase
from agent.models.task_schema import TaskRequest
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class TaskController:
    """任务控制器"""

    def __init__(
        self,
        state_machine: Optional[StateMachine] = None,
        llm_client: Optional[LLMClient] = None,
        browser_adapter: Optional[BrowserAdapter] = None,
    ):
        """
        初始化任务控制器

        Args:
            state_machine: 状态机实例（可选，默认创建新实例）
            llm_client: LLM 客户端实例（可选，默认创建新实例）
            browser_adapter: Browser Adapter 实例（可选，默认创建新实例）
        """
        self.state_machine = state_machine or StateMachine()
        self.llm_client = llm_client or LLMClient()
        self.browser_adapter = browser_adapter or BrowserAdapter()

        # 初始化提取器
        self.list_parser = ListParser(self.browser_adapter)
        self.detail_parser = DetailParser(self.browser_adapter, self.llm_client)

        # 任务状态
        self.current_task: Optional[TaskRequest] = None
        self.results: List[MarketingCase] = []

    async def execute_task(self, task: TaskRequest) -> List[MarketingCase]:
        """
        执行任务（第 13 节流程）

        流程：
        1. 接收任务
        2. 打开平台
        3. 搜索关键词
        4. 解析列表页
        5. LLM 判断相关性
        6. 打开详情页并提取
        7. 返回结果

        Args:
            task: 任务请求

        Returns:
            营销案例列表

        Raises:
            TaskException: 任务执行失败
        """
        self.current_task = task
        self.results = []

        try:
            logger.info(f"开始执行任务: {task.task_id}, 平台: {task.platform}, 关键词: {task.keywords}")

            # 1. 接收任务
            self.state_machine.transition_to(State.RECEIVED_TASK)
            logger.info(f"任务状态: {self.state_machine.current_state.value}")

            # 2. 打开平台
            # 对于小红书，默认打开 explore 页面以便搜索
            platform_url = self._get_platform_url(task.platform)
            if task.platform.lower() == "xiaohongshu":
                platform_url = "https://www.xiaohongshu.com/explore"
            logger.info(f"打开平台: {platform_url}")
            open_result = await self.browser_adapter.open_page(platform_url)
            if not open_result.get("success"):
                raise TaskException(
                    f"打开平台失败: {open_result.get('error')}",
                    task_id=task.task_id,
                    state=self.state_machine.current_state.value,
                )

            # 3. 搜索关键词
            self.state_machine.transition_to(State.SEARCHING)
            logger.info(f"任务状态: {self.state_machine.current_state.value}")
            query = " ".join(task.keywords)
            # #region debug log
            import json
            import time
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "task_controller.py:109",
                        "message": "Before calling search()",
                        "data": {
                            "query": query,
                            "currentUrl": "N/A"  # Will be updated if page exists
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            search_result = await self.browser_adapter.search(query)
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "hypothesisId": "C",
                        "location": "task_controller.py:125",
                        "message": "After calling search()",
                        "data": {
                            "searchSuccess": search_result.get("success"),
                            "searchError": search_result.get("error"),
                            "searchContent": str(search_result.get("content", ""))[:100]
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            if not search_result.get("success"):
                logger.warning(f"搜索可能失败: {search_result.get('error')}")
                # 搜索失败不中断任务，继续尝试解析列表页

            # 4. 解析列表页
            logger.info(f"开始解析列表页，最大项数: {task.max_items}")
            items = await self.list_parser.parse_list_page(max_items=task.max_items)
            logger.info(f"列表页解析完成，提取到 {len(items)} 个项")

            if not items:
                logger.warning("列表页未提取到任何项")
                # #region debug log
                import json
                import time
                can_trans = self.state_machine.can_transition_to(State.FINISHED)
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run2",
                            "hypothesisId": "A",
                            "location": "task_controller.py:119",
                            "message": "Attempting early exit to FINISHED (no items)",
                            "data": {
                                "currentState": self.state_machine.current_state.value,
                                "targetState": "FINISHED",
                                "itemsCount": len(items),
                                "canTransition": can_trans
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                self.state_machine.transition_to(State.FINISHED)
                return self.results

            # 5. LLM 判断相关性
            self.state_machine.transition_to(State.FILTERING)
            logger.info(f"任务状态: {self.state_machine.current_state.value}")
            relevant_items = await self._filter_relevant_items(items, task.keywords)
            logger.info(f"相关性过滤完成，相关项数: {len(relevant_items)}/{len(items)}")

            if not relevant_items:
                logger.warning("没有相关项")
                # #region debug log
                import json
                import time
                can_trans = self.state_machine.can_transition_to(State.FINISHED)
                try:
                    with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run2",
                            "hypothesisId": "B",
                            "location": "task_controller.py:130",
                            "message": "Attempting early exit to FINISHED from FILTERING (no relevant items)",
                            "data": {
                                "currentState": self.state_machine.current_state.value,
                                "targetState": "FINISHED",
                                "relevantItemsCount": len(relevant_items),
                                "canTransition": can_trans
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
                self.state_machine.transition_to(State.FINISHED)
                return self.results

            # 6. 打开详情页并提取
            self.state_machine.transition_to(State.EXTRACTING)
            logger.info(f"任务状态: {self.state_machine.current_state.value}")

            # 限制提取数量（符合 MVP 硬约束）
            items_to_extract = relevant_items[:task.max_items]
            logger.info(f"开始提取详情页，目标项数: {len(items_to_extract)}")

            for idx, item in enumerate(items_to_extract, 1):
                item_url = item.get("url", "")
                if not item_url:
                    logger.warning(f"项 {idx} 缺少 URL，跳过")
                    continue

                try:
                    logger.info(f"提取详情页 [{idx}/{len(items_to_extract)}]: {item_url}")
                    case = await self.detail_parser.parse_detail_page(
                        item_url, platform=task.platform
                    )
                    self.results.append(case)
                    logger.info(f"成功提取案例: {case.brand} - {case.theme}")

                except Exception as e:
                    # 页面异常直接跳过（第 15 节策略）
                    logger.warning(f"详情页提取失败，跳过: {item_url}, 错误: {e}")
                    continue

                # 检查是否达到最大数量
                if len(self.results) >= task.max_items:
                    logger.info(f"已达到最大提取数量: {task.max_items}")
                    break

            # 7. 完成
            self.state_machine.transition_to(State.FINISHED)
            logger.info(f"任务完成: {task.task_id}, 提取到 {len(self.results)} 个案例")
            return self.results

        except TaskException:
            raise
        except Exception as e:
            logger.error(f"任务执行异常: {e}, 任务ID: {task.task_id}")
            # 转换到 ABORTED 状态（现在所有状态都允许转换到 ABORTED）
            try:
                self.state_machine.transition_to(State.ABORTED)
            except Exception as state_error:
                logger.warning(f"无法转换到 ABORTED 状态: {state_error}")
            raise TaskException(
                f"任务执行失败: {e}",
                task_id=task.task_id,
                state=self.state_machine.current_state.value,
            )

    async def _filter_relevant_items(
        self, items: List[dict], keywords: List[str]
    ) -> List[dict]:
        """
        使用 LLM 过滤相关项

        Args:
            items: 列表项列表
            keywords: 关键词列表

        Returns:
            相关项列表
        """
        if not items or not keywords:
            return items

        relevant_items: List[dict] = []

        for item in items:
            # 构建内容用于相关性判断
            title = item.get("title", "")
            description = item.get("description", "")
            content = f"{title} {description}".strip()

            if not content:
                # 如果没有内容，默认认为相关（避免过度过滤）
                relevant_items.append(item)
                continue

            try:
                is_relevant = await self.llm_client.judge_relevance(content, keywords)
                if is_relevant:
                    relevant_items.append(item)
                    logger.debug(f"项相关: {title[:50]}")
                else:
                    logger.debug(f"项不相关: {title[:50]}")
            except Exception as e:
                # LLM 判断失败，默认认为相关（避免过度过滤）
                logger.warning(f"相关性判断失败，默认认为相关: {e}")
                relevant_items.append(item)

        return relevant_items

    def _get_platform_url(self, platform: str) -> str:
        """
        获取平台 URL

        Args:
            platform: 平台名称

        Returns:
            平台 URL
        """
        urls = {
            "xiaohongshu": "https://www.xiaohongshu.com",
            "douyin": "https://www.douyin.com",
            "weibo": "https://weibo.com",
        }
        return urls.get(platform.lower(), urls["xiaohongshu"])

    def get_current_state(self) -> State:
        """获取当前状态"""
        return self.state_machine.current_state

    def get_progress(self) -> int:
        """获取进度百分比"""
        return self.state_machine.progress()

    def reset(self) -> None:
        """重置任务控制器（用于新任务）"""
        self.state_machine.reset()
        self.current_task = None
        self.results = []
