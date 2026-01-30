#!/bin/bash
# 运行真实用例测试的便捷脚本

cd "$(dirname "$0")"
echo "运行真实用例测试：小红书新能源汽车营销案例检索"
echo ""
python3 agent/tests/test_real_case.py
