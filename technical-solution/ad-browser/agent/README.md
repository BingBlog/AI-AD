# Ad Browser Agent

本地智能研究工具 Agent 模块

## 项目结构

```
agent/
├── __init__.py              # 包初始化文件
├── main.py                  # Agent 启动入口（✅ 阶段四完成）
├── config.py                # 配置管理（✅ 阶段一完成）
├── exceptions.py            # 异常处理框架（✅ 阶段一完成）
├── server/                  # WebSocket 服务器模块
│   ├── __init__.py
│   ├── ws_server.py         # WebSocket 服务器（阶段四实现）
│   └── protocol.py          # 消息协议（阶段四实现）
├── controller/              # 控制器模块
│   ├── __init__.py
│   ├── task_controller.py  # 任务控制器（阶段三实现）
│   └── state_machine.py     # 状态机（阶段二实现）
├── browser/                 # Browser-Use Adapter 模块
│   ├── __init__.py
│   ├── adapter.py           # Browser-Use Adapter（阶段二实现）
│   └── actions.py           # Browser Actions 接口（阶段二实现）
├── llm/                     # LLM 客户端模块
│   ├── __init__.py
│   ├── client.py            # LLM 客户端（阶段二实现）
│   └── prompts.py          # Prompt 模板（阶段二实现）
├── extractor/              # 提取器模块
│   ├── __init__.py
│   ├── list_parser.py      # 列表页解析器（阶段三实现）
│   └── detail_parser.py    # 详情页解析器（阶段三实现）
├── models/                  # 数据模型模块
│   ├── __init__.py
│   ├── case_schema.py       # 营销案例模型（阶段二实现）
│   └── task_schema.py       # 任务模型（阶段二实现）
├── utils/                   # 工具模块
│   ├── __init__.py
│   └── logger.py            # 日志系统（✅ 阶段一完成）
└── tests/                   # 测试目录
    ├── __init__.py
    └── test_stage1.py        # 阶段一验收测试（✅ 完成）
```

## 开发状态

### 阶段一：基础设施搭建 ✅ 已完成

- ✅ **任务 1.1**: 项目结构初始化
  - 所有目录和文件创建完成
  - 所有 `__init__.py` 文件存在
  - 项目结构符合技术文档第 4 节要求

- ✅ **任务 1.2**: 配置管理模块 (`agent/config.py`)
  - ✅ 从 `.env` 文件加载配置
  - ✅ 所有 MVP 硬约束参数可配置（第 14 节）
  - ✅ 配置验证逻辑正确
  - ✅ 提供默认值
  - ✅ 延迟加载机制，避免导入时错误

- ✅ **任务 1.3**: 日志系统 (`agent/utils/logger.py`)
  - ✅ 支持不同日志级别（DEBUG, INFO, WARNING, ERROR）
  - ✅ 控制台和文件输出
  - ✅ 日志格式清晰易读
  - ✅ 避免重复添加处理器

- ✅ **任务 1.4**: 异常处理框架 (`agent/exceptions.py`)
  - ✅ 自定义异常类定义完整
  - ✅ 异常处理逻辑清晰
  - ✅ 符合第 15 节异常策略
  - ✅ 提供异常详情和错误代码

### 阶段二：核心模块开发 ✅ 已完成

- ✅ **任务 2.1**: 数据模型实现 (`agent/models/`)
  - ✅ `MarketingCase` 数据模型
  - ✅ `TaskRequest`、`TaskStatus` 任务模型
  - ✅ 协议层消息模型

- ✅ **任务 2.2**: 状态机实现 (`agent/controller/state_machine.py`)
  - ✅ 状态枚举和转换逻辑
  - ✅ 状态回调机制
  - ✅ 状态历史记录
  - ✅ 进度映射

- ✅ **任务 2.3**: LLM 客户端实现 (`agent/llm/`)
  - ✅ DeepSeek Chat 集成（支持延迟导入）
  - ✅ 三类 LLM 任务：相关性判断、结构化提取、洞察生成
  - ✅ JSON 容错解析

- ✅ **任务 2.4**: Browser-Use Adapter 实现 (`agent/browser/`)
  - ✅ 动作级 API（open_page、search、scroll、open_item、extract）
  - ✅ 固定执行型 Prompt（不暴露自由 Prompt）
  - ✅ 标准化返回结果
  - ✅ 自然语言驱动浏览器测试通过

### 阶段三：任务执行引擎 ✅ 已完成

- ✅ **任务 3.1**: 提取器模块实现 (`agent/extractor/`)
  - ✅ 列表页解析器（支持分页、去重、容错）
  - ✅ 详情页解析器（集成 LLM 提取）
  - ✅ 错误处理完善

