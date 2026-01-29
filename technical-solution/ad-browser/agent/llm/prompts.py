"""agent.llm.prompts

LLM Prompt 模板（用于 LLMClient）

约束：
- 只输出需要的结构化内容
- 不返回原文
- 字段固定
"""

RELEVANCE_PROMPT_TEMPLATE = """\
判断以下内容是否与关键词相关。

关键词：{keywords}

内容：
{content}

只返回 true 或 false（全小写），不要输出其他文字。\
"""


EXTRACTION_PROMPT_TEMPLATE = """\
你是营销案例结构化提取器。请从以下内容中提取结构化字段。

内容：
{content}

输出要求：
- 只输出 JSON
- 不要输出 markdown code block
- 不要输出解释
- 不返回原文

JSON schema（字段必须齐全，策略/洞察为数组）：
{{
  "brand": "",
  "theme": "",
  "creative_type": "",
  "strategy": [],
  "insights": []
}}\
"""


INSIGHTS_PROMPT_TEMPLATE = """\
你是营销策略分析师。基于以下结构化案例信息，补充 3-5 条可复用洞察（短句）。

案例：
{case_json}

输出要求：
- 只输出 JSON 数组，例如：["洞察1", "洞察2"]
- 不要输出其他文字\
"""
