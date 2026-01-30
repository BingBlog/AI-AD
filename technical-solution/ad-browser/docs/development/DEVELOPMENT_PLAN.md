# Ad Browser MVP 开发计划

## 文档信息

- **版本**: v1.0
- **创建日期**: 2025-01-XX
- **基于文档**: [AGET-TECH_MVP.md](../design/AGET-TECH_MVP.md)
- **项目目标**: 构建面向广告营销创意策划师的本地智能研究工具 MVP

---

## 一、开发阶段概览

### 阶段划分

```
阶段一：基础设施搭建（1-2 周）
  ├─ 环境配置
  ├─ 项目结构初始化
  ├─ 配置管理
  └─ 基础工具类

阶段二：核心模块开发（3-4 周）
  ├─ 状态机实现
  ├─ Browser-Use Adapter
  ├─ LLM 客户端
  └─ 数据模型

阶段三：任务执行引擎（2-3 周）
  ├─ 任务控制器
  ├─ 提取器模块
  └─ 执行流程集成

阶段四：通信与集成（2-3 周）
  ├─ WebSocket 服务器
  ├─ 消息协议
  └─ 插件通信

阶段五：测试与优化（1-2 周）
  ├─ 单元测试
  ├─ 集成测试
  ├─ MVP 成功标准验证
  └─ 性能优化

总计：9-14 周（约 2.5-3.5 个月）
```

---

## 二、阶段一：基础设施搭建（1-2 周）

### 2.1 目标

搭建项目基础架构，配置开发环境，建立代码规范。

### 2.2 任务清单

#### 任务 1.1：项目结构初始化

**优先级**: P0（必须）

**任务描述**：

- 创建项目目录结构
- 初始化 Python 包结构
- 创建基础配置文件

**交付物**：

```
agent/
├── __init__.py
├── main.py                  # Agent 启动入口（占位）
├── config.py                # 配置管理
├── server/                  # WebSocket 服务器（占位）
│   ├── __init__.py
│   ├── ws_server.py
│   └── protocol.py
├── controller/              # 控制器模块（占位）
│   ├── __init__.py
│   ├── task_controller.py
│   └── state_machine.py
├── browser/                 # Browser-Use Adapter（占位）
│   ├── __init__.py
│   ├── adapter.py
│   └── actions.py
├── llm/                     # LLM 客户端（占位）
│   ├── __init__.py
│   ├── client.py
│   └── prompts.py
├── extractor/              # 提取器模块（占位）
│   ├── __init__.py
│   ├── list_parser.py
│   └── detail_parser.py
├── models/                  # 数据模型（占位）
│   ├── __init__.py
│   └── case_schema.py
└── tests/                   # 测试目录
    └── __init__.py
```

**验收标准**：

- ✅ 所有目录和文件创建完成
- ✅ 所有 `__init__.py` 文件存在
- ✅ 项目结构符合技术文档第 4 节要求

**预估时间**: 0.5 天

---

#### 任务 1.2：配置管理模块

**优先级**: P0（必须）

**任务描述**：

- 实现配置加载（从 `.env` 文件）
- 定义配置项（API Key、超时时间、限制参数等）
- 提供配置验证

**代码示例**：

```python
# agent/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # DeepSeek API 配置
    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        env="DEEPSEEK_API_BASE_URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        env="DEEPSEEK_MODEL"
    )

    # 性能限制（MVP 硬约束）
    max_items: int = Field(default=10, env="MAX_ITEMS")
    max_pages: int = Field(default=3, env="MAX_PAGES")
    max_steps: int = Field(default=100, env="MAX_STEPS")
    timeout_per_item: int = Field(default=60, env="TIMEOUT_PER_ITEM")

    # WebSocket 配置
    ws_host: str = Field(default="localhost", env="WS_HOST")
    ws_port: int = Field(default=8765, env="WS_PORT")

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 全局配置实例
settings = Settings()
```

**验收标准**：

- ✅ 配置可以从 `.env` 文件加载
- ✅ 所有 MVP 硬约束参数可配置（第 14 节）
- ✅ 配置验证逻辑正确
- ✅ 提供默认值

**预估时间**: 1 天

---

#### 任务 1.3：日志系统

**优先级**: P1（重要）

**任务描述**：

- 配置日志系统
- 定义日志级别和格式
- 支持文件和控制台输出

**代码示例**：

```python
# agent/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "agent", log_file: Path = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    logger.addHandler(console_handler)
    return logger
```

**验收标准**：

- ✅ 日志系统正常工作
- ✅ 支持不同日志级别
- ✅ 日志格式清晰易读

**预估时间**: 0.5 天

---

#### 任务 1.4：异常处理框架

**优先级**: P1（重要）

**任务描述**：

- 定义自定义异常类
- 实现异常处理装饰器
- 统一错误响应格式

**代码示例**：

```python
# agent/exceptions.py
class AgentException(Exception):
    """Agent 基础异常"""
    pass

class StateMachineException(AgentException):
    """状态机异常"""
    pass

class BrowserAdapterException(AgentException):
    """Browser Adapter 异常"""
    pass

class LLMException(AgentException):
    """LLM 调用异常"""
    pass

class TaskException(AgentException):
    """任务执行异常"""
    pass
```

