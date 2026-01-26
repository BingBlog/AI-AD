#!/bin/bash

# 广告案例库统一启动脚本
# 用途：统一启动前后端服务，确保使用正确的配置和环境

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}广告案例库统一启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 检查必要的目录和文件
echo -e "\n${YELLOW}[1/6] 检查项目结构...${NC}"
if [ ! -d "${BACKEND_DIR}" ]; then
    echo -e "${RED}❌ 后端目录不存在: ${BACKEND_DIR}${NC}"
    exit 1
fi
if [ ! -d "${FRONTEND_DIR}" ]; then
    echo -e "${RED}❌ 前端目录不存在: ${FRONTEND_DIR}${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 项目结构检查通过${NC}"

# 2. 检查后端环境变量文件
echo -e "\n${YELLOW}[2/6] 检查后端环境配置...${NC}"
BACKEND_ENV="${BACKEND_DIR}/.env"
if [ ! -f "${BACKEND_ENV}" ]; then
    echo -e "${YELLOW}⚠️  后端 .env 文件不存在，从 env.example 创建...${NC}"
    if [ -f "${BACKEND_DIR}/env.example" ]; then
        cp "${BACKEND_DIR}/env.example" "${BACKEND_ENV}"
        echo -e "${YELLOW}⚠️  请编辑 ${BACKEND_ENV} 文件，设置正确的配置（特别是数据库和向量模型路径）${NC}"
        echo -e "${YELLOW}⚠️  按 Enter 继续，或 Ctrl+C 退出进行配置...${NC}"
        read
    else
        echo -e "${RED}❌ env.example 文件不存在${NC}"
        exit 1
    fi
fi

# 检查关键配置
source "${BACKEND_ENV}"
if [ -z "${DB_NAME}" ]; then
    echo -e "${RED}❌ 数据库名称未配置 (DB_NAME)${NC}"
    exit 1
fi
if [ -z "${VECTOR_MODEL_PATH}" ] && [ "${VECTOR_OFFLINE_MODE}" != "false" ]; then
    echo -e "${YELLOW}⚠️  警告: VECTOR_MODEL_PATH 未配置，将使用在线模型（可能失败）${NC}"
    echo -e "${YELLOW}⚠️  建议设置 VECTOR_MODEL_PATH 指向本地模型路径${NC}"
fi
echo -e "${GREEN}✅ 后端环境配置检查通过${NC}"

# 3. 检查数据库连接
echo -e "\n${YELLOW}[3/6] 检查数据库连接...${NC}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ad_case_db}"
DB_USER="${DB_USER:-postgres}"

if command -v psql &> /dev/null; then
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &> /dev/null; then
        echo -e "${GREEN}✅ 数据库连接成功: ${DB_HOST}:${DB_PORT}/${DB_NAME}${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败: ${DB_HOST}:${DB_PORT}/${DB_NAME}${NC}"
        echo -e "${YELLOW}⚠️  请检查：${NC}"
        echo -e "${YELLOW}   1. PostgreSQL 服务是否启动${NC}"
        echo -e "${YELLOW}   2. 数据库 ${DB_NAME} 是否存在${NC}"
        echo -e "${YELLOW}   3. 用户 ${DB_USER} 是否有权限${NC}"
        echo -e "${YELLOW}   4. 密码是否正确${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  psql 命令未找到，跳过数据库连接检查${NC}"
fi

# 4. 检查 Python 虚拟环境
echo -e "\n${YELLOW}[4/6] 检查 Python 虚拟环境...${NC}"
DETECTED_VENV_DIR=""
if [ -z "${VIRTUAL_ENV}" ]; then
    # 尝试查找常见的虚拟环境目录
    VENV_DIRS=(
        "${BACKEND_DIR}/venv"
        "${BACKEND_DIR}/.venv"
        "${PROJECT_ROOT}/venv"
        "${PROJECT_ROOT}/.venv"
    )
    
    VENV_FOUND=false
    for venv_dir in "${VENV_DIRS[@]}"; do
        if [ -d "${venv_dir}" ] && [ -f "${venv_dir}/bin/activate" ]; then
            echo -e "${YELLOW}⚠️  发现虚拟环境: ${venv_dir}${NC}"
            echo -e "${YELLOW}⚠️  正在激活虚拟环境...${NC}"
            source "${venv_dir}/bin/activate"
            DETECTED_VENV_DIR="${venv_dir}"
            VENV_FOUND=true
            break
        fi
    done
    
    if [ "${VENV_FOUND}" = false ]; then
        echo -e "${RED}❌ 未找到 Python 虚拟环境${NC}"
        echo -e "${YELLOW}⚠️  请创建虚拟环境：${NC}"
        echo -e "${YELLOW}   cd ${BACKEND_DIR}${NC}"
        echo -e "${YELLOW}   python3 -m venv venv${NC}"
        echo -e "${YELLOW}   source venv/bin/activate${NC}"
        echo -e "${YELLOW}   pip install -r requirements.txt${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 虚拟环境已激活: ${VIRTUAL_ENV}${NC}"
    DETECTED_VENV_DIR="${VIRTUAL_ENV}"
