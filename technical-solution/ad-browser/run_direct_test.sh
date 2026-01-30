#!/bin/bash

# 直接测试任务控制器（绕过 WebSocket）

cd "$(dirname "$0")"

echo "运行直接任务测试：小红书新能源汽车营销案例检索"
echo ""

python3 agent/tests/test_direct_task.py