**验收标准**：

- ✅ 异常类定义完整
- ✅ 异常处理逻辑清晰
- ✅ 符合第 15 节异常策略

**预估时间**: 0.5 天

---

### 2.3 阶段一验收标准

- ✅ 项目结构完整
- ✅ 配置管理可用
- ✅ 日志系统正常
- ✅ 异常处理框架就绪
- ✅ 代码符合规范（PEP 8）

**阶段一总时间**: 2.5 天（约 1 周，包含缓冲）

**✅ 阶段一状态：已完成（2025-01-29）**

---

## 三、阶段二：核心模块开发（3-4 周）

### 3.1 目标

实现核心功能模块：状态机、Browser-Use Adapter、LLM 客户端、数据模型。

### 3.2 任务清单

#### 任务 2.1：数据模型实现

**优先级**: P0（必须）

**任务描述**：

- 实现 `MarketingCase` 数据模型（第 12 节）
- 定义任务请求和响应模型
- 实现数据验证

**代码示例**：

```python
# agent/models/case_schema.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from enum import Enum

class MarketingCase(BaseModel):
    """营销案例数据模型"""
    platform: str = Field(..., description="平台名称")
    brand: str = Field(..., description="品牌名称")
    theme: str = Field(..., description="营销主题")
    creative_type: str = Field(..., description="创意类型")
    strategy: List[str] = Field(default_factory=list, description="策略列表")
    insights: List[str] = Field(default_factory=list, description="洞察列表")
    source_url: HttpUrl = Field(..., description="来源 URL")
    title: Optional[str] = Field(default=None, description="案例标题")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "xiaohongshu",
                "brand": "某汽车品牌",
                "theme": "春节营销",
                "creative_type": "视频广告",
                "strategy": ["情感共鸣", "节日营销"],
                "insights": ["利用春节氛围", "突出家庭场景"],
                "source_url": "https://www.xiaohongshu.com/...",
                "title": "某汽车品牌春节营销案例"
            }
        }

# agent/models/task_schema.py
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class TaskRequest(BaseModel):
    """任务请求模型"""
    task_id: str = Field(..., description="任务 ID")
    platform: str = Field(default="xiaohongshu", description="平台")
    keywords: List[str] = Field(..., description="关键词列表")
    max_items: int = Field(default=10, ge=1, le=10, description="最大提取数量")

class TaskStatus(BaseModel):
    """任务状态模型"""
    state: str = Field(..., description="当前状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    message: str = Field(default="", description="状态消息")
```

**验收标准**：

- ✅ 数据模型定义完整
- ✅ 符合第 12 节规范
- ✅ 数据验证正确
- ✅ 支持 JSON 序列化
- ✅ 包含 `title` 字段（可选，从弹层提取）

**预估时间**: 1 天

---

#### 任务 2.2：状态机实现

**优先级**: P0（必须）

**任务描述**：

- 实现状态机（第 5 节）
- 定义状态转换逻辑
- 实现状态持久化（可选）

**代码示例**：

```python
# agent/controller/state_machine.py
from enum import Enum
from typing import Optional, Callable
from datetime import datetime
from agent.exceptions import StateMachineException

class State(Enum):
    """状态枚举"""
    IDLE = "IDLE"
    RECEIVED_TASK = "RECEIVED_TASK"
    SEARCHING = "SEARCHING"
    FILTERING = "FILTERING"
    EXTRACTING = "EXTRACTING"
    FINISHED = "FINISHED"
    ABORTED = "ABORTED"

class StateMachine:
    """状态机"""

    # 状态转换表
    TRANSITIONS = {
        State.IDLE: [State.RECEIVED_TASK],
        State.RECEIVED_TASK: [State.SEARCHING],
        State.SEARCHING: [State.FILTERING, State.ABORTED],
        State.FILTERING: [State.EXTRACTING, State.ABORTED],
        State.EXTRACTING: [State.FINISHED, State.ABORTED],
        State.FINISHED: [],
        State.ABORTED: [],
    }

    def __init__(self):
        self.current_state = State.IDLE
        self.state_history: List[tuple[State, datetime]] = []
        self._callbacks: dict[State, List[Callable]] = {}

    def transition_to(self, new_state: State) -> None:
        """状态转换"""
        if new_state not in self.TRANSITIONS.get(self.current_state, []):
            raise StateMachineException(
                f"Invalid transition: {self.current_state} -> {new_state}"
            )

        self.state_history.append((self.current_state, datetime.now()))
        self.current_state = new_state

        # 触发回调
        if self.current_state in self._callbacks:
            for callback in self._callbacks[self.current_state]:
                callback(self.current_state)

    def register_callback(self, state: State, callback: Callable):
        """注册状态回调"""
        if state not in self._callbacks:
            self._callbacks[state] = []
        self._callbacks[state].append(callback)

    def can_transition_to(self, state: State) -> bool:
        """检查是否可以转换到指定状态"""
        return state in self.TRANSITIONS.get(self.current_state, [])
```

**验收标准**：

