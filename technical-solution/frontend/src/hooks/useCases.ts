/**
 * 案例数据获取 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { searchCases } from '@/services/caseService';
import type { SearchParams } from '@/types/case';
import { useSearchStore } from '@/store/searchStore';

/**
 * 获取案例列表
 */
export const useCases = () => {
  const searchParams = useSearchStore();

  // 构建查询参数（移除空值）
  const buildParams = (params: typeof searchParams): SearchParams => {
    const result: SearchParams = {
      search_type: params.search_type || 'keyword',
      sort_by: params.sort_by || 'relevance',
      sort_order: params.sort_order || 'desc',
      page: params.page || 1,
      page_size: params.page_size || 20,
    };

    if (params.query) result.query = params.query;
    if (params.semantic_query) result.semantic_query = params.semantic_query;
    if (params.min_similarity !== undefined) result.min_similarity = params.min_similarity;
    if (params.brand_name) result.brand_name = params.brand_name;
    if (params.brand_industry) result.brand_industry = params.brand_industry;
    if (params.activity_type) result.activity_type = params.activity_type;
    if (params.location) result.location = params.location;
    if (params.tags && params.tags.length > 0) result.tags = params.tags;
    if (params.start_date) result.start_date = params.start_date;
    if (params.end_date) result.end_date = params.end_date;
    if (params.min_score) result.min_score = params.min_score;

    return result;
  };

  // 验证搜索参数
  const validateParams = (params: typeof searchParams): { valid: boolean; error?: string } => {
    const searchType = params.search_type || 'keyword';
    
    // 语义检索：必须提供语义查询文本
    if (searchType === 'semantic') {
      if (!params.semantic_query || !params.semantic_query.trim()) {
        return { valid: false, error: '语义检索需要输入查询文本' };
      }
    }
    
    // 混合检索：必须提供关键词或语义查询文本
    if (searchType === 'hybrid') {
      const hasQuery = params.query && params.query.trim();
      const hasSemanticQuery = params.semantic_query && params.semantic_query.trim();
      if (!hasQuery && !hasSemanticQuery) {
        return { valid: false, error: '混合检索需要输入关键词或语义查询文本' };
      }
    }
    
    return { valid: true };
  };

  const params = buildParams(searchParams);
  const validation = validateParams(searchParams);

  const queryResult = useQuery({
    queryKey: ['cases', params],
    queryFn: () => searchCases(params),
    staleTime: 30 * 1000, // 30 秒
    // 验证失败时不发送请求
    enabled: validation.valid,
    retry: false, // 错误不重试
  });

  // 调试信息（开发环境）
  if (process.env.NODE_ENV === 'development') {
    console.log('useCases - Query params:', params);
    console.log('useCases - Query result:', queryResult);
  }

  // 添加验证错误信息到查询结果中（用于UI显示）
  return {
    ...queryResult,
    validationError: validation.valid ? undefined : validation.error,
  };
};
