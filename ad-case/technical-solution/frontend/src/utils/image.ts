/**
 * 图片URL处理工具
 */

/**
 * 将缩略图URL转换为原图URL
 * 广告门平台的图片URL通常包含缩略图参数，需要移除或替换
 */
export const getOriginalImageUrl = (url: string | undefined): string | undefined => {
  if (!url) return undefined;

  try {
    const imageUrl = new URL(url);

    // 广告门平台的图片URL模式：
    // 1. 缩略图通常包含尺寸参数，如 ?w=200&h=200
    // 2. 缩略图文件名可能包含 _thumb, _small, _mini 等后缀
    // 3. 原图通常没有这些参数或后缀

    // 1. 移除查询参数中的尺寸限制
    const paramsToRemove = ['w', 'h', 'width', 'height', 'size', 'thumb', 'scale'];
    paramsToRemove.forEach(param => {
      imageUrl.searchParams.delete(param);
    });

    // 2. 替换缩略图文件名模式
    let pathname = imageUrl.pathname;
    
    // 替换常见的缩略图模式（保持文件扩展名）
    pathname = pathname.replace(/_thumb\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    pathname = pathname.replace(/thumb\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    pathname = pathname.replace(/_small\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    pathname = pathname.replace(/small\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    pathname = pathname.replace(/_mini\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    pathname = pathname.replace(/_thumbnail\.(jpg|jpeg|png|webp|gif)$/i, '.$1');
    
    // 3. 对于广告门平台，如果URL包含特定路径，可能需要调整
    // 例如：/uploads/thumb/xxx.jpg -> /uploads/xxx.jpg
    pathname = pathname.replace(/\/thumb\//, '/');
    pathname = pathname.replace(/\/thumbnail\//, '/');
    pathname = pathname.replace(/\/small\//, '/');
    
    imageUrl.pathname = pathname;

    return imageUrl.toString();
  } catch (error) {
    // 如果URL解析失败，返回原URL
    console.warn('Failed to parse image URL:', url, error);
    return url;
  }
};

/**
 * 获取图片代理URL（如果需要绕过防盗链）
 * 如果图片有防盗链保护，可以通过后端代理访问
 */
export const getProxiedImageUrl = (url: string | undefined): string | undefined => {
  if (!url) return undefined;
  
  // 如果图片URL是外部链接，可以通过后端代理
  // 格式：/api/proxy/image?url=原始URL
  try {
    const imageUrl = new URL(url);
    // 如果是广告门域名的图片，可能需要代理
    if (imageUrl.hostname.includes('adquan.com')) {
      return `/api/proxy/image?url=${encodeURIComponent(url)}`;
    }
  } catch (error) {
    // URL解析失败，返回原URL
  }
  
  return url;
};

/**
 * 获取图片显示URL（优先使用原图，如果失败则使用缩略图）
 */
export const getImageDisplayUrl = (
  originalUrl: string | undefined,
  fallbackUrl?: string | undefined
): string | undefined => {
  // 优先使用原图URL
  if (originalUrl) {
    const original = getOriginalImageUrl(originalUrl);
    if (original) return original;
  }
  
  // 如果没有原图，使用备用URL
  if (fallbackUrl) {
    return getOriginalImageUrl(fallbackUrl) || fallbackUrl;
  }
  
  return originalUrl;
};