- ✅ 状态机实现完整
- ✅ 符合第 5 节状态定义
- ✅ 状态转换逻辑正确
- ✅ 异常状态处理正确

**预估时间**: 2 天

---

#### 任务 2.3：LLM 客户端实现

**优先级**: P0（必须）

**任务描述**：

- 集成 DeepSeek Chat（第 11.1 节）
- 实现三类 LLM 任务（第 11.2 节）
- 实现结构化输出

**代码示例**：

```python
# agent/llm/client.py
import os
from typing import List, Dict, Any
from browser_use.llm import ChatDeepSeek
from agent.config import settings
from agent.models.case_schema import MarketingCase
from agent.exceptions import LLMException

class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        self.llm = ChatDeepSeek(
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
        )

    async def judge_relevance(
        self,
        content: str,
        keywords: List[str]
    ) -> bool:
        """
        内容相关性判断

        Args:
            content: 待判断的内容
            keywords: 关键词列表

        Returns:
            True 表示相关，False 表示不相关
        """
        prompt = self._build_relevance_prompt(content, keywords)
        try:
            response = await self.llm.ainvoke(prompt)
            # 解析响应，返回 bool
            return self._parse_relevance_response(response.content)
        except Exception as e:
            raise LLMException(f"相关性判断失败: {e}")

    async def extract_structured_info(
        self,
        content: str
    ) -> MarketingCase:
        """
        结构化字段提取

        Args:
            content: 案例内容

        Returns:
            MarketingCase 对象
        """
        prompt = self._build_extraction_prompt(content)
        try:
            response = await self.llm.ainvoke(prompt)
            # 解析 JSON 响应
            data = self._parse_json_response(response.content)
            return MarketingCase(**data)
        except Exception as e:
            raise LLMException(f"结构化提取失败: {e}")

    async def generate_insights(
        self,
        case: MarketingCase
    ) -> List[str]:
        """
        简短洞察总结

        Args:
            case: 营销案例

        Returns:
            洞察列表
        """
        prompt = self._build_insights_prompt(case)
        try:
            response = await self.llm.ainvoke(prompt)
            return self._parse_insights_response(response.content)
        except Exception as e:
            raise LLMException(f"洞察生成失败: {e}")

    def _build_relevance_prompt(self, content: str, keywords: List[str]) -> str:
        """构建相关性判断 Prompt"""
        # 实现 Prompt 构建逻辑
        pass

    def _parse_relevance_response(self, response: str) -> bool:
        """解析相关性判断响应"""
        # 实现响应解析逻辑
        pass

# agent/llm/prompts.py
"""LLM Prompt 模板"""

RELEVANCE_PROMPT_TEMPLATE = """
判断以下内容是否与关键词相关。

关键词：{keywords}

内容：
{content}

请只返回 true 或 false。
"""

EXTRACTION_PROMPT_TEMPLATE = """
从以下内容中提取营销案例的结构化信息。

内容：
{content}

请返回 JSON 格式，包含以下字段：
- brand: 品牌名称
- theme: 营销主题
- creative_type: 创意类型
- strategy: 策略列表（数组）
- insights: 洞察列表（数组）

不返回原文内容，字段数量固定。
"""
```

**验收标准**：

- ✅ DeepSeek Chat 集成成功
- ✅ 三类 LLM 任务实现完整
- ✅ 结构化输出符合第 11.3 节规范
- ✅ 错误处理正确

**预估时间**: 3 天

---

#### 任务 2.4：Browser-Use Adapter 实现

**优先级**: P0（必须）

**任务描述**：

- 封装 Browser-Use 接口（第 8 节）
- 实现动作级 API（第 8.2 节）
- 标准化返回结果（第 10 节）

**代码示例**：

