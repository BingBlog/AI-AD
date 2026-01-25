"""
图片下载服务
用于下载和存储案例的主图
"""
import logging
import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
from app.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """图片下载服务类"""
    
    def __init__(self):
        """初始化图片服务"""
        self.storage_dir = Path(settings.IMAGE_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = aiohttp.ClientTimeout(total=settings.IMAGE_DOWNLOAD_TIMEOUT)
        self.retry_count = settings.IMAGE_DOWNLOAD_RETRY
    
    def _get_image_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """
        获取图片扩展名
        
        Args:
            url: 图片 URL
            content_type: HTTP Content-Type 头
            
        Returns:
            图片扩展名（如 .png, .jpg）
        """
        # 优先从 URL 提取扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            ext = path.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return ext
        
        # 从 Content-Type 判断
        if content_type:
            if 'jpeg' in content_type or 'jpg' in content_type:
                return 'jpg'
            elif 'png' in content_type:
                return 'png'
            elif 'gif' in content_type:
                return 'gif'
            elif 'webp' in content_type:
                return 'webp'
        
        # 默认使用 jpg
        return 'jpg'
    
    def _get_image_path(self, case_id: int, ext: str) -> Path:
        """
        获取图片存储路径
        
        Args:
            case_id: 案例 ID
            ext: 图片扩展名
            
        Returns:
            图片文件路径
        """
        case_dir = self.storage_dir / str(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir / f"main_image.{ext}"
    
    def _get_local_image_url(self, case_id: int, ext: str) -> str:
        """
        生成本地图片访问 URL
        
        Args:
            case_id: 案例 ID
            ext: 图片扩展名
            
        Returns:
            本地图片 URL
        """
        return f"{settings.IMAGE_STATIC_URL_PREFIX}/{case_id}/main_image.{ext}"
    
    async def download_image(
        self,
        url: str,
        case_id: int,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        下载图片到本地
        
        Args:
            url: 图片 URL
            case_id: 案例 ID
            session: aiohttp 会话（可选，如果不提供则创建新会话）
            
        Returns:
            (是否成功, 本地图片路径, 错误信息)
        """
        if not url or not url.strip():
            return False, None, "URL 为空"
        
        url = url.strip()
        
        # 设置请求头，模拟浏览器请求以绕过防盗链
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.adquan.com/'
        }
        
        # 重试逻辑
        last_error = None
        for attempt in range(self.retry_count):
            try:
                # 如果提供了 session，使用它；否则创建新会话
                if session:
                    async with session.get(url, headers=headers, timeout=self.timeout) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            image_data = await response.read()
                            
                            # 确定扩展名
                            ext = self._get_image_extension(url, content_type)
                            
                            # 保存图片
                            image_path = self._get_image_path(case_id, ext)
                            image_path.write_bytes(image_data)
                            
                            # 生成本地 URL
                            local_url = self._get_local_image_url(case_id, ext)
                            
                            logger.info(f"成功下载图片: case_id={case_id}, url={url}, path={image_path}")
                            return True, local_url, None
                        else:
                            error_msg = f"HTTP {response.status}: {url}"
                            logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.retry_count}): {error_msg}")
                            last_error = error_msg
                            
                            # 如果不是 4xx 错误，可以重试
                            if response.status < 400 or response.status >= 500:
                                if attempt < self.retry_count - 1:
                                    await asyncio.sleep(2 ** attempt)  # 指数退避
                                    continue
                            else:
                                # 4xx 错误不重试
                                break
                else:
                    # 创建新会话
                    async with aiohttp.ClientSession() as new_session:
                        async with new_session.get(url, headers=headers, timeout=self.timeout) as response:
                            if response.status == 200:
                                content_type = response.headers.get('Content-Type', '')
                                image_data = await response.read()
                                
                                ext = self._get_image_extension(url, content_type)
                                image_path = self._get_image_path(case_id, ext)
                                image_path.write_bytes(image_data)
                                
                                local_url = self._get_local_image_url(case_id, ext)
                                
                                logger.info(f"成功下载图片: case_id={case_id}, url={url}, path={image_path}")
                                return True, local_url, None
                            else:
                                error_msg = f"HTTP {response.status}: {url}"
                                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.retry_count}): {error_msg}")
                                last_error = error_msg
                                
                                if response.status < 400 or response.status >= 500:
                                    if attempt < self.retry_count - 1:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                else:
                                    break
                                    
            except asyncio.TimeoutError:
                error_msg = f"下载超时: {url}"
                logger.warning(f"下载超时 (尝试 {attempt + 1}/{self.retry_count}): {error_msg}")
                last_error = error_msg
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except aiohttp.ClientError as e:
                error_msg = f"网络错误: {type(e).__name__}: {e}"
                logger.warning(f"网络错误 (尝试 {attempt + 1}/{self.retry_count}): {error_msg}")
                last_error = error_msg
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                error_msg = f"未知错误: {type(e).__name__}: {e}"
                logger.error(f"下载图片时发生错误: {error_msg}")
                return False, None, error_msg
        
        return False, None, last_error or "下载失败"
    
    def is_image_downloaded(self, case_id: int) -> Tuple[bool, Optional[str]]:
        """
        检查图片是否已下载
        
        Args:
            case_id: 案例 ID
            
        Returns:
            (是否已下载, 本地图片路径)
        """
        case_dir = self.storage_dir / str(case_id)
        if not case_dir.exists():
            return False, None
        
        # 检查常见扩展名
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            image_path = case_dir / f"main_image.{ext}"
            if image_path.exists():
                local_url = self._get_local_image_url(case_id, ext)
                return True, local_url
        
        return False, None
    
    def get_local_image_url(self, case_id: int) -> Optional[str]:
        """
        获取本地图片 URL（如果已下载）
        
        Args:
            case_id: 案例 ID
            
        Returns:
            本地图片 URL，如果未下载则返回 None
        """
        is_downloaded, local_url = self.is_image_downloaded(case_id)
        return local_url if is_downloaded else None
