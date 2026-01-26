/**
 * 搜索状态管理
 */
import { create } from 'zustand';
import type { SearchParams } from '@/types/case';

interface SearchState extends SearchParams {
  // 从 API 响应中获取的总数（用于显示）
  total?: number;
  
  // Actions
  setQuery: (query: string) => void;
  setSemanticQuery: (semanticQuery: string) => void;
  setSearchType: (searchType: SearchParams['search_type']) => void;
  setMinSimilarity: (minSimilarity: number) => void;
  setFilters: (filters: Partial<SearchParams>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setSortBy: (sortBy: SearchParams['sort_by']) => void;
  setSortOrder: (sortOrder: SearchParams['sort_order']) => void;
  setTotal: (total: number) => void;
}

const initialState: SearchParams = {
  query: '',
  semantic_query: '',
  search_type: 'keyword',
  min_similarity: 0.5,
  sort_by: 'relevance',
  sort_order: 'desc',
  page: 1,
  page_size: 20,
};

export const useSearchStore = create<SearchState>((set) => ({
  ...initialState,
  
  setQuery: (query) => set({ query, page: 1 }),
  
  setSemanticQuery: (semanticQuery) => set({ semantic_query: semanticQuery, page: 1 }),
  
  setSearchType: (searchType) => set({ search_type: searchType, page: 1 }),
  
  setMinSimilarity: (minSimilarity) => set({ min_similarity: minSimilarity, page: 1 }),
  
  setFilters: (filters) => set((state) => ({
    ...state,
    ...filters,
    page: 1, // 重置到第一页
  })),
  
  resetFilters: () => set(initialState),
  
  setPage: (page) => set({ page }),
  
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  
  setSortBy: (sortBy) => set({ sortBy }),
  
  setSortOrder: (sortOrder) => set({ sortOrder }),
  
  setTotal: (total) => set({ total }),
}));
