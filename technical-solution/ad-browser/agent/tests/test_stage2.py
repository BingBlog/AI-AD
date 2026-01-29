"""
阶段二任务验收测试

覆盖：
- 任务 2.1 数据模型
- 任务 2.2 状态机
- 任务 2.3 LLM 客户端（使用 fake llm）
- 任务 2.4 Browser Adapter（使用 fake runner）
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class FakeLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    async def ainvoke(self, prompt: str):
        if not self._responses:
            return type("R", (), {"content": "false"})()
        return type("R", (), {"content": self._responses.pop(0)})()


async def test_models_and_state_machine():
    from agent.controller.state_machine import State, StateMachine
    from agent.models.case_schema import MarketingCase
    from agent.models.task_schema import TaskRequest

    # model
    case = MarketingCase(
        platform="xiaohongshu",
        brand="BrandA",
        theme="春节营销",
        creative_type="视频",
        strategy=["情感共鸣"],
        insights=["突出家庭场景"],
        source_url="https://example.com/x",
    )
    assert case.brand == "BrandA"

    task = TaskRequest(task_id="t1", keywords=["春节", "汽车"], max_items=10)
    assert task.max_items == 10

    # state machine
    sm = StateMachine()
    seen = []
    sm.register_callback(State.SEARCHING, lambda s: seen.append(s))
    sm.transition_to(State.RECEIVED_TASK)
    sm.transition_to(State.SEARCHING)
    assert sm.current_state == State.SEARCHING
    assert seen == [State.SEARCHING]
    assert sm.progress() == 30


async def test_llm_client_parsing():
    from agent.llm.client import LLMClient

    fake = FakeLLM(
        responses=[
            "true",
            '{"brand":"B","theme":"T","creative_type":"C","strategy":["S"],"insights":["I"]}',
            '["洞察1","洞察2"]',
        ]
    )
    client = LLMClient(llm=fake)

    ok = await client.judge_relevance("content", ["k1"])
    assert ok is True

    data = await client.extract_structured_fields("content")
    assert data["brand"] == "B"
    assert isinstance(data["strategy"], list)

    from agent.models.case_schema import MarketingCase

    case = MarketingCase(
        platform="xiaohongshu",
        brand=data["brand"],
        theme=data["theme"],
        creative_type=data["creative_type"],
        strategy=data["strategy"],
        insights=[],
        source_url="https://example.com/x",
    )
    insights = await client.generate_insights(case)
    assert insights == ["洞察1", "洞察2"]


async def test_browser_adapter_standardization():
    from agent.browser.adapter import BrowserAdapter

    calls = []

    async def fake_runner(task: str):
        calls.append(task)
        return "ok"

    adapter = BrowserAdapter(runner=fake_runner)
    r = await adapter.open_page("https://example.com")
    assert r["success"] is True
    assert r["meta"]["url"] == "https://example.com"
    assert "Perform only the requested action" in calls[0]


async def main():
    # 让 logger/setup_settings 不因为没 key 崩（仅用于测试）
    os.environ.setdefault("DEEPSEEK_API_KEY", "test_key")

    await test_models_and_state_machine()
    await test_llm_client_parsing()
    await test_browser_adapter_standardization()
    print("✅ stage2 tests passed")


if __name__ == "__main__":
    asyncio.run(main())

