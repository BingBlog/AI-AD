#!/usr/bin/env python3
"""
批量下载缺失的图片

从数据库中查询有 main_image 但没有本地图片文件的案例，批量下载图片。
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.database import db
from app.services.image_service import ImageService
from app.config import settings
from tqdm import tqdm


async def fetch_cases_without_local_images(batch_size: int = 1000) -> List[Dict]:
    """
    查询有 main_image 但没有本地图片文件的案例
    
    Args:
        batch_size: 批次大小
        
    Returns:
        案例列表
    """
    # 注意：调用此函数前需要先调用 db.connect()
    try:
        # 查询有 main_image 的案例
        query = """
            SELECT case_id, main_image
            FROM ad_cases
            WHERE main_image IS NOT NULL
            AND main_image != ''
            ORDER BY case_id
        """
        rows = await db.fetch(query)
        
        # 检查哪些案例没有本地图片文件
        image_storage_dir = Path(settings.IMAGE_STORAGE_DIR)
        cases_to_download = []
        
        for row in rows:
            case_id = row['case_id']
            main_image = row['main_image']
            
            # 检查本地文件系统是否有图片文件
            case_dir = image_storage_dir / str(case_id)
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            has_local_image = False
            
            for ext in image_extensions:
                image_file = case_dir / f"main_image.{ext}"
                if image_file.exists():
                    has_local_image = True
                    break
            
            # 如果没有本地图片文件，添加到下载列表
            if not has_local_image:
                cases_to_download.append({
                    'case_id': case_id,
                    'main_image': main_image
                })
        
        return cases_to_download
    except Exception as e:
        print(f"查询失败: {e}")
        return []


async def download_images_batch(
    cases: List[Dict],
    image_service: ImageService,
    semaphore: asyncio.Semaphore,
    skip_existing: bool = True
) -> Dict[str, int]:
    """
    批量下载图片
    
    Args:
        cases: 案例列表
        image_service: 图片服务实例
        semaphore: 并发控制信号量
        skip_existing: 是否跳过已下载的图片
        
    Returns:
        统计信息字典
    """
    # 注意：调用此函数前需要先调用 db.connect()
    stats = {
        'total': len(cases),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # 用于批量更新的列表
    updates_queue = []
    updates_lock = asyncio.Lock()
    
    async def download_with_limit(case: Dict):
        """带并发限制的下载函数"""
        async with semaphore:
            case_id = case['case_id']
            url = case['main_image']
            
            # 检查是否已下载
            if skip_existing:
                is_downloaded, local_url = image_service.is_image_downloaded(case_id)
                if is_downloaded:
                    async with updates_lock:
                        stats['skipped'] += 1
                    return
            
            # 下载图片
            success, local_url, error = await image_service.download_image(url, case_id)
            
            if success and local_url:
                # 添加到批量更新队列
                async with updates_lock:
                    updates_queue.append((case_id, local_url))
                    stats['success'] += 1
            else:
                async with updates_lock:
                    stats['failed'] += 1
                    stats['errors'].append({
                        'case_id': case_id,
                        'error': error or "下载失败"
                    })
    
    # 创建任务列表
    tasks = [download_with_limit(case) for case in cases]
    
    # 执行下载（使用进度条）
    if tasks:
        with tqdm(total=len(tasks), desc="下载图片") as pbar:
            for coro in asyncio.as_completed(tasks):
                await coro
                pbar.update(1)
    
    # 批量更新数据库
    if updates_queue:
        print(f"\n批量更新数据库中的 main_image_local 字段（共 {len(updates_queue)} 条）...")
        await batch_update_image_local_path(updates_queue)
    
    return stats


async def batch_update_image_local_path(updates: List[tuple]):
    """
    批量更新数据库中的 main_image_local 字段
    
    Args:
        updates: 更新列表，每个元素为 (case_id, local_url)
    """
    if not updates:
        return
    
    try:
        # 使用批量更新
        query = """
            UPDATE ad_cases
            SET main_image_local = $2
            WHERE case_id = $1
        """
        
        # 分批更新，每批100条
        batch_size = 100
        total_updated = 0
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            # 使用连接池执行批量更新
            async with db.pool.acquire() as conn:
                await conn.executemany(query, batch)
            total_updated += len(batch)
        
        print(f"✓ 已更新 {total_updated} 条记录的 main_image_local 字段")
    except Exception as e:
        print(f"✗ 批量更新失败: {e}")
        # 如果批量更新失败，尝试逐个更新
        print("尝试逐个更新...")
        for case_id, local_url in updates:
            try:
                query = """
                    UPDATE ad_cases
                    SET main_image_local = $1
                    WHERE case_id = $2
                """
                await db.execute(query, local_url, case_id)
            except Exception as e2:
                print(f"  更新案例 {case_id} 失败: {e2}")


async def main():
    """主函数"""
    print("=" * 60)
    print("批量下载缺失的图片")
    print("=" * 60)
    
    # 确保数据库连接已建立
    await db.connect()
    
    try:
        # 查询需要下载的案例
        print("\n查询需要下载图片的案例...")
        cases = await fetch_cases_without_local_images()
        
        if not cases:
            print("✓ 所有案例的图片都已下载到本地")
            return
        
        print(f"找到 {len(cases)} 个需要下载图片的案例")
        
        # 创建图片服务实例
        image_service = ImageService()
        
        # 设置并发数
        concurrency = settings.IMAGE_DOWNLOAD_CONCURRENCY
        semaphore = asyncio.Semaphore(concurrency)
        
        # 批量下载图片
        print(f"\n开始批量下载图片（并发数: {concurrency}）...")
        stats = await download_images_batch(cases, image_service, semaphore)
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("下载完成")
        print("=" * 60)
        print(f"总计: {stats['total']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")
        print(f"跳过: {stats['skipped']}")
        
        if stats['errors']:
            print(f"\n失败的案例（前10个）:")
            for error in stats['errors'][:10]:
                print(f"  案例ID {error['case_id']}: {error['error']}")
            if len(stats['errors']) > 10:
                print(f"  ... 还有 {len(stats['errors']) - 10} 个失败的案例")
    finally:
        # 关闭数据库连接
        await db.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