```python
# agent/browser/adapter.py
from typing import Dict, Any, Optional
from browser_use import Agent
from browser_use.llm import ChatDeepSeek
from agent.config import settings
from agent.llm.client import LLMClient
from agent.exceptions import BrowserAdapterException

class BrowserAdapter:
    """Browser-Use Adapter"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agent: Optional[Agent] = None

    async def initialize(self):
        """初始化 Browser-Use Agent"""
        llm = ChatDeepSeek(
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
        )
        # 注意：这里不直接创建 Agent，而是通过 actions 调用
        self.llm = llm

    async def open_page(self, url: str) -> Dict[str, Any]:
        """
        打开页面

        Args:
            url: 页面 URL

        Returns:
            标准化结果
        """
        prompt = f"打开页面：{url}"
        try:
            result = await self._execute_action(prompt)
            return self._standardize_result(result, url=url)
        except Exception as e:
            raise BrowserAdapterException(f"打开页面失败: {e}")

    async def search(self, query: str) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索关键词

        Returns:
            标准化结果
        """
        prompt = f"在搜索框中输入 '{query}' 并点击搜索按钮"
        try:
            result = await self._execute_action(prompt)
            return self._standardize_result(result)
        except Exception as e:
            raise BrowserAdapterException(f"搜索失败: {e}")

    async def scroll(self, times: int = 1) -> Dict[str, Any]:
        """
        滚动页面

        Args:
            times: 滚动次数

        Returns:
            标准化结果
        """
        prompt = f"向下滚动页面 {times} 次"
        try:
            result = await self._execute_action(prompt)
            return self._standardize_result(result)
        except Exception as e:
            raise BrowserAdapterException(f"滚动失败: {e}")

    async def open_item(self, index: int) -> Dict[str, Any]:
        """
        打开列表项

        Args:
            index: 列表项索引（从 0 开始）

        Returns:
            标准化结果
        """
        prompt = f"点击第 {index + 1} 个搜索结果"
        try:
            result = await self._execute_action(prompt)
            return self._standardize_result(result)
        except Exception as e:
            raise BrowserAdapterException(f"打开列表项失败: {e}")

    async def extract(self, rule: str) -> Dict[str, Any]:
        """
        提取内容

        Args:
            rule: 提取规则描述

        Returns:
            标准化结果
        """
        prompt = f"提取以下内容：{rule}"
        try:
            result = await self._execute_action(prompt)
            return self._standardize_result(result)
        except Exception as e:
            raise BrowserAdapterException(f"提取失败: {e}")

    async def _execute_action(self, prompt: str) -> Any:
        """执行 Browser-Use 动作"""
        # 使用固定的执行型 Prompt
        full_prompt = f"""
Perform only the requested action.
Do not explain.
Do not add extra steps.

{prompt}
"""
        # 调用 Browser-Use Agent
        # 这里需要根据 Browser-Use 的实际 API 实现
        # agent = Agent(task=full_prompt, llm=self.llm)
        # result = await agent.run()
        # return result
        pass

    def _standardize_result(
        self,
        result: Any,
        **meta
    ) -> Dict[str, Any]:
        """
        标准化返回结果（第 10.1 节）

        Returns:
            标准化的结果字典
        """
        return {
            "success": True,
            "meta": {
                "url": meta.get("url", ""),
                "title": meta.get("title", ""),
            },
            "content": {
                "text": str(result) if result else "",
            },
            "error": None,
        }

# agent/browser/actions.py
"""Browser Actions 接口定义"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BrowserActions(ABC):
    """Browser Actions 接口"""

    @abstractmethod
    async def open_page(self, url: str) -> Dict[str, Any]:
        """打开页面"""
        pass

    @abstractmethod
    async def search(self, query: str) -> Dict[str, Any]:
        """执行搜索"""
        pass

    @abstractmethod
    async def scroll(self, times: int = 1) -> Dict[str, Any]:
        """滚动页面"""
        pass

    @abstractmethod
    async def open_item(self, index: int) -> Dict[str, Any]:
        """打开列表项"""
        pass

    @abstractmethod
    async def extract(self, rule: str) -> Dict[str, Any]:
        """提取内容"""
        pass
```

**验收标准**：

- ✅ Browser-Use 封装完整
- ✅ 动作级 API 实现（第 8.2 节）
- ✅ 返回结果标准化（第 10.1 节）
- ✅ 不暴露自由 Prompt（第 8.2 节设计原则）
- ✅ 错误处理符合第 10.2 节原则

**预估时间**: 4 天

---

### 3.3 阶段二验收标准

- ✅ 数据模型完整可用
- ✅ 状态机正常工作
- ✅ LLM 客户端集成成功
- ✅ Browser-Use Adapter 封装完成
- ✅ 各模块单元测试通过
- ✅ 自然语言驱动浏览器测试通过

**阶段二总时间**: 10 天（约 2 周，包含缓冲）

**✅ 阶段二状态：已完成（2025-01-29）**

---

## 四、阶段三：任务执行引擎（2-3 周）

### 4.1 目标

实现任务执行引擎，集成各模块，完成核心业务流程。

### 4.2 任务清单

#### 任务 3.1：提取器模块实现

**优先级**: P0（必须）

**任务描述**：

- 实现列表页解析器
- 实现详情页解析器
- 集成 LLM 进行内容提取

**代码示例**：

```python
# agent/extractor/list_parser.py
from typing import List, Dict, Any
from agent.browser.adapter import BrowserAdapter

class ListParser:
    """列表页解析器"""

    def __init__(self, browser_adapter: BrowserAdapter):
        self.browser_adapter = browser_adapter

    async def parse_list_page(
        self,
        max_items: int = 10
    ) -> List[Dict[str, Any]]:
        """
        解析列表页

        Args:
            max_items: 最大提取数量

        Returns:
            列表项信息列表
        """
        items = []

        # 提取列表项
        result = await self.browser_adapter.extract(
            "提取所有搜索结果列表项，包括标题、链接、预览图"
        )

        # 解析结果
        # 这里需要根据实际页面结构实现解析逻辑
        # items = self._parse_items(result["content"]["text"])

        return items[:max_items]

# agent/extractor/detail_parser.py
from typing import Dict, Any
from agent.browser.adapter import BrowserAdapter
from agent.llm.client import LLMClient
from agent.models.case_schema import MarketingCase

class DetailParser:
    """详情页解析器"""

    def __init__(
        self,
        browser_adapter: BrowserAdapter,
        llm_client: LLMClient
    ):
        self.browser_adapter = browser_adapter
        self.llm_client = llm_client

    async def parse_detail_page(
        self,
        url: str
    ) -> MarketingCase:
        """
        解析详情页并提取结构化信息

        Args:
            url: 详情页 URL

        Returns:
            MarketingCase 对象
        """
        # 打开详情页
        await self.browser_adapter.open_page(url)

        # 提取页面内容
        result = await self.browser_adapter.extract(
            "提取页面主要内容，包括标题、正文、图片、视频等"
        )

        content = result["content"]["text"]

        # 使用 LLM 提取结构化信息
        case = await self.llm_client.extract_structured_info(content)
        case.source_url = url

        return case
```

