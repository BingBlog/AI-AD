"""
批量下载所有案例的主图
从数据库读取所有有 main_image 的案例，下载图片到本地，并更新数据库
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import aiohttp

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import db
from app.config import settings
from app.services.image_service import ImageService
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_images.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def fetch_cases_with_images(batch_size: int = 1000) -> List[Dict]:
    """
    从数据库获取所有有 main_image 的案例
    
    Args:
        batch_size: 每批查询的数量
        
    Returns:
        案例列表
    """
    query = """
        SELECT case_id, main_image, main_image_local
        FROM ad_cases
        WHERE main_image IS NOT NULL 
          AND main_image != ''
        ORDER BY case_id
    """
    
    rows = await db.fetch(query)
    cases = [dict(row) for row in rows]
    logger.info(f"从数据库获取到 {len(cases)} 个有 main_image 的案例")
    return cases


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
    stats = {
        'total': len(cases),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    async def download_with_limit(case: Dict):
        """带并发限制的下载函数"""
        async with semaphore:
            case_id = case['case_id']
            url = case['main_image']
            main_image_local = case.get('main_image_local')
            
            # 检查是否已下载
            if skip_existing:
                is_downloaded, local_url = image_service.is_image_downloaded(case_id)
                if is_downloaded:
                    # 如果已下载但数据库中没有记录，更新数据库
                    if not main_image_local:
                        await update_image_local_path(case_id, local_url)
                    stats['skipped'] += 1
                    return
                # 如果数据库中有记录但文件不存在，重新下载
                elif main_image_local:
                    logger.warning(f"数据库中有记录但文件不存在: case_id={case_id}, 重新下载")
            
            # 下载图片（使用共享的 session）
            success, local_url, error = await image_service.download_image(url, case_id, session=session)
            
            if success and local_url:
                # 更新数据库
                await update_image_local_path(case_id, local_url)
                stats['success'] += 1
            else:
                stats['failed'] += 1
                error_info = {
                    'case_id': case_id,
                    'url': url,
                    'error': error
                }
                stats['errors'].append(error_info)
                logger.error(f"下载失败: case_id={case_id}, url={url}, error={error}")
    
    # 创建 aiohttp 会话（共享会话可以提高性能）
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = []
        for case in cases:
            # 为每个任务创建新的 image_service 实例，但共享 session
            task = download_with_limit(case)
            tasks.append(task)
        
        # 使用 tqdm 显示进度
        with tqdm(total=len(tasks), desc="下载图片") as pbar:
            for coro in asyncio.as_completed(tasks):
                await coro
                pbar.update(1)
    
    return stats


async def update_image_local_path(case_id: int, local_url: str):
    """
    更新数据库中的 main_image_local 字段
    
    Args:
        case_id: 案例 ID
        local_url: 本地图片 URL
    """
    query = """
        UPDATE ad_cases
        SET main_image_local = $1
        WHERE case_id = $2
    """
    await db.execute(query, local_url, case_id)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始批量下载案例主图")
    logger.info("=" * 60)
    
    # 连接数据库
    await db.connect()
    
    try:
        # 初始化图片服务
        image_service = ImageService()
        logger.info(f"图片存储目录: {image_service.storage_dir}")
        
        # 获取所有案例
        cases = await fetch_cases_with_images()
        
        if not cases:
            logger.warning("没有找到需要下载图片的案例")
            return
        
        # 创建并发控制信号量
        concurrency = settings.IMAGE_DOWNLOAD_CONCURRENCY
        semaphore = asyncio.Semaphore(concurrency)
        logger.info(f"并发数: {concurrency}")
        
        # 询问是否跳过已下载的图片
        skip_existing = True
        logger.info(f"跳过已下载的图片: {skip_existing}")
        
        # 批量下载
        stats = await download_images_batch(
            cases,
            image_service,
            semaphore,
            skip_existing=skip_existing
        )
        
        # 打印统计信息
        logger.info("=" * 60)
        logger.info("下载完成！统计信息：")
        logger.info(f"  总数: {stats['total']}")
        logger.info(f"  成功: {stats['success']}")
        logger.info(f"  失败: {stats['failed']}")
        logger.info(f"  跳过: {stats['skipped']}")
        logger.info("=" * 60)
        
        # 如果有错误，打印前10个错误
        if stats['errors']:
            logger.warning(f"失败案例（前10个）:")
            for error in stats['errors'][:10]:
                logger.warning(f"  case_id={error['case_id']}, url={error['url']}, error={error['error']}")
            if len(stats['errors']) > 10:
                logger.warning(f"  ... 还有 {len(stats['errors']) - 10} 个失败案例")
        
    except Exception as e:
        logger.error(f"批量下载过程中发生错误: {e}", exc_info=True)
        raise
    finally:
        # 断开数据库连接
        await db.disconnect()
        logger.info("数据库连接已关闭")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断下载")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        sys.exit(1)
