#!/bin/bash
# 启动 Agent 服务器的便捷脚本

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查端口是否被占用
PORT=8765
if lsof -ti :$PORT > /dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用"
    echo ""
    echo "占用端口的进程："
    lsof -i :$PORT
    echo ""
    read -p "是否关闭占用端口的进程？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PIDS=$(lsof -ti :$PORT)
        kill -9 $PIDS 2>/dev/null
        sleep 1
        if lsof -ti :$PORT > /dev/null 2>&1; then
            echo "❌ 未能关闭所有进程，请手动处理"
            exit 1
        fi
        echo "✅ 端口已释放"
        echo ""
    else
        echo "请手动关闭占用端口的进程，或运行: ./scripts/check_port.sh"
        exit 1
    fi
fi

echo "启动 Ad Browser Agent 服务器..."
echo "WebSocket 地址: ws://localhost:8765"
echo ""

# 使用 -m 参数运行模块，确保 Python 路径正确
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 -m agent.main