**验收标准**：

- ✅ 列表页解析正确
- ✅ 详情页解析正确（支持从弹层提取，避免 404 页面）
- ✅ 支持提取案例标题（`title` 字段）
- ✅ 集成 LLM 提取功能
- ✅ 错误处理完善

**预估时间**: 3 天

---

#### 任务 3.2：任务控制器实现

**优先级**: P0（必须）

**任务描述**：

- 实现任务控制器（第 3.1 节）
- 集成状态机
- 实现任务执行流程（第 13 节）

**代码示例**：

```python
# agent/controller/task_controller.py
from typing import List, Optional
from agent.controller.state_machine import StateMachine, State
from agent.browser.adapter import BrowserAdapter
from agent.llm.client import LLMClient
from agent.extractor.list_parser import ListParser
from agent.extractor.detail_parser import DetailParser
from agent.models.case_schema import MarketingCase
from agent.models.task_schema import TaskRequest
from agent.config import settings
from agent.exceptions import TaskException

class TaskController:
    """任务控制器"""

    def __init__(self):
        self.state_machine = StateMachine()
        self.llm_client = LLMClient()
        self.browser_adapter = BrowserAdapter(self.llm_client)
        self.list_parser = ListParser(self.browser_adapter)
        self.detail_parser = DetailParser(
            self.browser_adapter,
            self.llm_client
        )
        self.current_task: Optional[TaskRequest] = None
        self.results: List[MarketingCase] = []

    async def initialize(self):
        """初始化各个模块"""
        await self.browser_adapter.initialize()

    async def execute_task(self, task: TaskRequest) -> List[MarketingCase]:
        """
        执行任务（第 13 节流程）

        Args:
            task: 任务请求

        Returns:
            营销案例列表
        """
        self.current_task = task
        self.results = []

        try:
            # 1. 接收任务
            self.state_machine.transition_to(State.RECEIVED_TASK)

            # 2. 打开平台
            platform_url = self._get_platform_url(task.platform)
            await self.browser_adapter.open_page(platform_url)

            # 3. 搜索关键词
            self.state_machine.transition_to(State.SEARCHING)
            query = " ".join(task.keywords)
            await self.browser_adapter.search(query)

            # 4. 解析列表页
            items = await self.list_parser.parse_list_page(
                max_items=task.max_items
            )

            # 5. LLM 判断相关性
            self.state_machine.transition_to(State.FILTERING)
            relevant_items = await self._filter_relevant_items(
                items,
                task.keywords
            )

            # 6. 打开详情页并提取
            self.state_machine.transition_to(State.EXTRACTING)
            for item in relevant_items[:task.max_items]:
                try:
                    case = await self.detail_parser.parse_detail_page(
                        item["url"]
                    )
                    self.results.append(case)
                except Exception as e:
                    # 页面异常直接跳过（第 15 节）
                    continue

            # 7. 完成
            self.state_machine.transition_to(State.FINISHED)
            return self.results

        except Exception as e:
            self.state_machine.transition_to(State.ABORTED)
            raise TaskException(f"任务执行失败: {e}")

    async def _filter_relevant_items(
        self,
        items: List[dict],
        keywords: List[str]
    ) -> List[dict]:
        """使用 LLM 过滤相关项"""
        relevant_items = []

        for item in items:
            content = item.get("title", "") + " " + item.get("description", "")
            is_relevant = await self.llm_client.judge_relevance(
                content,
                keywords
            )
            if is_relevant:
                relevant_items.append(item)

        return relevant_items

    def _get_platform_url(self, platform: str) -> str:
        """获取平台 URL"""
        urls = {
            "xiaohongshu": "https://www.xiaohongshu.com",
            # 其他平台...
        }
        return urls.get(platform, urls["xiaohongshu"])

    def get_current_state(self) -> State:
        """获取当前状态"""
        return self.state_machine.current_state

    def get_progress(self) -> int:
        """获取进度百分比"""
        state_progress = {
            State.IDLE: 0,
            State.RECEIVED_TASK: 10,
            State.SEARCHING: 30,
            State.FILTERING: 50,
            State.EXTRACTING: 70,
            State.FINISHED: 100,
            State.ABORTED: 0,
        }
        return state_progress.get(self.state_machine.current_state, 0)
```

**验收标准**：

- ✅ 任务执行流程完整（第 13 节）
- ✅ 状态机集成正确
- ✅ 符合 MVP 硬约束（第 14 节）
- ✅ 异常处理符合第 15 节策略
- ✅ 进度计算正确
- ✅ 支持从弹层提取案例详情（包括标题）
- ✅ 使用 Chrome 浏览器保持登录状态

