#!/bin/bash
# 检查并关闭占用 8765 端口的进程

PORT=8765

echo "检查端口 $PORT 占用情况..."
echo ""

# 查找占用端口的进程
PIDS=$(lsof -ti :$PORT)

if [ -z "$PIDS" ]; then
    echo "✅ 端口 $PORT 未被占用，可以启动 Agent 服务器"
    exit 0
fi

echo "⚠️  发现以下进程占用端口 $PORT:"
lsof -i :$PORT
echo ""

read -p "是否关闭这些进程？(y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在关闭进程..."
    kill -9 $PIDS
    sleep 1
    
    # 再次检查
    if lsof -ti :$PORT > /dev/null 2>&1; then
        echo "❌ 部分进程未能关闭，请手动处理"
        exit 1
    else
        echo "✅ 端口 $PORT 已释放，可以启动 Agent 服务器"
        exit 0
    fi
else
    echo "未关闭进程，请手动处理或修改端口配置"
    exit 1
fi
