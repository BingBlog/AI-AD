# 项目配置和启动指南

本文档记录项目的关键配置信息，避免数据丢失、环境错误等问题。

## ⚠️ 重要提示

在启动项目前，请务必确认以下配置：

1. **数据库配置**：确保使用正确的数据库，避免数据丢失
2. **虚拟环境**：确保使用正确的 Python 虚拟环境
3. **向量模型**：确保使用本地模型路径，避免在线下载失败
4. **启动脚本**：使用统一的启动脚本 `start.sh`

## 📋 项目配置信息

### 数据库配置

**数据库名称**: `ad_case_db`

**连接信息**（在 `backend/.env` 中配置）:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ad_case_db
DB_USER=bing          # 根据实际情况修改
DB_PASSWORD=          # 根据实际情况修改
```

**重要提示**:

- ⚠️ 确保数据库名称正确，避免连接到错误的数据库
- ⚠️ 定期备份数据库，避免数据丢失
- ⚠️ 开发环境不要使用生产数据库

**数据库验证命令**:

```bash
psql -h localhost -p 5432 -U bing -d ad_case_db -c "SELECT 1;"
```

### Python 虚拟环境

**虚拟环境位置**（推荐）:

- `${PROJECT_ROOT}/backend/venv`
- `${PROJECT_ROOT}/backend/.venv`
- `${PROJECT_ROOT}/venv`
- `${PROJECT_ROOT}/.venv`

**创建虚拟环境**:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

**重要提示**:

- ⚠️ 每次启动前确认虚拟环境已激活
- ⚠️ 不要在系统 Python 环境中安装依赖
- ⚠️ 使用 `which python` 或 `where python` 确认 Python 路径

### 向量模型配置

**模型信息**:

- 模型名称: `BAAI/bge-large-zh-v1.5`
- 向量维度: 1024
- 推荐使用本地模型路径

**配置位置**: `backend/.env`

```env
# 向量模型配置（重要：使用本地模型路径）
VECTOR_MODEL_PATH=/path/to/bge-large-zh-v1.5  # 本地模型路径
VECTOR_DIMENSION=1024
VECTOR_OFFLINE_MODE=true  # 离线模式，避免请求 HuggingFace
```

**重要提示**:

- ⚠️ **必须配置 `VECTOR_MODEL_PATH`** 指向本地模型目录
- ⚠️ 设置 `VECTOR_OFFLINE_MODE=true` 确保使用本地模型
- ⚠️ 如果未配置本地路径，可能尝试在线下载，导致失败

**下载模型**（如果还没有）:

```bash
# 使用 huggingface-cli 下载
huggingface-cli download BAAI/bge-large-zh-v1.5 --local-dir /path/to/bge-large-zh-v1.5
```

### 后端服务配置

**启动脚本**: `backend/run.py`

**配置文件**: `backend/.env`

**关键配置项**:

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# 数据库配置（见上方）
# 向量模型配置（见上方）

# 日志配置
LOG_LEVEL=INFO
```

**启动方式**:

```bash
# 方式1：使用统一启动脚本（推荐）
cd technical-solution
./start.sh

# 方式2：手动启动
cd backend
source venv/bin/activate  # 激活虚拟环境
python run.py
```

**热重载（Hot Reload）配置**:

`run.py` 默认启用热重载功能，修改代码后会自动重启服务。

```env
# 开发环境（默认启用热重载）
API_RELOAD=true

# 生产环境（禁用热重载，使用多 worker）
API_RELOAD=false
API_WORKERS=4
```

**重要提示**:

- ⚠️ 使用 `run.py` 启动，支持热重载功能
- ⚠️ 开发环境默认 `API_RELOAD=true`，修改代码会自动重启
- ⚠️ 如果热重载不工作，检查 `.env` 中 `API_RELOAD=true` 是否设置
- ⚠️ 确保 `.env` 文件存在且配置正确
- ⚠️ 启动前检查端口 8000 是否被占用

### 前端服务配置

**配置文件**: `frontend/.env.local`

**关键配置项**:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=广告案例库
VITE_APP_VERSION=1.0.0
```

**启动方式**:

```bash
# 方式1：使用统一启动脚本（推荐）
cd technical-solution
./start.sh

# 方式2：手动启动
cd frontend
pnpm install  # 首次需要安装依赖
pnpm run dev
```

**重要提示**:

- ⚠️ 前端默认端口为 3000（在 `vite.config.ts` 中配置）
- ⚠️ 确保后端服务已启动（前端会代理到后端）
- ⚠️ 如果端口被占用，Vite 会自动选择下一个可用端口

## 🚀 快速启动

### 使用统一启动脚本（必须，推荐）

**⚠️ 重要：必须使用统一启动脚本启动服务**

```bash
# macOS/Linux
cd ad-case/technical-solution
./start.sh