**预估时间**: 4 天

---

### 4.3 阶段三验收标准

- ✅ 提取器模块正常工作
- ✅ 任务控制器实现完整
- ✅ 核心业务流程可执行
- ✅ 集成测试通过

**阶段三总时间**: 7 天（约 1.5 周，包含缓冲）

**✅ 阶段三状态：已完成（2025-01-29）**

---

## 五、阶段四：通信与集成（2-3 周）

### 5.1 目标

实现 WebSocket 通信，完成插件与 Agent 的集成。

### 5.2 任务清单

#### 任务 4.1：消息协议实现

**优先级**: P0（必须）

**任务描述**：

- 定义消息协议（第 6 节）
- 实现消息序列化/反序列化
- 实现消息验证

**代码示例**：

```python
# agent/server/protocol.py
from typing import Literal, Dict, Any, List
from pydantic import BaseModel, Field
from agent.models.case_schema import MarketingCase

class Message(BaseModel):
    """基础消息模型"""
    type: str

class StartTaskMessage(Message):
    """启动任务消息（第 6.1 节）"""
    type: Literal["START_TASK"] = "START_TASK"
    task_id: str
    payload: Dict[str, Any] = Field(..., description="任务负载")

class StatusUpdateMessage(Message):
    """状态更新消息（第 6.2 节）"""
    type: Literal["STATUS_UPDATE"] = "STATUS_UPDATE"
    state: str
    progress: int = Field(ge=0, le=100)

class TaskResultMessage(Message):
    """任务结果消息（第 6.3 节）"""
    type: Literal["TASK_RESULT"] = "TASK_RESULT"
    results: List[MarketingCase]

class ErrorMessage(Message):
    """错误消息"""
    type: Literal["ERROR"] = "ERROR"
    error: str
    task_id: Optional[str] = None

def parse_message(data: str) -> Message:
    """解析消息"""
    import json
    obj = json.loads(data)
    msg_type = obj.get("type")

    if msg_type == "START_TASK":
        return StartTaskMessage(**obj)
    elif msg_type == "STATUS_UPDATE":
        return StatusUpdateMessage(**obj)
    elif msg_type == "TASK_RESULT":
        return TaskResultMessage(**obj)
    elif msg_type == "ERROR":
        return ErrorMessage(**obj)
    else:
        raise ValueError(f"Unknown message type: {msg_type}")

def serialize_message(message: Message) -> str:
    """序列化消息"""
    import json
    return json.dumps(message.model_dump(), ensure_ascii=False)
```

**验收标准**：

- ✅ 消息协议定义完整（第 6 节）
- ✅ 消息解析正确
- ✅ 消息验证完善

**预估时间**: 1 天

---

#### 任务 4.2：WebSocket 服务器实现

**优先级**: P0（必须）

**任务描述**：

- 实现 WebSocket 服务器
- 处理客户端连接
- 实现消息路由

**代码示例**：

```python
# agent/server/ws_server.py
import asyncio
import websockets
import json
from typing import Set
from agent.server.protocol import (
    parse_message,
    serialize_message,
    StartTaskMessage,
    StatusUpdateMessage,
    TaskResultMessage,
    ErrorMessage
)
from agent.controller.task_controller import TaskController
from agent.models.task_schema import TaskRequest
from agent.config import settings

class WebSocketServer:
    """WebSocket 服务器"""

    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.task_controller = TaskController()

    async def register_client(self, websocket):
        """注册客户端"""
        self.clients.add(websocket)
        print(f"客户端已连接，当前连接数: {len(self.clients)}")

    async def unregister_client(self, websocket):
        """注销客户端"""
        self.clients.remove(websocket)
        print(f"客户端已断开，当前连接数: {len(self.clients)}")

    async def handle_message(self, websocket, message: str):
        """处理消息"""
        try:
            msg = parse_message(message)

            if isinstance(msg, StartTaskMessage):
                await self._handle_start_task(websocket, msg)
            else:
                await self._send_error(
                    websocket,
                    f"Unknown message type: {msg.type}"
                )
        except Exception as e:
            await self._send_error(websocket, str(e))

    async def _handle_start_task(
        self,
        websocket,
        message: StartTaskMessage
    ):
        """处理启动任务消息"""
        try:
            # 创建任务请求
            task = TaskRequest(
                task_id=message.task_id,
                platform=message.payload.get("platform", "xiaohongshu"),
                keywords=message.payload.get("keywords", []),
                max_items=message.payload.get("max_items", 10),
            )

            # 启动任务执行（异步）
            asyncio.create_task(
                self._execute_task_with_updates(websocket, task)
            )

        except Exception as e:
            await self._send_error(websocket, str(e), message.task_id)

    async def _execute_task_with_updates(
        self,
        websocket,
        task: TaskRequest
    ):
        """执行任务并发送状态更新"""
        try:
            # 注册状态更新回调
            def on_state_change(state):
                asyncio.create_task(
                    self._send_status_update(websocket, state, task.task_id)
                )

            self.task_controller.state_machine.register_callback(
                self.task_controller.state_machine.current_state,
                on_state_change
            )

            # 执行任务
            results = await self.task_controller.execute_task(task)

            # 发送结果
            result_msg = TaskResultMessage(results=results)
            await websocket.send(serialize_message(result_msg))

        except Exception as e:
            await self._send_error(websocket, str(e), task.task_id)

    async def _send_status_update(
        self,
        websocket,
        state,
        task_id: str
    ):
        """发送状态更新"""
        progress = self.task_controller.get_progress()
        msg = StatusUpdateMessage(
            state=state.value,
            progress=progress
        )
        await websocket.send(serialize_message(msg))

    async def _send_error(
        self,
        websocket,
        error: str,
        task_id: str = None
    ):
        """发送错误消息"""
        msg = ErrorMessage(error=error, task_id=task_id)
        await websocket.send(serialize_message(msg))

    async def start(self):
        """启动服务器"""
        await self.task_controller.initialize()

        async with websockets.serve(
            self._handle_client,
            settings.ws_host,
            settings.ws_port
        ):
            print(f"WebSocket 服务器启动: ws://{settings.ws_host}:{settings.ws_port}")
            await asyncio.Future()  # 永久运行

    async def _handle_client(self, websocket, path):
        """处理客户端连接"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            await self.unregister_client(websocket)
```

