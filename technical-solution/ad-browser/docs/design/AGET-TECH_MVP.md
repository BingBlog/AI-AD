> 📚 **文档索引**: 开发过程中需要参考 Browser-Use 官方文档时，请查看 [REFERENCES.md](../references/REFERENCES.md) 获取完整的文档链接索引。
>
> 📋 **开发计划**: 详细的开发计划、任务分解和时间估算请查看 [DEVELOPMENT_PLAN.md](../development/DEVELOPMENT_PLAN.md)。

1. 项目目标与适用范围

1.1 项目目标

构建一个 面向广告营销创意策划师 的本地智能研究工具，使其能够：
• 在 用户本地浏览器环境 中运行
• 基于 Browser-Use 执行网页级自动化
• 从小红书 / 抖音等平台中
• 搜索、筛选、提取 营销案例级结构化信息
• 用于后续 平台知识库 / RAG / AI 分析

1.2 MVP 范围限定
• 本地运行（localhost）
• 单用户
• 单 Agent
• 单浏览器实例
• 单平台（建议：小红书）
• 不包含云端服务
• 不包含域名
• 不支持并发任务

1.3 本地开发环境搭建（macOS）

参考：[Browser-Use 官方文档](https://docs.browser-use.com/quickstart)

1.3.1 安装 UV 环境管理工具

```bash
pip install uv
```

1.3.2 创建 Python 虚拟环境

```bash
uv venv --python 3.12
```

1.3.3 激活虚拟环境

```bash
source .venv/bin/activate
```

1.3.4 安装 Browser-Use 和 Chromium

```bash
uv pip install browser-use
uvx browser-use install
```

1.3.5 配置环境变量

创建 `.env` 文件：

```bash
touch .env
```

在 `.env` 文件中添加 DeepSeek API Key：

```bash
# DeepSeek API Key
DEEPSEEK_API_KEY=your_api_key_here
```

1.3.6 安装项目依赖

```bash
uv pip install python-dotenv
```

注意：项目代码中需要使用 `from dotenv import load_dotenv` 和 `load_dotenv()` 来加载环境变量。

2. 总体架构（Agent 视角）

```shell
Chrome 插件
  └─ 用户发起任务 / 查看结果
        │ WebSocket
        ▼
本地 Agent
  ├─ 状态机
  ├─ 任务调度
  ├─ LLM 决策
  └─ Browser-Use 控制
        │ In-Process 调用
        ▼
Browser-Use Adapter
  ├─ 动作抽象
  ├─ Prompt 封装
  └─ 结果标准化
        │ Playwright
        ▼
用户本地浏览器（已登录）
```

3. Agent 的系统定位

3.1 Agent 是什么

Agent = 研究任务的执行控制器（Execution Controller）

负责：
• 任务生命周期管理
• 决策与调度
• LLM 调用
• 结果组织与输出

3.2 Agent 不负责的内容
• 不直接操作浏览器 DOM
• 不直接编写浏览器 Prompt
• 不保存平台原始内容
• 不做页面级行为决策

3.3 Agent 框架选择

**结论：不需要引入额外的 Agent 框架**（如 LangChain、AutoGPT、CrewAI 等）

**理由**：
• Browser-Use 本身已提供浏览器自动化的 Agent 能力
• 任务流程固定且线性，不需要动态规划
• LLM 使用场景有限（判断、提取、总结），不需要复杂工具链
• MVP 范围限定为单 Agent、单任务，符合简单性原则
• 已有状态机设计，足以约束执行流程

**推荐架构**：状态机 + Browser-Use Adapter + LLM 客户端

详细分析请参考：[AGENT_FRAMEWORK_ANALYSIS.md](./AGENT_FRAMEWORK_ANALYSIS.md)

4. Agent 内部模块设计（MVP）

```shell
agent/
├── main.py                  # Agent 启动入口
├── server/
│   ├── ws_server.py         # 插件通信
│   └── protocol.py          # 消息协议
├── controller/
│   ├── task_controller.py   # 任务调度
│   └── state_machine.py     # 状态机
├── browser/
│   ├── adapter.py           # Browser-Use Adapter
│   └── actions.py           # 动作接口
├── llm/
│   ├── client.py            # DeepSeek Chat 客户端
│   └── prompts.py           # 结构化 Prompt
├── extractor/
│   ├── list_parser.py
│   └── detail_parser.py
├── models/
│   └── case_schema.py
└── config.py
```

5. Agent 状态机设计（核心）

5.1 状态定义

```shell
IDLE
 → RECEIVED_TASK
 → SEARCHING
 → FILTERING
 → EXTRACTING
 → FINISHED / ABORTED
```

5.2 状态机作用
• 约束执行流程
• 防止逻辑发散
• 支持失败兜底
• 支持进度回传

6. 插件 ↔ Agent 通信协议

6.1 插件 → Agent（启动任务）

```json
{
  "type": "START_TASK",
  "task_id": "uuid",
  "payload": {
    "platform": "xiaohongshu",
    "keywords": ["春节", "汽车", "营销"],
    "max_items": 10
  }
}
```

6.2 Agent → 插件（状态更新）

```json
{
  "type": "STATUS_UPDATE",
  "state": "EXTRACTING",
  "progress": 6
}
```

6.3 Agent → 插件（任务结果）

```json
{
  "type": "TASK_RESULT",
  "results": []
}
```

7. Agent ↔ Browser-Use 通信方式

7.1 通信模式（MVP 推荐）

同进程函数调用（In-Process）
• Browser-Use 作为 Python 模块被 Agent 引用
• 不独立成服务
• 不通过 HTTP / WebSocket

7.2 角色关系

Agent
→ Browser-Use Adapter
→ Browser-Use
→ Browser（Playwright）

8. Browser-Use Adapter 设计

8.1 Adapter 的职责
• 封装 Browser-Use 原始接口
• 管理并固定 Prompt
• 提供动作级 API
• 标准化返回结果

8.2 对外动作级 API

```python
class BrowserActions:
    async def open_page(url: str)
    async def search(query: str)
    async def scroll(times: int = 1)
    async def open_item(index: int)
    async def extract(rule)
```

设计原则
• 不暴露自由 Prompt
• Agent 不允许直接调用 run(prompt)

9. Prompt 设计原则

9.1 Prompt 所在层级

Prompt 仅存在于 Browser-Use Adapter 内部
Agent 只表达“动作意图”。

9.2 Prompt 类型
类型 说明
执行型 Prompt 搜索 / 点击 / 滚动
提取型 Prompt 按规则抽取文本

9.3 执行型 Prompt 示例

```shell
Perform only the requested action.
Do not explain.
Do not add extra steps.
```

10. Browser-Use 返回结果规范

10.1 标准返回结构

```json
{
  "success": true,
  "meta": {
    "url": "",
    "title": ""
  },
  "content": {
    "text": ""
  },
  "error": null
}
```

10.2 错误处理原则
• 错误属于正常路径
• Browser-Use 不做业务判断
• Agent 决定是否跳过或重试

11. LLM 配置与职责

11.1 LLM 模型配置（MVP）

使用 DeepSeek Chat 作为 LLM 模型：

browser_use 中集成 deepseek 的方式如下，详细见：https://github.com/browser-use/browser-use/blob/main/examples/models/deepseek-chat.py

```python
from browser_use.llm import ChatDeepSeek

llm = ChatDeepSeek(
    base_url='https://api.deepseek.com/v1',
    model='deepseek-chat',
    api_key=os.getenv('DEEPSEEK_API_KEY'),
)
```

配置要求：
• 从环境变量 `DEEPSEEK_API_KEY` 读取 API Key
• 使用官方 API 地址：`https://api.deepseek.com/v1`
• 模型名称：`deepseek-chat`

11.2 LLM 在 Agent 中的职责

仅承担三类任务：

• 内容相关性判断（true / false）
• 结构化字段提取
• 简短洞察总结

11.3 结构化输出示例

```json
{
  "brand": "",
  "campaign_theme": "",
  "creative_type": "",
  "strategy": [],
  "insights": []
}
```

约束：
• 不返回原文
• 字段数量固定

12. 数据模型（Agent 输出）

```python
class MarketingCase(BaseModel):
    platform: str
    brand: str
    theme: str
    creative_type: str
    strategy: list[str]
    insights: list[str]
    source_url: str
```

Agent 仅输出结构化结果，不存原始内容。

13. 单任务执行流程

```shell
接收任务
 → 打开平台
 → 搜索关键词
 → 解析列表页
 → LLM 判断相关性
 → 打开详情页
 → 提取结构化信息
 → 返回结果
```

14. 性能与限制（MVP 硬约束）
    项目 限制
    最大详情数 10
    最大页数 3
    最大操作步数 100
    单条超时 60 秒

15. 异常与风控策略
    • 页面异常直接跳过
    • 最多重试 1 次
    • 不绕过登录
    • 不处理验证码
    • 不模拟复杂人类行为

16. MVP 成功标准
    • 连续运行 ≥ 10 次不崩溃
    • 同类任务结果差异 < 20%
    • 不执行多余操作
    • 不触发平台风控

17. MVP 成功标准
    • 连续运行 ≥ 10 次不崩溃
    • 同类任务结果差异 < 20%
    • 不执行多余操作
    • 不触发平台风控

18. 非 MVP 范围（未来演进）
    • 多平台 Adapter
    • 多 Agent 并行
    • 云端任务调度
    • 企业级知识库
