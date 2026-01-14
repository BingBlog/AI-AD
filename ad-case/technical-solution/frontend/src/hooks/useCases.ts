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

  const params = buildParams(searchParams);

  const queryResult = useQuery({
    queryKey: ['cases', params],
    queryFn: () => searchCases(params),
    staleTime: 30 * 1000, // 30 秒
    // 允许在没有查询条件时也执行查询（显示所有案例或默认数据）
    enabled: true,
  });

  // 调试信息（开发环境）
  if (process.env.NODE_ENV === 'development') {
    console.log('useCases - Query params:', params);
    console.log('useCases - Query result:', queryResult);
  }

  return queryResult;
};