- ✅ **任务 3.2**: 任务控制器实现 (`agent/controller/task_controller.py`)
  - ✅ 完整任务执行流程（第 13 节）
  - ✅ 状态机集成
  - ✅ LLM 相关性过滤
  - ✅ 符合 MVP 硬约束
  - ✅ 异常处理符合第 15 节策略

### 阶段四：通信与集成 ✅ 已完成

- ✅ **任务 4.1**: 消息协议实现 (`agent/server/protocol.py`)
  - ✅ 消息序列化/反序列化
  - ✅ 消息验证
  - ✅ 支持所有消息类型（START_TASK、STATUS_UPDATE、TASK_RESULT、ERROR）

- ✅ **任务 4.2**: WebSocket 服务器实现 (`agent/server/ws_server.py`)
  - ✅ 客户端连接处理
  - ✅ 消息路由
  - ✅ 状态更新实时推送
  - ✅ 任务执行管理
  - ✅ 优雅关闭

- ✅ **任务 4.3**: Agent 启动入口 (`agent/main.py`)
  - ✅ WebSocket 服务器集成
  - ✅ 信号处理（SIGINT、SIGTERM）
  - ✅ 优雅关闭机制

### 测试验证

运行测试脚本验证所有模块：

```bash
# 设置环境变量后运行测试
DEEPSEEK_API_KEY=your_key python3 agent/tests/test_stage1.py
```

测试覆盖：
- ✅ 配置加载和验证（test_stage1.py）
- ✅ 日志系统功能（test_stage1.py）
- ✅ 异常类定义和使用（test_stage1.py）
- ✅ 核心模块功能（test_stage2.py）
- ✅ 任务执行引擎（test_stage3.py）
- ✅ 通信与集成（test_stage4.py）

## 依赖管理

### 安装依赖

项目使用 **UV** 作为包管理工具（参考技术文档 `AGET-TECH_MVP.md` 第 1.3 节）。

**方式一：使用 requirements.txt（推荐）**

```bash
# 1. 安装 UV（如果未安装）
pip install uv

# 2. 创建并激活虚拟环境
uv venv --python 3.12
source .venv/bin/activate

# 3. 安装依赖
uv pip install -r requirements.txt

# 4. 安装 Browser-Use 的 Chromium（必需）
uvx browser-use install
```

**方式二：手动安装**

```bash
uv pip install pydantic pydantic-settings python-dotenv browser-use websockets
```

### 依赖说明

- **核心依赖**（必需）：
  - `pydantic` - 数据验证和模型定义
  - `pydantic-settings` - 配置管理
  - `python-dotenv` - 环境变量加载

- **运行时依赖**：
  - `browser-use` - Browser-Use 框架（延迟导入，未安装时会抛出异常）
  - `websockets` - WebSocket 服务器（阶段四需要）

- **开发依赖**（可选）：
  - `pytest` - 测试框架
  - `pytest-asyncio` - 异步测试支持

详细说明请参考 [DEPENDENCIES.md](./DEPENDENCIES.md)。

## 配置说明

### 环境变量配置

创建 `.env` 文件（参考技术文档 `AGET-TECH_MVP.md` 的 1.3.5 小节示例）：

```bash
# DeepSeek API 配置（必需）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 性能限制（MVP 硬约束）
MAX_ITEMS=10
MAX_PAGES=3
MAX_STEPS=100
TIMEOUT_PER_ITEM=60

# WebSocket 配置
WS_HOST=localhost
WS_PORT=8765

# 日志配置
LOG_LEVEL=INFO
# LOG_FILE=logs/agent.log  # 可选
```

### 使用示例

```python
# 使用配置
from agent.config import settings
print(settings.max_items)  # 10

# 使用日志
from agent.utils.logger import setup_logger
logger = setup_logger("my_module")
logger.info("这是一条日志")

# 使用异常
from agent.exceptions import TaskException
raise TaskException("任务执行失败", task_id="task-123")
```

## 启动 Agent

启动 WebSocket 服务器：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 agent/main.py
```

服务器将在 `ws://localhost:8765` 上监听连接。

## 下一步

按照 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) 继续开发：

**阶段五：测试与优化**
1. **任务 5.1**：单元测试（覆盖率 ≥ 70%）
2. **任务 5.2**：集成测试（完整任务流程）
3. **任务 5.3**：MVP 成功标准验证（第 16 节）
4. **任务 5.4**：性能优化（可选）

## 参考文档

- [技术设计文档](../AGET-TECH_MVP.md)
- [开发计划](../DEVELOPMENT_PLAN.md)
- [文档索引](../REFERENCES.md)
