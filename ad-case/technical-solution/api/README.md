# 广告案例库 API 服务

## 项目结构

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py              # 数据库连接
│   ├── models/                  # 数据模型
│   ├── schemas/                 # Pydantic 模式
│   │   └── response.py          # 响应模型
│   ├── services/                # 业务逻辑层
│   ├── repositories/            # 数据访问层
│   └── routers/                 # 路由
│       └── health.py           # 健康检查路由
├── requirements.txt
├── env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd api
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并修改配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置数据库连接信息：

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ad_case_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. 启动服务

开发环境（支持热重载）：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

生产环境：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API 端点

### 健康检查
- `GET /health` - 健康检查接口

### 根路径
- `GET /` - API 基本信息

## 开发说明

### 项目结构说明

- **app/main.py**: FastAPI 应用入口，注册路由和中间件
- **app/config.py**: 配置管理，使用 Pydantic Settings 从环境变量读取配置
- **app/database.py**: 数据库连接池管理，使用 asyncpg
- **app/schemas/**: Pydantic 模式定义，用于请求/响应验证
- **app/routers/**: API 路由定义
- **app/services/**: 业务逻辑层（待实现）
- **app/repositories/**: 数据访问层（待实现）

### 数据库连接

使用 asyncpg 连接池管理数据库连接，支持异步操作。

### 响应格式

所有 API 响应遵循统一格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

错误响应：

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null,
  "errors": [
    {
      "field": "page",
      "message": "页码必须大于0"
    }
  ]
}
```

## 下一步

按照开发计划，接下来将实现：
- 阶段二：核心检索功能（关键词检索、语义检索、混合检索）
- 阶段三：辅助功能（案例详情、相似案例推荐等）
