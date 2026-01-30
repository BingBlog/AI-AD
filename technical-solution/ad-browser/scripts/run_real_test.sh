#!/bin/bash
# 运行真实用例测试的便捷脚本

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "运行真实用例测试：小红书新能源汽车营销案例检索"
echo ""
python3 agent/tests/test_real_case.py
