#!/usr/bin/env python3
"""
修复任务状态脚本
用于将任务状态从 completed 修改为 failed，并更新错误信息
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.database import db
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.services.crawl_task_service import CrawlTaskService


async def fix_task_status(task_id: str, error_message: str, error_stack: str = None):
    """
    修复任务状态
    
    Args:
        task_id: 任务ID
        error_message: 错误信息
        error_stack: 错误堆栈（可选）
    """
    print(f"开始修复任务状态: {task_id}")
    
    # 获取任务信息
    task_data = await CrawlTaskRepository.get_task(task_id)
    if not task_data:
        print(f"错误: 任务 {task_id} 不存在")
        return False
    
    print(f"当前任务状态: {task_data.get('status')}")
    print(f"当前错误信息: {task_data.get('error_message')}")
    
    # 更新任务状态为 failed
    success = await CrawlTaskRepository.update_task_status(
        task_id=task_id,
        status="failed"
    )
    
    if not success:
        print(f"错误: 更新任务状态失败")
        return False
    
    print(f"✓ 任务状态已更新为 failed")
    
    # 更新错误信息
    success = await CrawlTaskRepository.update_task_error(
        task_id=task_id,
        error_message=error_message,
        error_stack=error_stack
    )
    
    if not success:
        print(f"警告: 更新错误信息失败")
    else:
        print(f"✓ 错误信息已更新")
    
    # 添加日志
    await CrawlTaskRepository.add_log(
        task_id=task_id,
        level="ERROR",
        message=f"任务状态已修复: {error_message}",
        details={
            "fixed_at": datetime.now().isoformat(),
            "previous_status": task_data.get('status'),
            "new_status": "failed"
        }
    )
    
    print(f"✓ 日志已添加")
    
    # 验证修复结果
    updated_task = await CrawlTaskRepository.get_task(task_id)
    if updated_task:
        print(f"\n修复后的任务状态:")
        print(f"  状态: {updated_task.get('status')}")
        print(f"  错误信息: {updated_task.get('error_message')}")
        print(f"  更新时间: {updated_task.get('updated_at')}")
    
    return True


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python fix_task_status.py <task_id> [error_message]")
        print("示例: python fix_task_status.py task_d8468637819f49dd")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    # 初始化数据库连接
    try:
        await db.connect()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 默认错误信息
    error_message = (
        "任务执行失败: 因IP被封禁导致出现大量HTTP 405错误。"
        "爬取过程中遇到大量405状态码响应，无法继续获取数据。"
        "建议：1) 更换IP地址或使用代理；2) 增加请求延迟；3) 检查目标网站的反爬虫策略。"
    )
    
    # 如果提供了自定义错误信息，使用自定义的
    if len(sys.argv) >= 3:
        error_message = sys.argv[2]
    
    error_stack = (
        "HTTP 405 Method Not Allowed\n"
        "任务在执行过程中遇到大量405错误响应，导致无法继续爬取数据。"
        "这通常是由于IP地址被封禁或目标网站的反爬虫机制触发导致的。"
    )
    
    try:
        success = await fix_task_status(task_id, error_message, error_stack)
        if success:
            print(f"\n✓ 任务状态修复完成")
        else:
            print(f"\n✗ 任务状态修复失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
