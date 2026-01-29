"""agent.llm.client

LLM 客户端（DeepSeek Chat）

对应技术文档 `AGET-TECH_MVP.md` 第 11 节：
- 相关性判断（bool）
- 结构化字段提取（MarketingCase 字段子集）
- 简短洞察总结（list[str]）
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from agent.config import settings
from agent.exceptions import LLMException
from agent.models.case_schema import MarketingCase
from agent.utils.logger import get_logger

from .prompts import (
    EXTRACTION_PROMPT_TEMPLATE,
    INSIGHTS_PROMPT_TEMPLATE,
    RELEVANCE_PROMPT_TEMPLATE,
)

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """兼容不同 LLM SDK 的最小响应对象。"""

    content: str


@runtime_checkable
class AsyncLLM(Protocol):
    async def ainvoke(self, prompt: str) -> Any:  # pragma: no cover
        ...


def _extract_content(resp: Any) -> str:
    """从不同 SDK 的返回值中提取 content。"""
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    content = getattr(resp, "content", None)
    if isinstance(content, str):
        return content
    # 兜底：尽量字符串化
    return str(resp)


def _parse_json_loose(text: str) -> Any:
    """尽量容错地解析 JSON（允许前后杂质/代码块）。"""
    if not text:
        raise ValueError("empty response")
    s = text.strip()
    # 去掉 ```json ... ```
    if s.startswith("```"):
        s = s.strip("`")
        s = s.replace("json", "", 1).strip()
    # 尝试截取第一个 JSON 对象/数组
    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj == -1 and first_arr == -1:
        raise ValueError(f"no json found: {text[:200]}")
    start = min([x for x in [first_obj, first_arr] if x != -1])
    s2 = s[start:]
    # 从尾部找匹配结束符（简单策略：找最后一个 } 或 ]）
    end_obj = s2.rfind("}")
    end_arr = s2.rfind("]")
    end = max(end_obj, end_arr)
    if end == -1:
        raise ValueError(f"json not closed: {text[:200]}")
    s3 = s2[: end + 1]
    return json.loads(s3)


class LLMClient:
    """LLM 客户端：默认使用 browser_use.llm.ChatDeepSeek（若可用）。"""

    def __init__(self, llm: Optional[AsyncLLM] = None):
        self._llm: Optional[AsyncLLM] = llm

    def _ensure_llm(self) -> AsyncLLM:
        if self._llm is not None:
            return self._llm

        # 延迟导入，避免测试/环境未安装 browser_use 时失败
        try:
            # 新版本 browser-use 可能提供 browser_use.llm.ChatDeepSeek
            from browser_use.llm import ChatDeepSeek  # type: ignore

            self._llm = ChatDeepSeek(
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                api_key=settings.deepseek_api_key,
            )
            return self._llm
        except Exception:
            # 兼容当前已安装版本（例如 0.1.40）：browser_use 直接依赖 LangChain，
            # 没有 browser_use.llm 子模块，此时使用 langchain_openai.ChatOpenAI
            try:
                from langchain_openai import ChatOpenAI  # type: ignore

                self._llm = ChatOpenAI(
                    model=settings.deepseek_model,
                    base_url=settings.deepseek_base_url,
                    api_key=settings.deepseek_api_key,
                    temperature=0,
                )
                return self._llm
            except Exception as e:  # pragma: no cover
                raise LLMException(f"LLM 初始化失败（ChatDeepSeek/ChatOpenAI 均不可用）: {e}", task_type="init")

        return self._llm

    async def _call(self, prompt: str) -> str:
        llm = self._ensure_llm()
        try:
            resp = await llm.ainvoke(prompt)  # type: ignore[attr-defined]
            return _extract_content(resp)
        except Exception as e:
            raise LLMException(f"LLM 调用失败: {e}", task_type="call")

    async def judge_relevance(self, content: str, keywords: List[str]) -> bool:
        """内容相关性判断（返回 bool）。"""
        prompt = RELEVANCE_PROMPT_TEMPLATE.format(keywords=" / ".join(keywords), content=content)
        text = (await self._call(prompt)).strip().lower()
        if "true" in text and "false" in text:
            # 模型可能输出了说明，做更严格判断：取第一个出现的
            return text.find("true") < text.find("false")
        if "true" in text:
            return True
        if "false" in text:
            return False
        raise LLMException(f"相关性判断返回不可解析: {text[:200]}", task_type="relevance")

    async def extract_structured_fields(self, content: str) -> Dict[str, Any]:
        """结构化字段提取：返回 dict（不含 platform/source_url）。"""
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(content=content)
        text = await self._call(prompt)
        try:
            data = _parse_json_loose(text)
        except Exception as e:
            raise LLMException(f"结构化提取 JSON 解析失败: {e}", task_type="extract")

        if not isinstance(data, dict):
            raise LLMException("结构化提取未返回 JSON 对象", task_type="extract")

        # 保证字段存在
        for k in ["brand", "theme", "creative_type", "strategy", "insights"]:
            data.setdefault(k, "" if k in ["brand", "theme", "creative_type"] else [])
        if not isinstance(data.get("strategy"), list):
            data["strategy"] = []
        if not isinstance(data.get("insights"), list):
            data["insights"] = []
        return data

    async def extract_marketing_case(
        self,
        content: str,
        *,
        platform: str,
        source_url: str,
    ) -> MarketingCase:
        """结构化提取并构造 MarketingCase。"""
        data = await self.extract_structured_fields(content)
        data_full = {**data, "platform": platform, "source_url": source_url}
        try:
            return MarketingCase(**data_full)
        except Exception as e:
            raise LLMException(f"MarketingCase 校验失败: {e}", task_type="extract")

    async def generate_insights(self, case: MarketingCase) -> List[str]:
        """基于结构化 case 生成/补充洞察列表。"""
        case_json = case.model_dump_json(exclude={"insights"})
        prompt = INSIGHTS_PROMPT_TEMPLATE.format(case_json=case_json)
        text = await self._call(prompt)
        try:
            data = _parse_json_loose(text)
        except Exception as e:
            raise LLMException(f"洞察 JSON 解析失败: {e}", task_type="insights")
        if not isinstance(data, list):
            raise LLMException("洞察未返回 JSON 数组", task_type="insights")
        # 只保留字符串
        return [str(x).strip() for x in data if str(x).strip()]
