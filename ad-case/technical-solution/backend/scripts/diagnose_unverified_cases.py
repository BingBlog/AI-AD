#!/usr/bin/env python3
"""
诊断未验证案例的原因
检查为什么某些案例在 crawl_case_records 中有 case_id，但在 ad_cases 表中不存在
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import db
from app.config import settings


async def diagnose_unverified_cases(task_id: str):
    """
    诊断未验证案例的原因
    
    Args:
        task_id: 任务ID
    """
    print("=" * 80)
    print(f"诊断任务: {task_id}")
    print("=" * 80)
    
    # 连接数据库
    await db.connect()
    
    try:
        # 1. 查询任务中所有有 case_id 的记录
        print("\n1️⃣ 查询任务中的案例记录...")
        records_query = """
            SELECT DISTINCT case_id, 
                   COUNT(*) as record_count,
                   COUNT(CASE WHEN imported = true THEN 1 END) as imported_count,
                   COUNT(CASE WHEN verified = true THEN 1 END) as verified_count
            FROM crawl_case_records 
            WHERE task_id = $1 AND case_id IS NOT NULL
            GROUP BY case_id
            ORDER BY case_id
        """
        records = await db.fetch(records_query, task_id)
        all_case_ids = [row['case_id'] for row in records]
        
        print(f"   找到 {len(all_case_ids)} 个唯一的 case_id")
        
        if not all_case_ids:
            print("   ⚠️ 没有找到任何 case_id")
            return
        
        # 2. 检查这些 case_id 是否在 ad_cases 表中存在
        print("\n2️⃣ 检查 case_id 是否在 ad_cases 表中存在...")
        existing_query = """
            SELECT case_id 
            FROM ad_cases 
            WHERE case_id = ANY($1::integer[])
        """
        existing_rows = await db.fetch(existing_query, all_case_ids)
        existing_case_ids = {row['case_id'] for row in existing_rows}
        
        verified_case_ids = [cid for cid in all_case_ids if cid in existing_case_ids]
        unverified_case_ids = [cid for cid in all_case_ids if cid not in existing_case_ids]
        
        print(f"   ✅ 已验证: {len(verified_case_ids)} 个")
        print(f"   ❌ 未验证: {len(unverified_case_ids)} 个")
        
        # 3. 分析未验证案例的详细信息
        if unverified_case_ids:
            print("\n3️⃣ 分析未验证案例的详细信息...")
            
            # 查询未验证案例的详细信息
            detail_query = """
                SELECT 
                    case_id,
                    COUNT(*) as record_count,
                    COUNT(CASE WHEN imported = true THEN 1 END) as imported_count,
                    COUNT(CASE WHEN verified = true THEN 1 END) as verified_count,
                    MAX(import_status) as import_status,
                    MAX(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM crawl_case_records 
                WHERE task_id = $1 AND case_id = ANY($2::integer[])
                GROUP BY case_id
                ORDER BY case_id
            """
            unverified_details = await db.fetch(detail_query, task_id, unverified_case_ids)
            
            # 统计各种状态
            imported_but_not_in_db = 0
            not_imported = 0
            import_status_failed = 0
            import_status_success = 0
            import_status_null = 0
            
            print("\n   未验证案例状态统计:")
            for row in unverified_details:
                case_id = row['case_id']
                imported_count = row['imported_count']
                import_status = row['import_status']
                
                if imported_count > 0:
                    imported_but_not_in_db += 1
                    if import_status == 'success':
                        import_status_success += 1
                    elif import_status == 'failed':
                        import_status_failed += 1
                    else:
                        import_status_null += 1
                else:
                    not_imported += 1
            
            print(f"   - 标记为已导入但不在 ad_cases 表中: {imported_but_not_in_db} 个")
            print(f"     * import_status = 'success': {import_status_success} 个")
            print(f"     * import_status = 'failed': {import_status_failed} 个")
            print(f"     * import_status = NULL: {import_status_null} 个")
            print(f"   - 未标记为已导入: {not_imported} 个")
            
            # 显示前10个未验证案例的详细信息
            print("\n   前10个未验证案例的详细信息:")
            for i, row in enumerate(unverified_details[:10], 1):
                case_id = row['case_id']
                record_count = row['record_count']
                imported_count = row['imported_count']
                verified_count = row['verified_count']
                import_status = row['import_status']
                created_at = row['created_at']
                
                print(f"\n   [{i}] case_id: {case_id}")
                print(f"       - 记录数: {record_count}")
                print(f"       - 已导入标记数: {imported_count}")
                print(f"       - 已验证标记数: {verified_count}")
                print(f"       - 导入状态: {import_status}")
                print(f"       - 创建时间: {created_at}")
        
        # 4. 检查导入任务历史
        print("\n4️⃣ 检查导入任务历史...")
        import_history_query = """
            SELECT 
                import_id,
                status,
                started_at,
                completed_at,
                total_cases,
                imported_cases,
                failed_cases,
                existing_cases,
                invalid_cases,
                skip_existing,
                skip_invalid,
                error_message
            FROM task_imports
            WHERE task_id = $1
            ORDER BY started_at DESC
            LIMIT 5
        """
        import_history = await db.fetch(import_history_query, task_id)
        
        if import_history:
            print(f"   找到 {len(import_history)} 个导入任务记录:")
            for i, row in enumerate(import_history, 1):
                print(f"\n   [{i}] 导入ID: {row['import_id']}")
                print(f"       - 状态: {row['status']}")
                print(f"       - 开始时间: {row['started_at']}")
                print(f"       - 完成时间: {row['completed_at']}")
                print(f"       - 总案例数: {row['total_cases']}")
                print(f"       - 导入成功: {row['imported_cases']}")
                print(f"       - 导入失败: {row['failed_cases']}")
                print(f"       - 已存在: {row['existing_cases']}")
                print(f"       - 无效: {row['invalid_cases']}")
                print(f"       - 跳过已存在: {row['skip_existing']}")
                print(f"       - 跳过无效: {row['skip_invalid']}")
                if row['error_message']:
                    print(f"       - 错误信息: {row['error_message'][:200]}")
                
                # 检查导入错误
                error_query = """
                    SELECT COUNT(*) as error_count
                    FROM task_import_errors
                    WHERE import_id = $1
                """
                error_count = await db.fetchval(error_query, row['import_id'])
                if error_count and error_count > 0:
                    print(f"       - 错误记录数: {error_count}")
                    
                    # 显示前3个错误
                    error_detail_query = """
                        SELECT error_type, error_message, file_name, case_id
                        FROM task_import_errors
                        WHERE import_id = $1
                        ORDER BY created_at DESC
                        LIMIT 3
                    """
                    errors = await db.fetch(error_detail_query, row['import_id'])
                    for j, err in enumerate(errors, 1):
                        print(f"         [{j}] {err['error_type']}: {err['error_message'][:100]}")
        else:
            print("   ⚠️ 没有找到导入任务记录")
        
        # 5. 总结和建议
        print("\n" + "=" * 80)
        print("📊 诊断总结")
        print("=" * 80)
        
        if unverified_case_ids:
            print(f"\n❌ 发现 {len(unverified_case_ids)} 个未验证的案例")
            print("\n可能的原因:")
            print("1. 这些案例在导入时被跳过了（skip_existing=True 或 skip_invalid=True）")
            print("2. 这些案例的向量生成失败（没有文本内容）")
            print("3. 这些案例在导入过程中出错")
            print("4. 这些案例从未被导入（导入任务未执行或失败）")
            
            if imported_but_not_in_db > 0:
                print(f"\n⚠️ 特别注意: {imported_but_not_in_db} 个案例被标记为已导入，但实际不在 ad_cases 表中")
                print("   这可能表示:")
                print("   - 导入过程中出现了错误，但状态更新不正确")
                print("   - 数据库事务回滚，但状态未回滚")
                print("   - 导入后数据被删除")
            
            if not_imported > 0:
                print(f"\n💡 建议: {not_imported} 个案例从未被导入，可以尝试重新导入")
        else:
            print("\n✅ 所有案例都已验证")
        
    finally:
        await db.disconnect()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python diagnose_unverified_cases.py <task_id>")
        print("示例: python diagnose_unverified_cases.py task_3d54f517fb0546e6")
        sys.exit(1)
    
    task_id = sys.argv[1]
    await diagnose_unverified_cases(task_id)


if __name__ == '__main__':
    asyncio.run(main())
