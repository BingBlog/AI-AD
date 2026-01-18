#!/usr/bin/env python3
"""
检查爬取任务状态的诊断脚本
"""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.database import db
from app.repositories.crawl_task_repository import CrawlTaskRepository


async def check_task_status(task_id: str):
    """检查任务状态"""
    print(f"\n{'='*60}")
    print(f"检查任务: {task_id}")
    print(f"{'='*60}\n")
    
    # 获取任务信息
    task = await CrawlTaskRepository.get_task(task_id)
    if not task:
        print(f"❌ 任务 {task_id} 不存在于数据库中")
        return
    
    # 显示基本信息
    print("📋 任务基本信息:")
    print(f"  名称: {task.get('name', 'N/A')}")
    print(f"  数据源: {task.get('data_source', 'N/A')}")
    print(f"  状态: {task.get('status', 'N/A')}")
    print(f"  创建时间: {task.get('created_at', 'N/A')}")
    print(f"  开始时间: {task.get('started_at', 'N/A')}")
    print(f"  完成时间: {task.get('completed_at', 'N/A')}")
    print(f"  暂停时间: {task.get('paused_at', 'N/A')}")
    print(f"  更新时间: {task.get('updated_at', 'N/A')}")
    
    # 显示配置信息
    print("\n⚙️  任务配置:")
    print(f"  起始页: {task.get('start_page', 'N/A')}")
    print(f"  结束页: {task.get('end_page', 'N/A')}")
    print(f"  总页数: {task.get('total_pages', 'N/A')}")
    print(f"  已完成页数: {task.get('completed_pages', 0)}")
    print(f"  当前页: {task.get('current_page', 'N/A')}")
    print(f"  批次大小: {task.get('batch_size', 'N/A')}")
    print(f"  案例类型: {task.get('case_type', 'N/A')}")
    print(f"  搜索关键词: {task.get('search_value', 'N/A')}")
    print(f"  启用断点续传: {task.get('enable_resume', 'N/A')}")
    
    # 显示进度信息
    print("\n📊 进度统计:")
    print(f"  总爬取数: {task.get('total_crawled', 0)}")
    print(f"  总保存数: {task.get('total_saved', 0)}")
    print(f"  总失败数: {task.get('total_failed', 0)}")
    print(f"  已保存批次: {task.get('batches_saved', 0)}")
    
    # 显示性能指标
    print("\n⚡ 性能指标:")
    print(f"  平均速度: {task.get('avg_speed', 'N/A')} 案例/分钟")
    print(f"  平均延迟: {task.get('avg_delay', 'N/A')} 秒")
    print(f"  错误率: {task.get('error_rate', 'N/A')}")
    
    # 显示错误信息
    if task.get('error_message'):
        print("\n❌ 错误信息:")
        print(f"  错误消息: {task.get('error_message', 'N/A')}")
        if task.get('error_stack'):
            print(f"  错误堆栈:\n{task.get('error_stack', 'N/A')}")
    
    # 检查断点续传文件
    print("\n📁 断点续传文件检查:")
    resume_file = backend_root / "data" / "json" / task_id / "crawl_resume.json"
    if resume_file.exists():
        try:
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
            crawled_ids = resume_data.get('crawled_ids', [])
            total_count = resume_data.get('total_count', 0)
            last_updated = resume_data.get('last_updated', 'N/A')
            
            print(f"  ✅ 文件存在")
            print(f"  已爬取ID数量: {len(crawled_ids)}")
            print(f"  总计数: {total_count}")
            print(f"  最后更新: {last_updated}")
            
            # 检查时间差
            try:
                last_update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                now = datetime.now(last_update_time.tzinfo)
                time_diff = (now - last_update_time).total_seconds()
                hours_diff = time_diff / 3600
                
                print(f"  距离最后更新: {hours_diff:.2f} 小时")
                
                # 如果超过1小时没有更新，且状态是running，可能卡住了
                if task.get('status') == 'running' and hours_diff > 1:
                    print(f"  ⚠️  警告: 任务状态为 'running'，但已超过 {hours_diff:.2f} 小时未更新，可能已卡住")
            except Exception as e:
                print(f"  ⚠️  无法解析时间: {e}")
        except Exception as e:
            print(f"  ❌ 读取文件失败: {e}")
    else:
        print(f"  ⚠️  文件不存在: {resume_file}")
    
    # 检查批次文件
    print("\n📦 批次文件检查:")
    batch_dir = backend_root / "data" / "json" / task_id
    if batch_dir.exists():
        batch_files = sorted(batch_dir.glob("cases_batch_*.json"))
        print(f"  找到 {len(batch_files)} 个批次文件")
        if batch_files:
            print(f"  第一个批次: {batch_files[0].name}")
            print(f"  最后一个批次: {batch_files[-1].name}")
            
            # 检查最后一个批次文件的大小和修改时间
            last_batch = batch_files[-1]
            stat = last_batch.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"  最后批次大小: {size_mb:.2f} MB")
            print(f"  最后批次修改时间: {mtime}")
    else:
        print(f"  ⚠️  批次目录不存在: {batch_dir}")
    
    # 诊断建议
    print("\n🔍 诊断建议:")
    status = task.get('status', '')
    
    if status == 'running':
        # 检查是否真的在运行
        from app.services.crawl_task_executor import get_executor
        executor = get_executor(task_id)
        if executor:
            print(f"  ✅ 执行器存在")
            print(f"    是否运行中: {executor.is_running}")
            print(f"    是否暂停: {executor.is_paused}")
        else:
            print(f"  ⚠️  执行器不存在（任务可能已停止但状态未更新）")
            print(f"     建议: 尝试恢复任务或手动更新状态")
        
        # 检查进度是否停滞
        if task.get('current_page') is not None and task.get('total_pages') is not None:
            current = task.get('current_page', 0)
            total = task.get('total_pages', 0)
            start = task.get('start_page', 0)
            completed = task.get('completed_pages', 0)
            
            if completed >= total:
                print(f"  ✅ 已完成所有页数 ({completed}/{total})")
                print(f"     建议: 任务应该已完成，可能需要手动更新状态为 'completed'")
            else:
                progress = (completed / total * 100) if total > 0 else 0
                print(f"  进度: {completed}/{total} ({progress:.1f}%)")
    
    elif status == 'paused':
        print(f"  ℹ️  任务已暂停")
        print(f"     建议: 使用 /api/v1/crawl-tasks/{task_id}/resume 恢复任务")
    
    elif status == 'failed':
        print(f"  ❌ 任务已失败")
        if task.get('error_message'):
            print(f"     错误: {task.get('error_message')}")
        print(f"     建议: 检查错误信息，使用 /api/v1/crawl-tasks/{task_id}/retry 重试")
    
    elif status == 'completed':
        print(f"  ✅ 任务已完成")
    
    elif status == 'pending':
        print(f"  ⏳ 任务等待中")
        print(f"     建议: 使用 /api/v1/crawl-tasks/{task_id}/start 启动任务")
    
    # 获取最近的日志
    print("\n📝 最近日志 (最多10条):")
    logs, total = await CrawlTaskRepository.get_logs(task_id, page=1, page_size=10)
    if logs:
        for log in logs[:10]:
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            created_at = log.get('created_at', '')
            icon = "✅" if level == "INFO" else "⚠️" if level == "WARNING" else "❌"
            print(f"  {icon} [{level}] {created_at}: {message}")
    else:
        print("  无日志记录")
    
    print(f"\n{'='*60}\n")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_task_status.py <task_id>")
        print("示例: python check_task_status.py task_aaefcd6593b84f94")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    try:
        # 初始化数据库连接
        await db.connect()
        await check_task_status(task_id)
    except Exception as e:
        print(f"❌ 检查失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
