# Ad Browser - 本地智能研究工具

面向广告营销创意策划师的本地智能研究工具 MVP，帮助策划师高效研究公开营销案例，将碎片内容转化为结构化、可复用的营销知识。

## 📋 项目简介

Ad Browser 是一个基于 Browser-Use Agent 的本地智能研究工具，通过浏览器自动化技术帮助用户：

- 🔍 **高效研究**：自动搜索和收集公开营销案例
- 📊 **结构化提取**：将碎片内容转化为结构化数据
- 💡 **洞察生成**：从案例中提取可复用的营销方法论
- 🎯 **知识沉淀**：构建行业级营销洞察知识库

## 🏗️ 项目结构

```
ad-browser/
├── agent/                    # Agent 核心模块
│   ├── browser/              # 浏览器适配器
│   ├── controller/           # 任务控制器
│   ├── extractor/            # 内容提取器
│   ├── llm/                  # LLM 客户端
│   ├── models/               # 数据模型
│   ├── server/               # WebSocket 服务器
│   ├── tests/                # 测试文件
│   └── utils/                # 工具模块
├── docs/                     # 项目文档
│   ├── design/               # 设计文档
│   ├── development/          # 开发文档
│   ├── references/           # 参考资料
│   └── requirements/         # 需求文档
├── scripts/                  # 工具脚本
│   ├── start_agent.sh        # 启动 Agent 服务器
│   ├── run_direct_test.sh    # 运行直接测试
│   ├── run_real_test.sh      # 运行真实用例测试
│   └── check_port.sh         # 检查端口占用
└── README.md                  # 本文件
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Playwright
- Chrome 浏览器（用于保持登录状态）

### 安装步骤

1. **安装依赖**

```bash
cd agent
pip install -r requirements.txt
playwright install chromium
```

2. **配置环境变量**

创建 `.env` 文件（参考 `agent/README.md` 中的配置说明）：

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

3. **启动 Agent 服务器**

```bash
./scripts/start_agent.sh
```

或直接运行：

```bash
cd agent
python3 -m agent.main
```

### 运行测试

```bash
# 直接测试（绕过 WebSocket）
./scripts/run_direct_test.sh

# 真实用例测试
./scripts/run_real_test.sh
```

## 📚 文档索引

### 需求与设计

- [产品需求文档 (PRD)](docs/design/PRD-MVP.md) - 产品功能需求与用户场景
- [技术设计文档](docs/design/AGET-TECH_MVP.md) - 技术架构与实现方案
- [需求文档](docs/requirements/requirement.md) - 详细需求说明

### 开发文档

- [开发计划](docs/development/DEVELOPMENT_PLAN.md) - 详细的开发计划与任务分解
- [下一步操作指南](docs/development/NEXT_STEPS.md) - 当前进度与下一步操作
- [真实用例测试指南](docs/development/REAL_CASE_TEST.md) - 测试用例说明

### 参考资料

- [文档索引](docs/references/REFERENCES.md) - 相关文档链接索引

### Agent 模块文档

- [Agent README](agent/README.md) - Agent 模块详细说明
- [Agent 使用指南](agent/USAGE.md) - Agent 使用说明
- [依赖说明](agent/DEPENDENCIES.md) - 项目依赖详细说明

## 🛠️ 开发状态

### ✅ 已完成

- **阶段一**：基础设施搭建（配置管理、日志系统、异常处理）
- **阶段二**：核心模块开发（状态机、Browser-Use Adapter、LLM 客户端、数据模型）
- **阶段三**：任务执行引擎（任务控制器、提取器模块）
- **阶段四**：通信与集成（WebSocket 服务器、消息协议）

### 🔄 进行中

- **阶段五**：测试与优化

详细开发状态请参考 [开发计划](docs/development/DEVELOPMENT_PLAN.md)。

## 🎯 核心特性

- ✅ **智能搜索**：自动在小红书等平台搜索营销案例
- ✅ **内容提取**：从搜索结果中提取结构化信息
- ✅ **相关性过滤**：使用 LLM 判断案例相关性
- ✅ **模态提取**：从弹层中提取详细信息，避免 404 错误
- ✅ **状态管理**：完整的状态机管理任务执行流程
- ✅ **WebSocket 通信**：支持实时任务状态更新

## 📝 技术栈

- **Python 3.10+** - 主要开发语言
- **Playwright** - 浏览器自动化
- **Browser-Use** - AI 驱动的浏览器操作
- **DeepSeek Chat** - LLM 服务
- **WebSocket** - 实时通信协议
- **Pydantic** - 数据验证与序列化

## 🤝 贡献指南

1. 查看 [开发计划](docs/development/DEVELOPMENT_PLAN.md) 了解当前任务
2. 阅读 [技术设计文档](docs/design/AGET-TECH_MVP.md) 了解架构
3. 运行测试确保代码质量
4. 提交 Pull Request

## 📄 许可证

[待定]

## 🔗 相关链接

- [Browser-Use 官方文档](https://github.com/browser-use/browser-use)
- [Playwright 文档](https://playwright.dev/python/)

---

**注意**：本项目仅用于研究和学习目的，请遵守相关平台的使用条款和法律法规。