# Windows
cd ad-case\technical-solution
start.bat
```

启动脚本会自动：

1. ✅ 检查项目结构
2. ✅ 检查后端环境配置
3. ✅ 检查数据库连接
4. ✅ 检查并激活 Python 虚拟环境
5. ✅ 检查前端依赖
6. ✅ 启动后端和前端服务

**⚠️ 重要规则**:
- ⚠️ **必须使用统一启动脚本启动服务**（这是唯一正确的启动方式）
- ⚠️ **禁止直接运行 `python run.py`**，必须通过启动脚本
- ⚠️ **禁止直接使用 `uvicorn` 命令启动**
- ⚠️ 启动脚本会自动处理所有必要的检查和配置

### 手动启动步骤（仅当启动脚本完全不可用时使用）

**⚠️ 警告：只有在启动脚本完全不可用的情况下才使用此方式**

#### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 检查环境变量
ls -la .env  # 确认 .env 文件存在

# 启动服务
python run.py
```

#### 2. 启动前端

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖（首次需要）
pnpm install

# 启动开发服务器
pnpm run dev
```

## 🔍 验证服务

启动后，访问以下地址验证服务：

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## ⚠️ 常见问题

### 1. 数据库连接失败

**症状**: 启动时提示数据库连接失败

**解决方案**:

- 检查 PostgreSQL 服务是否启动: `pg_isready` 或 `systemctl status postgresql`
- 检查数据库是否存在: `psql -l | grep ad_case_db`
- 检查 `.env` 中的数据库配置是否正确
- 检查用户权限: `psql -U bing -d ad_case_db -c "SELECT 1;"`

### 2. 虚拟环境未激活

**症状**: 提示模块未找到（如 `ModuleNotFoundError: No module named 'fastapi'`）

**解决方案**:

- 确认虚拟环境已激活: `which python` 应该指向虚拟环境中的 Python
- 重新激活虚拟环境: `source venv/bin/activate`
- 如果虚拟环境不存在，创建并安装依赖（见上方）

### 3. 热重载不工作

**症状**: 修改代码后服务没有自动重启

**解决方案**:

- 检查 `.env` 文件中 `API_RELOAD=true` 是否设置
- 确认使用的是 `run.py` 启动（不是直接使用 `uvicorn`）
- 检查 `uvicorn[standard]` 是否已安装（包含 watchfiles 依赖）
- 如果仍然不工作，尝试重新安装依赖: `pip install -r requirements.txt --upgrade`
- 查看启动日志，确认是否显示 "✅ 热重载已启用"

### 4. 向量模型加载失败

**症状**: 启动时提示向量模型加载失败

**解决方案**:

- 检查 `VECTOR_MODEL_PATH` 是否配置且路径正确
- 检查模型文件是否存在: `ls -la /path/to/bge-large-zh-v1.5`
- 设置 `VECTOR_OFFLINE_MODE=true` 确保使用本地模型
- 如果模型不存在，下载模型（见上方）

### 5. 端口被占用

**症状**: 启动时提示端口已被占用

**解决方案**:

- 后端端口 8000: `lsof -i :8000` 或 `netstat -an | grep 8000`
- 前端端口 3000: `lsof -i :3000` 或 `netstat -an | grep 3000`
- 杀死占用进程: `kill -9 <PID>`
- 或修改配置文件中的端口号

### 6. 前端无法连接后端

**症状**: 前端页面显示 API 请求失败

**解决方案**:

- 确认后端服务已启动: 访问 http://localhost:8000/health
- 检查 `frontend/.env.local` 中的 `VITE_API_BASE_URL` 配置
- 检查浏览器控制台是否有 CORS 错误
- 检查 `vite.config.ts` 中的代理配置

## 📝 配置检查清单

启动前，请确认以下配置：

- [ ] 数据库配置正确（`backend/.env` 中的 `DB_NAME`, `DB_USER`, `DB_PASSWORD`）
- [ ] Python 虚拟环境已创建并激活
- [ ] 后端依赖已安装（`pip install -r requirements.txt`）
- [ ] 向量模型路径已配置（`VECTOR_MODEL_PATH`）
- [ ] 向量模型离线模式已启用（`VECTOR_OFFLINE_MODE=true`）
- [ ] 前端依赖已安装（`pnpm install`）
- [ ] 端口 8000 和 3000 未被占用
- [ ] PostgreSQL 服务已启动

## 🔄 更新配置

如果修改了配置，需要：

1. **后端配置**: 修改 `backend/.env` 后，重启后端服务
2. **前端配置**: 修改 `frontend/.env.local` 后，重启前端服务
3. **数据库配置**: 修改后需要重启后端服务

## 📚 相关文档

- 后端文档: `backend/README.md`
- 前端文档: `frontend/README.md`
- 数据库文档: `backend/database/README.md`
- 项目主文档: `README.md`
