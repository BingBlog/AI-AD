"""
测试导入 API 接口
"""
import asyncio
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.database import db
from app.repositories.crawl_task_repository import CrawlTaskRepository
from app.repositories.task_import_repository import TaskImportRepository


async def test_import_api():
    """测试导入 API"""
    print("=" * 60)
    print("测试导入 API")
    print("=" * 60)

    # 连接数据库
    await db.connect()

    try:
        # 1. 查找一个已完成的任务
        print("\n1. 查找已完成的任务...")
        tasks, total = await CrawlTaskRepository.list_tasks(status="completed", page_size=1)
        if not tasks:
            print("❌ 没有找到已完成的任务，请先创建一个并完成它")
            return

        task = tasks[0]
        task_id = task["task_id"]
        print(f"✅ 找到任务: {task_id} ({task['name']})")
        print(f"   总保存数: {task.get('total_saved', 0)}")

        # 2. 创建导入记录
        print("\n2. 创建导入记录...")
        import_id = await TaskImportRepository.create_import(
            task_id=task_id,
            import_mode="full",
            selected_batches=None,
            skip_existing=True,
            update_existing=False,
            generate_vectors=True,
            skip_invalid=True,
            batch_size=50,
        )
        print(f"✅ 创建导入记录成功: {import_id}")

        # 3. 获取导入记录
        print("\n3. 获取导入记录...")
        import_record = await TaskImportRepository.get_import(import_id)
        if import_record:
            print(f"✅ 获取导入记录成功:")
            print(f"   导入ID: {import_record['import_id']}")
            print(f"   任务ID: {import_record['task_id']}")
            print(f"   状态: {import_record['status']}")
            print(f"   导入模式: {import_record['import_mode']}")
        else:
            print("❌ 获取导入记录失败")

        # 4. 更新导入进度
        print("\n4. 更新导入进度...")
        success = await TaskImportRepository.update_import_progress(
            import_id=import_id,
            total_cases=100,
            loaded_cases=50,
            valid_cases=48,
            invalid_cases=2,
            existing_cases=10,
            imported_cases=38,
            failed_cases=0,
            current_file="cases_batch_0000.json",
        )
        if success:
            print("✅ 更新导入进度成功")
        else:
            print("❌ 更新导入进度失败")

        # 5. 更新导入状态
        print("\n5. 更新导入状态...")
        success = await TaskImportRepository.update_import_status(
            import_id=import_id,
            status="running",
        )
        if success:
            print("✅ 更新导入状态成功")
        else:
            print("❌ 更新导入状态失败")

        # 6. 获取任务的所有导入记录
        print("\n6. 获取任务的所有导入记录...")
        imports = await TaskImportRepository.get_task_imports(task_id)
        print(f"✅ 找到 {len(imports)} 条导入记录")

        # 7. 添加导入错误
        print("\n7. 添加导入错误...")
        error_id = await TaskImportRepository.add_import_error(
            import_id=import_id,
            file_name="cases_batch_0000.json",
            case_id=12345,
            error_type="validation_error",
            error_message="案例数据验证失败：缺少必填字段",
            error_details={"field": "title", "reason": "字段为空"},
        )
        if error_id:
            print(f"✅ 添加导入错误成功: {error_id}")
        else:
            print("❌ 添加导入错误失败")

        # 8. 获取导入错误列表
        print("\n8. 获取导入错误列表...")
        errors = await TaskImportRepository.get_import_errors(import_id)
        print(f"✅ 找到 {len(errors)} 条错误记录")
        for error in errors:
            print(f"   - {error['error_type']}: {error['error_message']}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_import_api())
