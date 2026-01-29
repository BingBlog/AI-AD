# 依赖管理说明

## 当前状态

**agent 目录目前没有正式的依赖管理文件**，依赖通过以下方式管理：

### 1. 隐式依赖管理

依赖通过代码中的 `import` 语句隐式声明，主要包括：

#### 核心依赖（必需）

- **pydantic** (`>=2.0.0`) - 数据验证和模型定义

  - 使用位置：`models/`, `config.py`
  - 用途：数据模型验证、配置管理

- **pydantic-settings** (`>=2.0.0`) - 配置管理

  - 使用位置：`config.py`
  - 用途：从环境变量加载配置

- **python-dotenv** (`>=1.0.0`) - 环境变量加载
  - 使用位置：`config.py`
  - 用途：加载 `.env` 文件

#### 可选依赖（延迟导入）

- **browser-use** (`>=1.0.0`) - Browser-Use 框架

  - 使用位置：`browser/adapter.py`, `llm/client.py`
  - 导入方式：延迟导入（`try/except`），避免未安装时失败
  - 用途：浏览器自动化、LLM 集成

- **websockets** (`>=12.0`) - WebSocket 服务器
  - 使用位置：`server/ws_server.py`（阶段四实现）
  - 状态：尚未实现，占位文件

### 2. 依赖安装方式

根据技术文档 `AGET-TECH_MVP.md` 第 1.3 节，项目使用 **UV** 作为包管理工具：

```bash
# 1. 安装 UV
pip install uv

# 2. 创建虚拟环境
uv venv --python 3.12

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 安装依赖（手动安装）
uv pip install pydantic pydantic-settings python-dotenv browser-use websockets

# 或使用 requirements.txt（如果存在）
uv pip install -r requirements.txt
```

### 3. 延迟导入策略

代码中使用了**延迟导入**策略，避免依赖未安装时导入失败：

**示例 1：Browser-Use Adapter**

```python
# agent/browser/adapter.py
def _default_runner(self, task: str) -> Any:
    try:
        from browser_use import Agent  # type: ignore
        from browser_use.llm import ChatDeepSeek  # type: ignore
    except ImportError as e:
        raise BrowserAdapterException(f"无法导入 browser_use: {e}")
```

**示例 2：LLM Client**

```python
# agent/llm/client.py
def _init_llm(self):
    try:
        from browser_use.llm import ChatDeepSeek  # type: ignore
    except ImportError as e:
        raise LLMException(f"无法导入 ChatDeepSeek: {e}")
```

### 4. 依赖分类

#### 必需依赖（Core Dependencies）

- `pydantic` - 数据模型验证
- `pydantic-settings` - 配置管理
- `python-dotenv` - 环境变量

#### 运行时依赖（Runtime Dependencies）

- `browser-use` - 浏览器自动化（MVP 必需）
- `websockets` - WebSocket 通信（阶段四）

#### 开发依赖（Development Dependencies）

- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持

### 5. 当前问题

1. **缺少依赖声明文件**

   - 没有 `requirements.txt`
   - 没有 `pyproject.toml`
   - 没有 `setup.py`

2. **依赖版本未锁定**

   - 没有指定具体版本号
   - 可能导致不同环境版本不一致

3. **依赖安装文档不完整**
   - README 中只提到了 `python-dotenv`
   - 没有完整的依赖安装说明

### 6. 建议改进

#### 方案一：创建 requirements.txt（推荐）

已在 `agent/requirements.txt` 中创建依赖清单。

**优点**：

- 简单直接
- 与 UV 兼容
- 易于维护

**使用方式**：

```bash
uv pip install -r agent/requirements.txt
```

#### 方案二：创建 pyproject.toml（更现代）

可以创建 `pyproject.toml` 文件，使用现代 Python 项目标准。

**优点**：

- 符合 PEP 518/621 标准
- 支持项目元数据
- 支持构建工具配置

**示例结构**：

```toml
[project]
name = "ad-browser-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "browser-use>=1.0.0",
    "websockets>=12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

## 总结

**当前依赖管理方式**：

- ✅ 使用 UV 作为包管理工具（符合技术文档）
- ✅ 延迟导入策略，避免依赖未安装时失败
- ⚠️ 缺少正式的依赖声明文件
- ⚠️ 依赖版本未锁定

**建议**：

1. 使用已创建的 `requirements.txt` 管理依赖
2. 在 README 中添加依赖安装说明
3. 考虑添加版本锁定文件（`requirements-lock.txt`）
