/**
 * 案例相关 API 服务
 */
import api from '@/utils/request';
import type {
  SearchParams,
  SearchResponse,
  Case,
  Facets,
} from '@/types/case';
import type { BaseResponse } from '@/types/api';

/**
 * 案例检索
 */
export const searchCases = async (
  params: SearchParams
): Promise<SearchResponse> => {
  // 响应拦截器已经处理了 BaseResponse，直接返回 data
  // baseURL 是 /api，所以路径只需要 /v1/cases/search
  const response = await api.get<BaseResponse<SearchResponse>>(
    '/v1/cases/search',
    { params }
  );
  return response;
};

/**
 * 获取案例详情
 */
export const getCaseDetail = async (caseId: number): Promise<Case> => {
  const response = await api.get<BaseResponse<Case>>(`/v1/cases/${caseId}`);
  return response;
};

/**
 * 获取筛选选项
 */
export const getFilters = async (): Promise<Facets> => {
  try {
    const response = await api.get<BaseResponse<Facets>>('/v1/cases/filters');
    return response;
  } catch (error) {
    // 如果接口未实现，返回空数据
    console.warn('获取筛选选项失败，返回空数据', error);
    return {
      brands: [],
      industries: [],
      activity_types: [],
      tags: [],
      locations: [],
    };
  }
};

/**
 * 统计信息接口
 */
export interface Stats {
  total_cases: number;
  total_brands: number;
  total_industries: number;
  total_tags: number;
  cases_with_vectors?: number;
  latest_case_date?: string;
  oldest_case_date?: string;
}

/**
 * 获取统计信息
 */
export const getStats = async (): Promise<Stats> => {
  try {
    const response = await api.get<BaseResponse<Stats>>('/v1/cases/stats');
    return response;
  } catch (error) {
    // 如果接口未实现，返回空数据
    console.warn('获取统计信息失败，返回空数据', error);
    return {
      total_cases: 0,
      total_brands: 0,
      total_industries: 0,
      total_tags: 0,
    };
  }
};
