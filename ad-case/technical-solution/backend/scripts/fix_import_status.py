#!/usr/bin/env python3
"""
修复导入状态脚本
更新所有已验证（verified=true）但未标记为已导入（imported=false）的记录
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.config import settings


async def fix_import_status(task_id: str = None):
    """
    修复导入状态
    
    Args:
        task_id: 任务ID，如果为None则修复所有任务
    """
    print("=" * 80)
    print("修复导入状态")
    print("=" * 80)
    
    # 连接数据库
    await db.connect()
    
    try:
        if task_id:
            # 修复指定任务
            print(f"\n修复任务: {task_id}")
            query = """
                UPDATE crawl_case_records
                SET imported = TRUE,
                    import_status = 'success',
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $1 
                  AND verified = TRUE 
                  AND imported = FALSE
            """
            result = await db.execute(query, task_id)
            print(f"✅ 已更新 {result} 条记录")
        else:
            # 修复所有任务
            print("\n修复所有任务...")
            query = """
                UPDATE crawl_case_records
                SET imported = TRUE,
                    import_status = 'success',
                    updated_at = CURRENT_TIMESTAMP
                WHERE verified = TRUE 
                  AND imported = FALSE
            """
            result = await db.execute(query)
            print(f"✅ 已更新 {result} 条记录")
        
        # 显示修复后的统计
        if task_id:
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN imported = TRUE THEN 1 END) as imported_count,
                    COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified_count,
                    COUNT(CASE WHEN imported = TRUE AND verified = TRUE THEN 1 END) as both_count
                FROM crawl_case_records
                WHERE task_id = $1
            """
            stats = await db.fetchrow(stats_query, task_id)
        else:
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN imported = TRUE THEN 1 END) as imported_count,
                    COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified_count,
                    COUNT(CASE WHEN imported = TRUE AND verified = TRUE THEN 1 END) as both_count
                FROM crawl_case_records
            """
            stats = await db.fetchrow(stats_query)
        
        print("\n📊 修复后统计:")
        print(f"   - 总记录数: {stats['total']}")
        print(f"   - 已导入: {stats['imported_count']}")
        print(f"   - 已验证: {stats['verified_count']}")
        print(f"   - 已导入且已验证: {stats['both_count']}")
        
    finally:
        await db.disconnect()


async def main():
    """主函数"""
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        await fix_import_status(task_id)
    else:
        print("用法: python fix_import_status.py [task_id]")
        print("示例: python fix_import_status.py task_3d54f517fb0546e6")
        print("如果不提供 task_id，将修复所有任务")
        choice = input("\n是否修复所有任务？(y/N): ")
        if choice.lower() == 'y':
            await fix_import_status()
        else:
            print("已取消")


if __name__ == '__main__':
    asyncio.run(main())