**验收标准**：

- ✅ WebSocket 服务器正常启动
- ✅ 客户端连接处理正确
- ✅ 消息路由正确
- ✅ 状态更新实时推送

**预估时间**: 3 天

---

#### 任务 4.3：Agent 启动入口

**优先级**: P0（必须）

**任务描述**：

- 实现 Agent 主入口
- 集成 WebSocket 服务器
- 实现优雅关闭

**代码示例**：

```python
# agent/main.py
import asyncio
import signal
from agent.server.ws_server import WebSocketServer
from agent.utils.logger import setup_logger

logger = setup_logger("agent")

async def main():
    """Agent 主入口"""
    server = WebSocketServer()

    # 注册信号处理
    def signal_handler(sig, frame):
        logger.info("收到停止信号，正在关闭...")
        # 实现优雅关闭逻辑
        asyncio.create_task(server.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Agent 已停止")
    except Exception as e:
        logger.error(f"Agent 运行错误: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

**验收标准**：

- ✅ Agent 可以正常启动
- ✅ WebSocket 服务器正常运行
- ✅ 优雅关闭功能正常

**预估时间**: 1 天

---

### 5.4 阶段四验收标准

- ✅ 消息协议实现完整
- ✅ WebSocket 服务器正常工作
- ✅ 插件与 Agent 通信正常
- ✅ 状态更新实时推送
- ✅ 错误处理完善

**阶段四总时间**: 5 天（约 1 周，包含缓冲）

**✅ 阶段四状态：已完成（2025-01-29）**

---

## 六、阶段五：测试与优化（1-2 周）

### 6.1 目标

完成测试，验证 MVP 成功标准，进行性能优化。

### 6.2 任务清单

#### 任务 5.1：单元测试

**优先级**: P1（重要）

**任务描述**：

- 为核心模块编写单元测试
- 测试覆盖率 ≥ 70%
- 使用 pytest 框架

**测试范围**：

- 状态机测试
- LLM 客户端测试（Mock）
- Browser Adapter 测试（Mock）
- 数据模型测试
- 提取器测试

**预估时间**: 3 天

---

#### 任务 5.2：集成测试

**优先级**: P1（重要）

**任务描述**：

- 测试完整任务执行流程
- 测试 WebSocket 通信
- 测试异常场景

**预估时间**: 2 天

---

#### 任务 5.3：MVP 成功标准验证

**优先级**: P0（必须）

**任务描述**：
验证第 16 节 MVP 成功标准：

1. **连续运行 ≥ 10 次不崩溃**

   ```python
   async def test_continuous_execution():
       controller = TaskController()
       for i in range(10):
           result = await controller.execute_task(sample_task)
           assert result is not None
   ```

2. **同类任务结果差异 < 20%**

   ```python
   async def test_result_consistency():
       controller = TaskController()
       results = []
       for i in range(5):
           result = await controller.execute_task(same_task)
           results.append(len(result))
       # 计算差异
       assert calculate_variance(results) < 0.2
   ```

3. **不执行多余操作**

   - 监控操作步数
   - 验证不超过限制

4. **不触发平台风控**
   - 验证请求频率
   - 验证操作间隔

**预估时间**: 2 天

---

#### 任务 5.4：性能优化

**优先级**: P2（可选）

**任务描述**：

- 优化 LLM 调用频率
- 优化浏览器操作
- 减少不必要的等待时间

**预估时间**: 2 天

---

### 6.3 阶段五验收标准

- ⏳ 单元测试覆盖率 ≥ 70%
- ⏳ 集成测试通过
- ⏳ MVP 成功标准全部验证通过（第 16 节）
- ⏳ 性能满足要求

**阶段五总时间**: 9 天（约 2 周，包含缓冲）

**⏳ 阶段五状态：待开始**

---

## 七、开发计划总结

### 7.1 时间估算

| 阶段                 | 任务数 | 预估时间    | 缓冲时间  | 总时间     |
| -------------------- | ------ | ----------- | --------- | ---------- |
| 阶段一：基础设施搭建 | 4      | 2.5 天      | 2 天      | **1 周**   |
| 阶段二：核心模块开发 | 4      | 10 天       | 4 天      | **2 周**   |
| 阶段三：任务执行引擎 | 2      | 7 天        | 3 天      | **1.5 周** |
| 阶段四：通信与集成   | 3      | 5 天        | 3 天      | **1 周**   |
| 阶段五：测试与优化   | 4      | 9 天        | 3 天      | **2 周**   |
| **总计**             | **17** | **33.5 天** | **15 天** | **7.5 周** |

**约 2 个月**（按每周 5 个工作日计算）

### 7.2 关键里程碑

| 里程碑           | 时间点      | 交付物                       | 状态      | 完成日期   |
| ---------------- | ----------- | ---------------------------- | --------- | ---------- |
| M1: 基础设施完成 | 第 1 周末   | 项目结构、配置管理           | ✅ 完成   | 2025-01-29 |
| M2: 核心模块完成 | 第 3 周末   | 状态机、LLM、Browser Adapter | ✅ 完成   | 2025-01-29 |
| M3: 任务引擎完成 | 第 4.5 周末 | 任务控制器、提取器           | ✅ 完成   | 2025-01-29 |
| M4: 通信集成完成 | 第 5.5 周末 | WebSocket 服务器             | ✅ 完成   | 2025-01-29 |
| M5: MVP 完成     | 第 7.5 周末 | 完整系统、测试通过           | ⏳ 待开始 | -          |

### 7.3 风险与应对

| 风险                 | 影响 | 应对措施                           |
| -------------------- | ---- | ---------------------------------- |
| Browser-Use API 变更 | 高   | 及时关注官方文档，预留适配时间     |
| LLM API 不稳定       | 中   | 实现重试机制，使用 Mock 测试       |
| 平台页面结构变化     | 高   | 实现灵活的解析策略，增加容错       |
| 性能不达标           | 中   | 提前进行性能测试，优化关键路径     |
| 时间延期             | 中   | 每个阶段预留缓冲时间，优先核心功能 |

### 7.4 依赖关系

```
阶段一（基础设施）
  ↓
