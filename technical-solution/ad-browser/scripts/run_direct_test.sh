#!/bin/bash

# 直接测试任务控制器（绕过 WebSocket）

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "运行直接任务测试：小红书新能源汽车营销案例检索"
echo ""

python3 agent/tests/test_direct_task.py
