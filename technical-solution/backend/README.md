# 广告案例库 API 服务

## 项目结构

```
backend/
├── app/                        # FastAPI 应用
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models/                 # 数据模型
│   ├── schemas/                # Pydantic 模式
│   ├── services/               # 业务逻辑层
│   ├── repositories/           # 数据访问层
│   └── routers/                # 路由
├── services/                   # 服务模块（pipeline、spider）
│   ├── pipeline/               # 数据管道
│   └── spider/                 # 爬虫模块
├── scripts/                     # 脚本工具
│   ├── crawl.py                # 爬取脚本
│   ├── import.py               # 入库脚本
│   └── validate.py             # 验证脚本
├── database/                   # 数据库脚本
│   ├── init.sql                # 初始化脚本
│   └── migrations/             # 迁移脚本
├── data/                       # 数据文件
│   ├── json/                   # JSON 数据文件
│   └── samples/                # 示例文件
├── tests/                       # 测试文件
├── requirements.txt
├── env.example
├── run.py                       # 启动脚本
└── README.md
```

## 快速开始

### 1. 创建并激活虚拟环境

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `env.example` 为 `.env` 并修改配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置关键配置：

```env
# API 配置（开发环境默认启用热重载）
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # 开发环境启用热重载

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ad_case_db  # ⚠️ 固定值，不要修改
DB_USER=postgres    # 根据实际情况修改
DB_PASSWORD=        # 根据实际情况修改

# 向量模型配置（必须配置本地模型路径）
VECTOR_MODEL_PATH=/path/to/bge-large-zh-v1.5  # 本地模型目录路径
VECTOR_OFFLINE_MODE=true  # 离线模式，使用本地模型
```

### 4. 启动服务

**⚠️ 重要：必须使用统一启动脚本启动服务**

#### 方式一：使用统一启动脚本（必须，推荐）

```bash
# macOS/Linux
cd ../technical-solution
./start.sh

# Windows
cd ..\technical-solution
start.bat
```

启动脚本会自动：

- ✅ 检查项目结构
- ✅ 检查后端环境配置（.env 文件）
- ✅ 检查数据库连接
- ✅ 检查并激活 Python 虚拟环境
- ✅ 检查前端依赖
- ✅ 启动后端和前端服务

#### 方式二：手动启动（仅当启动脚本完全不可用时使用）

**⚠️ 警告：只有在启动脚本完全不可用的情况下才使用此方式**

开发环境（支持热重载，默认）：

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 使用 run.py 启动（自动启用热重载）
python run.py
```

启动时会看到：

```
✅ 热重载已启用，监视目录: ['/path/to/backend/app']
🚀 启动后端服务: http://0.0.0.0:8000
📚 API 文档: http://0.0.0.0:8000/docs
```

生产环境（禁用热重载，使用多 worker）：

在 `.env` 中设置：

```env
API_RELOAD=false
API_WORKERS=4
```

然后使用 `run.py` 启动：

```bash
python run.py
```

**⚠️ 重要提示**:

- ⚠️ **必须使用统一启动脚本 `start.sh` 或 `start.bat` 启动服务**
- ⚠️ **禁止直接运行 `python run.py`**，必须通过启动脚本
- ⚠️ **禁止直接使用 `uvicorn` 命令启动**
- ⚠️ 启动脚本会自动处理虚拟环境激活、配置检查等
- ⚠️ 开发环境默认 `API_RELOAD=true`，修改代码会自动重启
- ⚠️ 数据库名称固定为 `ad_case_db`，不要修改
- ⚠️ 必须配置 `VECTOR_MODEL_PATH` 指向本地模型目录

### 5. 访问 API 文档

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

## 常见问题

### 热重载不工作

如果修改代码后服务没有自动重启：

1. 检查 `.env` 文件中 `API_RELOAD=true` 是否设置
2. 确认使用的是 `run.py` 启动（不是直接使用 `uvicorn`）
3. 查看启动日志，确认是否显示 "✅ 热重载已启用"
4. 如果仍然不工作，尝试重新安装依赖: `pip install -r requirements.txt --upgrade`

### 数据库连接失败

1. 检查 PostgreSQL 服务是否启动
2. 检查数据库 `ad_case_db` 是否存在
3. 检查 `.env` 中的数据库配置是否正确
4. 验证连接: `psql -h localhost -p 5432 -U postgres -d ad_case_db -c "SELECT 1;"`

### 向量模型加载失败

1. 检查 `VECTOR_MODEL_PATH` 是否配置且路径正确
2. 检查模型文件是否存在
3. 设置 `VECTOR_OFFLINE_MODE=true` 确保使用本地模型

### 虚拟环境问题

如果提示模块未找到：

1. 确认虚拟环境已激活: `which python` 应该指向 `venv/bin/python`
2. 重新激活虚拟环境: `source venv/bin/activate`
3. 如果虚拟环境不存在，创建并安装依赖（见上方步骤 1-2）

## 下一步

按照开发计划，接下来将实现：

- 阶段二：核心检索功能（关键词检索、语义检索、混合检索）
- 阶段三：辅助功能（案例详情、相似案例推荐等）

## 相关文档

- 详细配置说明: `../SETUP.md`
- 平台技术方案总览: `../README.md`
- 广告案例库文档: `../AD_CASE_LIBRARY.md`
- 数据库文档: `database/README.md`