阶段二（核心模块）
  ├─→ 状态机（依赖阶段一）
  ├─→ LLM 客户端（依赖阶段一）
  └─→ Browser Adapter（依赖阶段一、LLM）
  ↓
阶段三（任务引擎）
  ├─→ 提取器（依赖阶段二）
  └─→ 任务控制器（依赖阶段二）
  ↓
阶段四（通信集成）
  └─→ WebSocket 服务器（依赖阶段三）
  ↓
阶段五（测试优化）
  └─→ 所有阶段
```

### 7.5 开发建议

1. **迭代开发**：每个阶段完成后进行集成测试
2. **持续集成**：建立 CI/CD 流程
3. **文档同步**：代码与文档同步更新
4. **代码审查**：关键模块进行代码审查
5. **MVP 优先**：优先实现核心功能，优化后续进行

---

## 八、附录

### 8.1 参考文档

- [AGET-TECH_MVP.md](../design/AGET-TECH_MVP.md) - 技术设计文档
- [PRD-MVP.md](../design/PRD-MVP.md) - 产品需求文档
- [REFERENCES.md](../references/REFERENCES.md) - 文档索引

### 8.2 开发工具

- **Python**: 3.12
- **包管理**: UV
- **测试框架**: pytest
- **代码规范**: PEP 8
- **类型检查**: mypy（可选）

### 8.3 更新日志

- **v1.4** (2025-01-30):
  - ✅ 添加 `title` 字段到 `MarketingCase` 模型
  - ✅ 修改 `_extract_from_modal` 方法支持提取并返回 `title`
  - ✅ 更新 `_extract_case_from_content` 方法支持传递 `title` 参数
  - ✅ 修复测试文件访问 `case.title` 时的 `AttributeError` 错误
  - ✅ 确保所有创建 `MarketingCase` 的地方都包含 `title` 参数
  - ✅ 代码已提交（commit: d4f730b）
- **v1.3** (2025-01-29):
  - ✅ 完成阶段四：通信与集成（100%）
  - ✅ 消息协议实现（序列化/反序列化/验证）
  - ✅ WebSocket 服务器实现（连接处理、消息路由、状态推送）
  - ✅ Agent 启动入口实现（优雅关闭）
  - ✅ 阶段四验收测试通过
- **v1.2** (2025-01-29):
  - ✅ 完成阶段三：任务执行引擎（100%）
  - ✅ 列表页解析器实现
  - ✅ 详情页解析器实现
  - ✅ 任务控制器实现
  - ✅ 完整任务执行流程集成
  - ✅ 阶段三验收测试通过
- **v1.1** (2025-01-29):
  - ✅ 完成阶段一：基础设施搭建（100%）
  - ✅ 完成阶段二：核心模块开发（100%）
  - ✅ 自然语言驱动浏览器测试通过
  - ✅ 代码已提交（commit: 69eb5f2）
  - 📝 更新进度文档
- **v1.0** (2025-01-XX): 初始版本
