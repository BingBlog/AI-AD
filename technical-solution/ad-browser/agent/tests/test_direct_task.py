#!/usr/bin/env python3
"""
直接测试任务控制器（绕过 WebSocket）

测试真实用例：小红书新能源汽车营销案例检索
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.controller.task_controller import TaskController
from agent.models.task_schema import TaskRequest


async def test_direct_task():
    """直接测试任务执行"""
    print("=" * 60)
    print("直接测试任务控制器：小红书新能源汽车营销案例检索")
    print("=" * 60)
    print()
    
    # 创建任务请求
    task = TaskRequest(
        task_id="direct-test-001",
        platform="xiaohongshu",
        keywords=["新能源汽车", "营销案例", "解析"],
        max_items=10
    )
    
    print(f"📋 任务信息：")
    print(f"   任务ID: {task.task_id}")
    print(f"   平台: {task.platform}")
    print(f"   关键词: {task.keywords}")
    print(f"   最大数量: {task.max_items}")
    print()
    
    # 创建任务控制器
    controller = TaskController()
    
    # 执行任务
    print("🚀 开始执行任务...")
    print()
    
    try:
        results = await controller.execute_task(task)
        
        print("=" * 60)
        print("✅ 任务执行完成")
        print("=" * 60)
        print()
        print(f"📊 结果统计：")
        print(f"   找到案例数: {len(results)}")
        print()
        
        if results:
            print("📝 案例详情：")
            for i, case in enumerate(results, 1):
                print(f"\n{i}. {case.title or '无标题'}")
                print(f"   品牌: {case.brand or '未知'}")
                print(f"   平台: {case.platform}")
                print(f"   主题: {case.theme or '未知'}")
                print(f"   来源: {case.source_url or '未知'}")
        else:
            print("⚠️  未找到任何案例")
            
    except Exception as e:
        print("=" * 60)
        print("❌ 任务执行失败")
        print("=" * 60)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct_task())