fi

# 验证 Python 和依赖
if ! python3 -c "import fastapi" &> /dev/null; then
    echo -e "${RED}❌ FastAPI 未安装，请运行: pip install -r ${BACKEND_DIR}/requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 环境检查通过${NC}"

# 5. 检查前端依赖
echo -e "\n${YELLOW}[5/6] 检查前端环境...${NC}"
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo -e "${YELLOW}⚠️  前端依赖未安装，正在安装...${NC}"
    cd "${FRONTEND_DIR}"
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v npm &> /dev/null; then
        npm install
    else
        echo -e "${RED}❌ 未找到 pnpm 或 npm${NC}"
        exit 1
    fi
    cd "${PROJECT_ROOT}"
fi

# 检查前端环境变量
FRONTEND_ENV="${FRONTEND_DIR}/.env.local"
if [ ! -f "${FRONTEND_ENV}" ] && [ -f "${FRONTEND_DIR}/env.example" ]; then
    echo -e "${YELLOW}⚠️  前端 .env.local 文件不存在，从 env.example 创建...${NC}"
    cp "${FRONTEND_DIR}/env.example" "${FRONTEND_ENV}"
fi
echo -e "${GREEN}✅ 前端环境检查通过${NC}"

# 6. 停止现有服务（如果存在）
echo -e "\n${YELLOW}[6/7] 停止现有服务...${NC}"

# 停止占用后端端口的进程
BACKEND_PORT="${API_PORT:-8000}"
if lsof -ti:${BACKEND_PORT} &> /dev/null; then
    echo -e "${YELLOW}⚠️  端口 ${BACKEND_PORT} 被占用，正在终止相关进程...${NC}"
    lsof -ti:${BACKEND_PORT} | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ 端口 ${BACKEND_PORT} 已释放${NC}"
fi

# 停止占用前端端口的进程
FRONTEND_PORT=3000
if lsof -ti:${FRONTEND_PORT} &> /dev/null; then
    echo -e "${YELLOW}⚠️  端口 ${FRONTEND_PORT} 被占用，正在终止相关进程...${NC}"
    lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ 端口 ${FRONTEND_PORT} 已释放${NC}"
fi

# 停止可能存在的后端进程（通过进程名）
if pgrep -f "run.py" &> /dev/null || pgrep -f "uvicorn" &> /dev/null; then
    echo -e "${YELLOW}⚠️  发现运行中的后端进程，正在终止...${NC}"
    pkill -f "run.py" 2>/dev/null || true
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ 后端进程已清理${NC}"
fi

# 停止可能存在的前端进程（通过进程名）
if pgrep -f "vite" &> /dev/null || pgrep -f "npm.*dev" &> /dev/null; then
    echo -e "${YELLOW}⚠️  发现运行中的前端进程，正在终止...${NC}"
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm.*dev" 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ 前端进程已清理${NC}"
fi

echo -e "${GREEN}✅ 现有服务清理完成${NC}"

# 7. 启动服务
echo -e "\n${YELLOW}[7/7] 启动服务...${NC}"

# 清理函数：退出时杀死所有后台进程
cleanup() {
    echo -e "\n${YELLOW}正在停止所有服务...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# 启动后端服务
echo -e "${GREEN}🚀 启动后端服务 (端口 ${BACKEND_PORT})...${NC}"
cd "${BACKEND_DIR}"
# 确保使用虚拟环境中的 Python
if [ -n "${DETECTED_VENV_DIR}" ] && [ -f "${DETECTED_VENV_DIR}/bin/python" ]; then
    "${DETECTED_VENV_DIR}/bin/python" run.py &
elif [ -n "${VIRTUAL_ENV}" ] && [ -f "${VIRTUAL_ENV}/bin/python" ]; then
    "${VIRTUAL_ENV}/bin/python" run.py &
elif [ -f "${BACKEND_DIR}/venv/bin/python" ]; then
    "${BACKEND_DIR}/venv/bin/python" run.py &
elif [ -f "${BACKEND_DIR}/.venv/bin/python" ]; then
    "${BACKEND_DIR}/.venv/bin/python" run.py &
else
    python3 run.py &
fi
BACKEND_PID=$!
cd "${PROJECT_ROOT}"

# 等待后端启动
sleep 3
if ! kill -0 ${BACKEND_PID} 2>/dev/null; then
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    exit 1
fi

# 启动前端服务
echo -e "${GREEN}🚀 启动前端服务 (端口 ${FRONTEND_PORT})...${NC}"

cd "${FRONTEND_DIR}"
if command -v pnpm &> /dev/null; then
    pnpm run dev &
else
    npm run dev &
fi
FRONTEND_PID=$!
cd "${PROJECT_ROOT}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 所有服务已启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}后端 API: http://localhost:${BACKEND_PORT}${NC}"
echo -e "${GREEN}前端应用: http://localhost:${FRONTEND_PORT}${NC}"
echo -e "${GREEN}API 文档: http://localhost:${BACKEND_PORT}/docs${NC}"
echo -e "\n${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# 等待所有后台进程
wait
