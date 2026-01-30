"""agent.models.case_schema

数据模型（Agent 输出）

对应技术文档 `AGET-TECH_MVP.md` 第 12 节。
Agent 仅输出结构化结果，不存原始内容。
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MarketingCase(BaseModel):
    """营销案例（结构化输出）"""

    model_config = ConfigDict(extra="forbid")

    platform: str = Field(..., description="平台名称")
    brand: str = Field(..., description="品牌")
    theme: str = Field(..., description="营销主题/活动主题")
    creative_type: str = Field(..., description="创意类型")
    strategy: List[str] = Field(default_factory=list, description="策略要点列表")
    insights: List[str] = Field(default_factory=list, description="洞察要点列表")
    source_url: HttpUrl = Field(..., description="来源 URL")
    title: Optional[str] = Field(default=None, description="案例标题")
