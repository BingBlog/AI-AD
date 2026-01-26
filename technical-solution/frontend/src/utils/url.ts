/**
 * URL 工具函数
 */

/**
 * 将广告门移动端 URL 转换为 PC 端 URL
 * @param url 原始 URL（可能是移动端或 PC 端）
 * @returns PC 端 URL
 */
export function convertToPcUrl(url: string): string {
  if (!url) return url;

  try {
    // 如果已经是 PC 端 URL，直接返回
    if (url.includes('www.adquan.com/article/')) {
      return url;
    }

    // 处理移动端 URL
    if (url.includes('m.adquan.com')) {
      // 提取文章 ID
      // 格式1: https://m.adquan.com/creative/detail/297041
      // 格式2: https://m.adquan.com/case2/detail-291696
      // 格式3: 其他可能的格式
      
      let articleId: string | null = null;

      // 尝试格式1: /creative/detail/{id}
      const match1 = url.match(/\/creative\/detail\/(\d+)/);
      if (match1) {
        articleId = match1[1];
      } else {
        // 尝试格式2: /case2/detail-{id}
        const match2 = url.match(/\/case2\/detail-(\d+)/);
        if (match2) {
          articleId = match2[1];
        } else {
          // 尝试从 URL 中提取任何数字 ID（作为最后的手段）
          const match3 = url.match(/(\d+)(?:\?|$)/);
          if (match3) {
            articleId = match3[1];
          }
        }
      }

      if (articleId) {
        return `https://www.adquan.com/article/${articleId}`;
      }
    }

    // 如果无法转换，返回原 URL
    return url;
  } catch (error) {
    console.error('URL 转换失败:', error);
    return url;
  }
}
