# 广告案例库项目

## 项目简介

广告案例库是一个完整的广告案例检索系统，包含数据爬取、数据处理、后端API服务和前端展示应用。

## 项目结构

```
technical-solution/
├── README.md                   # 本文件
├── backend/                    # 后端API服务
│   ├── app/                    # 应用代码
│   ├── tests/                  # 测试文件
│   ├── requirements.txt        # Python依赖
│   ├── env.example            # 环境变量模板
│   └── run.py                 # 启动脚本
├── frontend/                   # 前端应用
│   ├── src/                   # 源代码
│   ├── package.json           # 项目配置
│   └── vite.config.ts         # Vite配置
├── services/                   # 服务和工具
│   ├── pipeline/              # 数据处理管道
│   └── spider/                # 爬虫服务
├── scripts/                    # 脚本工具
│   ├── crawl.py               # 爬取脚本
│   ├── import.py              # 导入脚本
│   └── ...
├── database/                   # 数据库相关
│   ├── init.sql               # 初始化脚本
│   └── README.md              # 数据库文档
├── data/                       # 数据文件
│   ├── json/                  # JSON数据文件
│   └── samples/               # 示例文件
└── docs/                       # 项目文档
    ├── design/                # 设计文档
    ├── api/                   # API文档
    └── verification/          # 验证文档
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- pnpm 或 npm

### 1. 后端服务

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，设置数据库连接信息

# 启动服务
python run.py
```

服务将在 http://localhost:8000 启动。

### 2. 前端应用

```bash
# 进入前端目录
cd frontend

# 安装依赖
pnpm install

# 配置环境变量
cp env.example .env.local

# 启动开发服务器
pnpm run dev
```

应用将在 http://localhost:3000 启动。

### 3. 数据爬取和导入

```bash
# 爬取数据
python scripts/crawl.py --output-dir data/json

# 导入数据到数据库
python scripts/import.py \
  --json-dir data/json \
  --db-name ad_case_db \
  --db-user postgres \
  --db-password your_password
```

## 项目模块说明

### Backend（后端服务）

基于 FastAPI 构建的 RESTful API 服务，提供案例检索、筛选等功能。

- **技术栈**: FastAPI, asyncpg, Pydantic
- **架构**: 分层架构（routers → services → repositories）
- **文档**: 见 `backend/README.md`

### Frontend（前端应用）

基于 React + TypeScript 构建的单页面应用。

- **技术栈**: React 18, TypeScript, Ant Design, Vite
- **状态管理**: Zustand
- **数据获取**: React Query
- **文档**: 见 `frontend/README.md`

### Services（服务模块）

#### Pipeline（数据处理管道）

负责数据验证、清洗和导入。

- `crawl_stage.py`: 爬取阶段
- `import_stage.py`: 导入阶段
- `validator.py`: 数据验证
- `utils.py`: 工具函数

#### Spider（爬虫服务）

负责从广告门网站爬取案例数据。

- `api_client.py`: API客户端
- `detail_parser.py`: 详情页解析器
- `csrf_token_manager.py`: CSRF令牌管理

### Scripts（脚本工具）

各种辅助脚本，包括：

- `crawl.py`: 爬取数据脚本
- `import.py`: 数据导入脚本
- `validate.py`: 数据验证脚本
- `update_vectors.py`: 向量更新脚本

### Database（数据库）

PostgreSQL 数据库脚本和文档。

- `init.sql`: 数据库初始化脚本（包含向量扩展）
- `init_without_vector.sql`: 不包含向量的初始化脚本
- `README.md`: 数据库使用文档

### Data（数据文件）

- `json/`: JSON格式的案例数据
- `samples/`: 示例HTML文件

### Docs（文档）

项目相关文档。

- `design/`: 设计文档（API设计、数据库设计、前端设计等）
- `api/`: API文档
- `verification/`: 验证和测试文档

## 开发指南

### 代码规范

- **Python**: 遵循 PEP 8，使用类型提示
- **TypeScript**: 使用 ESLint 和 TypeScript 严格模式
- **提交信息**: 使用清晰的提交信息，遵循约定式提交

### 测试

```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd frontend
pnpm test
```

### 环境变量

各模块都有对应的环境变量配置文件（`env.example`），请参考对应目录的 README。

## 部署

### 后端部署

推荐使用 Docker 或直接在服务器上运行。

```bash
# 生产环境启动
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端部署

```bash
# 构建生产版本
cd frontend
pnpm run build

# 预览构建结果
pnpm run preview
```

构建产物在 `dist/` 目录，可以部署到 Nginx、Vercel 等静态文件服务器。

## 常见问题

详见各模块的 README 文档。

## 许可证

[根据实际情况添加许可证信息]
