# 下一步操作指南

## ✅ 已完成

- ✅ 阶段一：基础设施搭建（配置管理、日志系统、异常处理）
- ✅ 阶段二：核心模块开发（数据模型、状态机、LLM 客户端、Browser-Use Adapter）
- ✅ 依赖管理文件（requirements.txt, DEPENDENCIES.md）

## 📋 当前任务：验证配置并继续开发

### 步骤 1：确认 .env 文件位置

`.env` 文件应该放在 `technical-solution/ad-browser/` 目录下（与 `agent/` 目录同级）。

**检查方法**：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
ls -la .env
```

**如果文件不存在，创建它**：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
cat > .env << 'EOF'
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
EOF
```

**重要**：将 `your_api_key_here` 替换为你的实际 DeepSeek API Key。

### 步骤 2：验证配置加载

运行测试脚本验证配置是否正确加载：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
DEEPSEEK_API_KEY=your_key python3 agent/tests/test_stage1.py
```

或者直接测试配置加载：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 -c "from agent.config import get_settings; s = get_settings(); print(f'✅ 配置加载成功'); print(f'   API Key: {s.deepseek_api_key[:10]}...'); print(f'   Base URL: {s.deepseek_base_url}'); print(f'   Model: {s.deepseek_model}')"
```

### 步骤 3：安装依赖（如果尚未安装）

```bash
# 确保在虚拟环境中
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser

# 如果使用 UV（推荐）
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r agent/requirements.txt
uvx browser-use install  # 安装 Chromium

# 或使用传统 pip
pip install -r agent/requirements.txt
```

### 步骤 4：运行阶段二测试

验证所有核心模块是否正常工作：

```bash
cd /Users/bing/Documents/AI-AD/technical-solution/ad-browser
python3 agent/tests/test_stage2.py
```

### 步骤 5：继续开发

根据开发计划，下一步是 **阶段三：业务逻辑实现**：

#### 任务 3.1：列表页解析器 (`agent/extractor/list_parser.py`)

- 解析列表页结构
- 提取列表项链接
- 实现分页逻辑

#### 任务 3.2：详情页解析器 (`agent/extractor/detail_parser.py`)

- 解析详情页内容
- 提取结构化数据
- 调用 LLM 进行提取

#### 任务 3.3：任务控制器 (`agent/controller/task_controller.py`)

- 整合状态机、Browser Adapter、LLM Client
- 实现完整任务流程
- 处理错误和重试

### 步骤 6：测试完整流程（可选）

如果阶段三已完成，可以测试完整的任务执行流程：

```python
# 示例：测试任务执行
from agent.controller.task_controller import TaskController
from agent.models.task_schema import TaskRequest

task = TaskRequest(
    task_id="test-001",
    platform="xiaohongshu",
    keywords=["春节营销"],
    max_items=5
)

controller = TaskController()
result = await controller.execute_task(task)
print(result)
```

## 🔍 常见问题

### Q1: 配置加载失败

**错误信息**：`Field required [type=missing, input_value={}, input_type=dict]`

**解决方法**：

1. 确认 `.env` 文件在正确位置（`technical-solution/ad-browser/.env`）
2. 确认 `.env` 文件格式正确（每行一个键值对，无多余空格）
3. 确认 `DEEPSEEK_API_KEY` 已设置

### Q2: browser-use 导入失败

**错误信息**：`无法导入 browser_use`

**解决方法**：

```bash
uv pip install browser-use
uvx browser-use install
```

### Q3: 测试失败

**解决方法**：

- 检查是否在虚拟环境中
- 检查依赖是否完整安装
- 查看测试输出中的具体错误信息

## 📚 参考文档

- [技术设计文档](./AGET-TECH_MVP.md)
- [开发计划](./DEVELOPMENT_PLAN.md)
- [依赖管理说明](./agent/DEPENDENCIES.md)
- [Agent README](./agent/README.md)

## 🎯 下一步建议

1. **立即执行**：验证配置加载（步骤 2）
2. **短期目标**：完成阶段三任务（列表页/详情页解析器、任务控制器）
3. **中期目标**：实现阶段四（WebSocket 服务器、协议处理）
4. **长期目标**：端到端测试和优化
