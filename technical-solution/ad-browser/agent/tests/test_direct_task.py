#!/usr/bin/env python3
"""
直接测试任务控制器（绕过 WebSocket）

测试真实用例：小红书新能源汽车营销案例检索
验证功能：
1. detail-desc 文本提取（包括标签文本）
2. 图片提取和下载
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
        max_items=3  # 减少数量以便快速测试
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
                print(f"\n{'='*60}")
                print(f"案例 {i}: {case.title or '无标题'}")
                print(f"{'='*60}")
                print(f"   品牌: {case.brand or '未知'}")
                print(f"   平台: {case.platform}")
                print(f"   主题: {case.theme or '未知'}")
                print(f"   创意类型: {case.creative_type or '未知'}")
                print(f"   来源: {case.source_url}")
                
                # 验证策略和洞察
                if case.strategy:
                    print(f"   策略要点 ({len(case.strategy)} 条):")
                    for j, strategy in enumerate(case.strategy[:3], 1):  # 只显示前3条
                        print(f"     {j}. {strategy[:80]}...")
                
                if case.insights:
                    print(f"   洞察要点 ({len(case.insights)} 条):")
                    for j, insight in enumerate(case.insights[:3], 1):  # 只显示前3条
                        print(f"     {j}. {insight[:80]}...")
                
                # 检查图片下载目录
                if case.source_url:
                    # 从 URL 提取 note_id
                    import re
                    note_id = None
                    if '/explore/' in str(case.source_url):
                        match = re.search(r'/explore/([^/?]+)', str(case.source_url))
                        if match:
                            note_id = match.group(1)
                    
                    if note_id:
                        # 检查图片目录
                        base_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'images' / note_id
                        if base_dir.exists():
                            image_files = list(base_dir.glob('image_*.*'))
                            if image_files:
                                print(f"   ✅ 图片下载: {len(image_files)} 张")
                                for img_file in image_files[:3]:  # 只显示前3张
                                    print(f"      - {img_file.name} ({img_file.stat().st_size / 1024:.1f} KB)")
                            else:
                                print(f"   ⚠️  图片目录存在但无图片文件")
                        else:
                            print(f"   ⚠️  图片目录不存在: {base_dir}")
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
